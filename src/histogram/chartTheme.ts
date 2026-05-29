import type * as d3 from 'd3';

export const AXIS_FILL = '#9aa3b8';
export const GRID_STROKE = 'rgba(154, 163, 184, 0.18)';
export const LABEL_FILL = '#c8d0e0';

export function styleGrid(
  g: d3.Selection<SVGGElement, unknown, null, undefined>,
) {
  g.selectAll('line').attr('stroke', GRID_STROKE);
  g.selectAll('path').attr('stroke', GRID_STROKE);
}

export function styleAxisText(
  sel: d3.Selection<d3.BaseType, unknown, null, undefined>,
) {
  sel.selectAll('text').attr('fill', AXIS_FILL);
  sel.selectAll('line').attr('stroke', AXIS_FILL);
  sel.selectAll('path').attr('stroke', AXIS_FILL);
}
