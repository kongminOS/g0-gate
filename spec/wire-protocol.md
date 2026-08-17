# G0 Wire Protocol v1.0

> G0 运行时与宿主（harness / MCP 桥接 / 记忆服务）之间的网络契约。
> 本协议是 **BSL 1.1** 资产的一部分；实现不随公开仓分发，但契约对集成方开放（只读实现指南）。
> 基础路径：`https://<host>/api/v1`（本地运行时为 `http://127.0.0.1:<port>/api/v1`）。

---

## 修订记录
- **v1.0.1 (2026-08-17)**：对齐真实端点。原 `/gate/{init,run,status}` 为早期设计占位；当前可用契约为 `POST /g0/run`（装配）、`GET /g0/status`（查询）。G0 装配也可经宿主 `session/start` 钩子触发（body 带 `g0:true`），一次注册 + 装配。

---

## 0. 通用约定

- **内容类型**：`application/json`；UTF-8；无 BOM。
- **版本协商**：请求头 `Accept-Version: 2`；服务端不支持时返回 `426 Upgrade Required` + `{"code":"version_mismatch","supported":[2]}`。
- **鉴权**：`Authorization: Bearer <token>`（token 由宿主注入，见 §4）。
- **幂等性**：`run` 支持 `Idempotency-Key` 头；重复 key 返回首次结果（缓存 5 分钟）。
- **重试语义**：`5xx` / 网络错误可安全重试（幂等）；`4xx` 不重试。
- **错误码**：见 §5。

## 1. POST /g0/run

执行开工装配（每次新会话调用）。项目初始化经资源注册表（`g0_registry.json`）配置，无需独立 init 端点。

**请求**
```json
{
  "session_id": "sess_20260813_001",
  "agent_id": "hermes",
  "project": "kongmin/backend",
  "tier": "standard",
  "domain": "engineering",
  "window_budget": 60,
  "accept_version": 2
}
```

**响应 200（成功装配）**
```json
{
  "ok": true,
  "tier": "standard",
  "domain": "engineering",
  "loaded": [
    { "source": "passport", "status": "ok", "bytes": 2140, "freshness": 1.0 },
    { "source": "daily", "status": "ok", "bytes": 8900, "freshness": 0.9 },
    { "source": "pb", "status": "warn", "bytes": 0, "freshness": 0.0, "reason": "endpoint unreachable" }
  ],
  "skipped": [],
  "context_trust": "partial"
}
```

**响应 200（降级/失败）**
```json
{
  "ok": true,
  "tier": "lite",
  "loaded": [{ "source": "passport", "status": "untrusted", "reason": "stale > 5x recency" }],
  "skipped": ["daily", "pb"],
  "context_trust": "none"
}
```

**错误**：`401`（未鉴权）；`426`（版本不匹配）；`503`（注册表不可达，可重试）。

## 2. GET /g0/status

查询当前 G0 注册表与档位配置（Enforcement B 层扣分与 KPI 看板轮询用）。

**响应 200**
```json
{
  "ok": true,
  "version": "1.0.0",
  "updated": "2026-08-11",
  "tiers": ["lite", "standard", "heavy"],
  "domains": ["engineering", "content", "operation", "strategy"],
  "defaults": {}
}
```

## 3. 会话级钩子（宿主集成）

宿主可在会话启动时一次注册 + 装配：`POST session/start`（body 带 `g0:true` 或 `g0_tier`），响应含 `g0.manifest` 与 `context_trust`。集成方应按此钩子作为最小路径先实现。

## 4. 鉴权规范

- 宿主在 session-init 时注入一次性 token（`G0_TOKEN` 环境变量或 IPC 传入）。
- token 有效期 = 会话生命周期；超时返回 `401`。
- 本地运行时（127.0.0.1）可降级为无鉴权（仅限开发模式，`G0_DEV=1` 时）。

## 5. 错误码表

| code | HTTP | 含义 | 可重试 |
|---|---|---|---|
| `unauthorized` | 401 | token 缺失/过期 | 否 |
| `version_mismatch` | 426 | Accept-Version 不支持 | 否 |
| `validation_failed` | 422 | schema 校验失败 | 否 |
| `registry_unreachable` | 503 | 协议注册表不可达 | 是 |
| `window_exhausted` | 429 | 窗口余量 < 5%，拒绝装配 | 否 |

## 6. 与 MCP / A2A 的关系

| 协议 | 层 | G0 的交互 |
|---|---|---|
| MCP | 工具层 | G0 可声明为 MCP server 端点（`gate://...`），供记忆服务拉取 |
| A2A | Agent 间层 | G0 状态（pass/fail）可作为 A2A 卡片元数据，供跨 Agent 协作时校验对方上下文质量 |