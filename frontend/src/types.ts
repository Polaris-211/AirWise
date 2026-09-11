/** 分析信号 */
export type Signal = "buy_now" | "consider" | "wait";

/** Monitor Agent 返回 */
export interface MonitorResult {
  agent: string;
  inserted: number;
  origin: string;
  destination: string;
}

/** Analyst Agent 返回 */
export interface AnalystResult {
  agent: string;
  current: number | null;
  mean: number | null;
  min: number | null;
  pct: number | null;
  signal: Signal;
  confidence: number;
  reason: string;
  llm_used: boolean;
}

/** Advisor Agent 返回 */
export interface AdvisorResult {
  agent: string;
  recommendation: string;
  message: string;
  urgency: "high" | "medium" | "low";
  suggested_action: string;
  llm_used: boolean;
}

/** POST /api/agents/run 完整响应 */
export interface AgentsRunResponse {
  monitor: MonitorResult;
  analyst: AnalystResult;
  advisor: AdvisorResult;
}

/** 历史每日最低价 */
export interface PriceHistoryPoint {
  date: string;
  min_price: number;
}

/** GET /api/routes/{o}/{d}/prices 单条航班报价 */
export interface FlightPriceRow {
  id: number;
  origin: string;
  destination: string;
  flight_date: string;
  flight_no: string;
  airline: string;
  depart_time: string | null;
  price: number;
  currency: string;
  source: string;
  captured_at: string;
}

/** 单条航线的监测结果 */
export interface SchedulerRouteResult {
  route: string;
  inserted: number;
  error: string | null;
}

/** 一次自动监测的执行记录 */
export interface SchedulerRun {
  ran_at: string;
  trigger: "auto" | "manual";
  flight_date: string;
  routes: SchedulerRouteResult[];
  inserted: number;
  duration_ms: number;
}

/** GET /api/scheduler/status 响应 */
export interface SchedulerStatus {
  running: boolean;
  interval_minutes: number;
  watched_routes: string[];
  last_run: SchedulerRun | null;
  next_run: string | null;
  total_runs: number;
  recent_runs: SchedulerRun[];
}

/** 查询表单 */
export interface QueryForm {
  origin: string;
  destination: string;
  flightDate: string;
  targetPrice: string;
}
