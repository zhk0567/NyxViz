interface InfographicHeaderProps {
  num: string;
  title: string;
  subtitle?: string;
}

export function InfographicHeader({ num, title, subtitle }: InfographicHeaderProps) {
  return (
    <header className="ig-header">
      <h2 className="ig-title">
        <span className="ig-num">{num}</span>
        <span className="ig-title-text">{title}</span>
      </h2>
      {subtitle ? <p className="ig-subtitle">{subtitle}</p> : null}
    </header>
  );
}
