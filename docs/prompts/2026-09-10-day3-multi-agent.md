# Day 3 — 多 Agent 协同 + DeepSeek LLM 接入
日期：2026-09-10

## 我的 Prompt

> 在 AirWise 项目基础上，实现完整的"多 Agent 协同"：Analyst Agent、Advisor Agent、
> Orchestrator 编排，并接入 DeepSeek LLM 让两个 Agent"会说话"。
>
> 【1】config.py 新增 llm_api_key / llm_base_url / llm_model
> 【2】backend/app/llm/client.py —— LLMClient 封装（openai SDK，
>      没 key 优雅降级返回 None，调用失败捕获异常）
> 【3】重写 agents/analyst.py —— 基于历史价格判断低点：
>      current/mean/min/pct 四指标 → buy_now/consider/wait 三信号；
>      加 _llm_enhance() 让 LLM 生成专业中文解释
> 【4】重写 agents/advisor.py —— 把结论转成"人话建议 + 通知话术"，
>      按 target_price 判定 购买/观望/继续监控；加 _llm_enhance()
> 【5】新建 agents/orchestrator.py —— 串起 Monitor → Analyst → Advisor
> 【6】router.py 新增 GET /api/insights/... 和 POST /api/agents/run
>
> 要求：LLM 只做增强，没 key 也必须完整跑通；中文注释

## Cursor 做了什么

生成/修改 9 个文件：
- config.py（+3 个 LLM 配置项）
- llm/client.py（LLMClient + 全局单例，懒加载 openai SDK，15 秒超时）
- agents/analyst.py（重写：4 指标统计 + 3 档信号 + LLM 增强）
- agents/advisor.py（重写：规则建议 + LLM 话术）
- agents/orchestrator.py（新建：三 Agent 流水线）
- app/queries.py（新建：抽出"每日最低价"查询，router 与 orchestrator 共用——主动重构）
- api/router.py（+2 个新接口）
- requirements.txt（+openai）
- .env.example（+3 行 LLM 配置）

## 验证过程与结果

POST /api/agents/run
Body: {"origin":"BJS","destination":"SHA","flight_date":"2026-09-20","target_price":800}

→ 200 OK，返回：
- monitor: inserted 4
- analyst: current=503.91, mean=618.1, min=500, pct=0.25,
           signal="buy_now", confidence=0.99, llm_used=true
  reason: "当前价503.91元已逼近历史最低500元并显著低于618.1元均价……"
- advisor: recommendation="购买", urgency="high",
           suggested_action="立即下单锁定价格", llm_used=true
  message: "9月20日出发这条线现在503.91元，已经很接近历史最低500元了……
           系统判断现在就是阶段性低点，建议别犹豫，直接下单买吧。"

## 我如何引导修正

- Claude Opus 5 报"地区不支持" → 改 Cursor 设置 disableHttp2 后可用
- Claude Opus 5 高负载 → 切 Composer 2.5 完成启动任务
- 后端未启动 → 让 Cursor Agent 直接启动，并确认 /api/health 与新接口

## 架构亮点

1. 三 Agent 协同：Monitor（采集）→ Analyst（判断）→ Advisor（建议），
   由 AgentOrchestrator 串联，单次调用完成完整决策链。
2. LLM 只做增强，不阻塞主流程：无 key/调用失败时自动降级为规则版，
   llm_used 字段标记是否使用了 LLM。
3. 可插拔 LLM：通过 OpenAI 兼容接口，换 base_url + model 即可切换任意模型。
4. 主动重构：抽出 queries.py 让 router 与 orchestrator 共用查询逻辑。
