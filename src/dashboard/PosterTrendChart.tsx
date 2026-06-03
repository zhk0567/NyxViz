import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { TimelineData } from '@/data/types';
import { useChartSize } from '@/hooks/useChartSize';
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
}

export function PosterTrendChart({
  timeline,
  title,
  badge,
  color,
  fill,
  metric,
}: PosterTrendChartProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const { width, height } = useChartSize(wrapRef, 200, 1.65, 260);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl || width < 40) return;

    const margin = { top: 36, right: 16, bottom: 36, left: 52 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;
    const data = timeline.timesteps;
    const values = data.map((d) => readMetric(d, metric));
    const yMin = d3.min(values) ?? 0;
    const yMax = d3.max(values) ?? 1;
    const pad = (yMax - yMin) * 0.08 || 0.01;

    const x = d3.scaleLinear().domain([0, 99]).range([0, innerW]);
    const y = d3
      .scaleLinear()
      .domain([yMin - pad, yMax + pad])
      .nice()
      .range([innerH, 0]);

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
        .ticks(5)
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
      .attr('stroke-width', 2.5);

    const xAxis = g.append('g').attr('transform', `translate(0,${innerH})`).call(d3.axisBottom(x).ticks(5));
    styleAxisText(xAxis);
    xAxis.selectAll('text').attr('font-size', 11);

    const yAxis = g.append('g').call(d3.axisLeft(y).ticks(5));
    styleAxisText(yAxis);
    yAxis.selectAll('text').attr('font-size', 11);

    g.append('text')
      .attr('x', 0)
      .attr('y', -12)
      .attr('fill', '#f5f9ff')
      .attr('font-size', 14)
      .attr('font-weight', 700)
      .text(title);

    g.append('text')
      .attr('x', innerW)
      .attr('y', -12)
      .attr('text-anchor', 'end')
      .attr('fill', color)
      .attr('font-size', 13)
      .attr('font-weight', 700)
      .text(badge);
  }, [timeline, width, height, title, badge, color, fill, metric]);

  return (
    <div ref={wrapRef} className="pl-trend-chart" style={{ height }}>
      <svg ref={svgRef} aria-label={title} />
    </div>
  );
}
