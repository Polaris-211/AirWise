import { useEffect, useMemo, useRef, useState } from "react";
import { searchCities, type City } from "../cities";

interface CitySearchInputProps {
  /** 当前值：城市三字码 */
  value: string;
  onChange: (code: string) => void;
  /** 列表关闭状态下按回车，冒泡给外部触发查询 */
  onEnter?: () => void;
  placeholder?: string;
  label: string;
}

/** 搜索式城市选择：支持中文、拼音、三字码匹配 + 键盘导航 */
export default function CitySearchInput({
  value,
  onChange,
  onEnter,
  placeholder,
  label,
}: CitySearchInputProps) {
  // 输入框里显示的文本，聚焦后可自由输入关键词
  const [keyword, setKeyword] = useState(value);
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(0);
  const wrapRef = useRef<HTMLDivElement>(null);
  const listRef = useRef<HTMLUListElement>(null);

  const matches = useMemo(() => searchCities(keyword), [keyword]);

  // 外部值变化时同步（例如表单重置）
  useEffect(() => {
    setKeyword(value);
  }, [value]);

  // 点击组件外部关闭列表，并把输入回滚为已选值
  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (!wrapRef.current?.contains(e.target as Node)) {
        setOpen(false);
        setKeyword(value);
      }
    };
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, [open, value]);

  // 键盘上下移动时把高亮项滚进可视区
  useEffect(() => {
    if (!open) return;
    listRef.current?.children[activeIdx]?.scrollIntoView({ block: "nearest" });
  }, [activeIdx, open]);

  /** 选中某个城市 */
  const pick = (city: City) => {
    onChange(city.code);
    setKeyword(city.code);
    setOpen(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!open) {
      // 列表已关闭：回车交给外部触发分析
      if (e.key === "Enter") onEnter?.();
      if (e.key === "ArrowDown") {
        setOpen(true);
        setActiveIdx(0);
        e.preventDefault();
      }
      return;
    }

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault();
        setActiveIdx((i) => (i + 1) % Math.max(matches.length, 1));
        break;
      case "ArrowUp":
        e.preventDefault();
        setActiveIdx(
          (i) => (i - 1 + Math.max(matches.length, 1)) % Math.max(matches.length, 1)
        );
        break;
      case "Enter":
        e.preventDefault();
        if (matches[activeIdx]) pick(matches[activeIdx]);
        break;
      case "Escape":
        setOpen(false);
        setKeyword(value);
        break;
    }
  };

  return (
    <div className="relative" ref={wrapRef}>
      <span className="mb-2 block text-[13px] text-subtle">{label}</span>
      <input
        className="w-full rounded-control border border-[rgba(255,255,255,0.85)] bg-white/55 px-3.5 py-2.5 text-[15px] text-[#1d1d1f] outline-none backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_2px_8px_rgba(0,0,0,0.06)] transition-all duration-250 ease-out-soft placeholder:text-[#86868b] focus:border-[#0071e3] focus:shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_0_0_3px_rgba(0,113,227,0.15)]"
        value={keyword}
        placeholder={placeholder}
        autoComplete="off"
        onChange={(e) => {
          setKeyword(e.target.value);
          setOpen(true);
          setActiveIdx(0);
        }}
        onFocus={() => {
          setOpen(true);
          setActiveIdx(0);
        }}
        onKeyDown={handleKeyDown}
      />

      {/* 匹配结果：Apple 毛玻璃浮层 */}
      {open && matches.length > 0 && (
        <ul
          ref={listRef}
          className="animate-rise-in absolute left-0 right-0 top-full z-50 mt-2 max-h-72 overflow-y-auto rounded-[16px] border border-white/50 bg-white/95 shadow-[0_12px_40px_rgba(0,0,0,0.12)] backdrop-blur-xl backdrop-saturate-150"
        >
          {matches.map((city, idx) => (
            <li key={city.code}>
              <button
                type="button"
                // 用 mousedown 抢在 blur 之前，避免点击丢失
                onMouseDown={(e) => {
                  e.preventDefault();
                  pick(city);
                }}
                onMouseEnter={() => setActiveIdx(idx)}
                className={`flex w-full items-baseline justify-between px-4 py-2.5 text-left transition-colors duration-150 ease-out-soft ${
                  idx === activeIdx ? "bg-black/5" : "hover:bg-black/5"
                }`}
              >
                <span className="flex items-baseline gap-2">
                  <span className="text-[15px] text-ink">{city.name}</span>
                  <span className="text-[12px] text-subtle">{city.airport}</span>
                </span>
                <span className="tnum text-[12px] text-subtle">{city.code}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
