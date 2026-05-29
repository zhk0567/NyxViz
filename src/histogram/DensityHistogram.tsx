import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { TimelineData } from '@/data/types';
import { useAppStore } from '@/store/useAppStore';

interface DensityHistogramProps {
  timeline: TimelineData;
  width?: number;
  height?: number;
}

export function DensityHistogram({
  timeline,
  width = 480,
  height = 220,
}: DensityHistogramProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const timestep = useAppStore((s) => s.timestep);
  const setBrushRange = useAppStore((s) => s.setBrushRange);
  const brushRange = useAppStore((s) => s.brushRange);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl) return;

    const margin = { top: 16, right: 16, bottom: 36, left: 52 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    const stats = timeline.timesteps[timestep];
    const hist = timeline.histograms[timestep];
    if (!stats || !hist) return;

    const edges = timeline.logBinEdges;
    const centers = edges.slice(0, -1).map((e, i) => {
      const e2 = edges[i + 1]!;
      return Math.sqrt(e * e2);
    });

    const x = d3
      .scaleLog()
      .domain([timeline.globalMin, timeline.globalMax])
      .range([0, innerW]);

    const y = d3
      .scaleLinear()
      .domain([0, d3.max(hist) ?? 0])
      .nice()
      .range([innerH, 0]);

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', height);

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const barW = innerW / hist.length;
    g.selectAll('rect')
      .data(hist)
      .join('rect')
      .attr('x', (_, i) => x(centers[i]!) - barW / 2)
      .attr('y', (d) => y(d))
      .attr('width', Math.max(1, barW * 0.9))
      .attr('height', (d) => innerH - y(d))
      .attr('fill', '#5b8def')
      .attr('opacity', 0.85);

    if (brushRange) {
      g.append('rect')
        .attr('x', x(brushRange.min))
        .attr('y', 0)
        .attr('width', Math.max(2, x(brushRange.max) - x(brushRange.min)))
        .attr('height', innerH)
        .attr('fill', '#f0c040')
        .attr('opacity', 0.25);
    }

    g.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6, '.2f'))
      .selectAll('text')
      .attr('fill', '#aab');

    g.append('g').call(d3.axisLeft(y).ticks(5)).selectAll('text').attr('fill', '#aab');

    g.append('text')
      .attr('x', innerW / 2)
      .attr('y', innerH + 30)
      .attr('text-anchor', 'middle')
      .attr('fill', '#ccd')
      .attr('font-size', 11)
      .text(`密度 (log 轴) — 时间步 ${timestep}`);

    const brush = d3
      .brushX()
      .extent([
        [0, 0],
        [innerW, innerH],
      ])
      .on('end', (event) => {
        if (!event.selection) return;
        const [x0, x1] = event.selection as [number, number];
        const min = x.invert(x0);
        const max = x.invert(x1);
        setBrushRange({ min: Math.min(min, max), max: Math.max(min, max) });
      });

    g.append('g').attr('class', 'brush').call(brush);
  }, [timeline, timestep, width, height, brushRange, setBrushRange]);

  return <svg ref={svgRef} className="density-histogram" />;
}
