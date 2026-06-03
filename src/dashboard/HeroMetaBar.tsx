interface HeroMetaBarProps {
  sigma: string;
  spanPct: string;
}

export function HeroMetaBar({ sigma, spanPct }: HeroMetaBarProps) {
  const items = [
    { label: '128³ 网格', value: 'Nyx 模拟' },
    { label: '100 时间步', value: 't=0…99' },
    { label: '物理量', value: '气体密度 ρ' },
  ];

  return (
    <div className="pl-hero-meta">
      <div className="pl-hero-meta-chips">
        {items.map((it) => (
          <span key={it.label} className="pl-hero-chip">
            <strong>{it.label}</strong>
            <span>{it.value}</span>
          </span>
        ))}
      </div>
      <p className="pl-hero-meta-stats">
        t=99 · σ={sigma} · p99−p01 +{spanPct}%
      </p>
    </div>
  );
}
