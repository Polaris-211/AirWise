import { SkeletonBar } from "./Skeleton";
import type { FlightPriceRow } from "../types";

interface FlightListProps {
  flights: FlightPriceRow[];
  loading?: boolean;
}

/** 可选航班列表：按价格升序，最低价加绿色标签 */
export default function FlightList({
  flights,
  loading = false,
}: FlightListProps) {
  // 同一航班号可能被多次采集，只保留每个航班最新的一条
  const latestByFlightNo = new Map<string, FlightPriceRow>();
  for (const f of flights) {
    const prev = latestByFlightNo.get(f.flight_no);
    if (!prev || f.captured_at > prev.captured_at) {
      latestByFlightNo.set(f.flight_no, f);
    }
  }
  const rows = [...latestByFlightNo.values()].sort((a, b) => a.price - b.price);
  const lowest = rows.length > 0 ? rows[0].price : null;

  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonBar key={i} className="h-14 w-full" />
        ))}
      </div>
    );
  }

  if (rows.length === 0) {
    return (
      <p className="py-10 text-center text-[15px] text-subtle">
        暂无航班数据，请先点击开始分析
      </p>
    );
  }

  return (
    <ul className="divide-y divide-hairline/50">
      {rows.map((f) => (
        <li
          key={f.id}
          className="flex items-center justify-between gap-4 py-3.5 transition-colors duration-250 ease-out-soft hover:bg-black/[0.02]"
        >
          {/* 航司 + 航班号 */}
          <div className="min-w-0 flex-1">
            <p className="truncate text-[15px] text-ink">
              {f.airline}
              <span className="tnum ml-2 text-subtle">{f.flight_no}</span>
            </p>
          </div>

          {/* 起飞时间 */}
          <span className="tnum shrink-0 text-[14px] text-subtle">
            {f.depart_time ?? "—"}
          </span>

          {/* 价格 + 最低价标签 */}
          <div className="flex shrink-0 items-center gap-2.5">
            {f.price === lowest && (
              <span className="rounded-full bg-[#e8f8ec] px-2 py-0.5 text-[12px] font-medium text-[#1a8c3c]">
                最低
              </span>
            )}
            <span className="tnum w-20 text-right text-[17px] font-semibold text-ink">
              ¥{f.price.toFixed(0)}
            </span>
          </div>
        </li>
      ))}
    </ul>
  );
}
