# Day 2 — 数据管道（PriceSource + MockSource + MonitorAgent + 3 APIs）
日期：2026-09-10

## 我的 Prompt

> 在现有 AirWise 项目基础上，实现"数据管道"部分。
> 背景：AirWise 是智能机票价格监测系统，Monitor Agent 负责采集票价。
> 因合规原因个人版不能直连 OTA 官方 API，故采用"可插拔数据源"设计：
> 先用内置历史数据重放源跑通全链路，未来可无缝替换为真实 API。
>
> 请实现以下 6 部分：
> 1. 数据模型 backend/app/models.py —— FlightPrice 表（id, origin, destination,
>    flight_date, flight_no, airline, price, currency, source, captured_at），
>    对 (origin,destination,flight_date) 建索引
> 2. 数据源抽象基类 backend/app/sources/base.py —— PriceSource 抽象类，
>    fetch_prices(origin, destination, flight_date) -> list[dict]
> 3. 内置重放数据源 backend/app/sources/mock_source.py —— MockPriceSource，
>    按航线真实价格区间生成（BJS-SHA 500~1200 等），用(航线+日期)做随机种子
>    保证可复现，每次生成 3-5 条不同航班
> 4. 重写 backend/app/agents/monitor.py —— MonitorAgent(source: PriceSource)，
>    run() 调用数据源并写入数据库，返回 inserted 数量
> 5. 扩充 backend/app/api/router.py —— 新增 POST /api/monitor/run、
>    GET /api/routes/{origin}/{destination}/prices、
>    GET /api/routes/{origin}/{destination}/history?days=30
> 6. 启动时自动建表
>
> 要求：文件职责单一、中文注释、暂不引入 LangChain、完成后告知测试方式

## Cursor 做了什么

一次性生成 6 个模块：
- models.py（FlightPrice ORM 表 + 复合索引）
- sources/base.py（PriceSource 抽象基类，定义 fetch_prices 接口）
- sources/mock_source.py（按航线价格区间 + 日期种子生成可复现数据）
- agents/monitor.py（重写为依赖注入版，接收任意 PriceSource）
- api/router.py（新增 3 个接口）
- main.py（启动时 create_all 自动建表）

并自动重启 uvicorn，顺带解决了 8000 端口被旧进程占用的问题。

## 验证过程与结果

1. POST /api/monitor/run {"origin":"BJS","destination":"SHA","flight_date":"2026-09-20"}
   → 200 OK，返回 {"agent":"monitor","inserted":4,...}
2. GET /api/routes/BJS/SHA/prices?flight_date=2026-09-20
   → 200 OK，返回 4-5 条航班记录（CA4150 / 中国国际航空 / 503.91 CNY / source=mock）
3. GET /api/routes/BJS/SHA/history?days=30
   → 200 OK，返回每日最低价：
     [{"date":"2026-09-08","min_price":677.16},
      {"date":"2026-09-09","min_price":693.38},
      {"date":"2026-09-20","min_price":503.91}]

## 我如何引导修正

本次 Cursor 一次生成成功，未出现需要反复修的 Bug。过程中处理的问题：
- 后端 8000 端口被之前的进程占用 → Cursor 自动结束旧进程后重启成功
- Swagger 测试 GET 接口时忘填必填参数 origin/destination → 页面给出红色
  必填提示，补填后正常返回

## 架构亮点

PriceSource 抽象层让"数据来源"与"业务逻辑"解耦：Monitor Agent 只依赖接口，
不关心数据从哪来。当前注入 MockPriceSource（内置重放源），未来拿到官方 API
授权后，只需新增一个 XxxPriceSource 实现类，业务代码零改动即可切换真实数据。
