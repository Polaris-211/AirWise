import { useState } from "react";
import PriceChart from "./PriceChart";
import AnimatedNumber from "./components/AnimatedNumber";
import BaggageToggle from "./components/BaggageToggle";
import CitySearchInput from "./components/CitySearchInput";
import DatePicker from "./components/DatePicker";
import FlightList from "./components/FlightList";
import CardSkeleton from "./components/Skeleton";
import Spinner from "./components/Spinner";
import Toast from "./components/Toast";
import TopBar from "./components/TopBar";
import { IconBulb, IconChart, IconSwap, IconWave } from "./components/icons";
import { notifyRemindersChanged } from "./events";
import { ctripOnewayUrl } from "./purchase";
import { findCityByCode } from "./cities";
import type {
  AdvisorResult,
  AgentsRunResponse,
  AnalystResult,
  FlightPriceRow,
  MonitorResult,
  PriceHistoryPoint,
  QueryForm,
  Signal,
} from "./types";

/** 默认航班日期：今天 +10 天 */
function defaultFlightDate(): string {
  const d = new Date();
  d.setDate(d.getDate() + 10);
  return d.toISOString().slice(0, 10);
}

/** 信号对应的中文与配色（保持克制：仅用小圆点与文字着色） */
const SIGNAL_STYLE: Record<Signal, { label: string; dot: string; text: string }> =
  {
    buy_now: { label: "立即购买", dot: "bg-[#34c759]", text: "text-[#1a8c3c]" },
    consider: { label: "可以考虑", dot: "bg-[#ff9500]", text: "text-[#b26a00]" },
    wait: { label: "继续等待", dot: "bg-hairline", text: "text-subtle" },
  };

const URGENCY_LABEL: Record<string, string> = {
  high: "紧急",
  medium: "一般",
  low: "不急",
};

/** 卡片：纯白 + 大圆角 + 柔和阴影，hover 上浮；三列等高、内容底部对齐 */
const CARD =
  "flex h-full flex-col rounded-card bg-white p-8 shadow-card transition-all duration-250 ease-out-soft hover:-translate-y-0.5 hover:shadow-card-hover";

/** 输入控件：半透明 + 模糊 + 白描边 + 内高光 + 柔和外阴影 */
const CONTROL =
  "w-full rounded-control border border-[rgba(255,255,255,0.85)] bg-white/55 px-3.5 py-2.5 text-[15px] text-[#1d1d1f] outline-none backdrop-blur-md shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_2px_8px_rgba(0,0,0,0.06)] transition-all duration-250 ease-out-soft placeholder:text-[#86868b] focus:border-[#0071e3] focus:shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_0_0_3px_rgba(0,113,227,0.15)]";

/** 主按钮：上亮下暗渐变 + 内高光 / 内阴影 + 蓝色光晕 */
const PRIMARY_BTN =
  "relative flex w-full items-center justify-center gap-2 rounded-button px-6 py-3 text-[16px] font-medium text-white [background:linear-gradient(180deg,#2b8cff_0%,#0071e3_100%)] [text-shadow:0_1px_1px_rgba(0,0,0,0.15)] shadow-[inset_0_1px_0_rgba(255,255,255,0.35),inset_0_-1px_0_rgba(0,0,0,0.15),0_4px_14px_rgba(0,113,227,0.35)] transition-all duration-250 ease-out-soft hover:brightness-[1.08] hover:shadow-[inset_0_1px_0_rgba(255,255,255,0.4),inset_0_-1px_0_rgba(0,0,0,0.12),0_6px_20px_rgba(0,113,227,0.48)] active:scale-[0.98] active:shadow-[inset_0_1px_0_rgba(255,255,255,0.3),inset_0_-1px_0_rgba(0,0,0,0.2),0_2px_8px_rgba(0,113,227,0.22)] disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:brightness-100";

const LABEL = "mb-2 block text-[13px] text-subtle";

