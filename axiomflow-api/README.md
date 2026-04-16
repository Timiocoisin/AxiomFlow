# axiomflow-api

FastAPI + MySQL 后端（注册/登录/邮箱验证/重置密码/SMTP 发信）。

## 本地启动（开发）

在仓库根目录：

```powershell
cd axiomflow-api
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/auth/_ping`

## 环境变量

见 `.env.example`（MySQL DSN、JWT 密钥、CORS Origins、SMTP 等）。

## Smoke Test（PowerShell）

```powershell
cd axiomflow-api
.\scripts\smoke.ps1
```

## 前端对接说明

见 `docs/frontend-integration.md`。

