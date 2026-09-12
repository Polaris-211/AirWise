# Day 6（续）— 收尾细节：favicon + 首次引导 + 手机端适配
日期：2026-09-12

## 我的 Prompt
> 一、favicon 与页面标题
>   - 创建 frontend/public/favicon.svg（蓝色圆角方块 #0071e3 + 白色飞机）
>   - index.html 设置 lang="zh-CN"、<title>AirWise · 智能机票价格监测</title>、
>     <link rel="icon"> 指向 favicon、meta description
> 二、首次使用引导
>   - 首次访问（localStorage 无标记）时显示提示条，可关闭且不再显示
>   - 样式浅蓝底圆角，延续 Apple 风格
> 三、手机端适配（375px）
>   - 查询栏输入框上下堆叠；交换按钮位置合理
>   - 三张 Agent 卡片单列堆叠
>   - 航班列表不重叠；顶栏不换行错乱；提醒面板宽度自适应
>
> 要求：延续 Apple 风格，Tailwind 实现

## 模型
Cursor Grok 4.6

## Cursor 做了什么
- 新增 frontend/public/favicon.svg（矢量图标）
- 补充 index.html 的 title / meta / lang / icon
- 新增首次访问引导提示条（localStorage 记忆已关闭）
- 修复窄屏下的布局问题（查询栏堆叠 / 卡片单列 / 列表布局 / 顶栏换行）

## 验证
- 浏览器标签页显示 AirWise 图标
- 首次访问显示引导条，关闭后刷新不再出现
- F12 设备模拟 375px 宽度：查询栏堆叠、三卡片单列、无元素重叠

## 说明
本轮为收尾细节优化，非核心功能迭代。
