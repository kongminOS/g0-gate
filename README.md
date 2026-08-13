# G0 Gate — AI Employee Governance: Session-Opening Context Assembly

> **AI 员工治理 · 开工闸门**：让 AI Agent 每次开局都装上"正确档位、验证已加载"的上下文——不靠人粘贴，不装睁眼瞎。

**G0 Gate** is a session-opening protocol for AI agents. It sits **before** G1–G4 (task-discipline gates) and owns one thing only: **context assembly quality at session start**. The system carries the rigor, so humans don't have to paste protocol text, guess the right tier, or chase expired documents.

```
G0 (context assembly) → G1 (grill-me) → G2/G3/G4 (task discipline)
```

## Why this matters (the AI employee governance problem)

- **Agents start blind**: without a gate, an agent opens a session with missing/wrong/expired context — and *acts confidently on it*.
- **Human habit assets don't scale**: relying on someone to paste the right protocol is fine for one operator, impossible for customers running AI employees.
- **The fix**: a gate the *system* runs — auto tier selection, auto load, self-verified.

If you're building AI employees / AI agent teams / multi-agent systems and care about **AI employee governance** (discipline, accountability, reproducible behavior), G0 is the entry gate you're missing.

## Core ideas

| Idea | What it does |
|---|---|
| **Tiered manifests** | `lite` / `standard` / `heavy` — the system picks by task type + window budget, humans don't memorize |
| **Window budget guard** | Constraint = context window, not tokens; low budget → auto-degrade + report what was skipped |
| **Self-check loop** | Every source returns `ok/stale/missing/unreachable` → aggregate `context_trust: full/partial/none`; never pretend to have read something |
| **Domain routing** | Load only the protocol sections + ≤3 skills for the task domain; no full scans |
| **Versioned registry** | `g0_registry.json`: protocol edit → bump version → next session effective; the registry file *is* the sync channel |
| **Enforcement (A/B/C)** | Harness hard-block (A) + machine auto-score (B) + embodied assistant voice (C) — skipping becomes *impossible*, not merely discouraged |

## Quick start（30 秒跑通）

```bash
# 1. 看 G0 跑起来的样子（无依赖，纯 Python）
python examples/run_g0_demo.py

# 2. 跑 8 个验证场景（全 PASS = 协议实现正确）
python examples/verify_gate.py --all
```

```
repo/
├── spec/
│   ├── G0-gate-spec-v2.md   # 🔴 现行规格 v2.0（BSL 1.1，含档位算法/manifest v2/自检公式）
│   ├── wire-protocol.md     # /gate/init + /gate/run + /gate/status 端点契约
│   └── verification.md      # 8 场景验证方法学
├── examples/
│   ├── g0_registry.example.json   # manifest v2 schema
│   ├── run_g0_demo.py             # 30 秒模拟演示
│   └── verify_gate.py             # 8 场景自动化断言
├── docs/
│   ├── migration-guide.md   # v1.0(MIT) → v2.0(BSL) 迁移说明（v1 已过时）
│   └── SKILL.md             # Layer A agent-side prototype
└── LICENSE                  # BSL 1.1（商用需授权）
```

**1. Read the spec** → `spec/G0-gate-spec-v2.md`（v2.0 现行；v1 见 docs/migration-guide.md 已过时）

**2. Add a session-init hook** to your agent runtime that calls `G0.run()` on every new session:

```bash
curl -X POST http://127.0.0.1:PORT/api/v1/session/start \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"my-agent","project":"my-project","g0":true,"g0_tier":"heavy","window_budget":55}'
```

**3. Point the registry** at your passport/daily/records sources (see `examples/g0_registry.example.json`).

**4. Wire enforcement**: harness blocks final output until gate = pass; machine scores gate-skipping; the assistant (if embodied) narrates the "facts I can check vs decisions I need from you" split.

## Example registry

```json
{
  "version": "1.0.0",
  "defaults": {
    "internal_aliases": ["steward", "lead", "operator"],
    "tier_policy": "auto",
    "budget_threshold": 40,
    "skill_cap": 3
  },
  "tiers": {
    "lite":     { "sources": ["passport:50", "records:5"] },
    "standard": { "sources": ["passport:full", "daily:1", "records:10", "framework:grep"] },
    "heavy":    { "sources": ["passport:full", "daily:3", "records:20", "framework:full", "gates:all"] }
  },
  "projects": {
    "company-ai": { "tier_policy": "auto", "domain": "engineering" }
  }
}
```

## Acceptance criteria (from SPEC §7)

- [x] New session → no human pasting; agent auto-pulls correct-tier manifest (field-tested)
- [x] Any source unreachable → marked `untrusted`, does not block
- [x] Window budget low → auto-degrade + report skipped items
- [x] Protocol edit → registry bump → next session effective

## Status

Production-tested in a multi-agent studio (internal + customer agents). Version 1.0.

## License

MIT — see [LICENSE](LICENSE).
