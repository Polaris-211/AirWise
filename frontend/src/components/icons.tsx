/** 细线条图标，统一 1.4px 线宽 */
const base = {
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.4,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
};

/** Monitor：采集信号 */
export function IconWave({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg {...base} className={className}>
      <path d="M2 12h3l2.5-6 3 12 3-9 2.5 5h6" />
    </svg>
  );
}

/** Analyst：走势图 */
export function IconChart({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg {...base} className={className}>
      <path d="M3 3v18h18" />
      <path d="M7 15l4-5 3 3 5-7" />
    </svg>
  );
}

/** Advisor：建议灯泡 */
export function IconBulb({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg {...base} className={className}>
      <path d="M9 18h6" />
      <path d="M10 21h4" />
      <path d="M12 3a6 6 0 0 0-3.5 10.9c.3.3.5.7.5 1.1v.5h6v-.5c0-.4.2-.8.5-1.1A6 6 0 0 0 12 3z" />
    </svg>
  );
}

/** 顶栏提醒铃铛 */
export function IconBell({ className = "h-5 w-5" }: { className?: string }) {
  return (
    <svg {...base} className={className}>
      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9" />
      <path d="M10 21a2 2 0 0 0 4 0" />
    </svg>
  );
}
