# AxiomFlow

当前仓库包含前端原型与可运行的认证后端（MySQL + 邮件）。

- `axiomflow-web`：Vue 3 + TypeScript 单页原型（已按最新首页设计迁移）
- `axiomflow-api`：FastAPI + MySQL 后端（注册/登录/邮箱验证/重置密码/SMTP 发信）

## 当前技术栈

- **前端**：Vue 3 / TypeScript / Vite
- **后端**：FastAPI / SQLAlchemy / MySQL / SMTP

## 环境要求

- **Node.js**：建议 18+（用于 `axiomflow-web`）
- **Python**：建议 **3.11**（最低建议 **3.10+**，用于 `axiomflow-api`）
- **MySQL**：8.x（本地安装运行，不使用 Docker）

## 运行前端（开发环境）

在项目根目录执行：

```powershell
cd axiomflow-web
npm install
npm run dev
```

默认访问地址：

- [http://localhost:5173](http://localhost:5173)

如需指定后端地址（默认 `http://localhost:8000`），在 `axiomflow-web` 目录创建/编辑 `.env`：

```bash
VITE_API_BASE_URL=http://localhost:8000
```

## 构建前端（生产构建）

```powershell
cd axiomflow-web
npm run build
```

构建产物位于：

- `axiomflow-web/dist`

## 启动后端（不使用 Docker）

### 1）准备 MySQL 数据库

确保本机 MySQL 已启动，并创建数据库：

```sql
CREATE DATABASE axiomflow CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
```

### 2）配置后端环境变量

```powershell
cd axiomflow-api
copy .env.example .env
```

编辑 `axiomflow-api/.env`，至少配置：

- `MYSQL_DSN`（示例）：`mysql+pymysql://root:你的密码@127.0.0.1:3306/axiomflow?charset=utf8mb4`
- `JWT_SECRET`：长度 >= 16 的随机字符串
- `SMTP_*`：你的邮箱/企业邮箱 SMTP 配置（用于注册验证与重置密码邮件）

### 3）安装依赖、建表、启动

```powershell
cd axiomflow-api
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

- `GET http://localhost:8000/health`
- `GET http://localhost:8000/auth/_ping`

### 4）后端 Smoke Test（可选）

```powershell
cd axiomflow-api
.\scripts\smoke.ps1
```

更多前端对接说明见：`axiomflow-api/docs/frontend-integration.md`。

## 说明

- 当前版本重点是 UI 设计对齐与前端原型重建，同时已补齐可运行的认证后端能力。
- 前端页面为单页原型，部分功能仍为演示数据；认证相关（注册/登录/邮箱验证/重置密码）已对接后端。

## i18n 开发约定（前端）

- 所有用户可见文案必须使用 `vue-i18n` 的 `t("key")`，禁止在 `.vue` 中直接写中文/英文提示语。
- 统一在 `axiomflow-web/src/i18n/locales/zh-CN.ts` 与 `axiomflow-web/src/i18n/locales/en-US.ts` 同步新增 key，保持双语结构一致。
- 推荐按页面或模块划分命名空间（如 `auth.*`、`profile.*`、`settings.*`），避免无语义的扁平 key。
- 错误提示、按钮文案、placeholder、空状态文案、toast 文案都属于“用户可见文案”，同样必须走 i18n。
- 允许保留 locale 相关格式逻辑（例如日期 `年/月/日` 拼接），但不应把完整提示句硬编码在组件中。
- 提交前建议执行：`cd axiomflow-web && npm run build`，并手动验证中英文切换与刷新后语言保持。
