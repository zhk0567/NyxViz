const STEPS = [
  {
    num: '1',
    title: 'Nyx 数据',
    sub: '128³ · 100 步',
    icon: (
      <svg viewBox="0 0 32 32" aria-hidden>
        <path
          d="M6 6h8v8H6V6zm12 0h8v8h-8V6zM6 18h8v8H6v-8zm12 0h8v8h-8v-8z"
          fill="currentColor"
        />
      </svg>
    ),
  },
  {
    num: '2',
    title: '体渲染',
    sub: 'vtk.js 体积',
    icon: (
      <svg viewBox="0 0 32 32" aria-hidden>
        <path
          d="M16 4l12 7v10l-12 7L4 21V11L16 4z"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
        />
        <circle cx="16" cy="16" r="3" fill="currentColor" />
      </svg>
    ),
  },
  {
    num: '3',
    title: '时序统计',
    sub: 'precompute',
    icon: (
      <svg viewBox="0 0 32 32" aria-hidden>
        <path
          d="M6 22V14l5 4 5-8 5 6 5-4v10H6z"
          fill="currentColor"
        />
      </svg>
    ),
  },
  {
    num: '4',
    title: '相空间刷选',
    sub: 'D3 + Worker',
    icon: (
      <svg viewBox="0 0 32 32" aria-hidden>
        <rect x="5" y="8" width="22" height="16" rx="2" fill="none" stroke="currentColor" strokeWidth="2" />
        <path d="M9 20 L14 14 L18 17 L23 10" stroke="currentColor" strokeWidth="2" fill="none" />
      </svg>
    ),
  },
  {
    num: '5',
    title: '空间映射',
    sub: 'XY 投影',
    icon: (
      <svg viewBox="0 0 32 32" aria-hidden>
        <ellipse cx="16" cy="16" rx="11" ry="7" fill="none" stroke="currentColor" strokeWidth="2" />
        <circle cx="16" cy="16" r="2" fill="currentColor" />
      </svg>
    ),
  },
  {
    num: '6',
    title: '验证分析',
    sub: '亮脊 / 节点',
    icon: (
      <svg viewBox="0 0 32 32" aria-hidden>
        <path
          d="M8 24 L12 12 L16 18 L20 8 L24 24 Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinejoin="round"
        />
      </svg>
    ),
  },
  {
    num: '7',
    title: '科学发现',
    sub: '宇宙网',
    icon: (
      <svg viewBox="0 0 32 32" aria-hidden>
        <circle cx="10" cy="12" r="3" fill="currentColor" />
        <circle cx="22" cy="10" r="4" fill="currentColor" />
        <circle cx="18" cy="22" r="3" fill="currentColor" />
        <path d="M10 12 L22 10 M22 10 L18 22 M18 22 L10 12" stroke="currentColor" strokeWidth="1.5" />
      </svg>
    ),
  },
] as const;

export function PosterFlowchart() {
  return (
    <div className="pl-flow" role="list" aria-label="分析流程：从涨落到宇宙网">
      {STEPS.map((step, i) => (
        <div key={step.num} className="pl-flow-segment" role="presentation">
          <article className="pl-flow-node" role="listitem">
            <span className="pl-flow-num">{step.num}</span>
            <span className="pl-flow-icon">{step.icon}</span>
            <h3 className="pl-flow-title">{step.title}</h3>
            <p className="pl-flow-sub">{step.sub}</p>
          </article>
          {i < STEPS.length - 1 ? (
            <div className="pl-flow-arrow" aria-hidden>
              <svg viewBox="0 0 48 24" className="pl-flow-arrow-svg">
                <path
                  d="M4 12 H36 M30 6 L38 12 L30 18"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