/** 航班报价里最近一条采集时间，没有则回落到分析完成时刻 */
function latestCaptureClock(flights: FlightPriceRow[], fallback: string): string {
  let max = 0;
  for (const f of flights) {
    const t = new Date(f.captured_at).getTime();
    if (!Number.isNaN(t) && t > max) max = t;
  }
  if (!max) return fallback || "—";
  return new Date(max).toLocaleTimeString("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** 卡片头部：圆形浅色底图标 + 标题 */
function CardHeader({
  icon,
  title,
  subtitle,
  trailing,
}: {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  trailing?: React.ReactNode;
}) {
  return (
    <div className="mb-6 flex items-start justify-between">
      <div className="flex items-center gap-3">
        <span className="flex h-10 w-10 items-center justify-center rounded-full bg-canvas text-subtle">
          {icon}
        </span>
        <div>
          <h3 className="text-[15px] font-semibold tracking-tighter text-ink">
            {title}
          </h3>
          <p className="text-[13px] text-subtle">{subtitle}</p>
        </div>
      </div>
      {trailing}
    </div>
  );
}

/** 一行统计数据 */
function StatRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between py-2">
      <span className="text-[13px] text-subtle">{label}</span>
      <span className="tnum text-[15px] font-medium text-ink">{value}</span>
    </div>
  );
}

/** 未分析时的占位文案 */
function Placeholder() {
  return <p className="text-[15px] text-subtle">等待分析…</p>;
}

