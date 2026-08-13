# G0 Gate · 开工闸门工程规格 v2.0

> AI Agent 开工纪律的第一步：新任务开始，自动装配正确档位的上下文，并自检"真加载到了"，不靠人粘贴。
> **v2.0 变更（2026-08-13）**：加入档位自动选择算法、manifest 协议 v2、自检评分公式、Wire Protocol 契约、验证方法学。本版为实质性修订，替代 v1.0（MIT 版已过时，见 docs/migration-guide.md）。
> License：**BSL 1.1**（商用需授权，见 LICENSE）。运行时实现（Kosmin 内嵌）不随本规格分发。

---

## 0. 背景与动机

AI Agent 开工协议（gate 协议）通常是"人的习惯资产"——靠人从文档里翻出协议文本、手动粘贴给 Agent。
问题：换个团队/客户就漏贴、贴错档、协议过期不同步 → Agent 睁眼瞎启动。

解法：把开工协议升级为 **G0 开工闸门**，排于 G1-G4 之前，专管"开局上下文"，让系统替人扛纪律。

**v2.0 新增动机**：v1.0 发布后三个真实失败案例（详见 §0.1），证明"概念正确 ≠ 可落地"。v2 聚焦可工程化的协议层。

### 0.1 失败案例集（v2 新增）

| 案例 | 现象 | 根因 | v2 对应解法 |
|---|---|---|---|
| C1 | 换团队后没人记得贴协议，Agent 空上下文开干 | 协议靠人记忆 | §3 manifest 注册表（版本化、按项目绑定） |
| C2 | 贴了旧版协议，新规则没同步 | 协议无版本概念 | §2.3 版本协商 + Accept-Version |
| C3 | 窗口将满还装 heavy 档，直接 OOM 级卡死 | 档位靠人判断 | §2.1 自动选择算法 + §2.4 预算守卫 |

## 1. G0 定位

- 闸门序号：G0（最前置），在 G1 grill-me 之前执行。
- 职责：新会话开局，自动装配正确档位的上下文，并自检"真加载到了"，不靠人粘贴。
- 不替代 G1-G4，只负责"开局上下文质量"。
- **v2 定位升级**：G0 是 Agent 治理协议的**会话层入口**，与 MCP（工具层）、A2A（Agent 间层）正交互补——G0 管"开局质量"，MCP/A2A 管"运行时交互"。

## 2. 分档模型（tier）

### 2.1 档位自动选择算法（v2 核心差异 ①）

系统按 `任务复杂度 × 域权重 × 窗口余量` 自动选档，不由人记。

```
score = task_complexity(0..1) * domain_weight(0.5..1.5) * window_factor
window_factor = clamp(window_remaining / window_total, 0.2, 1.0)

tier = lite      if score < 0.30
tier = standard  if 0.30 <= score < 0.65
tier = heavy     if score >= 0.65
```

| 输入 | 来源 | 示例 |
|---|---|---|
| task_complexity | 任务首轮意图分类（§5 决策树） | 问答=0.1，单文件改=0.4，跨模块=0.7，战略=0.9 |
| domain_weight | 域配置表（manifest 内） | 内容=0.7，工程=1.0，运营=1.2，战略=1.5 |
| window_remaining | 运行时窗口探针（§6.5） | 当前余量 / 总窗口 |

### 2.2 档位读取清单（默认提案）

| 档位 | 读取清单 | 适用 |
|---|---|---|
| lite | 护照摘要(≤50行) + 最近5条记录 | 轻量问答 / 单步 |
| standard | 护照全文 + 近1天日志 + 最近10条记录 + 进度板相关段 | 常规任务 |
| heavy | 护照全文 + 近3天日志 + 最近20条记录 + 进度板 + 闸门协议 | 内部总管 / 跨项目 / 战略 |

- **默认档**：内部 Agent 走 heavy；外部/客户 Agent 默认 standard，可按项目配置。

### 2.3 版本协商（v2 新增）

- 请求必须带 `Accept-Version: 2` 头；服务端拒绝不支持的版本（`426 Upgrade Required`）。
- manifest 绑定版本号：`manifest.version`，Agent 与注册表版本不匹配时按 §4 自检标"不可信"。

### 2.4 窗口预算守卫

若 `window_remaining < 15%`，自动降一档并报告"跳过项"（列表）。约束是窗口不是 token。

## 3. 自动发现 + 自动加载（核心，去掉人工粘贴）

- 新会话时 Agent 调用 `G0.run()`，由 session-init 钩子触发，非人触发。
- G0 从**协议注册表**拉当前项目绑定的 manifest（按项目归属解析）。
- 按 manifest 执行读取；人只配置一次（项目归属 + 选档策略 auto/forced）。
- 关键：Agent 自己 pull，人不再 paste。

### 3.1 manifest 协议 JSON Schema v2（v2 核心差异 ②）

```json
{
  "$schema": "https://g0.kongmin.ccwu.cc/schema/manifest-v2.json",
  "version": "2.0",
  "project": "kongmin/backend",
  "binding": { "path": ["backend", "worker"], "priority": 10 },
  "tier_policy": "auto",
  "domain": "engineering",
  "domain_weight": 1.0,
  "sources": [
    { "id": "passport", "kind": "file", "path": "《必查》-记忆护照.md", "tiers": ["standard", "heavy"], "min_size": 100 },
    { "id": "daily", "kind": "file", "path": "Daily/", "tiers": ["heavy"], "recency_hours": 72 },
    { "id": "pb", "kind": "mcp", "endpoint": "gate://pb/recent", "tiers": ["lite", "standard", "heavy"], "limit": 20 }
  ],
  "conflict_resolution": "priority-desc-then-freshness",
  "updated_at": "2026-08-13T12:00:00Z"
}
```

