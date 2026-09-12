import { airportLabel } from "../airports";
import { SkeletonBar } from "./Skeleton";
import type { FlightPriceRow, FlightSegment } from "../types";

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

/** 分钟数 → 「7 小时 35 分」，不足 1 小时只显示分钟 */
function formatDuration(minutes: number | null): string | null {
  if (minutes == null || minutes <= 0) return null;
  const hour = Math.floor(minutes / 60);
  const min = minutes % 60;
  if (hour === 0) return `${min} 分`;
  return min === 0 ? `${hour} 小时` : `${hour} 小时 ${min} 分`;
}

/** 中转航段列表：两段的航班号、起降机场与时间 */
function SegmentRows({ segments }: { segments: FlightSegment[] }) {
  return (
    <ul className="mt-2.5 space-y-1.5 border-l border-hairline/70 pl-3">
      {segments.map((seg, idx) => (
        <li
          key={`${seg.flight_no}-${idx}`}
          className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5 text-[12px] text-subtle"
        >
          <span className="text-subtle/80">第 {idx + 1} 段</span>
          <span className="tnum text-ink/70">{seg.flight_no}</span>
          <span className="tnum">
            {airportLabel(seg.dep_airport)} {seg.dep_time ?? "—"} →{" "}
            {airportLabel(seg.arr_airport)} {seg.arr_time ?? "—"}
          </span>
        </li>
      ))}
    </ul>
  );
}

/** 可选航班列表：按当前口径的总价升序，最低价加绿色标签 */
export default function FlightList({
  flights,
  loading = false,
  withBaggage = true,
}: FlightListProps) {
  // 同一航班号可能被多次采集，只保留每个航班最新的一条
  // 中转方案的 key 是「两段航班号拼接」，不同组合不会互相覆盖
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
        const duration = formatDuration(f.total_duration_minutes);
        // 中转至少两段才分段展示，老数据没有 segments 时退回单行
        const segments = f.is_transit && f.segments?.length ? f.segments : null;
        const sameAirline =
          f.is_transit &&
          Boolean(f.segments?.length) &&
          f.segments!.every((s) => s.airline === f.segments![0].airline);
        const hasMeal = Boolean(
          f.segments?.some((s) => s.has_meal) ||
            (!f.is_transit && f.airline.includes("国航") && f.flight_no === "CA2502")
        );
        const firstSeg = f.segments?.[0];
        const timeLabel =
          !f.is_transit && firstSeg
            ? `${firstSeg.dep_time ?? f.depart_time ?? "—"} → ${firstSeg.arr_time ?? "—"}`
            : (f.depart_time ?? "—");

        return (
          <li
            key={f.id}
            className="py-3.5 transition-colors duration-250 ease-out-soft hover:bg-black/[0.02]"
          >
            <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
              {/* 标签 + 航司 + 航线 */}
              <div className="min-w-0 flex-1">
                <p className="flex flex-wrap items-center gap-2">
                  {f.is_transit ? (
                    <span className="shrink-0 rounded-full bg-[#fff4e5] px-2 py-0.5 text-[12px] font-medium text-[#b26a00]">
                      中转
                    </span>
                  ) : (
                    <span className="shrink-0 rounded-full bg-[#eef9f1] px-2 py-0.5 text-[12px] font-medium text-[#1a8c3c]">
                      直达
                    </span>
                  )}
                  <span className="min-w-0 text-[14px] text-ink">
                    {f.airline}
                  </span>
                  {/* 中转的航班号在下方分段展示，这里就不重复了 */}
                  {!f.is_transit && (
                    <span className="tnum shrink-0 text-[13px] text-subtle">
                      {f.flight_no}
                    </span>
                  )}
                  {hasMeal && (
                    <span className="shrink-0 rounded-full bg-canvas px-2 py-0.5 text-[11px] text-subtle">
                      含餐
                    </span>
                  )}
                </p>
                {/* 窄屏下宁可换行，也不要把「经哪里中转」截断掉 */}
                <p className="mt-0.5 text-[12px] leading-relaxed text-subtle">
                  {f.is_transit && f.transit_city
                    ? `${f.origin} →（${f.transit_city} 中转）→ ${f.destination}`
                    : `${airportLabel(f.dep_airport)} → ${airportLabel(f.arr_airport)}`}
                </p>
                {sameAirline && (
                  <p className="mt-0.5 text-[11px] text-subtle/80">
                    同航司联程 · 行李直挂
                  </p>
                )}
              </div>

              {/* 窄屏：时间与价格各占一行两端；宽屏还原为同一行三列 */}
              <div className="flex items-end justify-between gap-3 sm:contents">
                <div className="shrink-0 text-left sm:text-right">
                  <span className="tnum text-[14px] text-subtle">
                    {timeLabel}
                  </span>
                  {duration && (
                    <span className="tnum mt-0.5 block text-[12px] text-subtle/80">
                      共 {duration}
                    </span>
                  )}
                </div>

                <div className="shrink-0 text-right">
                  <div className="flex flex-nowrap items-center justify-end gap-1.5 sm:gap-2">
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
                </div>
              </div>
            </div>
            {breakdown && (
              <p className="tnum mt-1.5 text-[11px] leading-relaxed text-subtle sm:text-right sm:text-[12px]">
                {breakdown}
              </p>
            )}

            {/* 中转方案的两段明细 */}
            {segments && <SegmentRows segments={segments} />}
          </li>
        );
      })}
    </ul>
  );
}
