import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { TimelineData } from '@/data/types';
import { useChartSizeFromOpts, type ChartSizeOptions } from '@/hooks/useChartSize';
import { getChartTheme, LABEL_FILL, styleAxisText, styleGrid } from './chartTheme';

const REPRESENTATIVE_STEPS = [0, 25, 50, 75, 99];
const COLORS = ['#7c6cf0', '#3dd6c6', '#5b9bd5', '#f5c842', '#e87a5a'];

interface HistogramOverlayProps {
  timeline: TimelineData;
  sizeOpts?: ChartSizeOptions;
}

function chartTier(sizeOpts: ChartSizeOptions | undefined, height: number) {
  if (sizeOpts?.videoReadable && height >= 130) return 'video' as const;
  if (height < 175) return 'compact' as const;
  const maxH = sizeOpts?.maxHeight ?? 320;
  const minH = sizeOpts?.minHeight ?? 260;
  if (height >= 280 && (minH >= 300 || maxH >= 360)) return 'poster' as const;
  if (maxH <= 200) return 'compact' as const;
  return 'default' as const;
}

const LEGEND_BOX_W = 62;
const LEGEND_GAP = 10;

function legendBottomReserve(height: number): number {
  if (height >= 200) return 52;
  if (height >= 160) return 42;
  return 34;
}

function shouldLegendBelow(
  innerW: number,
  tier: string,
  height: number,
  externalLegend = false,
): boolean {
  if (externalLegend) return false;
  if (height < 130) return true;
  const sideReserve = LEGEND_BOX_W + LEGEND_GAP + 8;
  return tier === 'compact' || innerW - 52 - sideReserve < 180;
}

function HistogramLegendStrip() {
  return (
    <div className="hist-overlay-legend" aria-hidden>
      {REPRESENTATIVE_STEPS.map((t, idx) => (
        <span
          key={t}
          className="hist-overlay-legend-item"
          style={{ color: COLORS[idx] }}
        >
          <span className="hist-overlay-legend-swatch" style={{ borderColor: COLORS[idx] }} />
          t={t}
        </span>
      ))}
    </div>
  );
}

function drawLegend(
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  curveW: number,
  innerH: number,
  tier: 'poster' | 'default' | 'compact' | 'video',
  below = false,
) {
  const n = REPRESENTATIVE_STEPS.length;
  const legendFont =
    tier === 'poster' ? 13 : tier === 'video' ? 12 : innerH < 95 ? 10 : 11;
  const step =
    tier === 'poster' ? 16 : tier === 'video' ? 14 : tier === 'compact' ? 12 : 14;
  const boxH = n * step + 8;

  if (below) {
    const legendY0 = innerH + 30;
    const boxW = Math.min(curveW, n * 36 + 16);
    const legendX0 = (curveW - boxW) / 2;
    g.append('rect')
      .attr('x', legendX0)
      .attr('y', legendY0 - 6)
      .attr('width', boxW)
      .attr('height', boxH)
      .attr('rx', 6)
      .attr('fill', 'rgba(6, 10, 20, 0.82)')
      .attr('stroke', 'rgba(78, 196, 255, 0.22)');

    REPRESENTATIVE_STEPS.forEach((t, idx) => {
      const lx = legendX0 + 10 + idx * (boxW / n);
      const ly = legendY0 + boxH / 2;
      const color = COLORS[idx]!;
      g.append('line')
        .attr('x1', lx)
        .attr('x2', lx + 14)
        .attr('y1', ly)
        .attr('y2', ly)
        .attr('stroke', color)
        .attr('stroke-width', 2.5)
        .attr('stroke-linecap', 'round');
      g.append('text')
        .attr('x', lx + 18)
        .attr('y', ly + 4)
        .attr('fill', color)
        .attr('font-size', legendFont)
        .attr('font-weight', 500)
        .text(`t=${t}`);
    });
    return;
  }

  const legendX = curveW + LEGEND_GAP;
  const legendY0 = Math.max(0, (innerH - boxH) / 2);

  g.insert('rect', ':first-child')
    .attr('x', legendX)
    .attr('y', legendY0 - 6)
    .attr('width', LEGEND_BOX_W)
    .attr('height', boxH)
    .attr('rx', 6)
    .attr('fill', 'rgba(6, 10, 20, 0.82)')
    .attr('stroke', 'rgba(78, 196, 255, 0.22)');

  REPRESENTATIVE_STEPS.forEach((t, idx) => {
    const ly = legendY0 + idx * step;
    const color = COLORS[idx]!;
    g.append('line')
      .attr('x1', legendX + 8)
      .attr('x2', legendX + 24)
      .attr('y1', ly)
      .attr('y2', ly)
      .attr('stroke', color)
      .attr('stroke-width', tier === 'poster' ? 3 : tier === 'video' ? 2.75 : 2.5)
      .attr('stroke-linecap', 'round');
    g.append('text')
      .attr('x', legendX + 28)
      .attr('y', ly + 4)
      .attr('fill', color)
      .attr('font-size', legendFont)
      .attr('font-weight', tier === 'poster' || tier === 'video' ? 600 : 500)
      .text(`t=${t}`);
  });
}

