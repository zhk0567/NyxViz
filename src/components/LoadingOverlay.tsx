interface LoadingOverlayProps {
  visible: boolean;
  label?: string;
  variant?: 'full' | 'badge';
}

export function LoadingOverlay({
  visible,
  label = '加载中…',
  variant = 'full',
}: LoadingOverlayProps) {
  if (!visible) return null;

  if (variant === 'badge') {
    return (
      <div className="vd-quality-badge" role="status">
        {label}
      </div>
    );
  }

  return (
    <div className="loading-overlay" role="status">
      <div className="loading-spinner" />
      <span>{label}</span>
    </div>
  );
}
