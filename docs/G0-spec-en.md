# G0 Gate — Session-Opening Context Assembly Protocol

> **Status**: Design v1.0 (production-tested)
> **Position**: G0 runs *before* G1–G4 — it owns "opening context quality", not task discipline.
> **Core promise**: AI agents open every session with the *right amount of context, verified loaded* — no human pasting, no hallucinated readiness.

---

## 0. Why G0 exists

- **The problem**: Agent startup protocols are usually "human habit assets" — someone must find the protocol text, pick the right tier, paste it into the prompt. Customers of AI-employee products have it worse: they lack the discipline, paste the wrong tier, use expired protocols → the agent starts blind.
- **The contradiction**: We sell "AI employees without gates = money burning in circles", yet our own agents depended on humans to remember the gates.
- **The fix**: Upgrade session opening into a **gate** — G0, placed before G1–G4, dedicated to *context assembly*. The system carries the rigor so humans don't have to.

## 1. Positioning

| Aspect | G0 |
|---|---|
| Gate number | G0 (most前置) |
| Responsibility | On session open, assemble the *correct tier* of context and **self-verify it actually loaded** |
| Does NOT replace | G1–G4 (task discipline gates) |
| Boundary | Context quality only |

## 2. Tier model (system-chosen, not human-remembered)

The system selects the tier from *task type + remaining context-window budget*.

| Tier | Read list (default proposal) | Use case |
|---|---|---|
| `lite` | Passport digest (≤50 lines) + last 5 PB records | Light Q&A / single step |
| `standard` | Full passport + last 1 day of Daily + last 10 PB records + relevant framework sections (grep) | Routine tasks |
| `heavy` | Full passport + last 3 days of Daily + last 20 PB records + full framework + gate protocols | Internal steward / cross-project / strategy |

- **Defaults**: internal agents (trusted) = `heavy`; customer agents = `standard` (configurable via registry).
- **Window budget guard**: pass `window_budget` (0–100 = remaining-window percentage). If below threshold → degrade one tier at a time and report `skipped` + `degraded_from`. **The constraint is the window, not tokens.**

## 3. Auto-discovery + auto-load (kills human pasting)

- A `session-init` hook triggers `G0.run()` on every new session — no human trigger.
- G0 pulls the project-bound manifest from a **versioned protocol registry** (§6).
- The agent pulls; humans configure once (project binding + tier policy `auto|forced`).

## 4. Self-check loop (anti-blind-start)

Each source returns a status:

| Status | Meaning |
|---|---|
| `ok` | Exists and fresh (mtime / latest record within staleness window) |
| `stale` | Exists but outdated (protocol changed without registry sync) |
| `missing` | File not found (wrong path or missing store) |
| `unreachable` | Backend unreachable (direct-connect probe; the bridge may lie, the source cannot) |

Aggregate → `context_trust`: `full` / `partial` (mark untrusted, keep running, don't block) / `none` (declare "context may be empty/untrusted", ask a human).

**Agent actions after receiving the manifest**:
1. Read each `sources[]` entry.
2. Any `status !== 'ok'`: skip **but report it in the opening declaration** — never pretend to have read it.
3. `skills[]`: load ≤3 domain skills (no full scans).
4. `skipped[]` / `degraded_from`: report downgrades transparently.

## 5. Domain routing

- Load only the protocol sections + ≤3 skills for the current task domain (engineering / content / operations / strategy…).
- Domain is decided by the first-turn task classification.

## 6. Versioned protocol registry

- Location: `<service-dir>/g0_registry.json` (dev / customer-installed, same layout).
- Structure: `version` / `defaults` (tier defaults + budget threshold + skill cap) / `tiers` (three-tier source lists) / `domains` (domain → extra_sources + skills) / `projects` (project → tier_policy + domain).
- **Protocol-change sync**: when the maintainer edits a protocol file → bump registry `version` (or per-source `staleness_days`) → next session picks it up. The registry file *is* the channel.

## 7. Acceptance criteria

- [ ] New session / new task: no human pasting; agent auto-pulls the correct-tier manifest and assembles context.
- [ ] Any source unreachable → marked `untrusted`, does not block.
- [ ] Window budget low → auto-degrade + report skipped items.
- [ ] Maintainer edits protocol → registry syncs → next session effective.
- [ ] **Enforcement A**: gate not `pass` → runtime blocks final output and write operations (machine-verified, not human).
- [ ] **Enforcement B**: gate-skip auto-scores (e.g. −10) into a KPI board without human discovery.
- [ ] **Enforcement C** (embodied): assistant speaks a "facts I can check vs decisions I need from you" split before executable instructions; holds its ground against "stop talking, just do it"; verbally reports gate-skip deductions.
- [ ] **Consistency**: A-layer enforcement is the precondition for C-layer voice — never let the assistant *perform* rigor while the backend doesn't enforce it.

## 8. Enforcement layer: why "reminding the agent to run G1" is wrong

If a customer must manually remind the agent "you skipped the gate", the gate is decoration. The fix: **make skipping impossible** — interception lives in the harness (A), scoring lives in the machine (B), experience lives in the embodied assistant (C). The customer never needs to know the word "G1".

| Layer | Channel | Nature | Owner |
|---|---|---|---|
| A | Harness hard block | Real enforcement: no final answer / no writes until gate = pass | Runtime |
| B | Machine auto-score | Per-turn gate state recording; skip → −10 into KPI board | Runtime + board |
| C | Embodied assistant | Visible discipline: the assistant *shows* it thinks before acting | Assistant runtime |

**Product narrative**: silent constraints (the gate) + a body that can talk and see (the assistant) = **"discipline grew a face and a voice."** Customers don't buy a black box; they buy a rigorous colleague who tells you why it stopped and why it asks one more question.

---

## License

MIT — see [LICENSE](../LICENSE).
