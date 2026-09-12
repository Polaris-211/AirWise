import { useEffect, useMemo, useRef, useState } from "react";
import { IconChevronLeft, IconChevronRight } from "./icons";

interface DatePickerProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  /** 面板关闭时按回车，交给外部触发查询 */
  onEnter?: () => void;
}

const WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"];

/** 输入控件：半透明白 + 细白边，聚焦蓝描边与光晕 */
const CONTROL =
  "w-full rounded-control border border-[rgba(255,255,255,0.85)] bg-white/55 px-3.5 py-2.5 text-left text-[15px] text-[#1d1d1f] outline-none backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_2px_8px_rgba(0,0,0,0.06)] transition-all duration-250 ease-out-soft focus:border-[#0071e3] focus:shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_0_0_3px_rgba(0,113,227,0.15)]";

function toYmd(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

function parseYmd(s: string): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
  if (!m) return null;
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return Number.isNaN(d.getTime()) ? null : d;
}

function formatDisplay(s: string): string {
  const d = parseYmd(s);
  if (!d) return s || "选择日期";
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`;
}

/** 周一为一周起点，最多 6 行；末周全是下月则收掉 */
function buildCells(year: number, month: number) {
  const first = new Date(year, month, 1);
  const lead = (first.getDay() + 6) % 7;
  const start = new Date(year, month, 1 - lead);
  const cells: { ymd: string; day: number; inMonth: boolean }[] = [];
  for (let i = 0; i < 42; i++) {
    const d = new Date(start.getFullYear(), start.getMonth(), start.getDate() + i);
    cells.push({
      ymd: toYmd(d),
      day: d.getDate(),
      inMonth: d.getMonth() === month,
    });
  }
  if (cells.slice(35).every((c) => !c.inMonth)) return cells.slice(0, 35);
  return cells;
}

/**
 * 玻璃质感日期选择：系统原生日历无法套样式，因此用自定义面板。
 */
export default function DatePicker({
  label,
  value,
  onChange,
  onEnter,
}: DatePickerProps) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  const parsed = parseYmd(value);
  const [cursor, setCursor] = useState(() => parsed ?? new Date());

  useEffect(() => {
    if (!open) return;
    setCursor(parseYmd(value) ?? new Date());
  }, [open, value]);

  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const year = cursor.getFullYear();
  const month = cursor.getMonth();
  const cells = useMemo(() => buildCells(year, month), [year, month]);
  const today = toYmd(new Date());

  const shiftMonth = (delta: number) => {
    setCursor((d) => new Date(d.getFullYear(), d.getMonth() + delta, 1));
  };

  const pick = (ymd: string) => {
    onChange(ymd);
    setOpen(false);
  };

  return (
    <div className="relative" ref={wrapRef}>
      <span className="mb-2 block text-[13px] text-subtle">{label}</span>
      <button
        type="button"
        aria-label={label}
        aria-expanded={open}
        aria-haspopup="dialog"
        onClick={() => setOpen((v) => !v)}
        onKeyDown={(e) => {
          if (!open && e.key === "Enter") {
            e.preventDefault();
            onEnter?.();
          }
        }}
        className={`${CONTROL} tnum`}
      >
        {formatDisplay(value)}
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="选择航班日期"
          className="animate-rise-in absolute left-0 top-full z-50 mt-2 w-[min(100%,308px)] rounded-[16px] border border-white/50 bg-white/95 p-3.5 shadow-[0_12px_40px_rgba(0,0,0,0.12)] backdrop-blur-xl backdrop-saturate-150"
        >
          <div className="mb-3 flex items-center justify-between">
            <button
              type="button"
              aria-label="上个月"
              onClick={() => shiftMonth(-1)}
              className="flex h-8 w-8 items-center justify-center rounded-[10px] text-ink transition-colors duration-250 ease-out-soft hover:bg-[#f5f5f7]"
            >
              <IconChevronLeft />
            </button>
            <p className="text-[15px] font-semibold tracking-tighter text-[#1d1d1f]">
              {year}年 {month + 1}月
            </p>
            <button
              type="button"
              aria-label="下个月"
              onClick={() => shiftMonth(1)}
              className="flex h-8 w-8 items-center justify-center rounded-[10px] text-ink transition-colors duration-250 ease-out-soft hover:bg-[#f5f5f7]"
            >
              <IconChevronRight />
            </button>
          </div>

          <div className="mb-1 grid grid-cols-7">
            {WEEKDAYS.map((w) => (
              <span
                key={w}
                className="py-1 text-center text-[12px] text-[#86868b]"
              >
                {w}
              </span>
            ))}
          </div>

          <div className="grid grid-cols-7">
            {cells.map((cell) => {
              const selected = cell.ymd === value;
              const isToday = cell.ymd === today && !selected;
              return (
                <button
                  key={cell.ymd}
                  type="button"
                  onClick={() => pick(cell.ymd)}
                  className={`mx-auto flex h-9 w-9 items-center justify-center rounded-full text-[13px] transition-colors duration-150 ease-out-soft ${
                    selected
                      ? "bg-accent text-white"
                      : isToday
                        ? "text-accent hover:bg-[#f5f5f7]"
                        : cell.inMonth
                          ? "text-[#1d1d1f] hover:bg-[#f5f5f7]"
                          : "text-[#86868b]/55 hover:bg-[#f5f5f7]"
                  }`}
                >
                  {cell.day}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
