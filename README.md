# AxiomFlow

**基于 AI 的智能 PDF 翻译平台**

精准保留数学公式、图表布局与排版结构

## 📋 系统要求

- **Python** >= 3.10
- **Node.js** >= 18.0
- **MySQL** >= 8.0
- **Ollama** (可选，用于本地 AI 翻译)

## 🚀 完整启动指南

### 1. 克隆项目

```bash
git clone <repository-url>
cd AxiomFlow
```

### 2. 后端设置

#### 2.1 安装 Python 依赖

```bash
cd axiomflow-api
pip install -e .
```

#### 2.2 创建数据库

```sql
CREATE DATABASE axiomflow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 2.3 配置环境变量

复制环境变量示例文件：

```bash
cp env.example .env
```

编辑 `.env` 文件，配置以下关键项：

```env
# 数据库配置（替换为你的数据库信息）
DATABASE_URL="mysql+pymysql://root:password@localhost:3306/axiomflow?charset=utf8mb4"
CELERY_BROKER_URL="sqla+mysql+pymysql://root:password@localhost:3306/axiomflow?charset=utf8mb4"
CELERY_RESULT_BACKEND="db+mysql+pymysql://root:password@localhost:3306/axiomflow?charset=utf8mb4"

# CORS 配置（前端地址）
CORS_ALLOW_ORIGINS='["http://localhost:5173","http://127.0.0.1:5173"]'

# OAuth 配置（见下方详细说明）
GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
GITHUB_CLIENT_ID="your-github-client-id"
GITHUB_CLIENT_SECRET="your-github-client-secret"
FRONTEND_BASE_URL="http://localhost:5173"

# Ollama 配置（如果使用本地 AI 翻译）
OLLAMA_API_BASE="http://127.0.0.1:11434"
OLLAMA_MODEL="gemma2"
```

#### 2.4 启动后端服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将在 `http://localhost:8000` 启动。

**注意**：数据库表会在首次运行时自动创建。

#### 2.5 启动 Celery Worker（用于异步任务）

**Celery Worker** 用于执行异步任务（如 PDF 翻译），建议启动。

打开新的终端窗口：

```bash
cd axiomflow-api
python scripts/start_celery_worker.py
```

#### 2.6 启动 Celery Beat（可选，用于定时健康检查）

**Celery Beat** 用于定时任务调度，主要用于系统健康检查。只有在启用健康检查功能时才需要启动。

检查 `.env` 文件中的 `OBS_HEALTH_CHECK_ENABLED` 配置：
- 如果为 `true`（默认），需要启动 Celery Beat
- 如果为 `false`，可以跳过此步骤

启动 Celery Beat（如果需要）：

```bash
# 打开另一个终端窗口
cd axiomflow-api
python scripts/start_celery_worker.py beat --loglevel=info
```

**注意**：
- **Celery Worker**：必需（用于异步任务处理）
- **Celery Beat**：可选（仅在启用健康检查时需要）

### 3. 前端设置

#### 3.1 安装 Node.js 依赖

```bash
cd axiomflow-web
npm install
```

#### 3.2 配置环境变量

复制环境变量示例文件：

```bash
cp env.example .env.local
```

编辑 `.env.local` 文件：

```env
VITE_GOOGLE_CLIENT_ID="your-google-client-id.apps.googleusercontent.com"
```

#### 3.3 启动开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:5173` 启动。

### 4. 访问应用

打开浏览器访问：`http://localhost:5173`

### 5. 验证安装

1. **检查后端健康状态**：
   ```bash
   curl http://localhost:8000/v1/health
   ```

2. **检查前端**：
   - 访问 `http://localhost:5173`
   - 应该能看到登录页面

3. **查看 API 文档**：
   - Swagger UI：`http://localhost:8000/docs`
   - ReDoc：`http://localhost:8000/redoc`

## 🔐 OAuth 配置（可选）

### Google OAuth 配置

