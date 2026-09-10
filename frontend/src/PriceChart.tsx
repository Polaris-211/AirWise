import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";
import type { PriceHistoryPoint } from "./types";

interface PriceChartProps {
  data: PriceHistoryPoint[];
  /** 加载中显示遮罩 */
  loading?: boolean;
}

const CHART_HEIGHT = 360;

/** 近 30 日最低价折线图，含均价线与最低价点标注 */
export default function PriceChart({ data, loading = false }: PriceChartProps) {
  const dates = data.map((d) => d.date);
  const prices = data.map((d) => d.min_price);
  const mean =
    prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : 0;
  const minIdx = prices.length > 0 ? prices.indexOf(Math.min(...prices)) : -1;

  const option: EChartsOption = {
    textStyle: {
      fontFamily:
        '-apple-system, BlinkMacSystemFont, "SF Pro Display", Inter, sans-serif',
    },
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(255,255,255,0.92)",
      borderWidth: 0,
      padding: [8, 12],
      extraCssText:
        "border-radius:12px; box-shadow:0 4px 20px rgba(0,0,0,0.10); backdrop-filter:saturate(180%) blur(16px);",
      textStyle: { color: "#1d1d1f", fontSize: 12 },
      formatter: (params) => {
        const p = Array.isArray(params) ? params[0] : params;
        if (!p || typeof p.value !== "number") return "";
        return `<span style="color:#86868b">${p.name}</span><br/><b>¥${p.value.toFixed(0)}</b>`;
      },
    },
    grid: { left: 44, right: 28, top: 28, bottom: 32 },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: dates,
      axisLabel: { color: "#86868b", fontSize: 11, margin: 12 },
      axisLine: { show: false },
      axisTick: { show: false },
    },
    yAxis: {
      type: "value",
      axisLabel: {
        color: "#86868b",
        fontSize: 11,
        margin: 12,
        formatter: (v: number) => `¥${v}`,
      },
      axisLine: { show: false },
      axisTick: { show: false },
      // 极细浅色网格线，几乎不可见
      splitLine: { lineStyle: { color: "#f0f0f2", width: 1 } },
    },
    series: [
      {
        name: "最低价",
        type: "line",
        smooth: 0.4,
        symbol: "circle",
        symbolSize: 5,
        showSymbol: false,
        lineStyle: { width: 2, color: "#0071e3" },
        itemStyle: { color: "#0071e3", borderColor: "#fff", borderWidth: 2 },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(0,113,227,0.10)" },
              { offset: 1, color: "rgba(0,113,227,0)" },
            ],
          },
        },
        data: prices,
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: { type: [4, 4], color: "#d2d2d7", width: 1 },
          label: {
            formatter: `均价 ¥${mean.toFixed(0)}`,
            color: "#86868b",
            fontSize: 11,
            padding: [0, 0, 4, 0],
          },
          data: [{ yAxis: mean }],
        },
        markPoint: {
          symbol: "circle",
          symbolSize: 8,
          itemStyle: { color: "#fff", borderColor: "#0071e3", borderWidth: 2 },
          label: {
            formatter: minIdx >= 0 ? `最低 ¥${prices[minIdx].toFixed(0)}` : "",
            position: "top",
            distance: 8,
            color: "#1d1d1f",
            fontSize: 11,
            fontWeight: 500,
          },
          data:
            minIdx >= 0
              ? [{ name: "最低价", coord: [dates[minIdx], prices[minIdx]] }]
              : [],
        },
      },
    ],
  };

  return (
    <div className="relative">
      {data.length === 0 ? (
        <div
          className="flex items-center justify-center text-[15px] text-subtle"
          style={{ height: CHART_HEIGHT }}
        >
          暂无数据，请先点击开始分析
        </div>
      ) : (
        <ReactECharts
          option={option}
          style={{ height: CHART_HEIGHT }}
          notMerge
          lazyUpdate
        />
      )}

      {/* 加载遮罩：半透明毛玻璃 + spinner */}
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center rounded-control bg-white/65 backdrop-blur-[2px] transition-opacity duration-250 ease-out-soft">
          <div className="flex items-center gap-2.5 text-[14px] text-subtle">
            <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
              <circle
                cx="12"
                cy="12"
                r="9"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeOpacity="0.25"
              />
              <path
                d="M21 12a9 9 0 0 0-9-9"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
              />
            </svg>
            正在加载价格曲线…
          </div>
        </div>
      )}
    </div>
  );
}
