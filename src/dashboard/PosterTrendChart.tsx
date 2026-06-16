import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { TimelineData } from '@/data/types';
import { useChartSizeFromOpts, type ChartSizeOptions } from '@/hooks/useChartSize';
import { getChartTheme, styleAxisText, styleGrid } from '@/histogram/chartTheme';

export type PosterTrendMetric = 'std' | 'span' | 'tailPct';

function readMetric(step: TimelineData['timesteps'][0], metric: PosterTrendMetric): number {
  switch (metric) {
    case 'std':
      return step.std;
    case 'span':
      return step.p99 - step.p01;
    case 'tailPct':
      return step.tailMassAboveP99 * 100;
  }
}

interface PosterTrendChartProps {
  timeline: TimelineData;
  title: string;
  badge: string;
  color: string;
  fill: string;
  metric: PosterTrendMetric;
  sizeOpts?: ChartSizeOptions;
  compact?: boolean;
}

/** 紧凑录屏模式：Top 1% 改绘相对 t=0 的变化率，避免 ~1.0000% 绝对值看不出波动 */
function buildSeries(
  data: TimelineData['timesteps'],
  metric: PosterTrendMetric,
  compact: boolean,
): { values: number[]; tailDelta: boolean } {
  const raw = data.map((d) => readMetric(d, metric));
  if (metric === 'tailPct' && compact) {
    const base = raw[0] ?? 1;
    return {
      values: raw.map((v) => (base > 0 ? (v / base - 1) * 100 : 0)),
      tailDelta: true,
    };
  }
  return { values: raw, tailDelta: false };
}

function compactYTick(
  v: d3.NumberValue,
  metric: PosterTrendMetric,
  ySpan: number,
  tailDelta: boolean,
): string {
  const n = Number(v);
  if (!Number.isFinite(n)) return '';
  if (tailDelta) {
    const abs = Math.abs(n);
    if (abs >= 0.1) return `${d3.format('+.2f')(n)}%`;
    if (abs >= 0.01) return `${d3.format('+.2f')(n)}%`;
    if (abs >= 0.001) return `${d3.format('+.3f')(n)}%`;
    return `${d3.format('+.2f')(n)}%`;
  }
  if (metric === 'tailPct' || ySpan < 0.02) {
    return d3.format('.3f')(n);
  }
  const abs = Math.abs(n);
  if (abs >= 1000) return d3.format('.2s')(n);
  if (abs >= 10) return d3.format('.1f')(n);
  if (abs >= 1) return d3.format('.2f')(n);
  if (abs >= 0.01) return d3.format('.3f')(n);
  return d3.format('.2e')(n);
}

function yPadding(
  yMin: number,
  yMax: number,
  metric: PosterTrendMetric,
  tailDelta: boolean,
): number {
  const span = yMax - yMin;
  if (tailDelta) {
    if (span <= 0) return 0.001;
    return Math.max(span * 0.15, 0.0005);
  }
  if (metric === 'tailPct') {
    if (span <= 0) return Math.max(Math.abs(yMax) * 1e-8, 1e-10);
    return span * 0.12;
  }
  if (span <= 0) {
    return Math.max(Math.abs(yMax) * 0.05, 0.01);
  }
  if (span / Math.max(Math.abs(yMax), 1e-9) < 0.02) {
    return Math.max(span * 0.15, span * 0.05);
  }
  return span * 0.08;
}

function compactLeftMargin(width: number, tailDelta: boolean): number {
  if (tailDelta) {
    return Math.min(44, Math.max(34, Math.round(width * 0.28)));
  }
  return Math.min(40, Math.max(30, Math.round(width * 0.24)));
}

