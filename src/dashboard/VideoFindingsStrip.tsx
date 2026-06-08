import { useCallback, useState, type KeyboardEvent } from 'react';
import { OverlayLightbox } from '@/components/ImageLightbox';
import { computeStoryMetrics } from '@/results/storyMetrics';
import type { TimelineData } from '@/data/types';

const EVO_STEPS = [0, 25, 50, 75, 99] as const;

type FindingId = '01' | '02' | '03' | '04';
type FindingVariant = 'strip' | 'lightbox';

const FINDING_LABELS: Record<FindingId, string> = {
  '01': '01 宇宙网形成',
  '02': '02 密度分布两极化',
  '03': '03 1% 体积 · 质量集中',
  '04': '04 统计—空间验证',
};

interface VideoFindingsStripProps {
  timeline: TimelineData;
  /** 综合发现专场景：卡片纵向撑满视口 */
  focusMode?: boolean;
}

interface FindingCardProps {
  id: FindingId;
  variant: FindingVariant;
  onExpand?: () => void;
  timeline: TimelineData;
  m: ReturnType<typeof computeStoryMetrics>;
  s: TimelineData['timesteps'][number];
}

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

function EvoFigure({ t }: { t: number }) {
  return (
    <figure>
      <div className="vd-finding-media vd-finding-media-square">
        <img
          src={`/figures/task1_evo_t${String(t).padStart(4, '0')}.png`}
          alt={`t=${t}`}
          loading="lazy"
          onError={(e) => {
            e.currentTarget.src = `/figures/task1_vol_t${String(t).padStart(4, '0')}.png`;
          }}
        />
      </div>
      <figcaption>t={t}</figcaption>
    </figure>
  );
}

function FindingEvoCard({ variant, onExpand }: Omit<FindingCardProps, 'id' | 'timeline' | 'm' | 's'>) {
  const isStrip = variant === 'strip';
  return (
    <article
      className={`vd-finding${isStrip ? ' vd-finding--expandable' : ' vd-finding--lightbox'}`}
      {...expandableProps('宇宙网形成', isStrip ? onExpand : undefined)}
    >
      <header>
        <span className="vd-finding-num">01</span>
        <h3 className="vd-finding-title">宇宙网形成</h3>
      </header>
      <div className="vd-finding-evo">
        {EVO_STEPS.map((t) => (
          <EvoFigure key={t} t={t} />
        ))}
      </div>
    </article>
  );
}

function FindingMetricsCard({
  variant,
  onExpand,
  m,
}: Pick<FindingCardProps, 'variant' | 'onExpand' | 'm'>) {
  const isStrip = variant === 'strip';
  return (
    <article
      className={`vd-finding vd-finding--metrics${isStrip ? ' vd-finding--expandable' : ' vd-finding--lightbox'}`}
      {...expandableProps('密度分布两极化', isStrip ? onExpand : undefined)}
    >
      <header className="vd-finding-head-stack">
        <span className="vd-finding-num">02</span>
        <div className="vd-finding-head-text">
          <h3 className="vd-finding-title">密度分布两极化</h3>
          <p className="vd-finding-note vd-finding-note--inline">
            <strong className="vd-metric-em">σ +{m.sigmaPct.toFixed(1)}%</strong>
            {' · '}
            <strong className="vd-metric-em">p99−p01 +{m.spanPct.toFixed(1)}%</strong>
            {' · 右尾增厚'}
          </p>
        </div>
      </header>
      <div className="vd-finding-media vd-finding-media-wide vd-finding-media-zoom">
        <img
          className="vd-finding-img"
          src="/figures/task3_evolution_metrics.png"
          alt="σ、偏度与 p99−p01 时序演化"
          loading="lazy"
        />
      </div>
    </article>
  );
}

function massLayoutClass(focusMode?: boolean, compactMass?: boolean): string {
  if (focusMode) return ' vd-finding-mass--focus';
  if (compactMass) return ' vd-finding-mass--strip';
  return '';
}

/** focus 模式：轨道代表有限域，避免 1% 在满宽轨道上只剩细线 */
function massBarWidthPct(value: number, focusMode: boolean | undefined, domainMax: number): number {
  if (!focusMode) return value;
  if (value <= 0) return 0;
  return Math.min(100, Math.max((value / domainMax) * 100, 4));
}

