import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { TimelineData } from '@/data/types';
import { useChartSize } from '@/hooks/useChartSize';
import { LABEL_FILL, styleAxisText, styleGrid } from './chartTheme';

const REPRESENTATIVE_STEPS = [0, 25, 50, 75, 99];
const COLORS = ['#7c6cf0', '#3dd6c6', '#5b9bd5', '#f5c842', '#e87a5a'];

interface HistogramOverlayProps {
  timeline: TimelineData;
}

export function HistogramOverlay({ timeline }: HistogramOverlayProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const { width, height } = useChartSize(wrapRef, 260, 2.1);
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

    const gridG = g.append('g').attr('class', 'grid');
    gridG.call(
      d3
        .axisLeft(y)
        .ticks(5)
        .tickSize(-innerW)
        .tickFormat(() => ''),
    );
    styleGrid(gridG);

    REPRESENTATIVE_STEPS.forEach((t, idx) => {
      const hist = timeline.histograms[t];
      if (!hist) return;
      g.append('path')
        .datum(hist)
        .attr('fill', 'none')
        .attr('stroke', COLORS[idx])
        .attr('stroke-width', 2.2)
        .attr('opacity', 0.95)
        .attr('d', line);
    });

    styleAxisText(
      g
        .append('g')
        .attr('transform', `translate(0,${innerH})`)
        .call(d3.axisBottom(x).ticks(6, '.2f')),
    );
    styleAxisText(g.append('g').call(d3.axisLeft(y).ticks(5)));

    REPRESENTATIVE_STEPS.forEach((t, idx) => {
      g.append('text')
        .attr('x', innerW - 60)
        .attr('y', 14 + idx * 14)
        .attr('fill', COLORS[idx]!)
        .attr('font-size', 10)
        .text(`t=${t}`);
    });
  }, [timeline, width, height]);

  return (
    <div ref={wrapRef} className="chart-responsive">
      <svg ref={svgRef} className="histogram-overlay" width="100%" />
    </div>
  );
}
