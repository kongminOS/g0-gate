#!/usr/bin/env python3
"""
run_g0_demo.py -- G0 in 30 seconds (pure simulation).

Demonstrates what G0 *output* looks like: the system picks a context tier
by task type, "loads" each source, self-checks every one, and reports an
aggregate trust level. A source that cannot be verified is marked untrusted
instead of being silently ignored.

Safety notes:
  - All data below is hard-coded. This script reads no files, calls no
    network endpoint, and touches no real registry.
  - It contains no G0 runtime logic. The production G0 implementation is
    distributed with commercial products (see LICENSE, BSL 1.1).
  - Purpose: let you see the contract (tier -> sources -> self-check ->
    context_trust) before reading docs/G0-spec.md.

Run:  python examples/run_g0_demo.py
"""

TASK = "regular development task"

TIERS = ["lite", "standard", "heavy"]

# Simulated registry lookup: task type -> tier
TIER_POLICY = {
    "quick question": "lite",
    "regular development task": "standard",
    "cross-project strategy": "heavy",
}

# Simulated sources for the selected tier (what a real registry manifest
# would list). Statuses are hard-coded demo outcomes.
DEMO_SOURCES = [
    ("passport", "ok", "non-empty, updated 2 days ago"),
    ("daily log", "ok", "today's entry found"),
    ("recent records", "ok", "10 records, newest < 24h"),
    ("memory bridge", "unreachable", "connection refused -> marked untrusted"),
]


def main():
    tier = TIER_POLICY[TASK]
    print(f"[G0] task registered: {TASK!r} -> tier: {tier}")
    print(f"[G0] loading {len(DEMO_SOURCES)} source(s)...")

    trusted = 0
    for name, status, note in DEMO_SOURCES:
        print(f"  {name:<16} {status:<12} {note}")
        if status == "ok":
            trusted += 1

    if trusted == len(DEMO_SOURCES):
        trust = "full"
    elif trusted > 0:
        trust = "partial"
    else:
        trust = "none"

    print(f"[G0] context_trust: {trust} ({trusted}/{len(DEMO_SOURCES)} trusted)")
    print("[G0] done: tier assembled. No source was silently skipped.")
    print("[G0] (simulation only -- see docs/G0-spec.md for the real contract)")


if __name__ == "__main__":
    main()
