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

function chartTier(sizeOpts?: ChartSizeOptions) {
  const maxH = sizeOpts?.maxHeight ?? 320;
  const minH = sizeOpts?.minHeight ?? 260;
  if (minH >= 300 || maxH >= 360) return 'poster' as const;
  if (maxH <= 200) return 'compact' as const;
  return 'default' as const;
}

export function HistogramOverlay({ timeline, sizeOpts }: HistogramOverlayProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const { width, height } = useChartSizeFromOpts(wrapRef, sizeOpts);
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl || width < 80) return;

    const tier = chartTier(sizeOpts);
    const theme = getChartTheme(
      tier === 'poster' ? 'poster' : tier === 'compact' ? 'compact' : 'default',
    );
    const margin =
      tier === 'poster'
        ? { top: 26, right: 84, bottom: 54, left: 64 }
        : tier === 'compact'
          ? { top: 12, right: 14, bottom: 28, left: 46 }
          : { top: 16, right: 16, bottom: 36, left: 52 };
    const legendFont = tier === 'poster' ? 13 : tier === 'compact' ? 12 : 11;
    const legendStep = tier === 'poster' ? 16 : tier === 'compact' ? 12 : 14;
    const axisFont = tier === 'poster' ? 12 : tier === 'compact' ? 11 : 11;
    const strokeW = tier === 'poster' ? 2.6 : 2.2;
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
        .ticks(tier === 'poster' ? 6 : 5)
        .tickSize(-innerW)
        .tickFormat(() => ''),
    );
    styleGrid(gridG, theme);

    REPRESENTATIVE_STEPS.forEach((t, idx) => {
      const hist = timeline.histograms[t];
      if (!hist) return;
      g.append('path')
        .datum(hist)
        .attr('fill', 'none')
        .attr('stroke', COLORS[idx])
        .attr('stroke-width', strokeW)
        .attr('stroke-linejoin', 'round')
        .attr('stroke-linecap', 'round')
        .attr('opacity', 0.96)
        .attr('d', line);
    });

    const xAxis = g
      .append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(
        d3
          .axisBottom(x)
          .ticks(tier === 'poster' ? 7 : tier === 'compact' ? 4 : 6, '.2f'),
      );
    styleAxisText(xAxis, theme);
    xAxis.selectAll('text').attr('font-size', axisFont).attr('fill', theme.labelFill);

    const yAxis = g.append('g').call(
      d3.axisLeft(y).ticks(tier === 'poster' ? 6 : tier === 'compact' ? 4 : 5),
    );
    styleAxisText(yAxis, theme);
    yAxis.selectAll('text').attr('font-size', axisFont).attr('fill', theme.labelFill);

    if (tier === 'poster') {
      g.append('text')
        .attr('x', innerW / 2)
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
        .text('归一化频数');
    }

    const legendX = innerW - 4;
    const legendY0 = 10;
    if (tier === 'poster') {
      g.insert('rect', ':first-child')
        .attr('x', legendX - 58)
        .attr('y', legendY0 - 6)
        .attr('width', 62)
        .attr('height', REPRESENTATIVE_STEPS.length * legendStep + 8)
        .attr('rx', 6)
        .attr('fill', 'rgba(6, 10, 20, 0.82)')
        .attr('stroke', 'rgba(78, 196, 255, 0.22)');
    }

    REPRESENTATIVE_STEPS.forEach((t, idx) => {
      const ly = legendY0 + idx * legendStep;
      if (tier === 'poster') {
        g.append('line')
          .attr('x1', legendX - 50)
          .attr('x2', legendX - 34)
          .attr('y1', ly)
          .attr('y2', ly)
          .attr('stroke', COLORS[idx]!)
          .attr('stroke-width', 3)
          .attr('stroke-linecap', 'round');
      }
      g.append('text')
        .attr('x', legendX - (tier === 'poster' ? 30 : 56))
        .attr('y', ly + (tier === 'poster' ? 4 : 0))
        .attr('fill', COLORS[idx]!)
        .attr('font-size', legendFont)
        .attr('font-weight', tier === 'poster' ? 600 : 400)
        .text(`t=${t}`);
    });
  }, [timeline, width, height, sizeOpts]);

  return (
    <div ref={wrapRef} className="chart-responsive chart-responsive-fill histogram-overlay-wrap">
      <svg ref={svgRef} className="histogram-overlay" aria-label="多时刻 log 直方图叠加" />
    </div>
  );
}
