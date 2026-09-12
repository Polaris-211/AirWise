import { useCallback, useEffect, useRef, useState } from "react";
import { REMINDERS_CHANGED } from "../events";
import {
  canNotify,
  notificationSupport,
  requestNotifyPermission,
  showPriceAlert,
  type NotifySupport,
} from "../notifications";
import { ctripOnewayUrl } from "../purchase";
import type { ReminderItem } from "../types";
import { IconBell } from "./icons";

/** 与监测状态共用同一套轮询节奏 */
const POLL_INTERVAL_MS = 20_000;

/** ISO 时间 → 相对中文，如「5 分钟前」 */
function formatRelativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const sec = Math.max(0, Math.floor((Date.now() - then) / 1000));
  if (sec < 60) return "刚刚";
  const min = Math.floor(sec / 60);
  if (min < 60) return `${min} 分钟前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return `${hr} 小时前`;
  const day = Math.floor(hr / 24);
  if (day === 1) return "昨天";
  if (day < 30) return `${day} 天前`;
  return new Date(iso).toLocaleDateString("zh-CN");
}

/**
 * 顶栏铃铛 + 毛玻璃提醒面板。
 * 定时任务写入新提醒后，若已授权浏览器通知则弹系统提示。
 */
export default function ReminderCenter() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<ReminderItem[]>([]);
  const [unread, setUnread] = useState(0);
  const [notifyState, setNotifyState] = useState<NotifySupport>(() =>
    notificationSupport()
  );
  const [busyAll, setBusyAll] = useState(false);

  const rootRef = useRef<HTMLDivElement>(null);
  const aliveRef = useRef(true);
  /** 已经见过的 id，避免首次加载把历史提醒当成「新到」去弹通知 */
  const knownIdsRef = useRef<Set<number>>(new Set());
  const primedRef = useRef(false);

  const applyPayload = useCallback(
    (list: ReminderItem[], count: number, allowNotify: boolean) => {
      const fresh = list.filter((item) => !knownIdsRef.current.has(item.id));
      for (const item of list) knownIdsRef.current.add(item.id);

      if (primedRef.current && allowNotify && canNotify()) {
        for (const item of fresh) {
          showPriceAlert(item.origin, item.destination, item.price);
        }
      }
      primedRef.current = true;
      if (aliveRef.current) {
        setItems(list);
        setUnread(count);
      }
    },
    []
  );

  const refresh = useCallback(
    async (allowNotify: boolean) => {
      try {
        const [listRes, countRes] = await Promise.all([
          fetch("/api/reminders?limit=20"),
          fetch("/api/reminders/unread-count"),
        ]);
        if (!listRes.ok || !countRes.ok) return;
        const list: ReminderItem[] = await listRes.json();
        const { count } = (await countRes.json()) as { count: number };
        applyPayload(list, count, allowNotify);
      } catch {
        // 后端未启动时保持现状，不弹错误
      }
    },
    [applyPayload]
  );

  useEffect(() => {
    aliveRef.current = true;
    refresh(false);
    const timer = window.setInterval(() => refresh(true), POLL_INTERVAL_MS);

    const onChanged = (event: Event) => {
      const silent = Boolean((event as CustomEvent<{ silent?: boolean }>).detail?.silent);
      void refresh(!silent);
    };
    window.addEventListener(REMINDERS_CHANGED, onChanged);

    return () => {
      aliveRef.current = false;
      window.clearInterval(timer);
      window.removeEventListener(REMINDERS_CHANGED, onChanged);
    };
  }, [refresh]);

  // 点击面板外部关闭
  useEffect(() => {
    if (!open) return;
    const onPointer = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  const handleMarkOne = async (id: number) => {
    const prev = items;
    setItems((list) =>
      list.map((item) => (item.id === id ? { ...item, is_read: true } : item))
    );
    setUnread((n) =>
      Math.max(0, n - (prev.find((item) => item.id === id && !item.is_read) ? 1 : 0))
    );
    try {
      const res = await fetch(`/api/reminders/${id}/read`, { method: "POST" });
      if (!res.ok) throw new Error("标记失败");
    } catch {
      void refresh(false);
    }
  };

  const handleMarkAll = async () => {
    if (busyAll || unread === 0) return;
    setBusyAll(true);
    setItems((list) => list.map((item) => ({ ...item, is_read: true })));
    setUnread(0);
    try {
      const res = await fetch("/api/reminders/read-all", { method: "POST" });
      if (!res.ok) throw new Error("标记失败");
    } catch {
      void refresh(false);
    } finally {
      setBusyAll(false);
    }
  };

  const handleEnableNotify = async () => {
    const next = await requestNotifyPermission();
    setNotifyState(next);
  };

  const badge = unread > 99 ? "99+" : String(unread);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        aria-label="提醒"
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        className="relative flex h-8 w-8 items-center justify-center rounded-[10px] text-ink transition-all duration-250 ease-out-soft hover:bg-canvas active:scale-[0.97]"
      >
        <IconBell className="h-[18px] w-[18px]" />
        {unread > 0 && (
          <span className="absolute -right-0.5 -top-0.5 flex h-[16px] min-w-[16px] items-center justify-center rounded-full bg-[#ff3b30] px-1 text-[10px] font-semibold leading-none text-white">
            {badge}
          </span>
        )}
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="提醒中心"
          className="animate-panel-in absolute right-0 top-[calc(100%+10px)] z-50 w-[min(360px,calc(100vw-32px))] overflow-hidden rounded-[18px] border border-hairline/60 bg-white/78 shadow-card backdrop-blur-xl backdrop-saturate-150"
        >
          <div className="flex items-center justify-between px-4 pb-2 pt-3.5">
            <h2 className="text-[15px] font-semibold tracking-tighter text-ink">
              提醒
            </h2>
            {notifyState === "default" && (
              <button
                type="button"
                onClick={handleEnableNotify}
                className="text-[12px] text-accent transition-opacity duration-250 ease-out-soft hover:opacity-70"
              >
                开启系统通知
              </button>
            )}
            {notifyState === "granted" && (
              <span className="text-[12px] text-subtle">已开启通知</span>
            )}
          </div>

          <div className="max-h-[360px] overflow-y-auto">
            {items.length === 0 ? (
              <p className="px-4 py-10 text-center text-[14px] text-subtle">
                暂无提醒
              </p>
            ) : (
              <ul>
                {items.map((item) => (
                  <li key={item.id} className="border-t border-hairline/50">
                    <div
                      role="button"
                      tabIndex={0}
                      onClick={() => {
                        if (!item.is_read) void handleMarkOne(item.id);
                      }}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" && !item.is_read) {
                          void handleMarkOne(item.id);
                        }
                      }}
                      className="flex cursor-pointer gap-2.5 px-4 py-3 transition-colors duration-250 ease-out-soft hover:bg-white/50"
                    >
                      <span
                        className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${
                          item.is_read
                            ? "bg-hairline"
                            : item.signal === "buy_now"
                              ? "bg-[#34c759]"
                              : "bg-[#ff9500]"
                        }`}
                      />
                      <div className="min-w-0 flex-1">
                        <p
                          className={`text-[13px] leading-relaxed ${
                            item.is_read ? "text-subtle" : "text-ink"
                          }`}
                        >
                          {item.message}
                        </p>
                        <div className="mt-1.5 flex items-center justify-between gap-3">
                          <span className="tnum text-[12px] text-subtle">
                            {formatRelativeTime(item.created_at)}
                          </span>
                          <a
                            href={ctripOnewayUrl(
                              item.origin,
                              item.destination,
                              item.flight_date
                            )}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => {
                              e.stopPropagation();
                              if (!item.is_read) void handleMarkOne(item.id);
                            }}
                            className="shrink-0 text-[12px] text-accent transition-opacity duration-250 ease-out-soft hover:opacity-70"
                          >
                            去购买
                          </a>
                        </div>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="border-t border-hairline/60 px-4 py-2.5">
            <button
              type="button"
              onClick={handleMarkAll}
              disabled={unread === 0 || busyAll}
              className="w-full rounded-[10px] py-1.5 text-[13px] text-accent transition-all duration-250 ease-out-soft hover:bg-canvas disabled:cursor-not-allowed disabled:text-subtle disabled:hover:bg-transparent"
            >
              全部标为已读
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