1. **创建 Google Cloud 项目**
   - 访问 [Google Cloud Console](https://console.cloud.google.com/)
   - 创建新项目或选择现有项目

2. **启用 Google Identity Services**
   - 在 API 和服务中启用 "Google Identity Services"

3. **创建 OAuth 2.0 客户端 ID**
   - 进入"凭据" → "创建凭据" → "OAuth 2.0 客户端 ID"
   - 应用类型选择"Web 应用"
   - **授权 JavaScript 来源**：
     ```
     http://localhost:5173
     http://127.0.0.1:5173
     ```
   - **授权重定向 URI**：
     ```
     http://localhost:5173/auth
     http://127.0.0.1:5173/auth
     ```

4. **配置环境变量**
   - 后端 `.env`：`GOOGLE_CLIENT_ID="xxxx.apps.googleusercontent.com"`
   - 前端 `.env.local`：`VITE_GOOGLE_CLIENT_ID="xxxx.apps.googleusercontent.com"`

### GitHub OAuth 配置

1. **创建 GitHub OAuth App**
   - 访问 [GitHub Developer Settings](https://github.com/settings/developers)
   - 点击 "New OAuth App"

2. **配置应用信息**
   - **Application name**：AxiomFlow
   - **Homepage URL**：`http://localhost:5173`
   - **Authorization callback URL**：`http://localhost:8000/v1/auth/github/callback`

3. **配置环境变量**
   - 后端 `.env`：
     ```env
     GITHUB_CLIENT_ID="your-github-client-id"
     GITHUB_CLIENT_SECRET="your-github-client-secret"
     FRONTEND_BASE_URL="http://localhost:5173"
     ```

## 🐛 常见问题

### 数据库连接失败

**问题**：`OperationalError: (2003, "Can't connect to MySQL server")`

**解决**：
- 确保 MySQL 服务已启动
- 检查 `DATABASE_URL` 配置是否正确（用户名、密码、数据库名）
- 确认数据库已创建

### Google OAuth 403 错误

**问题**：`The given origin is not allowed for the given client ID`

**解决**：
- 检查 Google Cloud Console 中的"授权 JavaScript 来源"是否包含 `http://localhost:5173`
- 确保前后端的 `GOOGLE_CLIENT_ID` 一致
- 清除浏览器缓存并重启服务

### Celery Worker 无法启动

**问题**：`ModuleNotFoundError` 或连接错误

**解决**：
- 确保在 `axiomflow-api` 目录下运行 worker
- 检查 `CELERY_BROKER_URL` 和 `CELERY_RESULT_BACKEND` 配置
- 确保数据库表已创建（启动后端服务会自动创建）
- 确保已安装所有依赖：`pip install -e .`

### 前端无法连接后端

**问题**：CORS 错误或 404

**解决**：
- 检查后端 `CORS_ALLOW_ORIGINS` 是否包含前端地址 `http://localhost:5173`
- 确认后端服务运行在 `http://localhost:8000`
- 检查浏览器控制台的网络请求

### 翻译服务不可用

**问题**：翻译时提示 "Provider not available"

**解决**：
- 如果使用 Ollama，确保 Ollama 服务已启动：`ollama serve`
- 检查 `OLLAMA_API_BASE` 和 `OLLAMA_MODEL` 配置
- 测试 Ollama 连接：`curl http://127.0.0.1:11434/api/tags`

---

## 📝 启动检查清单

启动前请确认：

- [ ] MySQL 服务已启动
- [ ] 数据库已创建
- [ ] 后端 `.env` 文件已配置
- [ ] 前端 `.env.local` 文件已配置（如使用 OAuth）
- [ ] Python 依赖已安装
- [ ] Node.js 依赖已安装
- [ ] Ollama 服务已启动（如使用本地 AI 翻译）

启动顺序：

1. ✅ 启动 MySQL
2. ✅ 启动后端服务（`uvicorn app.main:app --reload`）
3. ✅ 启动 Celery Worker（`python scripts/start_celery_worker.py`）
4. ✅ 启动 Celery Beat（可选，仅在 `OBS_HEALTH_CHECK_ENABLED=true` 时需要）
5. ✅ 启动前端服务（`npm run dev`）
6. ✅ 访问 `http://localhost:5173`

**说明**：
- **Celery Worker**：必需，用于执行异步任务（如 PDF 翻译）
- **Celery Beat**：可选，仅在启用健康检查功能时需要（默认启用）
