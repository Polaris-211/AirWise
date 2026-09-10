import { useEffect, useRef, useState } from "react";

interface AnimatedNumberProps {
  value: number;
  /** 小数位数 */
  decimals?: number;
  /** 动画时长，克制一些 */
  duration?: number;
  prefix?: string;
  suffix?: string;
}

/** 数字滚动动画：从上一个值缓动到新值 */
export default function AnimatedNumber({
  value,
  decimals = 0,
  duration = 600,
  prefix = "",
  suffix = "",
}: AnimatedNumberProps) {
  const [display, setDisplay] = useState(value);
  const fromRef = useRef(value);
  const frameRef = useRef(0);

  useEffect(() => {
    const from = fromRef.current;
    const delta = value - from;
    if (delta === 0) {
      setDisplay(value);
      return;
    }

    const start = performance.now();
    const tick = (now: number) => {
      const t = Math.min(1, (now - start) / duration);
      // ease-out，末尾自然减速
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(from + delta * eased);
      if (t < 1) {
        frameRef.current = requestAnimationFrame(tick);
      } else {
        fromRef.current = value;
      }
    };

    frameRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameRef.current);
  }, [value, duration]);

  return (
    <span className="tnum">
      {prefix}
      {display.toFixed(decimals)}
      {suffix}
    </span>
  );
}
