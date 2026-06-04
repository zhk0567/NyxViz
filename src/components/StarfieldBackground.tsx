import { useMemo } from 'react';
import '@/styles/starfield.css';

export interface StarfieldBackgroundProps {
  count?: number;
  seed?: number;
  className?: string;
}

type StarTone = 'white' | 'cyan' | 'gold';

interface Star {
  x: number;
  y: number;
  size: number;
  baseOpacity: number;
  delay: number;
  duration: number;
  tone: StarTone;
}

function seededRandom(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

function buildStars(count: number, seed: number): Star[] {
  const rnd = seededRandom(seed);
  return Array.from({ length: count }, () => {
    const pick = rnd();
    const tone: StarTone = pick > 0.92 ? 'gold' : pick > 0.78 ? 'cyan' : 'white';
    return {
      x: rnd() * 100,
      y: rnd() * 100,
      size: rnd() * 1.8 + 0.6,
      baseOpacity: rnd() * 0.45 + 0.25,
      delay: rnd() * 6,
      duration: rnd() * 2.5 + 2.5,
      tone,
    };
  });
}

export function StarfieldBackground({
  count = 140,
  seed = 7,
  className = '',
}: StarfieldBackgroundProps) {
  const stars = useMemo(() => buildStars(count, seed), [count, seed]);

  return (
    <div className={`starfield-bg${className ? ` ${className}` : ''}`} aria-hidden>
      <div className="starfield-nebula" />
      {stars.map((star, i) => (
        <span
          key={i}
          className={`starfield-star starfield-star--${star.tone}`}
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
    </div>
  );
}
