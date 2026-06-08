import {
  useCallback,
  useEffect,
  useState,
  type ImgHTMLAttributes,
  type MouseEvent,
  type ReactNode,
} from 'react';
import { createPortal } from 'react-dom';
import '@/components/image-lightbox.css';

interface OverlayLightboxProps {
  open: boolean;
  label: string;
  onClose: () => void;
  children: ReactNode;
}

export function OverlayLightbox({ open, label, onClose, children }: OverlayLightboxProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = prev;
    };
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      className="image-lightbox"
      role="dialog"
      aria-modal="true"
      aria-label={label}
      onClick={onClose}
    >
      <button type="button" className="image-lightbox-close" onClick={onClose}>
        关闭
      </button>
      <div className="image-lightbox-panel" onClick={(e) => e.stopPropagation()}>
        {children}
      </div>
    </div>,
    document.body,
  );
}

interface ZoomableImageProps extends ImgHTMLAttributes<HTMLImageElement> {
  /** 阻止点击冒泡（如缩略图按钮内） */
  stopPropagation?: boolean;
}

export function ZoomableImage({
  className,
  alt = '',
  src,
  onClick,
  stopPropagation = true,
  ...rest
}: ZoomableImageProps) {
  const [open, setOpen] = useState(false);
  const [lightboxSrc, setLightboxSrc] = useState<string | undefined>(src);
  const close = useCallback(() => setOpen(false), []);

  const handleClick = useCallback(
    (e: MouseEvent<HTMLImageElement>) => {
      if (stopPropagation) e.stopPropagation();
      onClick?.(e);
      setLightboxSrc(e.currentTarget.currentSrc || e.currentTarget.src);
      setOpen(true);
    },
    [onClick, stopPropagation],
  );

  return (
    <>
      <img
        {...rest}
        src={src}
        alt={alt}
        className={['vd-zoomable', className].filter(Boolean).join(' ')}
        onClick={handleClick}
      />
      <OverlayLightbox open={open} label={alt || '图片预览'} onClose={close}>
        <figure className="vd-lightbox-figure">
          <img src={lightboxSrc} alt={alt} className="vd-lightbox-img" />
        </figure>
      </OverlayLightbox>
    </>
  );
}
