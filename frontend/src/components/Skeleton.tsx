/** 灰色脉冲占位块 */
export function SkeletonBar({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse rounded-md bg-canvas ${className}`} />
  );
}

/** Agent 卡片骨架屏：圆形图标 + 标题 + 大数字 + 若干行说明 */
export default function CardSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div>
      <div className="mb-6 flex items-center gap-3">
        <div className="h-10 w-10 animate-pulse rounded-full bg-canvas" />
        <div className="space-y-1.5">
          <SkeletonBar className="h-3.5 w-20" />
          <SkeletonBar className="h-3 w-14" />
        </div>
      </div>
      <SkeletonBar className="h-11 w-32" />
      <div className="mt-6 space-y-2.5">
        {Array.from({ length: rows }).map((_, i) => (
          <SkeletonBar key={i} className="h-3 w-full" />
        ))}
        <SkeletonBar className="h-3 w-3/5" />
      </div>
    </div>
  );
}
