'use client';

import { useEffect, useRef, useState } from 'react';

interface AnimatedCounterProps {
  value: number;
  formatter: (val: number) => string;
  duration?: number;
}

export function AnimatedCounter({ value, formatter, duration = 1200 }: AnimatedCounterProps) {
  const [displayValue, setDisplayValue] = useState(0);
  const startTime = useRef<number | null>(null);
  const rafId = useRef<number | null>(null);

  useEffect(() => {
    startTime.current = null;

    function animate(timestamp: number) {
      if (startTime.current === null) startTime.current = timestamp;
      const progress = Math.min((timestamp - startTime.current) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(eased * value);

      if (progress < 1) {
        rafId.current = requestAnimationFrame(animate);
      }
    }

    rafId.current = requestAnimationFrame(animate);
    return () => {
      if (rafId.current) cancelAnimationFrame(rafId.current);
    };
  }, [value, duration]);

  return <span>{formatter(displayValue)}</span>;
}
