/** 提醒列表需要立刻刷新时派发，例如分析完成或手动监测结束。 */
export const REMINDERS_CHANGED = "airwise:reminders-changed";

export function notifyRemindersChanged(silent = false) {
  window.dispatchEvent(
    new CustomEvent(REMINDERS_CHANGED, { detail: { silent } })
  );
}
