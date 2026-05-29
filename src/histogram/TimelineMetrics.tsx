import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { TimelineData } from '@/data/types';
import { useChartSize } from '@/hooks/useChartSize';
import { LABEL_FILL, styleAxisText, styleGrid } from './chartTheme';

interface TimelineMetricsProps {
  timeline: TimelineData;
}

const SERIES = [
  { key: 'mean' as const, label: '均值', color: '#7c6cf0', fill: 'rgba(124, 108, 240, 0.14)' },
  { key: 'p99' as const, label: 'p99', color: '#f5c842', fill: 'rgba(245, 200, 66, 0.1)' },
  { key: 'std' as const, label: '标准差', color: '#3dd6c6', fill: 'rgba(61, 214, 198, 0.1)' },
];

export function TimelineMetrics({ timeline }: TimelineMetricsProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const { width, height } = useChartSize(wrapRef, 260, 2.4);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl) return;

    const margin = { top: 16, right: 88, bottom: 32, left: 48 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    const data = timeline.timesteps;
    const x = d3.scaleLinear().domain([0, 99]).range([0, innerW]);
    const y = d3
      .scaleLinear()
      .domain([
        d3.min(data, (d) => d.mean - d.std) ?? 0,
        d3.max(data, (d) => d.p99) ?? 1,
      ])
      .nice()
      .range([innerH, 0]);

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', height);

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const gridG = g.append('g').attr('class', 'grid');
    gridG.call(
      d3
        .axisLeft(y)
        .ticks(6)
        .tickSize(-innerW)
        .tickFormat(() => ''),
    );
    styleGrid(gridG);

    SERIES.forEach((s) => {
      const area = d3
        .area<(typeof data)[0]>()
        .x((d) => x(d.timestep))
        .y0(innerH)
        .y1((d) => y(d[s.key]));
      g.append('path').datum(data).attr('fill', s.fill).attr('d', area);

      const line = d3
        .line<(typeof data)[0]>()
        .x((d) => x(d.timestep))
        .y((d) => y(d[s.key]));
      g.append('path')
        .datum(data)
        .attr('fill', 'none')
        .attr('stroke', s.color)
        .attr('stroke-width', s.key === 'mean' ? 2.2 : 1.6)
        .attr('d', line);
    });

    styleAxisText(
      g
        .append('g')
        .attr('transform', `translate(0,${innerH})`)
        .call(d3.axisBottom(x).ticks(10)),
    );
    styleAxisText(g.append('g').call(d3.axisLeft(y)));

    SERIES.forEach((item, i) => {
      g.append('line')
        .attr('x1', innerW + 8)
        .attr('x2', innerW + 28)
        .attr('y1', 8 + i * 16)
        .attr('y2', 8 + i * 16)
        .attr('stroke', item.color);
      g.append('text')
        .attr('x', innerW + 32)
        .attr('y', 12 + i * 16)
        .attr('fill', LABEL_FILL)
        .attr('font-size', 10)
        .text(item.label);
    });
  }, [timeline, width, height]);

  return (
    <div ref={wrapRef} className="chart-responsive">
      <svg ref={svgRef} className="timeline-metrics" width="100%" />
    </div>
  );
}
