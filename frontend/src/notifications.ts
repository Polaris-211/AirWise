/** 浏览器系统通知：未授权或不支持时全部静默降级，不打断页面。 */

export type NotifySupport = NotificationPermission | "unsupported";

export function notificationSupport(): NotifySupport {
  if (typeof window === "undefined" || typeof Notification === "undefined") {
    return "unsupported";
  }
  return Notification.permission;
}

export function canNotify(): boolean {
  return notificationSupport() === "granted";
}

/** 向用户申请通知权限；拒绝或不支持时返回对应状态，不抛错。 */
export async function requestNotifyPermission(): Promise<NotifySupport> {
  if (typeof window === "undefined" || typeof Notification === "undefined") {
    return "unsupported";
  }
  if (Notification.permission === "granted") return "granted";
  if (Notification.permission === "denied") return "denied";
  try {
    return await Notification.requestPermission();
  } catch {
    return "denied";
  }
}

/** 弹出一条低价系统通知；无权限时直接返回。 */
export function showPriceAlert(origin: string, destination: string, price: number) {
  if (!canNotify()) return;
  try {
    new Notification("AirWise · 发现低价", {
      body: `${origin}→${destination} 跌到 ¥${Math.round(price)}，建议购买`,
    });
  } catch {
    // 部分浏览器在后台标签会抛错，忽略即可
  }
}
