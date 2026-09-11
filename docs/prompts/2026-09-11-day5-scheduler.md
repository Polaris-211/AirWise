# Day 5（续）— 定时监测 + 前端状态指示
日期：2026-09-11

## 我的 Prompt

> 一、后端定时监测
> 1. requirements.txt 加 APScheduler
> 2. 新建 backend/app/scheduler.py：
>    - BackgroundScheduler，每隔 N 分钟（默认 30，从 config 读）对关注航线
>      （BJS-SHA / BJS-CTU / SHA-CAN）跑一次 MonitorAgent
>    - 每次记录：时间、航线、插入条数，保留最近 20 次
> 3. main.py 启动时启动调度器
>    ⚠️ 关键：uvicorn --reload 会重复导入模块，必须防重复启动
> 4. 新增接口：GET /api/scheduler/status、POST /api/scheduler/run-now
> 5. config.py 加配置项 monitor_interval_minutes
>
> 二、前端状态显示（延续 Apple 风格，配色统一）
> - 顶栏右侧：蓝色呼吸点（8px，主色 #0071e3）+ "自动监测中 · 每 30 分钟"
> - 旁边"上次更新 HH:MM"（12px 浅灰）
> - "立即监测"小尺寸描边式按钮
> - 页面加载调 status，之后每 30 秒轮询
> - 不用 emoji，用 CSS 圆点实现

## 模型与设置
- Claude Opus 5（首次超时，开新对话后完成）

## Cursor 做了什么
- `backend/app/scheduler.py`（新增）：MonitorScheduler
  - 防重复启动三层保障：模块级单例 + `_start_lock` + `_started` 标记 +
    绑定回环端口 47921 作为跨进程互斥锁
  - `coalesce=True + max_instances=1` 防止堆积
  - 单条航线异常只记入该航线的 error 字段，不影响其他航线
- `config.py`（+monitor_interval_minutes）/ `main.py`（启动与关闭钩子）/
  `router.py`（+2 个接口）/ `requirements.txt`（+apscheduler）
- `frontend/src/MonitorStatus.tsx`（新增）：状态点 + 上次更新 + 立即监测按钮
- `tailwind.config.js`（+breathe / halo keyframes）/ `types.ts`（+SchedulerStatus）

## 验证结果
GET /api/scheduler/status →
```json
{"running": true, "interval_minutes": 1,
 "watched_routes": ["BJS-SHA", "BJS-CTU", "SHA-CAN"],
 "last_run": {"trigger": "auto", "routes": [
   {"route": "BJS-SHA", "inserted": 4},
   {"route": "BJS-CTU", "inserted": 3},
   {"route": "SHA-CAN", "inserted": 4}], "inserted": 11},
 "total_runs": 1}
```
前端顶栏：蓝色呼吸点 + "自动监测中 · 每 1 分钟" + "立即监测"按钮

## 我如何引导修正
1. Cursor 重建 .env 时把真实 DeepSeek key 覆盖为占位符
   → 重新生成 key 填回（并出于安全考虑更换了已暴露的旧 key）
2. 前端未启动导致 ERR_CONNECTION_REFUSED
   → 让 Cursor 重新拉起 npm run dev

## 亮点
1. **真正的"自动"**：系统定时自动采集，无需人工点击——产品名里的"自动检测"落地
2. **工程严谨性**：防重复启动三层保障（模块单例 + 线程锁 + 端口互斥），
   解决了 uvicorn --reload 下调度器重复启动这一真实工程问题
3. **UI 一致性**：新增状态指示严格复用现有设计 token（accent/ink/subtle），
   视觉上像原生组件而非后加的
