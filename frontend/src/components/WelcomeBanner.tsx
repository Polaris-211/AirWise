import { useState } from "react";

const STORAGE_KEY = "airwise.welcome.dismissed";

function wasDismissed(): boolean {
  try {
    return localStorage.getItem(STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

/** 首次访问的轻量引导条，关闭后写入 localStorage，不再出现 */
export default function WelcomeBanner() {
  const [visible, setVisible] = useState(() => !wasDismissed());

  if (!visible) return null;

  const dismiss = () => {
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch {
      // 隐私模式写不进去也只关掉本次
    }
    setVisible(false);
  };

  return (
    <div
      role="status"
      className="mb-4 flex items-start gap-3 rounded-[14px] bg-[#e8f2fc] px-4 py-3 text-[13px] leading-relaxed text-[#3a5a7a] sm:mb-5"
    >
      <p className="min-w-0 flex-1">
        欢迎使用 AirWise · 输入出发地与目的地，点击「开始分析」查看价格走势与购买建议
      </p>
      <button
        type="button"
        aria-label="关闭引导"
        onClick={dismiss}
        className="-mr-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[#7a93a8] transition-colors duration-250 ease-out-soft hover:bg-white/80 hover:text-[#1d1d1f]"
      >
        <svg
          viewBox="0 0 12 12"
          className="h-3 w-3"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          aria-hidden="true"
        >
          <path d="M2 2l8 8M10 2L2 10" />
        </svg>
      </button>
    </div>
  );
}
