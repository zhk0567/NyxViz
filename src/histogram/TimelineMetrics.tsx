import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { TimelineData } from '@/data/types';

interface TimelineMetricsProps {
  timeline: TimelineData;
  width?: number;
  height?: number;
}

export function TimelineMetrics({
  timeline,
  width = 520,
  height = 200,
}: TimelineMetricsProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl) return;

    const margin = { top: 16, right: 80, bottom: 32, left: 48 };
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

    const line = d3
      .line<typeof data[0]>()
      .x((d) => x(d.timestep))
      .y((d) => y(d.mean));

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', height);

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    g.append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', '#5b8def')
      .attr('stroke-width', 2)
      .attr('d', line);

    g.append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', '#f0c040')
      .attr('stroke-width', 1.5)
      .attr(
        'd',
        d3
          .line<typeof data[0]>()
          .x((d) => x(d.timestep))
          .y((d) => y(d.p99)),
      );

    g.append('path')
      .datum(data)
      .attr('fill', 'none')
      .attr('stroke', '#6ad49b')
      .attr('stroke-width', 1.5)
      .attr(
        'd',
        d3
          .line<typeof data[0]>()
          .x((d) => x(d.timestep))
          .y((d) => y(d.std)),
      );

    g.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(10))
      .selectAll('text')
      .attr('fill', '#aab');

    g.append('g').call(d3.axisLeft(y)).selectAll('text').attr('fill', '#aab');

    const legend = [
      { label: '均值', color: '#5b8def' },
      { label: 'p99', color: '#f0c040' },
      { label: '标准差', color: '#6ad49b' },
    ];
    legend.forEach((item, i) => {
      g.append('line')
        .attr('x1', innerW + 8)
        .attr('x2', innerW + 28)
        .attr('y1', 8 + i * 16)
        .attr('y2', 8 + i * 16)
        .attr('stroke', item.color);
      g.append('text')
        .attr('x', innerW + 32)
        .attr('y', 12 + i * 16)
        .attr('fill', '#ccd')
        .attr('font-size', 10)
        .text(item.label);
    });
  }, [timeline, width, height]);

  return <svg ref={svgRef} className="timeline-metrics" />;
}
