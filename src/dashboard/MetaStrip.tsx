const ITEMS = [
  {
    glyph: (
      <svg viewBox="0 0 24 24" aria-hidden>
        <path d="M4 4h6v6H4V4zm10 0h6v6h-6V4zM4 14h6v6H4v-6zm10 0h6v6h-6v-6z" fill="currentColor" />
      </svg>
    ),
    label: '模拟网格',
    value: '128³',
  },
  {
    glyph: (
      <svg viewBox="0 0 24 24" aria-hidden>
        <circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" strokeWidth="2" />
        <path d="M12 7v5l3 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
    ),
    label: '时间步',
    value: '100 步',
  },
  {
    glyph: (
      <svg viewBox="0 0 24 24" aria-hidden>
        <text x="5" y="17" fill="currentColor" fontSize="14" fontWeight="700">
          ρ
        </text>
      </svg>
    ),
    label: '物理量',
    value: '气体密度',
  },
];

export function MetaStrip() {
  return (
    <ul className="meta-strip" aria-label="模拟参数">
      {ITEMS.map((it) => (
        <li key={it.label} className="meta-item">
          <span className="meta-glyph">{it.glyph}</span>
          <span className="meta-copy">
            <span className="meta-label">{it.label}</span>
            <span className="meta-value">{it.value}</span>
          </span>
        </li>
      ))}
    </ul>
  );
}
