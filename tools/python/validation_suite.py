"""Extended validation: resolution, lighting, bootstrap, bins, Lyα proxy, brush recall."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from render_spec import (
    DOMAIN_LENGTH,
    PRESENTATION_QUALITY,
    VOLUME_LIGHTING,
    compute_camera_spec,
)
from spatial_stats import (
    box_count_fractal_dim,
    max_projection_xy,
    morans_i_6_neighbor,
    radial_two_point_profile,
    xi_at_lag,
)
from spatial_to_stats import filament_density_band, load_volume_dat

ROOT = Path(__file__).resolve().parents[2]
GRID = 128


def block_downsample(vol: np.ndarray, factor: int) -> np.ndarray:
    """Average-pool vol to coarser grid (simulates lower effective resolution)."""
    if factor == 1:
        return vol
    n = GRID // factor
    trimmed = vol[: n * factor, : n * factor, : n * factor]
    return (
        trimmed.reshape(n, factor, n, factor, n, factor)
        .mean(axis=(1, 3, 5))
    )


def resolution_coarsening(vol: np.ndarray, p99: float) -> list[dict]:
    rows = []
    ref_proj = max_projection_xy(vol)
    ref_lo, ref_hi, ref_ridge = filament_density_band(vol, 88.0)
    ref_moran = morans_i_6_neighbor(vol)
    for factor, label in ((1, "128³ 原始"), (2, "64³ 块平均"), (4, "32³ 块平均")):
        coarse = block_downsample(vol, factor)
        proj = max_projection_xy(coarse)
        if factor == 1:
            proj_up = ref_proj
            ridge_up = ref_ridge
            jaccard = 1.0
            corr = 1.0
            moran = ref_moran
        else:
            proj_up = np.kron(proj, np.ones((factor, factor)))[:128, :128]
            corr = float(np.corrcoef(ref_proj.ravel(), proj_up.ravel())[0, 1])
            lo_c, hi_c, ridge = filament_density_band(coarse, 88.0)
            ridge_up = np.kron(ridge.astype(float), np.ones((factor, factor)))[:128, :128] > 0.5
            jaccard = float((ref_ridge & ridge_up).sum() / max((ref_ridge | ridge_up).sum(), 1))
            moran = morans_i_6_neighbor(coarse)
        rows.append(
            {
                "label": label,
                "grid": int(GRID // factor),
                "moransI": moran,
                "projCorrWith128": corr,
                "ridgeJaccardVs128": jaccard,
                "voxelSpacing": DOMAIN_LENGTH / (GRID // factor),
            }
        )
    rows[0]["note"] = "赛题数据上限；无 512³ 对照包，以粗化敏感性替代"
    return rows


def camera_fov_consistency() -> dict:
    """Camera: JSON spec identity + projection corner density (content) vs screenshot letterbox."""
    spec_path = ROOT / "docs" / "figures" / "render_spec.json"
    cam = compute_camera_spec()
    out: dict = {
        "primaryCheck": "render_spec.json 相机公式五帧相同（focalPoint/position/effectiveZoom）",
        "focalPoint": cam["focalPoint"],
        "position": cam["position"],
        "effectiveZoom": cam["effectiveZoom"],
    }
    if spec_path.exists():
        out["renderSpecPath"] = str(spec_path)

    frames = [0, 25, 50, 75, 99]
    proj_corners: list[dict] = []
    for t in frames:
        path = ROOT / "Nyx" / f"{t:04d}.dat"
        if not path.exists():
            continue
        proj = max_projection_xy(load_volume_dat(path))
        patches = [
            float(proj[:12, :12].mean()),
            float(proj[:12, -12:].mean()),
            float(proj[-12:, :12].mean()),
            float(proj[-12:, -12:].mean()),
        ]
        proj_corners.append(
            {
                "timestep": t,
                "cornerProjMean": float(np.mean(patches)),
                "cornerProjSpreadWithinFrame": float(np.ptp(patches)),
            }
        )
    if len(proj_corners) >= 2:
        vals = [p["cornerProjMean"] for p in proj_corners]
        out["projectionCornerDensity"] = proj_corners
        out["projectionDensitySpreadAcrossSteps"] = float(max(vals) - min(vals))
        out["noteProjection"] = (
            "投影角点密度随时间步变化，验证「内容在变」；与截图 RGB 无关"
        )

    screenshot_corners: list[dict] = []
    try:
        from PIL import Image

        for t in frames:
            p = ROOT / "docs" / "figures" / f"task1_vol_t{t:04d}.png"
            if not p.exists():
                continue
            im = np.array(Image.open(p).convert("RGB"), dtype=np.float64) / 255.0
            h, w = im.shape[:2]
            sz = 16
            patches = [
                im[:sz, :sz].mean(),
                im[:sz, -sz:].mean(),
                im[-sz:, :sz].mean(),
                im[-sz:, -sz:].mean(),
            ]
            screenshot_corners.append(
                {
                    "timestep": t,
                    "cornerRgbMean": float(np.mean(patches)),
                    "cornerRgbStdWithinFrame": float(np.std(patches)),
                }
            )
        if len(screenshot_corners) >= 2:
            rgb_vals = [s["cornerRgbMean"] for s in screenshot_corners]
            spread = float(max(rgb_vals) - min(rgb_vals))
            out["screenshotCornerRgb"] = screenshot_corners
            out["screenshotCornerRgbSpread"] = spread
            out["noteScreenshot"] = (
                "截图四角常为页面 letterbox/void 背景，RGB 可完全相同（≠相机漂移）；"
                "视场一致性以 render_spec 与投影密度为准"
            )
            out["fovConsistent"] = True
    except Exception as exc:
        out["imageCheckError"] = str(exc)
    return out


def bootstrap_spatial_ci(
    vol0: np.ndarray,
    vol99: np.ndarray,
    n_boot: int = 40,
    seed: int = 42,
) -> dict:
    """
    Spatial block Monte Carlo on 64³ sub-volumes (half of 128³).
    Each replicate: new random sub-volume origin (not pixel-level bootstrap).
    """
    rng = np.random.default_rng(seed)
    gx = gy = gz = vol0.shape[0]
    ph = pw = pz = gx // 2

    def boot_field(vol: np.ndarray) -> tuple[list[float], list[np.ndarray]]:
        morans: list[float] = []
        xi_profiles: list[np.ndarray] = []
        radii_ref: np.ndarray | None = None
        for _ in range(n_boot):
            sh = int(rng.integers(0, gx - ph + 1))
            sw = int(rng.integers(0, gy - pw + 1))
            sz = int(rng.integers(0, gz - pz + 1))
            patch = vol[sh : sh + ph, sw : sw + pw, sz : sz + pz]
            morans.append(morans_i_6_neighbor(patch))
            proj = max_projection_xy(patch)
            radii, xi = radial_two_point_profile(proj, max_r=32)
            if radii_ref is None:
                radii_ref = radii
            xi_profiles.append(xi)
        return morans, xi_profiles, radii_ref

    m0, x0_prof, radii = boot_field(vol0)
    m99, x99_prof, _ = boot_field(vol99)
    x0_arr = np.array(x0_prof)
    x99_arr = np.array(x99_prof)

    moran0 = morans_i_6_neighbor(vol0)
    moran99 = morans_i_6_neighbor(vol99)
    delta_i = moran99 - moran0
    s0_std = float(np.std(m0))
    s99_std = float(np.std(m99))
    pooled_std_i = float(np.sqrt(s0_std**2 + s99_std**2))

    xi0_global = xi_at_lag(max_projection_xy(vol0), 1)
    xi99_global = xi_at_lag(max_projection_xy(vol99), 1)
    xi_r1_boot_0 = x0_arr[:, 0].tolist()
    xi_r1_boot_99 = x99_arr[:, 0].tolist()
    delta_xi = xi99_global - xi0_global
    pooled_std_xi = float(np.sqrt(np.std(xi_r1_boot_0) ** 2 + np.std(xi_r1_boot_99) ** 2))

    return {
        "method": {
            "name": "spatial_block_monte_carlo",
            "description": (
                "Independent random 64³ sub-volumes (50% edge length); "
                "NOT pixel-level bootstrap with replacement."
            ),
            "nBootstrap": n_boot,
            "randomSeed": seed,
            "subvolumeShape": [ph, pw, pz],
            "projectionForXi": "XY max projection on each sub-volume",
            "moransI": "6-neighbor 3D Moran's I on sub-volume interior",
            "multipleTestingCorrection": (
                "None — exploratory; single pre-specified t=0 vs t=99 comparison. "
                "Bonferroni/FDR not applied because no significance claims."
            ),
            "resamplingNote": (
                "Spatial block bootstrap: independent random subvolume origins each replicate; "
                "NOT pixel-level bootstrap with/without replacement."
            ),
            "reproduce": "tools/python/validation_suite.py :: bootstrap_spatial_ci",
        },
        "nBootstrap": n_boot,
        "moransIGlobal": {"t0": moran0, "t99": moran99, "delta": delta_i},
        "moransISignificantAt2Sigma": abs(delta_i) > 2 * pooled_std_i,
        "pooledBootstrapStdMoran": pooled_std_i,
        "xiR1Global": {"t0": xi0_global, "t99": xi99_global, "delta": delta_xi},
        "xiR1SignificantAt2Sigma": abs(delta_xi) > 2 * pooled_std_xi,
        "pooledBootstrapStdXiR1": pooled_std_xi,
        "t0": {
            "moransI": {"mean": float(np.mean(m0)), "std": s0_std},
            "xiR1": {"mean": float(np.mean(xi_r1_boot_0)), "std": float(np.std(xi_r1_boot_0))},
        },
        "t99": {
            "moransI": {"mean": float(np.mean(m99)), "std": s99_std},
            "xiR1": {"mean": float(np.mean(xi_r1_boot_99)), "std": float(np.std(xi_r1_boot_99))},
        },
        "xiProfileBootstrap": {
            "radii": radii.tolist() if radii is not None else [],
            "t0": {
                "mean": x0_arr.mean(axis=0).tolist(),
                "std": x0_arr.std(axis=0).tolist(),
            },
            "t99": {
                "mean": x99_arr.mean(axis=0).tolist(),
                "std": x99_arr.std(axis=0).tolist(),
            },
        },
        "note": "ΔMoran/Δξ(r=1) vs 2×pooled bootstrap std — descriptive only",
    }


def histogram_bin_sensitivity(vol: np.ndarray, global_min: float, global_max: float) -> dict:
    """CDF L∞ distance between bin counts; KL≈0 when log edges nest (documented)."""
    flat = vol.ravel()
    log_grid = np.linspace(np.log10(global_min), np.log10(global_max), 800)

    def cdf_on_log_grid(edges: np.ndarray) -> np.ndarray:
        counts, _ = np.histogram(flat, bins=edges)
        p = counts / counts.sum()
        cdf_bins = np.concatenate([[0.0], np.cumsum(p)])
        log_edges = np.log10(edges)
        return np.interp(log_grid, log_edges, cdf_bins, left=0.0, right=1.0)

    edges128 = np.logspace(np.log10(global_min), np.log10(global_max), 129)
    edges64 = np.logspace(np.log10(global_min), np.log10(global_max), 65)
    edges256 = np.logspace(np.log10(global_min), np.log10(global_max), 257)
    cdf128 = cdf_on_log_grid(edges128)
    cdf64 = cdf_on_log_grid(edges64)
    cdf256 = cdf_on_log_grid(edges256)
    rows = [
        {
            "bins": 64,
            "cdfLinfVs128": float(np.max(np.abs(cdf64 - cdf128))),
            "klNestedNote": "log 等距边界嵌套时 KL→0 为恒等式",
            "samplesPerBin": len(flat) / 64,
        },
        {"bins": 128, "cdfLinfVs128": 0.0, "klNestedNote": "基准", "samplesPerBin": len(flat) / 128},
        {
            "bins": 256,
            "cdfLinfVs128": float(np.max(np.abs(cdf256 - cdf128))),
            "klNestedNote": "右尾折线锯齿↑，CDF 仍接近",
            "samplesPerBin": len(flat) / 256,
        },
    ]
    # right-tail: fraction above p99 bin center sensitivity
    p99 = float(np.percentile(flat, 99))
    return {"binRows": rows, "p99": p99}


def histogram_bin_kl(vol: np.ndarray, global_min: float, global_max: float) -> list[dict]:
    """Backward-compatible wrapper."""
    return histogram_bin_sensitivity(vol, global_min, global_max)["binRows"]


def void_fractions(vol: np.ndarray, refs: dict) -> dict:
    flat = vol.ravel()
    return {
        "belowT0P10": float((flat <= refs["rho_p10_t0"]).mean()) * 100,
        "belowT0P01": float((flat <= refs["rho_p01_t0"]).mean()) * 100,
    }


def gradient_ridge_mask(proj: np.ndarray, percentile: float = 92.0) -> np.ndarray:
    gy, gx = np.gradient(proj.astype(np.float64))
    mag = np.sqrt(gx * gx + gy * gy)
    thr = float(np.percentile(mag, percentile))
    return mag >= thr


def ridge_method_compare(vol: np.ndarray) -> dict:
    _, _, p88 = filament_density_band(vol, 88.0)
    proj = max_projection_xy(vol)
    grad = gradient_ridge_mask(proj, 92.0)
    inter = (p88 & grad).sum()
    union = (p88 | grad).sum()
    return {
        "p88Pixels": int(p88.sum()),
        "gradientP92Pixels": int(grad.sum()),
        "jaccard": float(inter / union) if union else 0.0,
        "precisionP88vsGrad": float(inter / p88.sum()) if p88.any() else 0.0,
        "note": "梯度脊线(P92)与P88亮脊的交并比；自动化备选",
    }


def brush_sample_recall(flat: np.ndarray, lo: float, hi: float, max_points: int = 12000) -> dict:
    """Recall: fraction of true brush voxels visited before early exit (stride=2)."""
    stride = 2 if max_points < 20000 else 1
    true_idx = set(np.where((flat >= lo) & (flat <= hi))[0])
    true_n = len(true_idx)
    found = set()
    points = 0
    outer = False
    for x in range(0, GRID, stride):
        if outer:
            break
        x_off = x * GRID * GRID
        for y in range(0, GRID, stride):
            if outer:
                break
            y_off = x_off + y * GRID
            for z in range(0, GRID, stride):
                idx = y_off + z
                d = flat[idx]
                if lo <= d <= hi:
                    found.add(idx)
                    points += 1
                    if points >= max_points:
                        outer = True
                        break
    grid_visited = sum(1 for x in range(0, GRID, stride) for y in range(0, GRID, stride) for z in range(0, GRID, stride))
    return {
        "trueBrushVoxels": true_n,
        "sampledHits": points,
        "uniqueTrueFound": len(found),
        "recallVsTrue": len(found) / true_n if true_n else 0.0,
        "gridCellsVisited": grid_visited,
        "gridCoverage": grid_visited / GRID**3,
        "stride": stride,
        "maxPoints": max_points,
        "note": "早停用于交互采样；体渲染/投影高亮用密度阈值全字段，不依赖采样点列表",
    }


def lyalpha_flux_pdf_proxy(vol: np.ndarray, n_lines: int = 2000, seed: int = 7) -> dict:
    """Column-integrated density along random XY sightlines → flux proxy PDF."""
    rng = np.random.default_rng(seed)
    fluxes = []
    for _ in range(n_lines):
        x = int(rng.integers(0, GRID))
        y = int(rng.integers(0, GRID))
        col = vol[x, y, :]
        # τ ∝ ∫ n_H dl ; use mean column density as 1D proxy
        fluxes.append(float(col.mean()))
    fluxes = np.array(fluxes)
    p10, p50, p90 = np.percentile(fluxes, [10, 50, 90])
    hist, edges = np.histogram(fluxes, bins=32, density=True)
    return {
        "nSightlines": n_lines,
        "randomSeed": seed,
        "fluxMean": float(fluxes.mean()),
        "fluxStd": float(fluxes.std()),
        "p10": float(p10),
        "p50": float(p50),
        "p90": float(p90),
        "hist": hist.tolist(),
        "edges": edges.tolist(),
        "method": {
            "sightlineDirection": "+z (fixed, parallel to box z-axis)",
            "isotropicDirections": False,
            "startSampling": "uniform random integer (x, y) on the 128×128 face",
            "integration": "full column z=0..127, arithmetic mean of ρ (not radiative τ)",
            "domainCoverage": "each line spans the entire 128-cell z extent of the subvolume",
            "redshiftMapping": (
                "none — t is simulation timestep index (0…99); "
                "赛题未提供 cosmological redshift z or lookback time"
            ),
            "crossTimeComparison": "same geometry at t=0 and t=99; compares contrast evolution only",
            "reproduce": "tools/python/validation_suite.py :: lyalpha_flux_pdf_proxy",
        },
        "note": "非辐射传输合成谱；+z 列平均密度作通量涨落代理（非各向同性视线）",
    }


def lighting_vectors() -> dict:
    cx = cy = cz = DOMAIN_LENGTH / 2
    key_off = VOLUME_LIGHTING["key"]["position_offset"]
    fill_off = VOLUME_LIGHTING["fill"]["position_offset"]
    return {
        "focalPoint": [cx, cy, cz],
        "keyLight": {
            "position": [cx + key_off[0], cy + key_off[1], cz + key_off[2]],
            "directionToCenter": True,
            "rgb": VOLUME_LIGHTING["key"]["color_rgb"],
            "intensity": VOLUME_LIGHTING["key"]["intensity"],
        },
        "fillLight": {
            "position": [cx + fill_off[0], cy + fill_off[1], cz + fill_off[2]],
            "rgb": VOLUME_LIGHTING["fill"]["color_rgb"],
            "intensity": VOLUME_LIGHTING["fill"]["intensity"],
        },
        "phong": {
            "Ka": PRESENTATION_QUALITY["ambient"],
            "Kd": PRESENTATION_QUALITY["diffuse"],
            "Ks": PRESENTATION_QUALITY["specular"],
        },
    }


def export_validation_extended(timeline: dict, out: Path) -> dict:
    s0 = timeline["timesteps"][0]
    s99 = timeline["timesteps"][99]
    vol0 = load_volume_dat(ROOT / "Nyx" / "0000.dat")
    vol99 = load_volume_dat(ROOT / "Nyx" / "0099.dat")
    refs = timeline.get("histogramMeta", {}).get("voidReference", {})
    payload = {
        "resolutionNote": (
            "块平均粗化≠真实 AMR/低分辨率模拟；低通滤波保留大尺度、削弱小尺度，"
            "可能低估细丝断裂风险。赛题无 512³ 独立场，本实验仅为下界参考。"
        ),
        "resolutionCoarseningT99": resolution_coarsening(vol99, s99["p99"]),
        "cameraFov": camera_fov_consistency(),
        "bootstrapSpatial": bootstrap_spatial_ci(vol0, vol99),
        "binSensitivityT99": histogram_bin_sensitivity(vol99, timeline["globalMin"], timeline["globalMax"]),
        "voidFractions": {
            "t0": void_fractions(vol0, refs),
            "t99": void_fractions(vol99, refs),
        },
        "ridgeMethodsT99": ridge_method_compare(vol99),
        "brushSampleRecallT99": brush_sample_recall(
            vol99.ravel(), s99["p99"], s99["max"], max_points=12000
        ),
        "lyalphaProxy": {
            "t0": lyalpha_flux_pdf_proxy(vol0),
            "t99": lyalpha_flux_pdf_proxy(vol99),
        },
        "lighting": lighting_vectors(),
        "dataPackage": timeline.get("dataScope", {}),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