function FindingMassCard({
  variant,
  onExpand,
  m,
  compactMass,
  focusMode,
}: Pick<FindingCardProps, 'variant' | 'onExpand' | 'm'> & {
  compactMass?: boolean;
  focusMode?: boolean;
}) {
  const isStrip = variant === 'strip';
  const isCompactTitle = compactMass && !focusMode;
  return (
    <article
      className={`vd-finding vd-finding--mass${isStrip ? ' vd-finding--expandable' : ' vd-finding--lightbox'}`}
      {...expandableProps('1% 体积 · 质量集中', isStrip ? onExpand : undefined)}
    >
      <header>
        <span className="vd-finding-num">03</span>
        <h3 className={`vd-finding-title${isCompactTitle ? ' vd-finding-title--compact' : ''}`}>
          <strong className="vd-metric-em">{m.tailAbovePct.toFixed(2)}%</strong> 体积 ·{' '}
          <strong className="vd-metric-em">{m.massAbovePct.toFixed(2)}%</strong> 质量
        </h3>
      </header>
      <div
        className={`vd-finding-mass${massLayoutClass(focusMode, compactMass)}`}
      >
        <div
          className="vd-finding-donut"
          style={{
            background: `conic-gradient(#ff6b2c 0 ${m.tailAbovePct}%, #1a2848 ${m.tailAbovePct}% 100%)`,
          }}
          role="img"
          aria-label={`≥p99 体积 ${m.tailAbovePct.toFixed(2)}%`}
        />
        <div className="vd-finding-mass-metrics">
          <div className="vd-finding-mass-row">
            <span className="vd-finding-mass-label">体积</span>
            <div className="vd-finding-mass-bar" aria-hidden>
              <span
                style={{
                  width: focusMode
                    ? `${massBarWidthPct(m.tailAbovePct, focusMode, 5)}%`
                    : `${Math.max(m.tailAbovePct, 2)}%`,
                }}
              />
            </div>
            <strong className="vd-metric-em vd-finding-mass-value">{m.tailAbovePct.toFixed(2)}%</strong>
          </div>
          <div className="vd-finding-mass-row">
            <span className="vd-finding-mass-label">质量</span>
            <div className="vd-finding-mass-bar vd-finding-mass-bar-mass" aria-hidden>
              <span
                style={{
                  width: focusMode
                    ? `${massBarWidthPct(m.massAbovePct, focusMode, 30)}%`
                    : `${Math.min(m.massAbovePct, 100)}%`,
                }}
              />
            </div>
            <strong className="vd-metric-em vd-finding-mass-value">{m.massAbovePct.toFixed(2)}%</strong>
          </div>
        </div>
      </div>
    </article>
  );
}

function FindingVerifyCard({
  variant,
  onExpand,
  s,
}: Pick<FindingCardProps, 'variant' | 'onExpand' | 's'>) {
  const isStrip = variant === 'strip';
  return (
    <article
      className={`vd-finding vd-finding--verify${isStrip ? ' vd-finding--expandable' : ' vd-finding--lightbox'}`}
      {...expandableProps('统计—空间验证', isStrip ? onExpand : undefined)}
    >
      <header>
        <span className="vd-finding-num">04</span>
        <h3 className="vd-finding-title">统计—空间验证</h3>
      </header>
      <div className="vd-finding-verify">
        <figure className="vd-finding-verify-item">
          <figcaption className="vd-finding-cap">
            <strong className="vd-metric-em">Top 1%</strong> · ρ≥{s.p99.toFixed(2)}
          </figcaption>
          <div className="vd-finding-media vd-finding-media-verify">
            <img
              src="/figures/task4_brush_top1_viz.png"
              alt="Top 1% 空间投影"
              loading="lazy"
              onError={(e) => {
                e.currentTarget.src = '/figures/task4_brush_top1.png';
              }}
            />
          </div>
        </figure>
        <figure className="vd-finding-verify-item">
          <figcaption className="vd-finding-cap">
            Bottom 1% · ρ≤{s.p01.toFixed(2)}
          </figcaption>
          <div className="vd-finding-media vd-finding-media-verify">
            <img
              src="/figures/task4_brush_bottom_hl.png"
              alt="Bottom 1% 刷选高亮"
              loading="lazy"
              onError={(e) => {
                e.currentTarget.src = '/figures/task4_brush_bottom1.png';
                e.currentTarget.parentElement?.classList.add('vd-finding-media-crop-right');
              }}
            />
          </div>
        </figure>
      </div>
    </article>
  );
}

function renderLightboxCard(
  id: FindingId,
  m: ReturnType<typeof computeStoryMetrics>,
  s: TimelineData['timesteps'][number],
) {
  switch (id) {
    case '01':
      return <FindingEvoCard variant="lightbox" />;
    case '02':
      return <FindingMetricsCard variant="lightbox" m={m} />;
    case '03':
      return <FindingMassCard variant="lightbox" m={m} />;
    case '04':
      return <FindingVerifyCard variant="lightbox" s={s} />;
    default:
      return null;
  }
}

export function VideoFindingsStrip({ timeline, focusMode = false }: VideoFindingsStripProps) {
  const m = computeStoryMetrics(timeline);
  const s = timeline.timesteps[99]!;
  const [expanded, setExpanded] = useState<FindingId | null>(null);
  const openCard = useCallback((id: FindingId) => setExpanded(id), []);
  const closeCard = useCallback(() => setExpanded(null), []);

  return (
    <section
      className={`vd-findings${focusMode ? ' vd-findings--focus' : ''}`}
      aria-label="科学发现摘要"
    >
      <div className="vd-findings-grid">
        <FindingEvoCard variant="strip" onExpand={() => openCard('01')} />
        <FindingMetricsCard variant="strip" m={m} onExpand={() => openCard('02')} />
        <FindingMassCard
          variant="strip"
          m={m}
          focusMode={focusMode}
          compactMass={!focusMode}
          onExpand={() => openCard('03')}
        />
        <FindingVerifyCard variant="strip" s={s} onExpand={() => openCard('04')} />
      </div>

      <OverlayLightbox
        open={expanded != null}
        label={expanded ? FINDING_LABELS[expanded] : ''}
        onClose={closeCard}
      >
        {expanded && renderLightboxCard(expanded, m, s)}
      </OverlayLightbox>
    </section>
  );
}
