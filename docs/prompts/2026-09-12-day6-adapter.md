# Day 6（续）— 真实数据源适配器（可插拔架构验证）
日期：2026-09-12

## 我的 Prompt
> 背景：项目当前使用内置模拟数据源保证演示稳定。为证明架构可扩展、
> 具备真实接入能力，需新增真实数据源适配器，默认不启用。
>
> 1. 新建 backend/app/sources/ctrip_source.py
>    - 类 CtripPriceSource(PriceSource)，实现 fetch_prices()
>    - 数据来源：携程公开低价日历接口
>    - 请求失败/解析失败：捕获异常、打警告、返回空列表（不崩溃）
>    - 文件顶部加【合规声明】（仅技术演示、低频、不绕反爬、不商用）
> 2. config.py 加 data_source: str = "mock"（mock | ctrip）
> 3. 新建 sources/factory.py：get_price_source() 按配置装配
> 4. MonitorAgent 装配处改用 get_price_source()（依赖注入不变）
> 5. requirements.txt 加 httpx；.env.example 加 DATA_SOURCE=mock
>
> 要求：默认行为完全不变（默认 mock）；中文注释；异常处理健全

## 模型
Cursor Grok 4.6

## Cursor 做了什么
- 新建 ctrip_source.py（含合规声明、异常降级返回空列表）
- 新建 factory.py（get_price_source 装配）
- config.py 加 data_source 配置项
- AgentOrchestrator 与调度器改用 get_price_source()
- ⭐ 关键细节：历史回填【固定使用 MockPriceSource】，
  确保切到 ctrip 时不会破坏 30 天可复现曲线

## 验证
1. 默认装配验证：输出 `mock MockPriceSource` ✅
2. 解析逻辑单测：日历 JSON → 标准字段（flight_no/price/airline）✅
3. 默认流程不变：BJS→SHA 的航班列表与曲线与之前一致 ✅

## 亮点
1. **可插拔架构的实证**：从"只有一个实现（口头声明）"变为
   "两个实现 + 配置切换（可验证事实）"——这是架构声明的最强证据
2. **降级设计**：真实源失败时返回空列表，不影响主流程
3. **可复现性保护**：历史回填固定走 Mock，避免真实源的波动污染演示数据
4. **合规边界明确**：文件顶部声明用途与边界，主动规避法律风险
