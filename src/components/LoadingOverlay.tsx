interface LoadingOverlayProps {
  visible: boolean;
  label?: string;
}

export function LoadingOverlay({ visible, label = '加载中…' }: LoadingOverlayProps) {
  if (!visible) return null;
  return (
    <div className="loading-overlay" role="status">
      <div className="loading-spinner" />
      <span>{label}</span>
    </div>
  );
}
