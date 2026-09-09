# AirWise

智能机票价格监测 Web App。用三个 Agent 做价格监测、趋势分析和购票建议。当前版本 **0.1.0**，仅骨架可跑通。

参加传智杯 Vibe Coding 比赛。

## 目录结构

```
airwise/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── agents/
│   │   └── api/
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── vite.config.ts
├── docs/
│   ├── prompts/
│   └── screenshots/
└── README.md
```

## 本地启动

先启动后端（端口 8000），再启动前端（端口 5173）。

### 后端

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
# source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

健康检查：访问 `http://localhost:8000/api/health`，应返回 `{"status":"ok","app":"AirWise","version":"0.1.0"}`。

### 前端

```bash
cd frontend
npm install
npm run dev
```

浏览器打开 `http://localhost:5173`。页面会请求 `/api/health`（Vite 已代理到 8000）。

## 技术栈

- 后端：FastAPI、SQLAlchemy、SQLite、LangChain
- 前端：React、Vite、ECharts、Tailwind CSS

## 当前进度

**0.1.0** — 项目骨架：健康检查接口、CORS、前端首页与后端连通状态。业务逻辑尚未实现。
