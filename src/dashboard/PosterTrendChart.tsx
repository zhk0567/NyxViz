import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { TimelineData } from '@/data/types';
import { useChartSizeFromOpts, type ChartSizeOptions } from '@/hooks/useChartSize';
import { styleAxisText, styleGrid } from '@/histogram/chartTheme';

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

function compactYTick(v: d3.NumberValue, metric: PosterTrendMetric, ySpan: number): string {
  const n = Number(v);
  if (!Number.isFinite(n)) return '';
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

function yPadding(yMin: number, yMax: number, metric: PosterTrendMetric): number {
  const span = yMax - yMin;
  if (span <= 0) {
    return Math.max(Math.abs(yMax) * 0.05, metric === 'tailPct' ? 0.002 : 0.01);
  }
  if (metric === 'tailPct' || span / Math.max(Math.abs(yMax), 1e-9) < 0.02) {
    return Math.max(span * 0.15, 0.001);
  }
  return span * 0.08;
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
  const { width, height } = useChartSizeFromOpts(sizeRef, sizeOpts);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl || width < 40) return;

    const margin = compact
      ? { top: 6, right: 6, bottom: 16, left: 40 }
      : { top: 36, right: 16, bottom: 36, left: 52 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    const data = timeline.timesteps;
    const values = data.map((d) => readMetric(d, metric));
    const yMin = d3.min(values) ?? 0;
    const yMax = d3.max(values) ?? 1;
    const ySpan = yMax - yMin;
    const pad = yPadding(yMin, yMax, metric);

    const x = d3.scaleLinear().domain([0, 99]).range([0, innerW]);
    const y = d3
      .scaleLinear()
      .domain([yMin - pad, yMax + pad])
      .nice()
      .range([innerH, 0]);

    const axisFont = compact ? (height >= 100 ? 10 : 9) : 13;

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', height);

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
    styleGrid(gridG);

    g.append('path')
      .datum(data)
      .attr(
        'd',
        d3
          .area<(typeof data)[0]>()
          .x((d) => x(d.timestep))
          .y0(innerH)
          .y1((d) => y(readMetric(d, metric))),
      )
      .attr('fill', fill);

    g.append('path')
      .datum(data)
      .attr(
        'd',
        d3
          .line<(typeof data)[0]>()
          .x((d) => x(d.timestep))
          .y((d) => y(readMetric(d, metric))),
      )
      .attr('fill', 'none')
      .attr('stroke', color)
      .attr('stroke-width', compact ? 2 : 2.5);

    const xAxis = g
      .append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(
        d3
          .axisBottom(x)
          .ticks(compact ? 2 : 5)
          .tickFormat((d) => String(Math.round(Number(d)))),
      );
    styleAxisText(xAxis);
    xAxis.selectAll('text').attr('font-size', axisFont);

    const yTickFormat = (v: d3.NumberValue) => compactYTick(v, metric, ySpan);
    const yAxisGen =
      ySpan > 0 && ySpan < 0.02 && compact
        ? d3
            .axisLeft(y)
            .tickValues([yMin, yMin + ySpan / 2, yMax])
            .tickFormat(yTickFormat)
        : d3
            .axisLeft(y)
            .ticks(compact ? 3 : 5)
            .tickFormat(compact ? yTickFormat : undefined);

    const yAxis = g.append('g').call(yAxisGen);
    styleAxisText(yAxis);
    yAxis.selectAll('text').attr('font-size', axisFont);

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
  }, [timeline, width, height, title, badge, color, fill, metric, compact]);

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
      <div ref={plotRef} className={compact ? 'pl-trend-plot' : undefined}>
        <svg ref={svgRef} aria-label={title} />
      </div>
    </div>
  );
}
