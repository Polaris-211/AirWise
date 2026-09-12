import { useCallback, useEffect, useRef, useState } from "react";
import { notifyRemindersChanged } from "../events";
import type { SchedulerStatus } from "../types";

/** 状态轮询间隔：30 秒 */
const POLL_INTERVAL_MS = 30_000;

/** ISO 时间 → HH:MM */
function toClock(iso: string): string {
  return new Date(iso).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * 顶栏右侧的自动监测状态区。
 * 与顶栏共用同一套配色与字重，视觉上属于顶栏本身而非叠加元素。
 */
export default function MonitorStatus() {
  const [status, setStatus] = useState<SchedulerStatus | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  /** 组件卸载后不再 setState */
  const aliveRef = useRef(true);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch("/api/scheduler/status");
      if (!res.ok) throw new Error("状态获取失败");
      const data: SchedulerStatus = await res.json();
      if (aliveRef.current) setStatus(data);
    } catch {
      // 后端没起来时按「已停止」展示，不弹错误打扰用户
      if (aliveRef.current) setStatus(null);
    } finally {
      if (aliveRef.current) setLoaded(true);
    }
  }, []);

  useEffect(() => {
    aliveRef.current = true;
    fetchStatus();
    const timer = window.setInterval(fetchStatus, POLL_INTERVAL_MS);
    return () => {
      aliveRef.current = false;
      window.clearInterval(timer);
    };
  }, [fetchStatus]);

  /** 手动触发一次全部关注航线的监测 */
  const handleRunNow = async () => {
    if (busy) return;
    setBusy(true);
    try {
      const res = await fetch("/api/scheduler/run-now", { method: "POST" });
      if (!res.ok) throw new Error("触发失败");
      const data: { status: SchedulerStatus } = await res.json();
      if (aliveRef.current) setStatus(data.status);
      // 定时/手动监测可能刚写入提醒，立刻刷新铃铛（允许弹系统通知）
      notifyRemindersChanged(false);
    } catch {
      if (aliveRef.current) await fetchStatus();
    } finally {
      if (aliveRef.current) setBusy(false);
    }
  };

  const running = status?.running ?? false;
  const lastRunAt = status?.last_run?.ran_at;

  return (
    <div
      className={`flex items-center gap-2 sm:gap-3 transition-opacity duration-250 ease-out-soft ${
        loaded ? "opacity-100" : "opacity-0"
      }`}
    >
      {/* 状态点 + 文字；窄屏只留圆点，避免和品牌名抢行 */}
      <span className="flex items-center gap-2">
        <span className="relative flex h-2 w-2 items-center justify-center">
          {running && (
            // 外扩光晕，只在运行中出现
            <span className="absolute h-2 w-2 animate-halo rounded-full bg-accent" />
          )}
          <span
            className={`h-2 w-2 rounded-full ${
              running ? "animate-breathe bg-accent" : "bg-subtle"
            }`}
          />
        </span>
        <span className="hidden whitespace-nowrap text-[14px] text-ink sm:inline">
          {running
            ? `自动监测中 · 每 ${status?.interval_minutes ?? 30} 分钟`
            : "已停止"}
        </span>
      </span>

      {/* 上次更新时间 */}
      {lastRunAt && (
        <span className="tnum hidden whitespace-nowrap text-[12px] text-subtle md:inline">
          上次更新 {toClock(lastRunAt)}
        </span>
      )}

      {/* 次要按钮：描边式，hover 浅灰底 */}
      <button
        type="button"
        onClick={handleRunNow}
        disabled={busy}
        className="whitespace-nowrap rounded-[10px] border border-white bg-white/60 px-2 py-1 text-[12px] text-accent backdrop-blur-sm transition-all duration-250 ease-out-soft hover:bg-white/80 active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-50 sm:px-2.5 sm:text-[13px]"
      >
        {busy ? "监测中…" : (
          <>
            <span className="sm:hidden">监测</span>
            <span className="hidden sm:inline">立即监测</span>
          </>
        )}
      </button>
    </div>
  );
}
