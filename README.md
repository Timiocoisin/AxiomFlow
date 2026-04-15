# AxiomFlow

当前仓库已调整为**前端 UI 原型重设计阶段**：

- `axiomflow-web`：Vue 3 + TypeScript 单页原型（已按最新首页设计迁移）
- `axiomflow-api`：后端代码已清空，仅保留目录结构（不提供可运行服务）

## 当前技术栈

- Vue 3
- TypeScript
- Vite

## 运行前端（开发环境）

在项目根目录执行：

```powershell
cd axiomflow-web
npm install
npm run dev
```

默认访问地址：

- [http://localhost:5173](http://localhost:5173)

## 构建前端（生产构建）

```powershell
cd axiomflow-web
npm run build
```

构建产物位于：

- `axiomflow-web/dist`

## 说明

- 当前版本重点是 UI 设计对齐与前端原型重建。
- 页面中的部分链接（如 `documents.html`）来自原型稿，用于保留交互演示路径。
