# G0 Gate · 开工闸门

> The missing gate before G1: automatic context assembly for AI agents, with a self-check loop. No more copy-pasting onboarding protocols by hand.
>
> G1 之前的那道闸门：为 AI Agent 自动装配正确档位的开工上下文，并自检"真加载到了"，不靠人粘贴。

---

## Try it in 30 seconds / 30 秒试用

```bash
git clone https://github.com/kongminOS/g0-gate.git
cd g0-gate
python examples/run_g0_demo.py
```

Expected output (pure simulation — hard-coded data, reads no real files, contains no runtime logic):

```
[G0] task registered: 'regular development task' -> tier: standard
[G0] loading 4 source(s)...
  passport         ok           non-empty, updated 2 days ago
  daily log        ok           today's entry found
  recent records   ok           10 records, newest < 24h
  memory bridge    unreachable  connection refused -> marked untrusted
[G0] context_trust: partial (3/4 trusted)
[G0] done: tier assembled. No source was silently skipped.
```

That is the whole contract: **tier → sources → self-check → trust level, nothing silently skipped**. The real spec is in `docs/G0-spec.md`; the production implementation ships with commercial products (see `LICENSE`).

---

## What is G0 / 这是什么

Most agent teams have task discipline (G1 grill-me → G2 spec → G3 tickets → G4 implementation). But every new session still starts blind: someone has to find the protocol doc, paste it, hope it's the right version.

G0 moves that step out of human hands. On session start, G0 pulls the correct context tier (lite / standard / heavy) from a registry, loads it, and verifies each source actually arrived (non-empty, fresh, reachable). A source that fails is marked untrusted instead of silently ignored.

**G0 does not replace G1–G4. It makes them work** — gates only function when the agent actually carries the context those gates assume.

多数团队有任务闸门（G1 盘问 → G2 规格 → G3 工单 → G4 验收），但每次新会话依然睁眼瞎启动：得人肉翻协议、粘贴、祈祷版本没过期。G0 把这一步从人手里拿走：会话开始即按档位（lite / standard / heavy）从注册表拉取上下文并逐源自检。G0 不替代 G1–G4，它让 G1–G4 真正跑起来。

## Repository contents / 仓库内容

- `docs/G0-spec.md` — full engineering specification: tier model, auto-discovery, self-check loop, domain routing, enforcement layers.
- `examples/g0_registry.example.json` — registry manifest schema: tiers, domains, project bindings, tier policy.

The G1–G4 methodology and the gate-state enforcement tooling live in [kongminOS/agent-gates](https://github.com/kongminOS/agent-gates) under the MIT License.

## License / 许可

This repository is licensed under the **Business Source License 1.1** (see `LICENSE`).

| You may | You may not (without a commercial license) |
|---|---|
| Read, study, fork, modify | Offer a competing paid product/service built on this work |
| Use it personally and educationally | Embed it in a competing commercial offering |
| Use it in production **internally** within your organization | Resell or sublicense it as a standalone/embedded commercial product |

On **2030-08-13** (Change Date), this work converts to the **MIT License**.

Commercial licensing: contact the repository owner.

本仓库采用 BSL 1.1：个人、学习、组织内部生产使用免费；将其用于对外收费的竞争性产品/服务（含嵌入式）需获得商业授权。2030-08-13 起自动转为 MIT。

---

© 2026 Wang Deyi (DeyiAI / Kongmin)
