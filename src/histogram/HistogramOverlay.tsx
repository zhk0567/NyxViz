import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { TimelineData } from '@/data/types';

const REPRESENTATIVE_STEPS = [0, 25, 50, 75, 99];
const COLORS = ['#5b8def', '#6ad49b', '#c678dd', '#f0c040', '#e06c75'];

interface HistogramOverlayProps {
  timeline: TimelineData;
  width?: number;
  height?: number;
}

export function HistogramOverlay({
  timeline,
  width = 520,
  height = 240,
}: HistogramOverlayProps) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl) return;

    const margin = { top: 16, right: 16, bottom: 36, left: 52 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    const edges = timeline.logBinEdges;
    const centers = edges.slice(0, -1).map((e, i) => Math.sqrt(e * edges[i + 1]!));

    const x = d3
      .scaleLog()
      .domain([timeline.globalMin, timeline.globalMax])
      .range([0, innerW]);

    const maxY = d3.max(
      REPRESENTATIVE_STEPS.flatMap((t) => timeline.histograms[t] ?? []),
    ) ?? 0;

    const y = d3.scaleLinear().domain([0, maxY]).nice().range([innerH, 0]);

    const line = d3
      .line<number>()
      .x((_, i) => x(centers[i]!))
      .y((d) => y(d))
      .curve(d3.curveMonotoneX);

    const svg = d3.select(svgEl);
    svg.selectAll('*').remove();
    svg.attr('width', width).attr('height', height);

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    REPRESENTATIVE_STEPS.forEach((t, idx) => {
      const hist = timeline.histograms[t];
      if (!hist) return;
      g.append('path')
        .datum(hist)
        .attr('fill', 'none')
        .attr('stroke', COLORS[idx])
        .attr('stroke-width', 2)
        .attr('opacity', 0.9)
        .attr('d', line);
    });

    g.append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6, '.2f'))
      .selectAll('text')
      .attr('fill', '#aab');

    g.append('g').call(d3.axisLeft(y).ticks(5)).selectAll('text').attr('fill', '#aab');

    REPRESENTATIVE_STEPS.forEach((t, idx) => {
      g.append('text')
        .attr('x', innerW - 60)
        .attr('y', 14 + idx * 14)
        .attr('fill', COLORS[idx]!)
        .attr('font-size', 10)
        .text(`t=${t}`);
    });
  }, [timeline, width, height]);

  return <svg ref={svgRef} className="histogram-overlay" />;
}
