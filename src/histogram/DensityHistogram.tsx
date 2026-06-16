import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { TimelineData } from '@/data/types';
import { useAppStore } from '@/store/useAppStore';
import { useChartSizeFromOpts, type ChartSizeOptions } from '@/hooks/useChartSize';
import { getChartTheme, LABEL_FILL, styleAxisText, styleGrid } from './chartTheme';

interface DensityHistogramProps {
  timeline: TimelineData;
  sizeOpts?: ChartSizeOptions;
}

export function DensityHistogram({ timeline, sizeOpts }: DensityHistogramProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const { width, height } = useChartSizeFromOpts(wrapRef, sizeOpts);
  const svgRef = useRef<SVGSVGElement>(null);
  const chartRef = useRef<{
    x: d3.ScaleLog<number, number>;
    innerH: number;
    g: d3.Selection<SVGGElement, unknown, null, undefined>;
    selection: d3.Selection<SVGRectElement, unknown, null, undefined> | null;
    bars: d3.Selection<SVGRectElement, number, SVGGElement, unknown>;
    centers: number[];
  } | null>(null);

  const timestep = useAppStore((s) => s.timestep);
  const setBrushRange = useAppStore((s) => s.setBrushRange);
  const brushRange = useAppStore((s) => s.brushRange);
  const videoReadable = sizeOpts?.videoReadable === true;
  const [drawStep, setDrawStep] = useState(timestep);

  useEffect(() => {
    if (!videoReadable) {
      setDrawStep(timestep);
      return;
    }
    const t = window.setTimeout(() => setDrawStep(timestep), 280);
    return () => window.clearTimeout(t);
  }, [timestep, videoReadable]);

  useEffect(() => {
    const svgEl = svgRef.current;
    if (!svgEl) return;

    const compact =
      !videoReadable && (sizeOpts?.maxHeight ?? 320) <= 200;
    const theme = getChartTheme(
      videoReadable ? 'video' : compact ? 'compact' : 'default',
    );
    const margin = videoReadable
      ? { top: 16, right: 16, bottom: 36, left: 54 }
      : compact
        ? { top: 14, right: 14, bottom: 32, left: 48 }
        : { top: 16, right: 16, bottom: 36, left: 52 };
    const innerW = width - margin.left - margin.right;
    const innerH = height - margin.top - margin.bottom;

    const hist = timeline.histograms[drawStep];
    if (!hist) return;

    const edges = timeline.logBinEdges;
    const centers = edges.slice(0, -1).map((e, i) => {
      const e2 = edges[i + 1]!;
      return Math.sqrt(e * e2);
    });

    const total = d3.sum(hist) || 1;
    const pct = hist.map((v) => (v / total) * 100);

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

    const defs = svg.append('defs');
    const grad = defs
      .append('linearGradient')
      .attr('id', 'hist-bar-grad')
      .attr('x1', '0%')
      .attr('y1', '0%')
      .attr('x2', '0%')
      .attr('y2', '100%');
    grad.append('stop').attr('offset', '0%').attr('stop-color', '#7c6cf0');
    grad.append('stop').attr('offset', '100%').attr('stop-color', '#3dd6c6');

    const g = svg
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const gridG = g.append('g').attr('class', 'grid');
    gridG
      .call(
        d3
          .axisLeft(y)
          .ticks(5)
          .tickSize(-innerW)
          .tickFormat(() => ''),
      );
    styleGrid(gridG, theme);

    const barW = innerW / pct.length;
    const bars = g
      .selectAll('rect.bar')
      .data(pct)
      .join('rect')
      .attr('class', 'bar')
      .attr('x', (_, i) => x(centers[i]!) - barW / 2)
      .attr('y', (d) => y(d))
      .attr('width', Math.max(1, barW * 0.9))
      .attr('height', (d) => innerH - y(d))
      .attr('fill', 'url(#hist-bar-grad)')
      .attr('opacity', 0.92);

    const selection = g
      .append('rect')
      .attr('class', 'brush-selection')
      .attr('y', 0)
      .attr('height', innerH)
      .attr('fill', 'rgba(245, 200, 66, 0.22)')
      .attr('stroke', '#f5c842')
      .attr('stroke-width', 2)
      .attr('opacity', 0)
      .attr('pointer-events', 'none');

    const xAxis = g
      .append('g')
      .attr('transform', `translate(0,${innerH})`)
      .call(d3.axisBottom(x).ticks(6, '.2f'));
    styleAxisText(xAxis, theme);
    const yAxis = g.append('g').call(d3.axisLeft(y).ticks(5));
    styleAxisText(yAxis, theme);

    g.append('text')
      .attr('class', 'step-label')
      .attr('x', innerW / 2)
      .attr('y', innerH + 30)
      .attr('text-anchor', 'middle')
      .attr('fill', LABEL_FILL)
      .attr('font-size', videoReadable ? 12 : 11)
      .text(`密度 (log) — 时间步 ${drawStep} · Y=Probability mass×100`);

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

    chartRef.current = { x, innerH, g, selection, bars, centers };
  }, [timeline, drawStep, width, height, setBrushRange, sizeOpts]);

  useEffect(() => {
    const chart = chartRef.current;
    const wrap = wrapRef.current;
    if (!chart || !wrap) return;

    let tip = wrap.querySelector('.histogram-tooltip') as HTMLDivElement | null;
    if (!tip) {
      tip = document.createElement('div');
      tip.className = 'histogram-tooltip';
      tip.style.display = 'none';
      wrap.appendChild(tip);
    }

    chart.bars
      .on('mouseenter', function (event, d) {
        const i = chart.bars.nodes().indexOf(this);
        tip!.textContent = `ρ≈${chart.centers[i]!.toExponential(2)} · ${d.toFixed(2)}%`;
        tip!.style.display = 'block';
        tip!.style.left = `${event.offsetX + 12}px`;
        tip!.style.top = `${event.offsetY - 8}px`;
        d3.select(this).attr('opacity', 1);
      })
      .on('mousemove', (event) => {
        tip!.style.left = `${event.offsetX + 12}px`;
        tip!.style.top = `${event.offsetY - 8}px`;
      })
      .on('mouseleave', function () {
        tip!.style.display = 'none';
        d3.select(this).attr('opacity', 0.92);
      });
  }, [drawStep, width, height]);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart?.selection) return;

    if (!brushRange) {
      chart.selection.attr('opacity', 0);
      return;
    }

    chart.selection
      .attr('x', chart.x(brushRange.min))
      .attr('width', Math.max(2, chart.x(brushRange.max) - chart.x(brushRange.min)))
      .attr('opacity', 1);
  }, [brushRange]);

  return (
    <div ref={wrapRef} className="chart-responsive" style={{ position: 'relative' }}>
      <svg ref={svgRef} className="density-histogram" width="100%" />
    </div>
  );
}
