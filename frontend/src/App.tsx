import { useState } from "react";
import PriceChart from "./PriceChart";
import type {
  AdvisorResult,
  AgentsRunResponse,
  AnalystResult,
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

/** 信号对应的中文与配色 */
const SIGNAL_STYLE: Record<
  Signal,
  { label: string; badge: string; border: string; bg: string }
> = {
  buy_now: {
    label: "立即购买",
    badge: "bg-emerald-100 text-emerald-700",
    border: "border-emerald-200",
    bg: "bg-emerald-50",
  },
  consider: {
    label: "可以考虑",
    badge: "bg-amber-100 text-amber-700",
    border: "border-amber-200",
    bg: "bg-amber-50",
  },
  wait: {
    label: "继续等待",
    badge: "bg-slate-100 text-slate-600",
    border: "border-slate-200",
    bg: "bg-slate-50",
  },
};

const URGENCY_LABEL: Record<string, string> = {
  high: "紧急",
  medium: "一般",
  low: "不急",
};

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
  const [monitor, setMonitor] = useState<MonitorResult | null>(null);
  const [analyst, setAnalyst] = useState<AnalystResult | null>(null);
  const [advisor, setAdvisor] = useState<AdvisorResult | null>(null);

  const updateForm = (key: keyof QueryForm, value: string) => {
    setForm((prev) => ({ ...prev, [key]: value }));
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

  /** 点击「开始分析」：跑三 Agent 流水线，再刷新曲线 */
  const handleAnalyze = async () => {
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
      await fetchHistory(origin, destination);
    } catch (e) {
      setError(e instanceof Error ? e.message : "未知错误");
    } finally {
      setLoading(false);
    }
  };

  const signal = analyst?.signal ?? "wait";
  const signalStyle = SIGNAL_STYLE[signal];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        {/* 品牌头部 */}
        <header className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            AirWise
          </h1>
          <p className="mt-1 text-slate-500">智能机票价格监测看板</p>
        </header>

        {/* 查询栏 */}
        <section className="mb-6 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-slate-500">
                出发地
              </span>
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm uppercase focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
                value={form.origin}
                onChange={(e) => updateForm("origin", e.target.value)}
                placeholder="BJS"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-slate-500">
                目的地
              </span>
              <input
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm uppercase focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
                value={form.destination}
                onChange={(e) => updateForm("destination", e.target.value)}
                placeholder="SHA"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-slate-500">
                航班日期
              </span>
              <input
                type="date"
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
                value={form.flightDate}
                onChange={(e) => updateForm("flightDate", e.target.value)}
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-xs font-medium text-slate-500">
                目标价（可留空）
              </span>
              <input
                type="number"
                className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
                value={form.targetPrice}
                onChange={(e) => updateForm("targetPrice", e.target.value)}
                placeholder="800"
              />
            </label>
            <div className="flex items-end">
              <button
                type="button"
                onClick={handleAnalyze}
                disabled={loading}
                className="w-full rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading ? "分析中…" : "开始分析"}
              </button>
            </div>
          </div>
          {error && (
            <p className="mt-3 text-sm text-red-600">{error}</p>
          )}
        </section>

        {/* 价格曲线 */}
        <section className="mb-6">
          <h2 className="mb-3 text-sm font-semibold text-slate-600">
            近 30 日最低价走势
          </h2>
          <PriceChart data={history} />
        </section>

        {/* 三 Agent 状态卡片 */}
        <section className="grid gap-4 md:grid-cols-3">
          {/* Monitor */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 text-sm">
                📡
              </span>
              <div>
                <h3 className="font-semibold text-slate-800">Monitor</h3>
                <p className="text-xs text-slate-400">价格采集</p>
              </div>
            </div>
            {monitor ? (
              <div>
                <p className="text-4xl font-bold text-blue-600">
                  {monitor.inserted}
                </p>
                <p className="mt-1 text-sm text-slate-500">
                  条报价已入库 · {monitor.origin} → {monitor.destination}
                </p>
              </div>
            ) : (
              <p className="text-sm text-slate-400">等待分析…</p>
            )}
          </div>

          {/* Analyst */}
          <div
            className={`rounded-xl border p-5 shadow-sm ${analyst ? `${signalStyle.border} ${signalStyle.bg}` : "border-slate-200 bg-white"}`}
          >
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-violet-100 text-sm">
                  📊
                </span>
                <div>
                  <h3 className="font-semibold text-slate-800">Analyst</h3>
                  <p className="text-xs text-slate-400">趋势分析</p>
                </div>
              </div>
              {analyst && (
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${signalStyle.badge}`}
                >
                  {signalStyle.label}
                </span>
              )}
            </div>
            {analyst ? (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">当前价</span>
                  <span className="text-2xl font-bold text-slate-900">
                    ¥{analyst.current?.toFixed(0) ?? "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">均价</span>
                  <span className="font-medium">
                    ¥{analyst.mean?.toFixed(0) ?? "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">历史最低</span>
                  <span className="font-medium">
                    ¥{analyst.min?.toFixed(0) ?? "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">更便宜天数占比</span>
                  <span className="font-medium">
                    {analyst.pct != null
                      ? `${(analyst.pct * 100).toFixed(0)}%`
                      : "—"}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">置信度</span>
                  <span className="font-medium">
                    {(analyst.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <p className="mt-2 text-xs leading-relaxed text-slate-600">
                  {analyst.reason}
                </p>
              </div>
            ) : (
              <p className="text-sm text-slate-400">等待分析…</p>
            )}
          </div>

          {/* Advisor */}
          <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="flex h-8 w-8 items-center justify-center rounded-full bg-rose-100 text-sm">
                  💡
                </span>
                <div>
                  <h3 className="font-semibold text-slate-800">Advisor</h3>
                  <p className="text-xs text-slate-400">购票建议</p>
                </div>
              </div>
              {advisor && (
                <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
                  {URGENCY_LABEL[advisor.urgency] ?? advisor.urgency}
                </span>
              )}
            </div>
            {advisor ? (
              <div>
                <p
                  className={`mb-3 text-3xl font-bold ${
                    advisor.recommendation === "购买"
                      ? "text-emerald-600"
                      : advisor.recommendation === "观望"
                        ? "text-amber-600"
                        : "text-slate-500"
                  }`}
                >
                  {advisor.recommendation}
                </p>
                <p className="text-base leading-relaxed text-slate-700">
                  {advisor.message}
                </p>
                <p className="mt-3 text-xs text-slate-400">
                  建议动作：{advisor.suggested_action}
                  {advisor.llm_used && " · LLM 增强"}
                </p>
              </div>
            ) : (
              <p className="text-sm text-slate-400">等待分析…</p>
            )}
          </div>
        </section>
      </div>
    </div>
  );
}
