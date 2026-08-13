# G0 Wire Protocol v1.0

> G0 运行时与宿主（harness / MCP 桥接 / 记忆服务）之间的网络契约。
> 本协议是 **BSL 1.1** 资产的一部分；实现不随公开仓分发，但契约对集成方开放（只读实现指南）。
> 基础路径：`https://<host>/gate`（本地运行时为 `http://127.0.0.1:<port>/gate`）。

---

## 0. 通用约定

- **内容类型**：`application/json`；UTF-8；无 BOM。
- **版本协商**：请求头 `Accept-Version: 2`；服务端不支持时返回 `426 Upgrade Required` + `{"code":"version_mismatch","supported":[2]}`。
- **鉴权**：`Authorization: Bearer <token>`（token 由宿主注入，见 §4）。
- **幂等性**：`run` 支持 `Idempotency-Key` 头；重复 key 返回首次结果（缓存 5 分钟）。
- **重试语义**：`5xx` / 网络错误可安全重试（幂等）；`4xx` 不重试。
- **错误码**：见 §5。

## 1. POST /gate/init

初始化项目绑定与档位策略（首次使用 / 项目变更时调用一次）。

**请求**
```json
{
  "project": "kongmin/backend",
  "binding": { "path": ["backend", "worker"], "priority": 10 },
  "tier_policy": "auto",
  "domain": "engineering",
  "domain_weight": 1.0
}
```

**响应 200**
```json
{
  "ok": true,
  "manifest_id": "m_8f3k",
  "manifest_version": "2.0",
  "bound_sources": 6
}
```

**错误**：`409 conflict`（已初始化，需显式 `overwrite: true`）；`422`（schema 校验失败，附 `errors[]`）。

## 2. POST /gate/run

执行开工装配（每次新会话调用）。

**请求**
```json
{
  "session_id": "sess_20260813_001",
  "agent_id": "hermes",
  "task_preview": "修复 auth 模块的 token 过期 bug",
  "window_remaining": 0.42,
  "accept_version": 2
}
```

**响应 200（成功装配）**
```json
{
  "ok": true,
  "tier": "standard",
  "score": 0.47,
  "gate_confidence": 82,
  "loaded": [
    { "source": "passport", "status": "ok", "bytes": 2140, "freshness": 1.0 },
    { "source": "daily", "status": "ok", "bytes": 8900, "freshness": 0.9 },
    { "source": "pb", "status": "warn", "bytes": 0, "freshness": 0.0, "reason": "endpoint unreachable" }
  ],
  "skipped": [],
  "gate_state": "pass",
  "watermark": null
}
```

**响应 200（降级/失败）**
```json
{
  "ok": true,
  "tier": "lite",
  "score": 0.18,
  "gate_confidence": 22,
  "loaded": [{ "source": "passport", "status": "untrusted", "reason": "stale > 5x recency" }],
  "skipped": ["daily", "pb"],
  "gate_state": "fail",
  "watermark": "上下文可能为空/不可信"
}
```

**错误**：`401`（未鉴权）；`426`（版本不匹配）；`503`（注册表不可达，可重试）。

## 3. GET /gate/status

查询当前会话的 gate 状态（Enforcement B 层扣分与 KPI 看板轮询用）。

**响应 200**
```json
{
  "session_id": "sess_20260813_001",
  "gate_state": "pass",
  "gate_confidence": 82,
  "violations": 0,
  "deduction": 0,
  "tier": "standard",
  "manifest_version": "2.0"
}
```

**说明**：`violations` 为本次会话跳门次数；`deduction` 为累计扣分（公式见 spec-v2 §7.2）。

## 4. 鉴权规范

- 宿主在 session-init 时注入一次性 token（`G0_TOKEN` 环境变量或 IPC 传入）。
- token 有效期 = 会话生命周期；超时返回 `401`。
- 本地运行时（127.0.0.1）可降级为无鉴权（仅限开发模式，`G0_DEV=1` 时）。

## 5. 错误码表

| code | HTTP | 含义 | 可重试 |
|---|---|---|---|
| `unauthorized` | 401 | token 缺失/过期 | 否 |
| `version_mismatch` | 426 | Accept-Version 不支持 | 否 |
| `conflict` | 409 | 已初始化未覆盖 | 否 |
| `validation_failed` | 422 | schema 校验失败 | 否 |
| `registry_unreachable` | 503 | 协议注册表不可达 | 是 |
| `window_exhausted` | 429 | 窗口余量 < 5%，拒绝装配 | 否 |

## 6. 与 MCP / A2A 的关系

| 协议 | 层 | G0 的交互 |
|---|---|---|
| MCP | 工具层 | G0 可声明为 MCP server 端点（`gate://...`），供记忆服务拉取 |
| A2A | Agent 间层 | G0 状态（pass/fail）可作为 A2A 卡片元数据，供跨 Agent 协作时校验对方上下文质量 |
