import { figuresUrl } from '@/config/publicPaths';
import { useCallback, useState, type KeyboardEvent } from 'react';
import { OverlayLightbox } from '@/components/ImageLightbox';
import { computeStoryMetrics } from '@/results/storyMetrics';
import type { BrushValidationData } from '@/data/statsLoader';

type CaseId = 'a' | 'b' | 'c';
type CaseVariant = 'strip' | 'lightbox';

interface VideoCaseCardsProps {
  brushValidation: BrushValidationData | null;
  storyMetrics: ReturnType<typeof computeStoryMetrics>;
}

const CASE_FIGURES = {
  a: figuresUrl('task3_metrics_timeline.png'),
  b: figuresUrl('task4_brush_top1.png'),
  c: figuresUrl('task4_p88_sensitivity.png'),
} as const;

const CASE_LABELS: Record<CaseId, string> = {
  a: '案例 A · 百步曲线 vs 挑帧叙事',
  b: '案例 B · Top 1% 质量集中',
  c: '案例 C · P88 亮脊反查',
};

function expandableProps(label: string, onExpand?: () => void) {
  if (!onExpand) return {};
  return {
    role: 'button' as const,
    tabIndex: 0,
    onClick: onExpand,
    onKeyDown: (e: KeyboardEvent<HTMLElement>) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        onExpand();
      }
    },
    'aria-label': `放大查看：${label}`,
  };
}

interface CaseCardProps {
  variant: CaseVariant;
  onExpand?: () => void;
  m: ReturnType<typeof computeStoryMetrics>;
  band: [number, number] | null;
}

function CaseCardA({ variant, onExpand }: Pick<CaseCardProps, 'variant' | 'onExpand'>) {
  const isStrip = variant === 'strip';
  return (
    <article
      className={`vd-case-card vd-case-card--row${isStrip ? ' vd-case-card--expandable' : ' vd-case-card--lightbox'}`}
      {...expandableProps(CASE_LABELS.a, isStrip ? onExpand : undefined)}
    >
      <div className="vd-case-media">
        <img src={CASE_FIGURES.a} alt="百步 σ/p99 曲线" loading="lazy" />
      </div>
      <div className="vd-case-body">
        <span className="vd-case-id">A</span>
        <div className="vd-case-copy">
          <h4>百步曲线 vs 挑帧叙事</h4>
          <p>若无百步 σ / 分位趋势，易只看 t=0 与 t=99 挑帧叙事，遗漏中间非线性成形。</p>
        </div>
      </div>
    </article>
  );
}

function CaseCardB({ variant, onExpand, m }: Pick<CaseCardProps, 'variant' | 'onExpand' | 'm'>) {
  const isStrip = variant === 'strip';
  return (
    <article
      className={`vd-case-card vd-case-card--row tone-orange${isStrip ? ' vd-case-card--expandable' : ' vd-case-card--lightbox'}`}
      {...expandableProps(CASE_LABELS.b, isStrip ? onExpand : undefined)}
    >
      <div className="vd-case-media">
        <img src={CASE_FIGURES.b} alt="Top 1% 空间投影" loading="lazy" />
      </div>
      <div className="vd-case-body">
        <span className="vd-case-id">B</span>
        <div className="vd-case-copy">
          <h4>Top 1% 质量集中</h4>
          <p>
            体积 {m.tailAbovePct.toFixed(2)}% 承载质量 {m.massAbovePct.toFixed(2)}
            %；刷选呈 filament 丝状聚集。
          </p>
        </div>
      </div>
    </article>
  );
}

function CaseCardC({ variant, onExpand, band }: Pick<CaseCardProps, 'variant' | 'onExpand' | 'band'>) {
  const isStrip = variant === 'strip';
  return (
    <article
      className={`vd-case-card vd-case-card--row tone-gold${isStrip ? ' vd-case-card--expandable' : ' vd-case-card--lightbox'}`}
      {...expandableProps(CASE_LABELS.c, isStrip ? onExpand : undefined)}
    >
      <div className="vd-case-media">
        <img src={CASE_FIGURES.c} alt="P88 亮脊敏感性" loading="lazy" />
      </div>
      <div className="vd-case-body">
        <span className="vd-case-id">C</span>
        <div className="vd-case-copy">
          <h4>P88 亮脊反查</h4>
          <p>
            投影像素第 88 百分位提取亮脊，反查密度{' '}
            {band
              ? `${band[0].toFixed(2)} – ${band[1].toFixed(2)}`
              : '11.23 – 12.16'}
            ，与 Top 1% 一致。
          </p>
        </div>
      </div>
    </article>
  );
}

function renderLightboxCard(id: CaseId, m: ReturnType<typeof computeStoryMetrics>, band: [number, number] | null) {
  switch (id) {
    case 'a':
      return <CaseCardA variant="lightbox" />;
    case 'b':
      return <CaseCardB variant="lightbox" m={m} />;
    case 'c':
      return <CaseCardC variant="lightbox" band={band} />;
    default:
      return null;
  }
}

export function VideoCaseCards({
  brushValidation,
  storyMetrics: m,
}: VideoCaseCardsProps) {
  const p88 = brushValidation?.p88Sweep.find((s) => s.projPercentile === 88);
  const band = p88?.densityBand ?? brushValidation?.fpFnDefault.filamentBand ?? null;
  const [expanded, setExpanded] = useState<CaseId | null>(null);
  const openCard = useCallback((id: CaseId) => setExpanded(id), []);
  const closeCard = useCallback(() => setExpanded(null), []);

  return (
    <div className="vd-scene-panel vd-case-cards">
      <header className="vd-scene-panel-head">
        <h3>可视化价值 · 三案例</h3>
      </header>

      <CaseCardA variant="strip" onExpand={() => openCard('a')} />
      <CaseCardB variant="strip" m={m} onExpand={() => openCard('b')} />
      <CaseCardC variant="strip" band={band} onExpand={() => openCard('c')} />

      <OverlayLightbox
        open={expanded != null}
        label={expanded ? CASE_LABELS[expanded] : ''}
        onClose={closeCard}
      >
        {expanded && renderLightboxCard(expanded, m, band)}
      </OverlayLightbox>
    </div>
  );
}
