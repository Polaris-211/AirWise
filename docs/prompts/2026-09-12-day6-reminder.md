# Day 6 — 提醒中心 + 浏览器通知 + 购买跳转
日期：2026-09-12

## 背景（为什么要做这个）
产品承诺是"到低点提醒用户，用户手动购买"，但之前只有页面展示，
缺少"提醒"和"购买入口"两环 —— 产品闭环断裂。
本轮补齐这两环。

## 我的 Prompt

> 背景：AirWise 的产品承诺是"到低点提醒用户，用户手动购买"，
> 但现在只有页面展示，缺少"提醒"和"购买入口"两环。请补齐。
>
> 一、提醒系统（后端）
> 1. 新增 Reminder 表：id / origin / destination / flight_date / price /
>    target_price / signal / message / created_at / is_read
> 2. Analyst 判定 buy_now 或 consider 时自动生成提醒（同航线同日期不重复）
> 3. 接口：GET /api/reminders、GET /api/reminders/unread-count、
>    POST /api/reminders/{id}/read、POST /api/reminders/read-all
>
> 二、提醒中心（前端）
> 1. 顶栏右侧铃铛 + 未读红点（数字角标），延续 Apple 风格
> 2. 点击展开毛玻璃面板：提醒列表 + 相对时间 + 单条已读 + 全部已读
> 3. 无提醒时"暂无提醒"；面板滑入动画；点击外部关闭
>
> 三、浏览器通知
> 1. Notification API，未授权时静默降级
> 2. 定时任务产生新提醒且页面打开时，弹系统通知
>    "AirWise · 发现低价   BJS→SHA 跌到 ¥504，建议购买"
>
> 四、购买跳转
> 1. Advisor 卡片底部加「去购买」主按钮（蓝色实心）
> 2. 跳转携程（三字码小写）：
>    https://flights.ctrip.com/online/list/oneway-{origin}-{destination}?depdate={flight_date}
> 3. 提醒面板每条也加跳转链接，target="_blank"
>
> 要求：延续现有 Apple 风格与现有组件（Toast / TopBar 等），Tailwind 实现。

## 模型
Cursor Grok 4.6

## Cursor 做了什么
- 后端：新增 Reminder 模型 + 4 个接口；AgentOrchestrator 与定时监测
  在 signal 为 buy_now / consider 时写提醒（同航线同日期唯一，避免重复）
- 前端：TopBar 加铃铛 + 未读角标；新增提醒面板（毛玻璃 + 相对时间 +
  已读操作 + 点击外部关闭）；Advisor 卡片加「去购买」按钮
- 浏览器通知：Notification API 封装，未授权静默降级

## 验证结果
1. GET /api/health → ok
2. GET /api/reminders/unread-count → {"count": 2}
3. GET /api/reminders?limit=5 →
   - BJS→CTU，2026-09-22，¥805，buy_now，未读，"[BJS→CTU 跌到 ¥805，建议购买]"
   - BJS→SHA，2026-09-22，¥626.85，consider，未读，"[BJS→SHA 跌到 ¥627，可以考虑]"
   （SHA-CAN 判定 wait → 正确地没有生成提醒，说明判定逻辑精准）
4. 页面：铃铛角标显示 2；面板可读、可标记已读、可跳转携程

## 我如何引导修正
- 数据库结构变更 → 停后端 → 删除 backend/airwise.db → 重启自动重建
- 首次监测需等约 15 秒才会产生提醒（由定时任务触发）

## 亮点
1. **产品闭环补全**：监测 → 判定 → 提醒 → 购买跳转，四环打通
2. **提醒去重设计**：同航线同日期不重复生成；仅 buy_now / consider 才提醒
   （wait 不打扰用户）—— 体现"不刷屏"的产品克制
3. **降级设计**：浏览器通知未授权时静默降级，不影响主流程
