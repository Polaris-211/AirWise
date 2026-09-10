import { useEffect } from "react";

interface ToastProps {
  message: string;
  /** 自动消失后回调，用于清空外部状态 */
  onClose: () => void;
  /** 停留时长，默认 3 秒 */
  duration?: number;
}

/** 顶部错误提示条：浅红底，3 秒后自动消失 */
export default function Toast({
  message,
  onClose,
  duration = 3000,
}: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, duration);
    return () => clearTimeout(timer);
  }, [message, duration, onClose]);

  return (
    <div className="fixed inset-x-0 top-16 z-50 flex justify-center px-6">
      <div
        role="alert"
        className="animate-slide-down flex items-center gap-2.5 rounded-control bg-[#fdecec] px-5 py-3 text-[14px] text-danger shadow-card"
      >
        <svg
          className="h-4 w-4 shrink-0"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
        >
          <circle cx="12" cy="12" r="9" />
          <path d="M12 8v5M12 16.5v.01" />
        </svg>
        <span>{message}</span>
      </div>
    </div>
  );
}
