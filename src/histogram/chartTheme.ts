import type * as d3 from 'd3';

export type ChartThemeTier = 'default' | 'compact' | 'poster';

export interface ChartTheme {
  axisFill: string;
  gridStroke: string;
  labelFill: string;
  domainWidth: number;
  tickWidth: number;
}

export const AXIS_FILL = '#9aa3b8';
export const GRID_STROKE = 'rgba(154, 163, 184, 0.18)';
export const LABEL_FILL = '#c8d0e0';

const DEFAULT_THEME: ChartTheme = {
  axisFill: AXIS_FILL,
  gridStroke: GRID_STROKE,
  labelFill: LABEL_FILL,
  domainWidth: 1,
  tickWidth: 1,
};

const COMPACT_THEME: ChartTheme = {
  axisFill: '#c8d8ec',
  gridStroke: 'rgba(184, 200, 220, 0.28)',
  labelFill: '#d4deee',
  domainWidth: 1.25,
  tickWidth: 1,
};

const POSTER_THEME: ChartTheme = {
  axisFill: '#b8c8dc',
  gridStroke: 'rgba(184, 200, 220, 0.22)',
  labelFill: '#dce4f0',
  domainWidth: 1.15,
  tickWidth: 1,
};

export function getChartTheme(tier: ChartThemeTier): ChartTheme {
  switch (tier) {
    case 'compact':
      return COMPACT_THEME;
    case 'poster':
      return POSTER_THEME;
    default:
      return DEFAULT_THEME;
  }
}

export function styleGrid(
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
  theme: ChartTheme = DEFAULT_THEME,
) {
  g.selectAll('line').attr('stroke', theme.gridStroke);
  g.selectAll('path').attr('stroke', theme.gridStroke);
}

export function styleAxisText(
  sel: d3.Selection<d3.BaseType, unknown, null, undefined>,
  theme: ChartTheme = DEFAULT_THEME,
) {
  sel.selectAll('text').attr('fill', theme.axisFill);
  sel.selectAll('line')
    .attr('stroke', theme.axisFill)
    .attr('stroke-width', theme.tickWidth);
  sel.selectAll('path.domain')
    .attr('stroke', theme.axisFill)
    .attr('stroke-width', theme.domainWidth);
  sel.selectAll('path:not(.domain)').attr('stroke', theme.axisFill);
}

/** @deprecated 使用 getChartTheme('compact') */
export const compactChartTheme = COMPACT_THEME;
