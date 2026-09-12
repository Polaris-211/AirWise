import MonitorStatus from "./MonitorStatus";
import ReminderCenter from "./ReminderCenter";

/** 固定顶栏：白色半透明 + 毛玻璃 + 1px 极细底边 */
export default function TopBar() {
  return (
    <header className="fixed inset-x-0 top-0 z-40 border-b border-hairline/60 bg-white/72 backdrop-blur-xl backdrop-saturate-150">
      <div className="mx-auto flex h-12 max-w-[1100px] flex-nowrap items-center justify-between gap-2 px-4 sm:gap-4 sm:px-6">
        <span className="shrink-0 text-[17px] font-bold tracking-tighter text-ink sm:text-[20px]">
          AirWise
        </span>
        {/* 右侧：监测状态 + 提醒铃铛 */}
        <div className="flex shrink-0 items-center gap-1.5 sm:gap-3">
          <MonitorStatus />
          <ReminderCenter />
        </div>
      </div>
    </header>
  );
}
