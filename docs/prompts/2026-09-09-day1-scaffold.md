# AirWise 项目骨架生成 — 2026-09-09

## 我的 Prompt（原话）
> 我要做一个名为「AirWise」的智能机票价格监测 Web App，
> 参加传智杯 Vibe Coding 比赛。技术栈：FastAPI + SQLAlchemy +
> SQLite + LangChain + React + Vite + ECharts + Tailwind CSS。
> ...（完整骨架生成指令，列出 backend/frontend/docs目录结构、
> /api/health 端点、前端 App.tsx 显示 AirWise 标题与健康卡片、
> README 启动指南等要求）

## Cursor 做了什么
> 一次性生成了 26 个文件：backend (FastAPI + 三个 Agent 占位
> monitor/advisor/analyzer + api路由) + frontend (React Vite +
> Tailwind 配置) + docs/prompts + docs/screenshots + README.md
> + .gitignore，并在 backend/requirements.txt 里列全依赖。

## 我如何引导修 Bug
> Cursor 一次生成成功，无需大改。验证：后端 /api/health 返回
> {"status":"ok","app":"AirWise","version":"0.1.0"}；
> 前端 npm install140 packages成功；npm run dev 启 Vite 5.4.21，
> 浏览器看到 AirWise 标题与"Backend Status: Connected"卡片。