export function HistogramOverlay({ timeline, sizeOpts }: HistogramOverlayProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const { width, height } = useChartSizeFromOpts(wrapRef, sizeOpts);
  const svgRef = useRef<SVGSVGElement>(null);
  const externalLegend = Boolean(sizeOpts?.videoReadable);
  const legendStripH = externalLegend ? 32 : 0;
  const plotHeight = Math.max(96, height - legendStripH);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl || width < 80) return;

    const tier = chartTier(sizeOpts, plotHeight);
    const theme = getChartTheme(
      tier === 'poster'
        ? 'poster'
        : tier === 'video'
          ? 'video'
          : tier === 'compact'
            ? 'compact'
            : 'default',
    );
    const legendReserve = LEGEND_BOX_W + LEGEND_GAP + 8;
    const baseMargin =
      tier === 'poster'
        ? { top: 26, right: 14, bottom: 54, left: 64 }
        : tier === 'video'
          ? { top: 14, right: 10, bottom: externalLegend ? 34 : 40, left: 54 }
          : tier === 'compact'
            ? { top: 12, right: 8, bottom: 36, left: 46 }
            : { top: 16, right: 10, bottom: 38, left: 52 };

    const preInnerW = width - baseMargin.left - baseMargin.right;
    const legendBelow = shouldLegendBelow(
      preInnerW,
      tier,
      plotHeight,
      externalLegend,
    );
    const bottomLegendExtra = legendBelow ? legendBottomReserve(plotHeight) : 0;
    const margin = {
      ...baseMargin,
      bottom: baseMargin.bottom + bottomLegendExtra,
    };
    const innerW = width - margin.left - margin.right;
    const innerH = plotHeight - margin.top - margin.bottom;
    const curveW = Math.max(
      40,
      innerW - (legendBelow ? 0 : legendReserve),
    );

    const axisFont =
      tier === 'poster' ? 12 : tier === 'video' ? 12 : tier === 'compact' ? 11 : 11;
    const strokeW =
      tier === 'poster' ? 2.6 : tier === 'video' ? 2.4 : 2.2;

    const edges = timeline.logBinEdges;
    const centers = edges.slice(0, -1).map((e, i) => Math.sqrt(e * edges[i + 1]!));

    const x = d3
      .scaleLog()
      .domain([timeline.globalMin, timeline.globalMax])
      .range([0, curveW]);

    const maxY = d3.max(
      REPRESENTATIVE_STEPS.flatMap((t) => timeline.histograms[t] ?? []),
    ) ?? 0;

    const y = d3
      .scaleLinear()
      .domain([0, maxY * 100 * 1.08 || 1])
      .nice()
      .range([innerH, 0]);

    const line = d3
      .line<number>()
      .x((_, i) => x(centers[i]!))
      .y((d) => y(d * 100))
      .curve(d3.curveLinear);

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', plotHeight);

    svg
      .append('defs')
      .append('clipPath')
      .attr('id', 'hist-overlay-clip')
      .append('rect')
      .attr('width', curveW)
      .attr('height', innerH);

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const plotG = g.append('g').attr('clip-path', 'url(#hist-overlay-clip)');

    const gridG = plotG.append('g').attr('class', 'grid');
    gridG.call(
      d3
        .axisLeft(y)
        .ticks(tier === 'poster' ? 6 : 5)
        .tickSize(-curveW)
        .tickFormat(() => ''),
    );
    styleGrid(gridG, theme);

    REPRESENTATIVE_STEPS.forEach((t, idx) => {
      const hist = timeline.histograms[t];
      if (!hist) return;
      plotG
        .append('path')
        .datum(hist)
        .attr('fill', 'none')
        .attr('stroke', COLORS[idx])
        .attr('stroke-width', strokeW)
        .attr('stroke-linejoin', 'round')
        .attr('stroke-linecap', 'round')
        .attr('opacity', 0.96)
        .attr('d', line);
    });

    const tickCount =
      curveW < 160 ? 3 : tier === 'poster' ? 7 : tier === 'compact' ? 4 : 5;
    const xTickFormat = d3.format(curveW < 200 ? '.1f' : '.2f');
    const xAxis = g
      .append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(
        d3
          .axisBottom(x)
          .tickValues(x.ticks(tickCount))
          .tickFormat((d) => xTickFormat(d as number))
          .tickPadding(6),
      );
    styleAxisText(xAxis, theme);
    xAxis
      .selectAll('text')
      .attr('font-size', axisFont)
      .attr('fill', theme.labelFill)
      .attr('dy', '0.85em');

    const yAxis = g.append('g').call(
      d3.axisLeft(y).ticks(tier === 'poster' ? 6 : tier === 'compact' ? 4 : 5),
    );
    styleAxisText(yAxis, theme);
    yAxis.selectAll('text').attr('font-size', axisFont).attr('fill', theme.labelFill);

    if (tier === 'poster') {
      g.append('text')
        .attr('x', curveW / 2)
        .attr('y', innerH + 42)
        .attr('text-anchor', 'middle')
        .attr('fill', LABEL_FILL)
        .attr('font-size', 13)
        .attr('font-weight', 600)
        .text('密度 ρ (log)');

      g.append('text')
        .attr('transform', 'rotate(-90)')
        .attr('x', -innerH / 2)
        .attr('y', -46)
        .attr('text-anchor', 'middle')
        .attr('fill', LABEL_FILL)
        .attr('font-size', 13)
        .attr('font-weight', 600)
        .text('Probability mass×100');
    } else if (!legendBelow && !externalLegend && tier !== 'compact') {
      g.append('text')
        .attr('x', curveW / 2)
        .attr('y', innerH + (tier === 'video' ? 32 : 30))
        .attr('text-anchor', 'middle')
        .attr('fill', theme.labelFill)
        .attr('font-size', axisFont)
        .attr('font-weight', 600)
        .text('密度 ρ (log)');
    }

    if (!externalLegend) {
      drawLegend(g, curveW, innerH, tier, legendBelow);
    }
  }, [timeline, width, height, plotHeight, externalLegend, sizeOpts]);

  const fillContainer = sizeOpts?.fillContainer ?? false;

  return (
    <div
      ref={wrapRef}
      className={`chart-responsive chart-responsive-fill histogram-overlay-wrap${externalLegend ? ' histogram-overlay-wrap--external-legend' : ''}`}
      style={
        fillContainer
          ? { width: '100%', height: '100%', minHeight: 0 }
          : { height, minHeight: height, maxHeight: height, flex: '0 0 auto' }
      }
    >
      <svg
        ref={svgRef}
        className="histogram-overlay"
        viewBox={`0 0 ${width} ${plotHeight}`}
        preserveAspectRatio="xMidYMid meet"
        aria-label="多时刻 log 直方图叠加"
      />
      {externalLegend && <HistogramLegendStrip />}
    </div>
  );
}
