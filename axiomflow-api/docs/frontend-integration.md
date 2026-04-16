# axiomflow-web 对接认证后端

后端基址（默认）：`http://localhost:8000`

## 关键约定（Access + Refresh）

- **Access Token**：后端在 `POST /auth/login`、`POST /auth/refresh` 返回 `access_token`（Bearer）。建议前端只放内存，或放 `sessionStorage`（视你的安全要求）。
- **Refresh Token**：后端通过 **HttpOnly Cookie** 下发与轮换；前端 JS **不可读**，只能在请求时自动携带。
- 因此前端请求务必开启凭证：
  - `fetch`: `credentials: 'include'`
  - `axios`: `withCredentials: true`

## axios 示例（推荐）

```ts
import axios from "axios";

export const api = axios.create({
  baseURL: "http://localhost:8000",
  withCredentials: true, // 让 refresh cookie 自动携带
});
```

## 接口清单

### 注册
- `POST /auth/register`
- Body:
  - `email`
  - `username`
  - `password`
- Response:
  - `{ ok: true, message?: string }`
- 失败：
  - `409 email_already_registered`

### 登录
- `POST /auth/login`
- Body：`email`、`password`
- Response：
  - `{ access_token, access_expires_at, token_type }`
- 失败：
  - `401 invalid_credentials`
- 副作用：
  - 下发 `axiomflow_refresh`（HttpOnly Cookie，Path=`/auth/refresh`）

### 刷新 Access（自动续期）
- `POST /auth/refresh`
- Body：无（读 cookie）
- Response：
  - `{ access_token, access_expires_at, token_type }`
- 失败：
  - `401 missing_refresh_cookie | invalid_refresh_token`

### 退出登录
- `POST /auth/logout`
- Body：无
- Response：`{ ok: true }`
- 副作用：
  - 撤销 refresh 并清 cookie（Path=`/auth/refresh`）

### 邮箱验证
- `POST /auth/verify-email`
- Body：`{ token }`
- Response：`{ ok: true }`
- 失败：
  - `400 invalid_or_expired_token`

### 重发验证邮件
- `POST /auth/resend-verification`
- Body：`{ email }`
- Response：`{ ok: true, message?: string }`
- 说明：为了避免枚举，不存在邮箱也返回 `ok: true`

### 申请重置密码
- `POST /auth/request-password-reset`
- Body：`{ email }`
- Response：`{ ok: true, message?: string }`
- 说明：为了避免枚举，不存在邮箱也返回 `ok: true`

### 重置密码
- `POST /auth/reset-password`
- Body：`{ token, new_password }`
- Response：`{ ok: true }`
- 失败：
  - `400 invalid_or_expired_token`
- 副作用：
  - 会撤销该用户所有 refresh（强制重新登录）

## 前端错误码到 UI 提示（建议）

- **409**：提示“邮箱已注册，请直接登录或找回密码”
- **401**：提示“账号或密码错误”或“登录已过期，请重新登录”
- **400 invalid_or_expired_token**：提示“链接已过期，请重新发送邮件/重新发起重置”

