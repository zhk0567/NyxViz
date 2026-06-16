"""Volume render spec mirrored from src/volume/renderSpec.ts for docs and figures."""
from __future__ import annotations

import json
import math
from pathlib import Path

DOMAIN_LENGTH = 14.245
GRID = 128
SPACING = DOMAIN_LENGTH / GRID
VIEW_MARGIN = 0.88
CAMERA_DISTANCE_FACTOR = 1.75
CAMERA_OFFSET = (0.92, 0.78, 0.68)
CAPTURE_CAMERA_ZOOM = 1.24
CAPTURE_ASPECT = 1920 / 1080

COSMIC_COLOR_STOPS = [
    (0.0, (0.02, 0.03, 0.10)),
    (0.15, (0.04, 0.08, 0.28)),
    (0.35, (0.12, 0.20, 0.48)),
    (0.55, (0.24, 0.55, 0.72)),
    (0.72, (0.55, 0.42, 0.78)),
    (0.85, (0.85, 0.65, 0.42)),
    (1.0, (0.98, 0.92, 0.78)),
]

CINEMATIC_COLOR_STOPS = [
    (0.0, (0.01, 0.02, 0.06)),
    (0.12, (0.02, 0.04, 0.12)),
    (0.25, (0.04, 0.07, 0.20)),
    (0.45, (0.15, 0.22, 0.55)),
    (0.65, (0.35, 0.48, 0.78)),
    (0.80, (0.95, 0.72, 0.35)),
    (0.88, (1.0, 0.82, 0.42)),
    (0.92, (1.0, 0.90, 0.58)),
    (0.96, (1.0, 0.96, 0.86)),
    (1.0, (1.0, 1.0, 0.96)),
]

COSMIC_OPACITY_STOPS = [
    (0.0, 0.0),
    (0.12, 0.02),
    (0.35, 0.06),
    (0.55, 0.14),
    (0.72, 0.32),
    (0.88, 0.65),
    (1.0, 0.95),
]

CINEMATIC_OPACITY_STOPS = [
    (0.0, 0.0),
    (0.18, 0.004),
    (0.35, 0.025),
    (0.55, 0.08),
    (0.72, 0.28),
    (0.85, 0.58),
    (0.90, 0.78),
    (0.94, 0.92),
    (0.97, 0.98),
    (1.0, 1.0),
]

VOLUME_LIGHTING = {
    "key": {
        "position_offset": [8, 10, 12],
        "color_rgb": [1.0, 1.0, 1.0],
        "intensity": 1.0,
    },
    "fill": {
        "position_offset": [-12, -8, -10],
        "color_rgb": [0.55, 0.75, 1.0],
        "intensity": 0.3,
    },
}

PRESENTATION_QUALITY = {
    "sampleDistance": 0.65,
    "maximumSamplesPerRay": 4096,
    "shade": True,
    "ambient": 0.10,
    "diffuse": 0.75,
    "specular": 0.52,
    "scalarOpacityUnitDistance": SPACING * 2.5,
    "gpuTextureInterpolation": "trilinear (WebGL LINEAR on 3D texture)",
}

CINEMATIC_QUALITY = {
    "sampleDistance": 1.6,
    "maximumSamplesPerRay": 1024,
    "shade": True,
    "ambient": 0.08,
    "diffuse": 0.82,
    "specular": 0.66,
    "scalarOpacityUnitDistance": SPACING * 2.5,
}


def compute_camera_spec(
    view_aspect: float = CAPTURE_ASPECT,
    zoom_factor: float = CAPTURE_CAMERA_ZOOM,
) -> dict:
    cx = cy = cz = DOMAIN_LENGTH / 2
    d = DOMAIN_LENGTH * CAMERA_DISTANCE_FACTOR
    wide_boost = 1 / math.sqrt(view_aspect) if view_aspect > 1.2 else 1.0
    fc = DOMAIN_LENGTH / 2
    return {
        "domainLength": DOMAIN_LENGTH,
        "voxelSpacing": SPACING,
        "focalPoint": [cx, cy, cz],
        "position": [
            cx + d * CAMERA_OFFSET[0],
            cy + d * CAMERA_OFFSET[1],
            cz + d * CAMERA_OFFSET[2],
        ],
        "viewUp": [0, 0, 1],
        "viewMargin": VIEW_MARGIN,
        "wideAspectBoost": wide_boost,
        "zoomFactor": zoom_factor,
        "effectiveZoom": VIEW_MARGIN * wide_boost * zoom_factor,
        "viewAspect": view_aspect,
        "lights": {
            "key": {
                "position": [fc + 8, fc + 10, fc + 12],
                "focalPoint": [fc, fc, fc],
                **VOLUME_LIGHTING["key"],
            },
            "fill": {
                "position": [fc - 12, fc - 8, fc - 10],
                "focalPoint": [fc, fc, fc],
                **VOLUME_LIGHTING["fill"],
            },
        },
        "presentation": PRESENTATION_QUALITY,
    }


def log10_safe(v: float, floor: float = 1e-6) -> float:
    return math.log10(max(v, floor))


def value_at_norm_t(t: float, data_min: float, data_max: float, use_log: bool = True) -> float:
    if use_log:
        lo = log10_safe(data_min)
        hi = log10_safe(data_max)
        return 10 ** (lo + t * (hi - lo))
    return data_min + t * (data_max - data_min)


def export_render_spec_json(out: Path) -> Path:
    spec = compute_camera_spec()
    spec["opacityStopsNormalized"] = COSMIC_OPACITY_STOPS
    spec["colorStopsNormalized"] = [
        {"t": t, "rgb": list(rgb)} for t, rgb in COSMIC_COLOR_STOPS
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    return out