export default function App() {
  const [form, setForm] = useState<QueryForm>({
    origin: "BJS",
    destination: "SHA",
    flightDate: defaultFlightDate(),
    targetPrice: "800",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<PriceHistoryPoint[]>([]);
  const [flights, setFlights] = useState<FlightPriceRow[]>([]);
  const [monitor, setMonitor] = useState<MonitorResult | null>(null);
  const [analyst, setAnalyst] = useState<AnalystResult | null>(null);
  const [advisor, setAdvisor] = useState<AdvisorResult | null>(null);
  const [updatedAt, setUpdatedAt] = useState("");
  /** 行李偏好：默认有行李，决定航班列表展示哪个总价 */
  const [withBaggage, setWithBaggage] = useState(true);
  /** 航班列表对应的航线与日期，用于标题展示 */
  const [queried, setQueried] = useState<{
    origin: string;
    destination: string;
    date: string;
  } | null>(null);

  const updateForm = (key: keyof QueryForm, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  /** 交换出发地 / 目的地 */
  const swapEnds = () => {
    setForm((prev) => ({
      ...prev,
      origin: prev.destination,
      destination: prev.origin,
    }));
  };

  /** 拉取历史曲线 */
  const fetchHistory = async (origin: string, destination: string) => {
    const res = await fetch(
      `/api/routes/${origin}/${destination}/history?days=30`
    );
    if (!res.ok) throw new Error("历史价格加载失败");
    const data: PriceHistoryPoint[] = await res.json();
    setHistory(data);
  };

  /** 拉取该航线该日期的全部航班报价 */
  const fetchFlights = async (
    origin: string,
    destination: string,
    flightDate: string
  ) => {
    const res = await fetch(
      `/api/routes/${origin}/${destination}/prices?flight_date=${flightDate}`
    );
    if (!res.ok) throw new Error("航班列表加载失败");
    const data: FlightPriceRow[] = await res.json();
    setFlights(data);
  };

  /** 点击「开始分析」：跑三 Agent 流水线，再刷新曲线 */
  const handleAnalyze = async () => {
    if (loading) return; // 防重复点击
    setLoading(true);
    setError("");
    try {
      const origin = form.origin.trim().toUpperCase();
      const destination = form.destination.trim().toUpperCase();
      const body: Record<string, string | number> = {
        origin,
        destination,
        flight_date: form.flightDate,
      };
      const tp = form.targetPrice.trim();
      if (tp) body.target_price = Number(tp);

      const res = await fetch("/api/agents/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error("分析请求失败，请确认后端已启动");

      const data: AgentsRunResponse = await res.json();
      setMonitor(data.monitor);
      setAnalyst(data.analyst);
      setAdvisor(data.advisor);
      await Promise.all([
        fetchHistory(origin, destination),
        fetchFlights(origin, destination, form.flightDate),
      ]);
      setQueried({ origin, destination, date: form.flightDate });
      setUpdatedAt(
        new Date().toLocaleTimeString("zh-CN", {
          hour: "2-digit",
          minute: "2-digit",
        })
      );
      // 分析可能刚写入提醒，刷新铃铛；用户自己点的，不弹系统通知
      notifyRemindersChanged(true);
    } catch (e) {
      // fetch 网络层失败会抛 TypeError，说明后端没起来
      setError(
        e instanceof TypeError
          ? "无法连接后端服务，请确认后端已启动"
          : e instanceof Error
            ? e.message
            : "未知错误"
      );
    } finally {
      setLoading(false);
    }
  };

  /** 输入框回车直接触发分析 */
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleAnalyze();
  };

  const signal = analyst?.signal ?? "wait";
  const signalStyle = SIGNAL_STYLE[signal];

  return (
    <div className="relative min-h-screen font-sans">
      {/* 固定光斑：给毛玻璃提供可透的色块，不随滚动 */}
      <div
        aria-hidden="true"
        className="pointer-events-none fixed inset-0 z-0 overflow-hidden bg-[#f5f5f7]"
      >
        <div className="absolute -left-24 -top-32 h-[500px] w-[500px] rounded-full bg-[rgba(0,113,227,0.15)] blur-3xl" />
        <div className="absolute -right-16 -top-20 h-[400px] w-[400px] rounded-full bg-[rgba(160,120,255,0.12)] blur-3xl" />
        <div className="absolute bottom-[-90px] left-1/2 h-[450px] w-[450px] -translate-x-1/2 rounded-full bg-[rgba(0,200,180,0.10)] blur-3xl" />
      </div>

      <div className="relative z-10">
      <TopBar />

      {/* 错误提示条，3 秒自动消失 */}
      {error && <Toast message={error} onClose={() => setError("")} />}

      <main className="mx-auto max-w-[1100px] px-6 pb-24 pt-12">
        {/* Hero 区 */}
        <section className="animate-rise-in py-12 text-center">
          <h1 className="text-[32px] font-bold leading-tight tracking-tighter text-ink sm:text-[40px]">
            智能机票价格监测
          </h1>
          <p className="mt-4 text-[17px] text-subtle">
            三个 Agent 协同采集、分析票价走势，告诉你什么时候该下单
          </p>
        </section>

        {/* 查询卡片：居中，最大 720px */}
        <section className="relative z-20 mx-auto mb-12 w-full max-w-[720px] animate-rise-in rounded-card border border-[rgba(255,255,255,0.85)] bg-white/40 p-8 shadow-card backdrop-blur-xl">
          {/* 出发地 / 交换 / 目的地：窄屏上下排列，宽屏左右夹按钮 */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:gap-2">
            <div className="min-w-0 flex-1">
              <CitySearchInput
                label="出发地"
                value={form.origin}
                onChange={(code) => updateForm("origin", code)}
                onEnter={handleAnalyze}
                placeholder="城市 / 拼音 / 三字码"
              />
            </div>
            <button
              type="button"
              title="交换出发地/目的地"
              aria-label="交换出发地/目的地"
              onClick={swapEnds}
              className="mx-auto flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-white bg-white/60 text-[#1d1d1f] shadow-[0_2px_8px_rgba(0,0,0,0.08)] backdrop-blur-sm transition-transform duration-250 ease-out hover:rotate-180 sm:mb-1.5 sm:mx-0"
            >
              <IconSwap />
            </button>
            <div className="min-w-0 flex-1">
              <CitySearchInput
                label="目的地"
                value={form.destination}
                onChange={(code) => updateForm("destination", code)}
                onEnter={handleAnalyze}
                placeholder="城市 / 拼音 / 三字码"
              />
            </div>
          </div>

          <div className="mt-5 grid gap-5 sm:grid-cols-2">
            <DatePicker
              label="航班日期"
              value={form.flightDate}
              onChange={(date) => updateForm("flightDate", date)}
              onEnter={handleAnalyze}
            />
            <label className="block">
              <span className={LABEL}>目标价（可留空）</span>
              <input
                type="text"
                inputMode="numeric"
                className={`${CONTROL} tnum`}
                value={form.targetPrice}
                // 只保留数字，禁止其他字符
                onChange={(e) =>
                  updateForm("targetPrice", e.target.value.replace(/[^\d]/g, ""))
                }
                onKeyDown={handleKeyDown}
                placeholder="800"
              />
            </label>
          </div>

          <button
            type="button"
            onClick={handleAnalyze}
            disabled={loading}
            className={`mt-7 ${PRIMARY_BTN}`}
          >
            {loading && <Spinner />}
            {loading ? "分析中..." : "开始分析"}
          </button>
        </section>

        {/* 曲线卡片 */}
        <section className="mb-12 animate-rise-in rounded-card bg-white p-8 shadow-card transition-shadow duration-250 ease-out-soft hover:shadow-card-hover">
          <div className="mb-5 flex items-baseline justify-between">
            <h2 className="text-[18px] font-semibold tracking-tighter text-ink">
              近 30 日最低价走势
            </h2>
            {updatedAt && (
              <span className="text-[13px] text-subtle">
                更新于 {updatedAt}
              </span>
            )}
          </div>
          <PriceChart data={history} loading={loading} />
        </section>

        {/* 可选航班列表 */}
        <section className="mb-12 animate-rise-in rounded-card bg-white p-8 shadow-card transition-shadow duration-250 ease-out-soft hover:shadow-card-hover">
          <div className="mb-4 flex items-start justify-between gap-4">
            <div>
              <h2 className="text-[18px] font-semibold tracking-tighter text-ink">
                可选航班
              </h2>
              {queried && (
                <p className="mt-1 text-[13px] text-subtle">
                  {findCityByCode(queried.origin)?.name ?? queried.origin} →{" "}
                  {findCityByCode(queried.destination)?.name ??
                    queried.destination}{" "}
                  · {queried.date}
                </p>
              )}
            </div>
            {/* 行李偏好：切换含 / 不含托运行李的总价 */}
            <BaggageToggle checked={withBaggage} onChange={setWithBaggage} />
          </div>
          <FlightList
            flights={flights}
            loading={loading}
            withBaggage={withBaggage}
          />
        </section>

        {/* 三张 Agent 卡片：等宽三列，间距 24px，底部对齐 */}
        <section className="grid items-stretch gap-6 md:grid-cols-3">
          {/* Monitor */}
          <div className={CARD}>
            {loading ? (
              <CardSkeleton rows={4} />
            ) : (
              <>
                <CardHeader
                  icon={<IconWave />}
                  title="价格采集"
                  subtitle="Monitor"
                  trailing={
                    monitor ? (
                      <span className="flex items-center gap-1.5 text-[13px] font-medium text-[#1a8c3c]">
                        <span className="h-1.5 w-1.5 rounded-full bg-[#34c759]" />
                        采集正常
                      </span>
                    ) : undefined
                  }
                />
                {monitor ? (
                  <div className="flex flex-1 flex-col animate-rise-in">
                    <p className="text-[56px] font-bold leading-none tracking-tighter text-ink">
                      <AnimatedNumber value={monitor.inserted} />
                    </p>
                    <p className="mt-3 text-[13px] text-subtle">条报价</p>
                    <div className="mt-auto divide-y divide-hairline/60 border-t border-hairline/60 pt-1">
                      <StatRow
                        label="航线"
                        value={`${monitor.origin} → ${monitor.destination}`}
                      />
                      <StatRow
                        label="最近采集"
                        value={latestCaptureClock(flights, updatedAt)}
                      />
                      <StatRow label="采集频率" value="每 30 分钟" />
                    </div>
                  </div>
                ) : (
                  <Placeholder />
                )}
              </>
            )}
          </div>

          {/* Analyst */}
          <div className={CARD}>
            {loading ? (
              <CardSkeleton rows={4} />
            ) : (
              <>
                <CardHeader
                  icon={<IconChart />}
                  title="Analyst"
                  subtitle="趋势分析"
                  trailing={
                    analyst ? (
                      <span
                        className={`flex items-center gap-1.5 text-[13px] font-medium ${signalStyle.text}`}
                      >
                        <span
                          className={`h-1.5 w-1.5 rounded-full ${signalStyle.dot}`}
                        />
                        {signalStyle.label}
                      </span>
                    ) : undefined
                  }
                />
                {analyst ? (
                  <div className="flex flex-1 flex-col animate-rise-in">
                    <p className="text-[48px] font-bold leading-none tracking-tighter text-ink">
                      {analyst.current != null ? (
                        <AnimatedNumber value={analyst.current} prefix="¥" />
                      ) : (
                        "—"
                      )}
                    </p>
                    <p className="mt-3 text-[13px] text-subtle">当前最低价</p>
                    <div className="mt-auto">
                      <div className="divide-y divide-hairline/60 border-t border-hairline/60">
                        <StatRow
                          label="均价"
                          value={`¥${analyst.mean?.toFixed(0) ?? "—"}`}
                        />
                        <StatRow
                          label="历史最低"
                          value={`¥${analyst.min?.toFixed(0) ?? "—"}`}
                        />
                        <StatRow
                          label="更便宜天数占比"
                          value={
                            analyst.pct != null
                              ? `${(analyst.pct * 100).toFixed(0)}%`
                              : "—"
                          }
                        />
                        <StatRow
                          label="置信度"
                          value={`${(analyst.confidence * 100).toFixed(0)}%`}
                        />
                      </div>
                      <p className="mt-5 text-[13px] leading-relaxed text-subtle">
                        {analyst.reason}
                      </p>
                    </div>
                  </div>
                ) : (
                  <Placeholder />
                )}
              </>
            )}
          </div>

          {/* Advisor */}
          <div className={CARD}>
            {loading ? (
              <CardSkeleton rows={3} />
            ) : (
              <>
                <CardHeader
                  icon={<IconBulb />}
                  title="Advisor"
                  subtitle="购票建议"
                  trailing={
                    advisor ? (
                      <span className="text-[13px] text-subtle">
                        {URGENCY_LABEL[advisor.urgency] ?? advisor.urgency}
                      </span>
                    ) : undefined
                  }
                />
                {advisor ? (
                  <div className="flex flex-1 flex-col animate-rise-in">
                    <p className="text-[40px] font-bold leading-none tracking-tighter text-ink">
                      {advisor.recommendation}
                    </p>
                    <p className="mt-5 text-[17px] leading-relaxed text-ink/80">
                      {advisor.message}
                    </p>
                    <div className="mt-auto">
                      <p className="mt-6 border-t border-hairline/60 pt-4 text-[13px] text-subtle">
                        建议动作：{advisor.suggested_action}
                        {advisor.llm_used && " · LLM 增强"}
                      </p>
                      <a
                        href={ctripOnewayUrl(
                          queried?.origin ?? form.origin,
                          queried?.destination ?? form.destination,
                          queried?.date ?? form.flightDate
                        )}
                        target="_blank"
                        rel="noopener noreferrer"
                        className={`mt-6 ${PRIMARY_BTN}`}
                      >
                        去购买
                      </a>
                    </div>
                  </div>
                ) : (
                  <Placeholder />
                )}
              </>
            )}
          </div>
        </section>
      </main>

      {/* 右下角数据来源标签 */}
      <div className="pointer-events-none fixed bottom-4 right-4 z-30 rounded-full border border-hairline/60 bg-white/72 px-3.5 py-1.5 text-[12px] text-subtle shadow-bar backdrop-blur-xl">
        数据来源：模拟数据（可替换真实 API）
      </div>
      </div>
    </div>
  );
}
