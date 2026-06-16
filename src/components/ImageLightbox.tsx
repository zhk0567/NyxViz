import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  type ImgHTMLAttributes,
  type MouseEvent,
  type PointerEvent,
  type ReactNode,
  type WheelEvent,
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
    document.documentElement.classList.add('image-lightbox-open');
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.documentElement.classList.remove('image-lightbox-open');
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

interface LightboxZoomViewProps {
  src: string;
  alt: string;
}

/** 滚轮/拖拽局部放大，最大可至原图像素 1:1 */
function LightboxZoomView({ src, alt }: LightboxZoomViewProps) {
  const stageRef = useRef<HTMLDivElement>(null);
  const [natural, setNatural] = useState({ w: 0, h: 0 });
  const [stage, setStage] = useState({ w: 0, h: 0 });
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragRef = useRef<{ px: number; py: number; ox: number; oy: number } | null>(null);
  const metricsRef = useRef({ fit: 1, max: 4, min: 0.35 });
  const lastStageRef = useRef({ w: 0, h: 0 });
  const fittedSrcRef = useRef<string | null>(null);

  const measureStage = useCallback(() => {
    const el = stageRef.current;
    if (!el) return;
    const w = el.clientWidth;
    const h = el.clientHeight;
    if (w === lastStageRef.current.w && h === lastStageRef.current.h) return;
    lastStageRef.current = { w, h };
    setStage({ w, h });
  }, []);

  useLayoutEffect(() => {
    measureStage();
    const el = stageRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => measureStage());
    ro.observe(el);
    return () => ro.disconnect();
  }, [measureStage]);

  useEffect(() => {
    fittedSrcRef.current = null;
    lastStageRef.current = { w: 0, h: 0 };
    setNatural({ w: 0, h: 0 });
    setScale(1);
    setOffset({ x: 0, y: 0 });
  }, [src]);

  useEffect(() => {
    if (!natural.w || !natural.h || !stage.w || !stage.h) return;
    const fit = Math.min(stage.w / natural.w, stage.h / natural.h);
    const max = fit * Math.max(natural.w / stage.w, natural.h / stage.h, 1);
    metricsRef.current = { fit, max: Math.max(max, fit * 1.5), min: fit * 0.4 };
    if (fittedSrcRef.current === src) return;
    fittedSrcRef.current = src;
    setScale(fit);
    setOffset({
      x: (stage.w - natural.w * fit) / 2,
      y: (stage.h - natural.h * fit) / 2,
    });
  }, [natural.w, natural.h, stage.w, stage.h, src]);

  const clampOffset = useCallback(
    (nx: number, ny: number, sc: number) => {
      const imgW = natural.w * sc;
      const imgH = natural.h * sc;
      const minX = Math.min(0, stage.w - imgW);
      const minY = Math.min(0, stage.h - imgH);
      return {
        x: Math.min(0, Math.max(minX, nx)),
        y: Math.min(0, Math.max(minY, ny)),
      };
    },
    [natural.w, natural.h, stage.w, stage.h],
  );

  const resetView = useCallback(() => {
    const { fit } = metricsRef.current;
    if (!natural.w) return;
    setScale(fit);
    setOffset({
      x: (stage.w - natural.w * fit) / 2,
      y: (stage.h - natural.h * fit) / 2,
    });
  }, [natural.w, natural.h, stage.w, stage.h]);

  const zoomAt = useCallback(
    (clientX: number, clientY: number, factor: number) => {
      const rect = stageRef.current?.getBoundingClientRect();
      if (!rect) return;
      const { min, max } = metricsRef.current;
      const mx = clientX - rect.left;
      const my = clientY - rect.top;
      setScale((prev) => {
        const next = Math.min(max, Math.max(min, prev * factor));
        setOffset((prevOff) => {
          const nx = mx - ((mx - prevOff.x) * next) / prev;
          const ny = my - ((my - prevOff.y) * next) / prev;
          return clampOffset(nx, ny, next);
        });
        return next;
      });
    },
    [clampOffset],
  );

  const onWheel = useCallback(
    (e: WheelEvent<HTMLDivElement>) => {
      e.preventDefault();
      e.stopPropagation();
      const factor = e.deltaY < 0 ? 1.12 : 1 / 1.12;
      zoomAt(e.clientX, e.clientY, factor);
    },
    [zoomAt],
  );

  const onPointerDown = (e: PointerEvent<HTMLDivElement>) => {
    if (e.button !== 0) return;
    e.currentTarget.setPointerCapture(e.pointerId);
    dragRef.current = { px: e.clientX, py: e.clientY, ox: offset.x, oy: offset.y };
  };

  const onPointerMove = (e: PointerEvent<HTMLDivElement>) => {
    const d = dragRef.current;
    if (!d) return;
    const nx = d.ox + (e.clientX - d.px);
    const ny = d.oy + (e.clientY - d.py);
    setOffset(clampOffset(nx, ny, scale));
  };

  const onPointerUp = () => {
    dragRef.current = null;
  };

  const atNative =
    natural.w > 0 && stage.w > 0 && scale >= metricsRef.current.max * 0.96;

  return (
    <figure className="vd-lightbox-figure vd-lightbox-figure--zoom">
      <div
        ref={stageRef}
        className="vd-lightbox-zoom-stage"
        onWheel={onWheel}
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onDoubleClick={resetView}
      >
        <div
          className="vd-lightbox-zoom-inner"
          style={{
            transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})`,
          }}
        >
          <img
            src={src}
            alt={alt}
            className="vd-lightbox-img vd-lightbox-img--native"
            draggable={false}
            onLoad={(e) => {
              const img = e.currentTarget;
              setNatural({ w: img.naturalWidth, h: img.naturalHeight });
            }}
          />
        </div>
      </div>
      <div className="vd-lightbox-zoom-hint" aria-hidden="true">
        滚轮缩放 · 拖拽平移 · 双击复位
        {atNative && <span className="vd-lightbox-zoom-badge">原图精度</span>}
      </div>
    </figure>
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
      if (stopPropagation) {
        e.stopPropagation();
        e.nativeEvent.stopImmediatePropagation();
      }
      e.preventDefault();
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
        {lightboxSrc && <LightboxZoomView src={lightboxSrc} alt={alt} />}
      </OverlayLightbox>
    </>
  );
}