export function PosterTrendChart({
  timeline,
  title,
  badge,
  color,
  fill,
  metric,
  sizeOpts,
  compact: compactProp,
}: PosterTrendChartProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const plotRef = useRef<HTMLDivElement>(null);
  const fillContainer = sizeOpts?.fillContainer ?? false;
  const compact =
    compactProp ?? (sizeOpts?.maxHeight != null && sizeOpts.maxHeight <= 110);
  const sizeRef = compact ? plotRef : wrapRef;
  const chartSizeOpts = compact
    ? {
        minHeight: sizeOpts?.minHeight ?? 86,
        maxHeight: sizeOpts?.maxHeight ?? 92,
        aspect: sizeOpts?.aspect ?? 1.55,
        fillContainer: true,
        videoReadable: sizeOpts?.videoReadable,
      }
    : sizeOpts;
  const { width, height } = useChartSizeFromOpts(sizeRef, chartSizeOpts);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl || width < 40 || height < 32) return;

    const data = timeline.timesteps;
    const { values, tailDelta } = buildSeries(data, metric, compact);
    const valueAt = (step: (typeof data)[0], i: number) => values[i] ?? 0;

    const rawMin = d3.min(values) ?? 0;
    const rawMax = d3.max(values) ?? 0;
    const yMin = tailDelta ? Math.min(0, rawMin) : rawMin;
    const yMax = tailDelta ? Math.max(0, rawMax) : rawMax;
    const ySpan = yMax - yMin;
    const pad = yPadding(yMin, yMax, metric, tailDelta);

    const theme = getChartTheme(
      sizeOpts?.videoReadable ? 'video' : compact ? 'compact' : 'default',
    );

    const margin = compact
      ? {
          top: 6,
          right: 4,
          bottom: 16,
          left: compactLeftMargin(width, tailDelta),
        }
      : { top: 36, right: 16, bottom: 36, left: 52 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    if (innerW < 8 || innerH < 8) return;

    const x = d3.scaleLinear().domain([0, 99]).range([0, innerW]);
    let y0 = yMin - pad;
    let y1 = yMax + pad;
    if (!tailDelta && metric !== 'tailPct') {
      [y0, y1] = d3.nice(y0, y1);
    }
    const y = d3.scaleLinear().domain([y0, y1]).range([innerH, 0]);
    const areaBaseline = tailDelta ? y(0) : innerH;

    const axisFont = compact ? 11 : 13;

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();
    svg
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', `0 0 ${width} ${height}`)
      .style('overflow', 'visible');

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const gridG = g.append('g');
    gridG.call(
      d3
        .axisLeft(y)
        .ticks(compact ? 3 : 5)
        .tickSize(-innerW)
        .tickFormat(() => ''),
    );
    styleGrid(gridG, theme);

    if (tailDelta) {
      g.append('line')
        .attr('x1', 0)
        .attr('x2', innerW)
        .attr('y1', y(0))
        .attr('y2', y(0))
        .attr('stroke', 'rgba(255,255,255,0.15)')
        .attr('stroke-dasharray', '3,3');
    }

    g.append('path')
      .datum(data)
      .attr(
        'd',
        d3
          .area<(typeof data)[0]>()
          .x((d) => x(d.timestep))
          .y0(areaBaseline)
          .y1((d, i) => y(valueAt(d, i))),
      )
      .attr('fill', fill);

    g.append('path')
      .datum(data)
      .attr(
        'd',
        d3
          .line<(typeof data)[0]>()
          .x((d) => x(d.timestep))
          .y((d, i) => y(valueAt(d, i))),
      )
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', compact ? 2.25 : 2.5);

    const xAxis = g
      .append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(
        d3
          .axisBottom(x)
          .ticks(compact ? 2 : 5)
          .tickFormat((d) => String(Math.round(Number(d)))),
      );
    styleAxisText(xAxis, theme);
    xAxis.selectAll('text').attr('font-size', axisFont).attr('fill', theme.labelFill);

    const yTickFormat = (v: d3.NumberValue) =>
      compactYTick(v, metric, ySpan, tailDelta);

    const yAxisGen = tailDelta
      ? d3
          .axisLeft(y)
          .ticks(3)
          .tickFormat(yTickFormat)
      : ySpan > 0 && ySpan < 0.02 && compact
        ? d3
            .axisLeft(y)
            .tickValues([yMin, yMin + ySpan / 2, yMax])
            .tickFormat(yTickFormat)
        : d3
            .axisLeft(y)
            .ticks(compact ? 3 : 5)
            .tickFormat(compact ? yTickFormat : undefined);

    const yAxis = g.append('g').call(yAxisGen);
    styleAxisText(yAxis, theme);
    yAxis
      .selectAll('text')
      .attr('font-size', axisFont)
      .attr('fill', theme.labelFill)
      .attr('text-anchor', 'end')
      .attr('x', -5);
    yAxis.selectAll('.tick:first-child text').attr('dy', '0.85em');
    yAxis.selectAll('.tick:last-child text').attr('dy', '-0.05em');

    if (!compact) {
      g.append('text')
        .attr('x', 0)
        .attr('y', -12)
        .attr('fill', '#f5f9ff')
        .attr('font-size', 16)
        .attr('font-weight', 700)
        .text(title);

      g.append('text')
        .attr('x', innerW)
        .attr('y', -12)
        .attr('text-anchor', 'end')
        .attr('fill', color)
        .attr('font-size', 15)
        .attr('font-weight', 700)
        .text(badge);
    }
  }, [timeline, width, height, title, badge, color, fill, metric, compact, sizeOpts?.videoReadable]);

  return (
    <div
      ref={wrapRef}
      className={`pl-trend-chart${compact ? ' pl-trend-chart-compact' : ''}`}
      style={fillContainer && !compact ? undefined : compact ? undefined : { height }}
    >
      {compact && (
        <header className="pl-trend-head">
          <span className="pl-trend-title">{title}</span>
          <span className="pl-trend-badge" style={{ color }}>
            {badge}
          </span>
        </header>
      )}
      <div
        ref={plotRef}
        className={compact ? 'pl-trend-plot cosmic-chart-shell' : undefined}
      >
        <svg ref={svgRef} aria-label={title} />
      </div>
    </div>
  );
}
