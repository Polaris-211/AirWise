"""定时监测调度器：按固定间隔对「关注中的航线」自动跑一次 MonitorAgent。

关于防重复启动：
- uvicorn --reload 会重复导入模块，且 startup 事件在某些场景下可能被触发多次，
  所以这里用「模块级单例 + 线程锁 + 本地端口占用」三重保险：
  1. 模块级单例 scheduler，重复 import 不会产生第二个调度器；
  2. _start_lock + _started 标记，防止同一进程内重复 start；
  3. 绑定一个本地回环端口作为跨进程互斥锁，多 worker 时只有第一个进程会真正调度。
"""

from __future__ import annotations

import logging
import socket
import threading
import time
from collections import deque
from datetime import date, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler

from .agents.analyst import AnalystAgent
from .agents.monitor import MonitorAgent
from .config import settings
from .queries import daily_min_prices
from .reminders import maybe_create_reminder
from .sources.factory import get_price_source

logger = logging.getLogger("airwise.scheduler")

# 关注中的航线，暂时内置（后续可挪到数据库或配置文件）
WATCHED_ROUTES: list[tuple[str, str]] = [
    ("BJS", "SHA"),
    ("BJS", "CTU"),
    ("SHA", "CAN"),
    # 无直达：克拉玛依 ↔ 合肥联程（交换出发地后也能查到回程）
    ("KRY", "HFE"),
    ("HFE", "KRY"),
    # 乌鲁木齐 ↔ 合肥直飞（含回程时刻）
    ("URC", "HFE"),
    ("HFE", "URC"),
]

_JOB_ID = "monitor_watched_routes"
_MAX_RECENT_RUNS = 20  # 只保留最近 20 次执行记录
_LOOKAHEAD_DAYS = 10  # 监测的航班日期 = 今天 + 10 天，与前端默认值一致
_LOCK_PORT = 47921  # 跨进程互斥用的回环端口，无实际通信


def _watched_flight_date() -> date:
    """自动监测统一盯同一个未来日期，保证历史曲线连续。"""
    return date.today() + timedelta(days=_LOOKAHEAD_DAYS)


