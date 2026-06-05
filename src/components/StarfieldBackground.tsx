import { CosmicBackdrop, type CosmicBackdropProps } from '@/components/CosmicBackdrop';

/** @deprecated 使用 CosmicBackdrop；保留兼容旧调用 */
export interface StarfieldBackgroundProps {
  count?: number;
  seed?: number;
  className?: string;
}

export function StarfieldBackground({
  className = '',
}: StarfieldBackgroundProps) {
  const fixed = className.includes('starfield-bg--fixed');
  const props: CosmicBackdropProps = {
    variant: 'poster',
    intensity: 'full',
    fixed,
    className: className.replace('starfield-bg--fixed', '').replace('starfield-bg', '').trim(),
  };
  return <CosmicBackdrop {...props} />;
}
