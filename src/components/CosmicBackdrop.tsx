import { useMemo } from 'react';
import '@/styles/cosmic-backdrop.css';

export type CosmicVariant = 'poster' | 'video' | 'results';
export type CosmicIntensity = 'full' | 'subtle';

export interface CosmicBackdropProps {
  variant?: CosmicVariant;
  intensity?: CosmicIntensity;
  fixed?: boolean;
  className?: string;
}

type StarTone = 'white' | 'cyan' | 'gold';
type StarLayer = 'far' | 'near';

interface Star {
  x: number;
  y: number;
  size: number;
  baseOpacity: number;
  delay: number;
  duration: number;
  tone: StarTone;
  layer: StarLayer;
  bright: boolean;
}

interface Meteor {
  x: number;
  y: number;
  len: number;
  angle: number;
  delay: number;
  cycle: number;
}

const VARIANT_CONFIG: Record<
  CosmicVariant,
  { seed: number; farCount: number; nearCount: number; meteorCount: number }
> = {
  poster: { seed: 13, farCount: 120, nearCount: 80, meteorCount: 5 },
  video: { seed: 42, farCount: 90, nearCount: 70, meteorCount: 4 },
  results: { seed: 7, farCount: 100, nearCount: 60, meteorCount: 3 },
};

function seededRandom(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

function buildStars(
  farCount: number,
  nearCount: number,
  seed: number,
): Star[] {
  const rnd = seededRandom(seed);
  const stars: Star[] = [];

  for (let i = 0; i < farCount; i++) {
    const pick = rnd();
    const tone: StarTone = pick > 0.9 ? 'gold' : pick > 0.75 ? 'cyan' : 'white';
    stars.push({
      x: rnd() * 100,
      y: rnd() * 100,
      size: rnd() * 1.2 + 0.4,
      baseOpacity: rnd() * 0.35 + 0.15,
      delay: rnd() * 8,
      duration: rnd() * 3 + 4,
      tone,
      layer: 'far',
      bright: false,
    });
  }

  for (let i = 0; i < nearCount; i++) {
    const pick = rnd();
    const tone: StarTone = pick > 0.88 ? 'gold' : pick > 0.72 ? 'cyan' : 'white';
    const bright = pick > 0.95;
    stars.push({
      x: rnd() * 100,
      y: rnd() * 100,
      size: bright ? rnd() * 1.2 + 2.2 : rnd() * 1.8 + 0.8,
      baseOpacity: rnd() * 0.5 + 0.3,
      delay: rnd() * 6,
      duration: rnd() * 2.5 + 2,
      tone,
      layer: 'near',
      bright,
    });
  }

  return stars;
}

function buildMeteors(count: number, seed: number): Meteor[] {
  const rnd = seededRandom(seed + 999);
  return Array.from({ length: count }, () => ({
    x: rnd() * 80 + 5,
    y: rnd() * 50 + 2,
    len: rnd() * 60 + 50,
    angle: rnd() * 20 - 45,
    delay: rnd() * 12,
    cycle: rnd() * 8 + 14,
  }));
}

export function CosmicBackdrop({
  variant = 'poster',
  intensity = 'full',
  fixed = false,
  className = '',
}: CosmicBackdropProps) {
  const cfg = VARIANT_CONFIG[variant];
  const stars = useMemo(
    () => buildStars(cfg.farCount, cfg.nearCount, cfg.seed),
    [cfg.farCount, cfg.nearCount, cfg.seed],
  );
  const meteors = useMemo(
    () => buildMeteors(cfg.meteorCount, cfg.seed),
    [cfg.meteorCount, cfg.seed],
  );

  const rootClass = [
    'cosmic-backdrop',
    `cosmic-backdrop--${variant}`,
    intensity === 'subtle' ? 'cosmic-backdrop--subtle' : '',
    fixed ? 'cosmic-backdrop--fixed' : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={rootClass} aria-hidden>
      <div className="cosmic-nebula cosmic-nebula--a" />
      <div className="cosmic-nebula cosmic-nebula--b" />
      <div className="cosmic-nebula cosmic-nebula--c" />
      {stars.map((star, i) => (
        <span
          key={`s-${i}`}
          className={[
            'cosmic-star',
            `cosmic-star--${star.tone}`,
            star.layer === 'far' ? 'cosmic-star--far' : '',
            star.bright ? 'cosmic-star--bright' : '',
          ]
            .filter(Boolean)
            .join(' ')}
          style={{
            left: `${star.x}%`,
            top: `${star.y}%`,
            width: star.size,
            height: star.size,
            opacity: star.baseOpacity,
            ['--star-delay' as string]: `${star.delay}s`,
            ['--star-duration' as string]: `${star.duration}s`,
          }}
        />
      ))}
      {intensity === 'full' &&
        meteors.map((m, i) => (
          <span
            key={`m-${i}`}
            className="cosmic-meteor"
            style={{
              left: `${m.x}%`,
              top: `${m.y}%`,
              ['--meteor-len' as string]: `${m.len}px`,
              ['--meteor-angle' as string]: `${m.angle}deg`,
              ['--meteor-delay' as string]: `${m.delay}s`,
              ['--meteor-cycle' as string]: `${m.cycle}s`,
            }}
          />
        ))}
      {intensity === 'full' && <div className="cosmic-aurora" />}
      <div className="cosmic-vignette" />
    </div>
  );
}
