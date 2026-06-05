import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { TimelineData } from '@/data/types';
import { useChartSizeFromOpts, type ChartSizeOptions } from '@/hooks/useChartSize';
import { LABEL_FILL, styleAxisText, styleGrid } from './chartTheme';

export interface BrushHistogramPreviewProps {
  timeline: TimelineData;
  timestep?: number;
  rangeMin: number;
  rangeMax: number;
  highlightColor: string;
  legendLabel: string;
  sizeOpts?: ChartSizeOptions;
}

const DEFAULT_SIZE: ChartSizeOptions = {
  minHeight: 260,
  maxHeight: 300,
  aspect: 1.65,
};

export function BrushHistogramPreview({
  timeline,
  timestep = 99,
  rangeMin,
  rangeMax,
  highlightColor,
  legendLabel,
  sizeOpts = DEFAULT_SIZE,
}: BrushHistogramPreviewProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const { width, height } = useChartSizeFromOpts(wrapRef, sizeOpts);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl || width < 80) return;

    const margin = { top: 34, right: 18, bottom: 46, left: 54 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    const hist = timeline.histograms[timestep];
    if (!hist) return;

    const edges = timeline.logBinEdges;
    const centers = edges.slice(0, -1).map((e, i) => Math.sqrt(e * edges[i + 1]!));
    const total = d3.sum(hist) || 1;
    const pct = hist.map((v) => (v / total) * 100);

    const lo = Math.min(rangeMin, rangeMax);
    const hi = Math.max(rangeMin, rangeMax);

    const x = d3
      .scaleLog()
      .domain([timeline.globalMin, timeline.globalMax])
      .range([0, innerW]);

    const y = d3
      .scaleLinear()
      .domain([0, d3.max(pct) ?? 0])
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
        .ticks(5)
        .tickSize(-innerW)
        .tickFormat(() => ''),
    );
    styleGrid(gridG);

    const barW = innerW / pct.length;
    g.selectAll('rect.bar')
      .data(pct)
      .join('rect')
      .attr('class', 'bar')
      .attr('x', (_, i) => x(centers[i]!) - barW / 2)
      .attr('y', (d) => y(d))
      .attr('width', Math.max(1, barW * 0.88))
      .attr('height', (d) => Math.max(0, innerH - y(d)))
      .attr('fill', (_, i) => {
        const c = centers[i]!;
        return c >= lo && c <= hi * 1.001 ? highlightColor : '#7c6cf0';
      })
      .attr('opacity', (_, i) => {
        const c = centers[i]!;
        return c >= lo && c <= hi * 1.001 ? 0.96 : 0.82;
      });

    const xAxis = g
      .append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6, '.2f'));
    styleAxisText(xAxis);
    xAxis.selectAll('text').attr('font-size', 11);

    const yAxis = g.append('g').call(d3.axisLeft(y).ticks(5));
    styleAxisText(yAxis);
    yAxis.selectAll('text').attr('font-size', 11);

    g.append('text')
      .attr('x', innerW / 2)
      .attr('y', innerH + 36)
      .attr('text-anchor', 'middle')
      .attr('fill', LABEL_FILL)
      .attr('font-size', 12)
      .attr('font-weight', 600)
      .text('密度 ρ (log)');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -innerH / 2)
      .attr('y', -40)
      .attr('text-anchor', 'middle')
      .attr('fill', LABEL_FILL)
      .attr('font-size', 12)
      .attr('font-weight', 600)
      .text('Probability mass×100');

    const legendW = Math.min(innerW * 0.52, 220);
    g.append('rect')
      .attr('x', innerW - legendW)
      .attr('y', -26)
      .attr('width', legendW)
      .attr('height', 22)
      .attr('rx', 5)
      .attr('fill', 'rgba(6, 10, 20, 0.88)')
      .attr('stroke', 'rgba(78, 196, 255, 0.22)');

    g.append('rect')
      .attr('x', innerW - legendW + 8)
      .attr('y', -20)
      .attr('width', 12)
      .attr('height', 12)
      .attr('rx', 2)
      .attr('fill', highlightColor);

    g.append('text')
      .attr('x', innerW - legendW + 26)
      .attr('y', -10)
      .attr('fill', LABEL_FILL)
      .attr('font-size', 11)
      .attr('font-weight', 600)
      .text(legendLabel);
  }, [
    timeline,
    timestep,
    rangeMin,
    rangeMax,
    highlightColor,
    legendLabel,
    width,
    height,
  ]);

  return (
    <div
      ref={wrapRef}
      className="chart-responsive chart-responsive-fill brush-hist-preview"
    >
      <svg ref={svgRef} aria-label={legendLabel} />
    </div>
  );
}
