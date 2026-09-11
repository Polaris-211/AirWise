# Day 5（续）— 数据真实度升级

## 我的 Prompt
> 一、后端加字段：起降机场、票面价、机建费(50)、燃油费(20-120)、双档价格
>    mock 生成两档价格 + 机场随机分配 + 航司限定三家
> 二、前端航司 logo（后被废弃）
> 三、行李开关（iOS 风格透明滑块）
> 四、起降机场展示
> 五、价格含税费说明

## 模型
Claude Opus 5 High

## Cursor 做了什么
- FlightPrice 表新增 dep_airport / arr_airport / base_price / tax_airport /
  tax_fuel / price_no_baggage / price_with_baggage
- MockPriceSource 生成机场、双档价格、税费
- 新增历史数据回填（过去 30 天，启动自动补 + POST /api/monitor/backfill）
- 前端：行李开关（iOS 风格）、含税价格展示、机场展示

## 遇到的问题与处理
1. 下载的"东航 logo"实际是别家航司 → 发现后**移除整个航司 logo 模块**，
   改为文字展示航司名（避免错误信息，答辩风险更小）
2. 删库重建后曲线只剩 1 天数据 → 新增"历史数据回填"能力，恢复 30 天走势

## 验证
- 曲线恢复 30 天走势（含均价线、最低点标注）
- 航班列表显示航司名 + 起降机场 + 含税总价
- 行李开关可切换价格口径
