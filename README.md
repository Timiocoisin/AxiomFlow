# AxiomFlow

**基于 AI 的智能 PDF 翻译平台**

精准保留数学公式、图表布局与排版结构

## 📋 系统要求

- **Python** >= 3.10
- **Node.js** >= 18.0
- **MySQL** >= 8.0
- **Ollama** (可选，用于本地 AI 翻译)

## 🚀 完整启动指南

## 🪟 Windows（PowerShell）快速启动（推荐）

在项目根目录 `AxiomFlow` 下依次执行（PowerShell 用 `;` 连接命令）：

### 1) 启动后端（FastAPI）

```powershell
cd axiomflow-api; pip install -e .; uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2) 启动 Celery Worker（异步任务）

打开新的 PowerShell 窗口：

```powershell
cd axiomflow-api; python scripts/start_celery_worker.py
```

### 3) 启动前端（Vue）

打开新的 PowerShell 窗口：

```powershell
cd axiomflow-web; npm install; npm run dev
```
