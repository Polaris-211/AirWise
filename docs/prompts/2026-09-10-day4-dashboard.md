# Day 4 — 前端可视化看板
日期：2026-09-10

## 我的 Prompt

> 在 AirWise 前端（React + Vite + TypeScript + Tailwind）基础上，把首页改造成
> "机票价格监测看板"。后端接口已就绪（POST /api/agents/run、GET history）。
>
> 【1】安装 echarts 和 echarts-for-react
> 【2】改造 App.tsx，分三块：
>      顶部查询栏（出发地/目的地/日期/目标价 + 开始分析按钮）
>      中间价格曲线（ECharts 折线，标注均价线与最低点）
>      底部三 Agent 卡片（Monitor 采集条数 / Analyst 信号+指标+置信度 /
>      Advisor 建议+紧急度+LLM 话术）
> 【3】卡片按信号变色：buy_now 绿 / consider 黄 / wait 灰
> 【4】数据流：点按钮 → POST /api/agents/run 更新卡片 → GET history 刷新曲线
> 【5】视觉：浅色卡片、圆角轻阴影、价格大字突出、响应式
>
> 要求：TypeScript 类型清晰、中文注释、不引入 UI 组件库

## Cursor 做了什么

新增/修改 4 个文件：
- `src/types.ts`（新建：API 响应类型定义）
- `src/PriceChart.tsx`（新建：ECharts 折线图组件，含均价虚线与最低点标注）
- `src/App.tsx`（改造：查询栏 + 曲线 + 三张 Agent 卡片）
- `package.json`（echarts / echarts-for-react）

## 验证过程与结果

1. 启动后端（8000）+ 前端（5173），浏览器打开 http://localhost:5173
2. 页面显示：AirWise 品牌名 + 查询栏（BJS/SHA/2026-09-20/目标价 800）+ 空状态提示
3. 点击「开始分析」→ 3 秒内完成：
   - 曲线画出近 30 日最低价走势（含均价虚线 ¥600、"最低"标记点）
   - Monitor 卡：4 条报价已入库
   - Analyst 卡（绿色）：立即购买 / 当前价 ¥504 / 均价 ¥618 / 最低 ¥500 /
     更便宜天数占比 25% / 置信度 99%
   - Advisor 卡（紧急）：购买 / 完整中文建议 / "LLM 增强"标记

## 我如何引导修正

- 首次访问报 ERR_CONNECTION_REFUSED → 说明服务未启动，让 Cursor Agent
  重新拉起后端 + 前端后恢复正常
- 页面初始显示"暂无数据，请先点击开始分析"（空状态设计合理），
  点击分析后数据正常填充

## 亮点

1. **三 Agent 结果可视化**：把后端抽象的 JSON 变成"一眼看懂"的卡片
2. **状态色彩语言**：buy_now 绿 / consider 黄 / wait 灰，用户不用读文字就知道结论
3. **LLM 增强可视化**：卡片底部标注"LLM 增强"，直观展示大模型的价值贡献
4. **空状态友好**：无数据时给明确引导，不是空白页