字段语义（v2 新增规范化）：
- `binding.path`：项目路径前缀匹配，最长前缀胜出
- `conflict_resolution`：同源多 manifest 冲突时，优先级降序 → 新鲜度升序
- `sources[].recency_hours`：超过则源标"过期"（触发 §4 自检）

## 4. 自检闭环（防睁眼瞎）

- 每个源读取后，G0 验证：非空、时间戳够新、连接可达。
- 失联/空 → 标"不可信"继续跑、不阻塞。
- 全部源不可信 → 开局声明"上下文可能为空/不可信"，提示人介入。

### 4.1 自检评分公式（v2 核心差异 ③）

```
score_i = freshness_i * reachability_i * nonempty_i
freshness_i = 1.0                     if age <= recency_hours
              1.0 - (age - recency) / (4 * recency)   if recency < age <= 5*recency
              0.0                     if age > 5*recency
reachability_i = 1.0 if connected else 0.0
nonempty_i = 1.0 if size >= min_size else 0.0

gate_confidence = avg(score_i)   # 0..100 分
可信阈值: >= 60 = pass, 30..59 = warn, < 30 = fail
```

- 输出 `gate_confidence` 进会话元数据（供 Enforcement B 层与 KPI 看板使用）。

## 5. 按域路由

- 仅加载当前任务域的协议段 + ≤3 个 Skill；不全量扫描。
- 域由任务首轮分类决定（工程 / 内容 / 运营 / 战略…）。

### 5.1 域分类决策树（v2 新增）

```
任务首轮输入
├─ 含"改代码/修bug/重构/测试" → engineering (权重1.0)
├─ 含"写/文章/视频/脚本/选题" → content (权重0.7)
├─ 含"上架/发布/运营/投流/数据" → operations (权重1.2)
├─ 含"决策/方向/预算/人选/战略" → strategy (权重1.5)
└─ 其他 → general (权重0.9)
```

## 6. 运行时集成点（工程实现清单）

1. **Session-init 钩子**：每次新会话自动调用 G0，无需人触发。
2. **协议注册表（版本化）**：存储三档 manifest，支持版本号、按项目绑定；支持"人改了协议 → 注册表同步更新"的通道。
3. **MCP/桥接端点**：若从记忆服务拉 manifest，需稳定端点 + 鉴权（见 wire-protocol.md）。
4. **配置 schema**：project binding + tier policy(auto|forced) + domain。
5. **上下文窗口探针**：运行时暴露当前窗口余量给 G0 做预算守卫。
6. **gate 状态机**（v2 新增，Enforcement A 层依赖）：`pending → (run) → pass | fail | degraded`；`pass` 是输出最终答复的前置条件。

## 7. Enforcement 层：硬拦截 + 机检扣分 + 具身

### 为什么"提醒 Agent 走 G1"是错的
若必须人手动提醒 Agent "你没走 G1"，说明闸门是摆设。治法是**让 Agent 想跳也跳不过**：拦截长在系统，扣分长在机器。

### 三层 Enforcement
| 层 | 通道 | 性质 |
|----|------|------|
| A | **harness 硬拦截** | 后台真强制：gate 未标 pass 前，运行时禁止输出最终答复 + 禁止写操作 |
| B | **机检自动扣分** | 运行时逐轮记录 gate 状态，跳门自动 -10 分，写入 KPI 看板，不需人发现 |
| C | **具身呈现** | 前台有声有脸：把纪律人格化为 Agent 的自然行为，让客户"看得到纪律" |

### 7.1 A 层拦截点时序（v2 新增）

```
session-start → G0.run()
  ├─ pass → 允许正常输出 + 写操作
  ├─ degraded → 允许输出但标记 "上下文不完整" 水印
  └─ fail → 禁止最终答复（仅允许"上下文缺失"解释）+ 禁止写操作
```

### 7.2 B 层扣分公式（v2 新增）

```
score_deduction = -10 * (1 + violations_this_session)   # 首次 -10，累犯 -20, -30...
恢复机制：连续 3 次合规会话后 penalty 归零
```

### 一致性约束（防表演）
后台硬拦截（A）是**真强制**，具身（C）是**体验层**。绝不允许"演"了纪律而后台没拦。

## 8. 验收标准（v2）

- [ ] 新会话 / 新任务无需人粘贴，Agent 自动拉到正确档位 manifest 并装配上下文。
- [ ] 档位由算法自动选择（§2.1），人可 forced 覆盖但需记录。
- [ ] 任一源失联时标"不可信"且不阻塞。
- [ ] 窗口不足时自动降级并报告跳过项。
- [ ] 人改协议 → 注册表可同步 → 下次会话生效。
- [ ] Enforcement A：gate 未 pass 时运行时拦截最终输出与写操作（机器验证，非人工）。
- [ ] Enforcement B：跳门自动 -10 分（累犯翻倍）并落入 KPI 看板，无需人发现。
- [ ] 一致性：A 层生效是 C 层出声的前置条件，禁止"演纪律"。
- [ ] **v2 新增**：8 个验证场景全部通过（见 verification.md）。
- [ ] **v2 新增**：Wire Protocol 三端点契约通过（见 wire-protocol.md）。

## License

**BSL 1.1** © 2026 Wang Deyi (DeyiAI / Kongmin)。商用需授权；个人/内部使用免费。v1.0（MIT）已过时，见 docs/migration-guide.md。
