import { airportLabel } from "../airports";
import { SkeletonBar } from "./Skeleton";
import type { FlightPriceRow } from "../types";

interface FlightListProps {
  flights: FlightPriceRow[];
  loading?: boolean;
  /** true = 有行李，展示含行李总价 */
  withBaggage?: boolean;
}

/** 当前口径下的含税总价；旧数据没有拆解字段时回落到 price */
function totalOf(f: FlightPriceRow, withBaggage: boolean): number {
  const value = withBaggage ? f.price_with_baggage : f.price_no_baggage;
  return value ?? f.price;
}

/** 价格明细文案：票面 + 机建 + 燃油（+ 行李） */
function breakdownOf(f: FlightPriceRow, withBaggage: boolean): string | null {
  if (f.base_price == null) return null;
  const parts = [
    `票面 ¥${f.base_price.toFixed(0)}`,
    `机建 ¥${(f.tax_airport ?? 0).toFixed(0)}`,
    `燃油 ¥${(f.tax_fuel ?? 0).toFixed(0)}`,
  ];
  if (withBaggage && f.price_with_baggage != null && f.price_no_baggage != null) {
    parts.push(`行李 ¥${(f.price_with_baggage - f.price_no_baggage).toFixed(0)}`);
  }
  return parts.join(" + ");
}

/** 可选航班列表：按当前口径的总价升序，最低价加绿色标签 */
export default function FlightList({
  flights,
  loading = false,
  withBaggage = true,
}: FlightListProps) {
  // 同一航班号可能被多次采集，只保留每个航班最新的一条
  const latestByFlightNo = new Map<string, FlightPriceRow>();
  for (const f of flights) {
    const prev = latestByFlightNo.get(f.flight_no);
    if (!prev || f.captured_at > prev.captured_at) {
      latestByFlightNo.set(f.flight_no, f);
    }
  }
  const rows = [...latestByFlightNo.values()].sort(
    (a, b) => totalOf(a, withBaggage) - totalOf(b, withBaggage)
  );
  const lowest = rows.length > 0 ? totalOf(rows[0], withBaggage) : null;

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
      {rows.map((f) => {
        const total = totalOf(f, withBaggage);
        const breakdown = breakdownOf(f, withBaggage);

        return (
          <li
            key={f.id}
            className="flex items-center gap-4 py-3.5 transition-colors duration-250 ease-out-soft hover:bg-black/[0.02]"
          >
            {/* 航司中文名 + 航班号 + 起降机场，纯文字展示 */}
            <div className="min-w-0 flex-1">
              <p className="truncate">
                <span className="text-[14px] text-ink">{f.airline}</span>
                <span className="tnum ml-2 text-[13px] text-subtle">
                  {f.flight_no}
                </span>
              </p>
              <p className="mt-0.5 truncate text-[12px] text-subtle">
                {airportLabel(f.dep_airport)} → {airportLabel(f.arr_airport)}
              </p>
            </div>

            {/* 起飞时间 */}
            <span className="tnum shrink-0 text-[14px] text-subtle">
              {f.depart_time ?? "—"}
            </span>

            {/* 含税总价 + 明细 */}
            <div className="shrink-0 text-right">
              <div className="flex items-center justify-end gap-2">
                {total === lowest && (
                  <span className="rounded-full bg-[#e8f8ec] px-2 py-0.5 text-[12px] font-medium text-[#1a8c3c]">
                    最低
                  </span>
                )}
                <span className="rounded-full bg-canvas px-1.5 py-0.5 text-[11px] text-subtle">
                  含税
                </span>
                <span className="tnum text-[17px] font-semibold text-ink">
                  ¥{total.toFixed(0)}
                </span>
              </div>
              {breakdown && (
                <p className="tnum mt-1 text-[12px] text-subtle">{breakdown}</p>
              )}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
