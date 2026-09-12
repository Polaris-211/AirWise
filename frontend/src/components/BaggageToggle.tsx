interface BaggageToggleProps {
  /** true = 有行李，展示含行李总价 */
  checked: boolean;
  onChange: (checked: boolean) => void;
}

/**
 * 行李偏好开关：iOS 液态玻璃风格。
 *
 * 分三层叠出玻璃质感（顺序不能乱，滑块必须在颜色层之上）：
 *   1. 轨道本体 —— 半透明白 + backdrop-blur，做出磨砂底
 *   2. 颜色层   —— 开启半透明蓝 / 关闭半透明灰，铺在磨砂底之上
 *   3. 滑块     —— 半透明白 + backdrop-blur，靠 backdrop 采样把第 2 层的
 *                  颜色透上来，所以看到的是"染色玻璃球"而不是纯白实心球
 *
 * 整体是一个 button，点轨道或右侧文字都能切换。
 */
export default function BaggageToggle({
  checked,
  onChange,
}: BaggageToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label="行李偏好"
      onClick={() => onChange(!checked)}
      className="flex select-none items-center gap-2.5 outline-none"
    >
      {/* 第 1 层 轨道：48×26 胶囊，半透明白磨砂底 + 1px 白描边 */}
      <span className="relative block h-[26px] w-12 shrink-0 rounded-full border border-[rgba(255,255,255,0.6)] bg-[rgba(255,255,255,0.3)] backdrop-blur-md">
        {/* 第 2 层 颜色：开启蓝 / 关闭灰，都带透明度，保证下层磨砂仍然透出来 */}
        <span
          className={`absolute inset-0 rounded-full transition-colors duration-250 ease-out-soft ${
            checked
              ? "bg-[rgba(0,113,227,0.75)]"
              : "bg-[rgba(120,120,128,0.3)]"
          }`}
        />

        {/* 第 3 层 滑块：22px 玻璃球，左右各留 1px */}
        <span
          className={`absolute left-[1px] top-[1px] block h-[22px] w-[22px] rounded-full border-[1.5px] border-[rgba(255,255,255,0.95)] bg-[rgba(255,255,255,0.35)] shadow-[0_2px_8px_rgba(0,0,0,0.18)] backdrop-blur-md transition-transform duration-250 ease-[cubic-bezier(0.4,0,0.2,1)] ${
            checked ? "translate-x-[22px]" : "translate-x-0"
          }`}
        >
          {/* 顶部高光只铺上半，下半透出轨道颜色 */}
          <span className="pointer-events-none absolute inset-x-0 top-0 h-1/2 rounded-t-full bg-[linear-gradient(180deg,rgba(255,255,255,0.85),rgba(255,255,255,0))]" />
        </span>
      </span>

      {/* 文字随状态切换，开启时用主文字色，关闭时用次要灰 */}
      <span
        className={`text-[14px] transition-colors duration-250 ease-out-soft ${
          checked ? "text-[#1d1d1f]" : "text-[#86868b]"
        }`}
      >
        {checked ? "有行李" : "无行李"}
      </span>
    </button>
  );
}