class MonitorScheduler:
    """封装 APScheduler，对外只暴露 start / shutdown / run_all / status。"""

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler()
        self._agent = MonitorAgent(get_price_source())
        # 定时任务只走规则引擎，避免轮询时打 LLM
        self._analyst = AnalystAgent(llm_enabled=False)
        self._recent_runs: deque[dict] = deque(maxlen=_MAX_RECENT_RUNS)
        self._total_runs = 0
        self._last_run: dict | None = None
        # 防止手动触发与定时触发同时跑
        self._run_lock = threading.Lock()
        # 防止重复 start
        self._start_lock = threading.Lock()
        self._started = False
        self._lock_socket: socket.socket | None = None

    # ---------- 生命周期 ----------

    def start(self) -> bool:
        """启动调度器；已启动或被其他进程抢先启动时返回 False。"""
        with self._start_lock:
            if self._started or self._scheduler.running:
                logger.info("调度器已在运行，跳过重复启动")
                return False
            if not self._acquire_process_lock():
                logger.info("已有进程在跑调度器，本进程跳过（多 worker / reload）")
                return False

            interval = max(1, settings.monitor_interval_minutes)
            self._scheduler.add_job(
                self._run_all_safely,
                trigger="interval",
                minutes=interval,
                id=_JOB_ID,
                # 错过的任务合并成一次，且同一时刻只允许一个实例在跑
                coalesce=True,
                max_instances=1,
                # 首次不要等满一个周期，启动 10 秒后先跑一次
                next_run_time=datetime.now() + timedelta(seconds=10),
            )
            self._scheduler.start()
            self._started = True
            logger.info("自动监测已启动，间隔 %s 分钟", interval)
            return True

    def shutdown(self) -> None:
        with self._start_lock:
            if self._scheduler.running:
                self._scheduler.shutdown(wait=False)
            self._started = False
            if self._lock_socket is not None:
                self._lock_socket.close()
                self._lock_socket = None

    def _acquire_process_lock(self) -> bool:
        """绑定本地端口作为跨进程锁。

        --reload 重启时旧进程刚退出、端口可能还没完全释放，所以重试几次。
        """
        for attempt in range(4):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                # 故意不设 SO_REUSEADDR，让第二个进程 bind 失败
                sock.bind(("127.0.0.1", _LOCK_PORT))
                sock.listen(1)
                self._lock_socket = sock
                return True
            except OSError:
                sock.close()
                if attempt < 3:
                    time.sleep(0.3)
        return False

    # ---------- 执行 ----------

    def _run_all_safely(self) -> dict | None:
        """定时任务入口：吞掉异常，避免一次失败让 APScheduler 停掉这个 job。"""
        try:
            return self.run_all(trigger="auto")
        except Exception:  # noqa: BLE001 - 定时任务不能把异常抛出去
            logger.exception("自动监测执行失败")
            return None

    def run_all(self, trigger: str = "manual") -> dict:
        """对全部关注航线各跑一次 MonitorAgent，返回本次执行记录。"""
        with self._run_lock:
            started = datetime.now()
            flight_date = _watched_flight_date()
            routes: list[dict] = []
            total_inserted = 0
            reminders_created = 0

            for origin, destination in WATCHED_ROUTES:
                route = f"{origin}-{destination}"
                try:
                    result = self._agent.run(origin, destination, flight_date)
                    inserted = int(result.get("inserted", 0))
                    total_inserted += inserted
                    # 采集后立刻判断水位，低点则写入提醒
                    reminder = self._maybe_remind(origin, destination, flight_date)
                    if reminder:
                        reminders_created += 1
                    routes.append(
                        {
                            "route": route,
                            "inserted": inserted,
                            "error": None,
                            "reminder_created": bool(reminder),
                        }
                    )
                except Exception as exc:  # noqa: BLE001 - 单条航线失败不影响其他航线
                    logger.exception("航线 %s 监测失败", route)
                    routes.append(
                        {
                            "route": route,
                            "inserted": 0,
                            "error": str(exc),
                            "reminder_created": False,
                        }
                    )

            finished = datetime.now()
            record = {
                "ran_at": started.isoformat(timespec="seconds"),
                "trigger": trigger,  # auto=定时触发，manual=手动触发
                "flight_date": flight_date.isoformat(),
                "routes": routes,
                "inserted": total_inserted,
                "reminders_created": reminders_created,
                "duration_ms": int((finished - started).total_seconds() * 1000),
            }
            self._recent_runs.append(record)
            self._total_runs += 1
            self._last_run = record
            logger.info(
                "监测完成（%s）：%d 条航线，共入库 %d 条，新增提醒 %d 条",
                trigger,
                len(routes),
                total_inserted,
                reminders_created,
            )
            return record

    def _maybe_remind(
        self, origin: str, destination: str, flight_date: date
    ) -> dict | None:
        """用近 30 日最低价跑 Analyst，低点则落提醒。"""
        prices = daily_min_prices(origin, destination, 30)
        analyst_result = self._analyst.analyze(prices)
        return maybe_create_reminder(
            origin=origin,
            destination=destination,
            flight_date=flight_date,
            price=analyst_result.get("current"),
            signal=analyst_result.get("signal", "wait"),
            target_price=None,
        )

    # ---------- 查询 ----------

    def status(self) -> dict:
        job = self._scheduler.get_job(_JOB_ID) if self._scheduler.running else None
        next_run = getattr(job, "next_run_time", None)
        return {
            "running": bool(self._scheduler.running),
            "interval_minutes": max(1, settings.monitor_interval_minutes),
            "watched_routes": [f"{o}-{d}" for o, d in WATCHED_ROUTES],
            "last_run": self._last_run,
            "next_run": next_run.isoformat(timespec="seconds") if next_run else None,
            "total_runs": self._total_runs,
            # 最近的排在最前面
            "recent_runs": list(reversed(self._recent_runs)),
        }


# 模块级单例：重复 import 只会拿到同一个实例
monitor_scheduler = MonitorScheduler()
