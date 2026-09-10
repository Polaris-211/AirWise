import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";
import type { PriceHistoryPoint } from "./types";

interface PriceChartProps {
  data: PriceHistoryPoint[];
}

/** 近 30 日最低价折线图，含均价线与最低点标注 */
export default function PriceChart({ data }: PriceChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex h-72 items-center justify-center rounded-xl border border-dashed border-slate-200 bg-white text-slate-400">
        暂无数据，请先点击开始分析
      </div>
    );
  }

  const dates = data.map((d) => d.date);
  const prices = data.map((d) => d.min_price);
  const mean = prices.reduce((a, b) => a + b, 0) / prices.length;
  const minIdx = prices.indexOf(Math.min(...prices));

  const option: EChartsOption = {
    tooltip: {
      trigger: "axis",
      formatter: (params) => {
        const p = Array.isArray(params) ? params[0] : params;
        if (!p || typeof p.value !== "number") return "";
        return `${p.name}<br/>最低价：¥${p.value.toFixed(0)}`;
      },
    },
    grid: { left: 48, right: 24, top: 32, bottom: 40 },
    xAxis: {
      type: "category",
      data: dates,
      axisLabel: { color: "#64748b", fontSize: 11 },
      axisLine: { lineStyle: { color: "#e2e8f0" } },
    },
    yAxis: {
      type: "value",
      name: "价格 (¥)",
      nameTextStyle: { color: "#94a3b8", fontSize: 11 },
      axisLabel: {
        color: "#64748b",
        formatter: (v: number) => `¥${v}`,
      },
      splitLine: { lineStyle: { color: "#f1f5f9" } },
    },
    series: [
      {
        name: "最低价",
        type: "line",
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        lineStyle: { width: 2, color: "#3b82f6" },
        itemStyle: { color: "#3b82f6" },
        areaStyle: {
          color: {
            type: "linear",
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(59,130,246,0.18)" },
              { offset: 1, color: "rgba(59,130,246,0.02)" },
            ],
          },
        },
        data: prices,
        markLine: {
          silent: true,
          symbol: "none",
          lineStyle: { type: "dashed", color: "#f59e0b" },
          label: {
            formatter: `均价 ¥${mean.toFixed(0)}`,
            color: "#d97706",
          },
          data: [{ yAxis: mean }],
        },
        markPoint: {
          symbol: "pin",
          symbolSize: 42,
          itemStyle: { color: "#22c55e" },
          label: {
            formatter: "最低",
            fontSize: 10,
            color: "#fff",
          },
          data: [{ name: "最低价", coord: [dates[minIdx], prices[minIdx]] }],
        },
      },
    ],
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <ReactECharts option={option} style={{ height: 288 }} notMerge lazyUpdate />
    </div>
  );
}
