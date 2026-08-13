---
name: g0-gate
description: G0 Gate — session-opening context assembly (tiered manifest + self-check + window-budget guard + domain routing). Runs before G1-G4. No human pasting.
---

# G0 Gate (Agent Skill Prototype)

> Layer A prototype: how an agent calls G0 and assembles context.
> Companion doc: `docs/SPEC.md` (the full protocol).

## When to run

- **Every new session start** (before G1 grill-me): the first thing any agent does.
- Goal: let the *system* carry rigor — no missing tiers, no wrong tiers, no expired protocols.

## Tier model (system picks, humans don't memorize)

| Tier | Read list | Use case |
|---|---|---|
| `lite` | passport digest (≤50 lines) + last 5 records | light Q&A / single step |
| `standard` | full passport + last 1d daily + last 10 records + framework sections (grep) | routine |
| `heavy` | full passport + last 3d daily + last 20 records + full framework + gate protocols | steward / cross-project / strategy |

- Default: internal (trusted) agents = `heavy`; customer agents = `standard` (registry defaults).
- Force: `tier:"lite"|"standard"|"heavy"` (or `g0_tier`).
- **Window budget guard**: pass `window_budget` (0–100 remaining %) → auto-degrade stepwise, report `skipped` + `degraded_from`. Constraint = window, not tokens.

## Calling

### A: session/start with g0 hook (recommended, one response)

```bash
curl -X POST http://127.0.0.1:PORT/api/v1/session/start \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"my-agent","project":"my-project","g0":true,"g0_tier":"heavy","window_budget":55}'
```

The `g0` field in the response = assembly manifest (sources / skills / context_trust).

### B: standalone

```bash
curl -X POST http://127.0.0.1:PORT/api/v1/g0/run \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"my-agent","project":"my-project","tier":"heavy","window_budget":55,"domain":"engineering"}'
```

- `project` supports aliases (PA mapping) — the registry can map "boss" → "company-ai" etc.
- `domain` default routes by project binding (engineering/content/operation/strategy), attaching ≤3 domain skills + extra sources.

## Self-check loop (anti-blind-start)

Each source returns a status:

| Status | Meaning |
|---|---|
| `ok` | exists + fresh (mtime / latest record within staleness_days) |
| `stale` | exists but outdated (protocol changed without registry sync) |
| `missing` | file not found |
| `unreachable` | backend unreachable (direct-connect probe: the bridge may lie, the source cannot) |

Aggregate `context_trust`: `full` / `partial` (mark untrusted, keep running, don't block) / `none` (declare "context may be empty/untrusted", ask a human).

**Agent actions after manifest**:
1. Read each `sources[]`.
2. `status!=='ok'` → skip **but report in the opening declaration**, never pretend.
3. `skills[]` → load ≤3 domain skills (no full scans).
4. `skipped[]` / `degraded_from` → report downgrades transparently.

## Versioned registry

- Location: `<service-dir>/g0_registry.json` (dev and customer installs, same layout).
- Structure: `version` / `defaults` (tier defaults + budget threshold + skill cap) / `tiers` / `domains` / `projects` (project → tier_policy + domain).
- Protocol edit → bump registry `version` + per-source `staleness_days` → next session effective.

## Acceptance (from SPEC §7)

- [x] Session start with g0 → auto-pull manifest, assemble (field-tested)
- [x] Any source unreachable → `untrusted`, does not block (context_trust=partial/none still returns)
- [x] Window budget low → auto-degrade + report skipped (budget=30 → heavy→standard→lite chain)
- [x] Protocol edit → registry bump → next session effective

## Known field notes

- **Tier misjudgment**: an agent that calls itself by a non-whitelisted id gets misjudged as customer-tier. Fix: tier lookup should consult an `internal_aliases` table in registry defaults, not a single hardcoded whitelist.
- **Manifest without source paths**: `/g0/run` responses must attach a `path` field per source (relative path / collection name), otherwise the agent cannot read.
- **Empty domain skills**: registry must pre-populate skills per domain; empty lists silently degrade routing.

## Boundaries / roadmap

- Registry location is service-dir; if the runtime migrates to a managed store, change `_G0_REG_FILE` in one place.
- Full no-human-trigger version (runtime-embedded auto-call) is pending the runtime's session-init hook.
