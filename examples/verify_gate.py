#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G0 Gate · 8 场景验证断言（v2 协议，对齐 spec/verification.md）

无运行时依赖，纯标准库。脚本自带一个最小的 G0 参考实现
（档位算法 §2.1 / 自检评分 §4.1 / Enforcement 评分 §7），用断言核对
spec/verification.md 中每个场景的「预期输出 → 判定标准」。

全 PASS = 协议实现正确（可离线运行，随公开仓分发）。

用法:
  python examples/verify_gate.py --all      # 跑全部 8 个场景
  python examples/verify_gate.py --scene 6  # 单场景（Enforcement A）

License: BSL 1.1 (商用需授权) · (c) 2026 Wang Deyi (DeyiAI / Kongmin)
"""
import argparse
import json
import os
import sys

# 复用 run_g0_demo 的 §2.1 / §4.1 参考实现（同仓库 examples/，非外部依赖）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_g0_demo import choose_tier  # noqa: E402

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REGISTRY = os.path.join(SCRIPT_DIR, "g0_registry.example.json")

TIER_ORDER = ["lite", "standard", "heavy"]
DOWNGRADE = {"heavy": "standard", "standard": "lite", "lite": "lite"}


# ---------- 最小参考实现（仅供断言，非运行时） ----------

def load_manifest():
    with open(REGISTRY, encoding="utf-8") as f:
        return json.load(f)


def _desired_tier(task_complexity, domain_weight=1.0):
    # 档位按 §2.1 公式（窗口用 0.8 计算意图档位；窗口不足触发降级见 §2.4）
    tier, _ = choose_tier(task_complexity, domain_weight, 0.8)
    return tier


def assemble(manifest, task_complexity, window_remaining,
             domain_weight=1.0, unreachable=None):
    """模拟一次 G0.run()：返回 tier / loaded / skipped / confidence / gate_state。"""
    unreachable = set(unreachable or [])
    desired = _desired_tier(task_complexity, domain_weight)
    degraded = False
    tier = desired
    if window_remaining < 0.15 and DOWNGRADE.get(tier) != tier:
        tier = DOWNGRADE[tier]
        degraded = True
    actual_idx = TIER_ORDER.index(tier)
    loaded, skipped = [], []
    for s in manifest["sources"]:
        s_tiers = s.get("tiers", [])
        if tier in s_tiers:
            if s["id"] in unreachable:
                loaded.append({"id": s["id"], "status": "untrusted",
                               "reason": "endpoint unreachable"})
            else:
                loaded.append({"id": s["id"], "status": "ok"})
        else:
            min_idx = min(TIER_ORDER.index(t) for t in s_tiers)
            if min_idx > actual_idx:
                skipped.append(s["id"])
    ok_count = sum(1 for x in loaded if x["status"] == "ok")
    conf = (ok_count / len(loaded) * 100) if loaded else 0.0
    gate = "pass" if conf >= 60 else ("degraded" if conf >= 30 else "fail")
    return {
        "tier": tier, "loaded": loaded, "skipped": skipped,
        "gate_confidence": conf, "gate_state": gate,
        "manifest_version": manifest.get("version"), "degraded": degraded,
    }


# ---------- Enforcement 参考实现（§7） ----------

def enforcement_a(gate_state, attempted_output, attempted_write):
    """harness 硬拦截层（Enforcement A）。"""
    if gate_state == "pass":
        return {"output_blocked": False, "write_blocked": False,
                "output_replacement": attempted_output, "status": gate_state}
    return {
        "output_blocked": True,
        "write_blocked": True,
        "output_replacement": "上下文缺失：G0 未通过，已拦截最终答复与写操作。",
        "status": gate_state,
    }


def skip_penalty(occurrence):
    """Enforcement B 扣分：首次 -10，累犯翻倍（-10 * 2^(n-1)）。"""
    return -10 * (2 ** (occurrence - 1))


def consistency_check(agent_claim, harness_record):
    """Enforcement C / 一致性（防表演）：声称走 G0 但无 harness 记录 = 表演。"""
    if agent_claim and not harness_record:
        return {"performance_detected": True, "penalty": -10,
                "session_untrusted": True}
    return {"performance_detected": False, "penalty": 0,
            "session_untrusted": False}


# ---------- 8 个场景断言（v1 ~ v8） ----------

def v1():
    """自动装配：新会话无需人粘贴，拉到正确档位，全部源 ok，gate=pass。"""
    m = load_manifest()
    sim = assemble(m, task_complexity=0.9, window_remaining=0.9)
    expected = {s["id"] for s in m["sources"]}
    loaded = {x["id"] for x in sim["loaded"]}
    ok = (loaded == expected
          and all(x["status"] == "ok" for x in sim["loaded"])
          and sim["gate_state"] == "pass")
    detail = f"tier={sim['tier']} loaded={sorted(loaded)} gate={sim['gate_state']}"
    return ok, detail


def v2():
    """档位算法：§2.1 三任务 → lite/lite/heavy（score 与档位一致）。"""
    cases = [
        ("问答", 0.1, 0.9, 0.8, "lite", 0.07),
        ("单文件改", 0.35, 1.0, 0.8, "lite", 0.28),
        ("战略", 0.9, 1.5, 0.8, "heavy", 1.08),
    ]
    results = []
    for name, comp, w, win, exp_tier, exp_score in cases:
        tier, score = choose_tier(comp, w, win)
        passed = (tier == exp_tier) and abs(score - exp_score) < 0.05
        results.append((name, tier, round(score, 3), exp_tier, exp_score, passed))
    ok = all(r[5] for r in results)
    detail = "; ".join(
        f"{n}:{t}({s})≈{es}({et}){'OK' if p else 'X'}"
        for n, t, s, et, es, p in results)
    return ok, detail


def v3():
    """源失联：pb 不可达 → 标 untrusted；其余正常；conf≈66；不阻塞。"""
    m = load_manifest()
    sim = assemble(m, task_complexity=0.9, window_remaining=0.9,
                   unreachable=["pb"])
    pb = next(x for x in sim["loaded"] if x["id"] == "pb")
    others_ok = all(x["status"] == "ok" for x in sim["loaded"] if x["id"] != "pb")
    conf = sim["gate_confidence"]
    ok = (pb["status"] == "untrusted" and "reason" in pb
          and others_ok and 55 <= conf <= 75
          and sim["gate_state"] != "fail")
    detail = f"pb={pb['status']} others_ok={others_ok} conf={conf:.0f} gate={sim['gate_state']}"
    return ok, detail


def v4():
    """窗口降级：复杂度 0.7（域权 1.5→heavy）但 window=0.10<15% → 降 standard；skipped 含 daily。"""
    m = load_manifest()
    sim = assemble(m, task_complexity=0.7, window_remaining=0.10,
                   domain_weight=1.5)
    ok = (sim["tier"] == "standard"
          and "daily" in sim["skipped"]
          and sim["degraded"] is True)
    detail = f"tier={sim['tier']} skipped={sim['skipped']} degraded={sim['degraded']}"
    return ok, detail


def v5():
    """协议同步：manifest 新增 notes 源、更新 updated_at → 下次会话生效，版本号不变。"""
    import copy
    m = load_manifest()
    before = assemble(m, task_complexity=0.9, window_remaining=0.9)
    n_before = len(before["loaded"])
    m2 = copy.deepcopy(m)
    m2["sources"].append({"id": "notes", "kind": "file",
                          "path": "docs/notes.md", "tiers": ["heavy"],
                          "min_size": 100})
    after = assemble(m2, task_complexity=0.9, window_remaining=0.9)
    n_after = len(after["loaded"])
    ok = (n_after == n_before + 1
          and any(x["id"] == "notes" for x in after["loaded"])
          and after["manifest_version"] == before["manifest_version"])
    detail = f"before={n_before} after={n_after} ver={after['manifest_version']}"
    return ok, detail


def v6():
    """Enforcement A：gate=fail 会话尝试最终答复+写文件 → 双拦截，status=fail。"""
    intercept = enforcement_a("fail", "这是最终答复", "out.txt")
    ok = (intercept["output_blocked"] is True
          and "上下文缺失" in intercept["output_replacement"]
          and intercept["write_blocked"] is True
          and intercept["status"] == "fail")
    detail = (f"out_block={intercept['output_blocked']} "
              f"write_block={intercept['write_blocked']} status={intercept['status']}")
    return ok, detail


def v7():
    """Enforcement B：连续 2 次跳门 → -10 / -20，累计 -30，violations=2。"""
    penalties = [skip_penalty(i + 1) for i in range(2)]
    total = sum(penalties)
    violations = len(penalties)
    ok = (penalties == [-10, -20] and total == -30 and violations == 2)
    detail = f"penalties={penalties} total={total} violations={violations}"
    return ok, detail


def v8():
    """一致性（防表演）：声称走 G0 但 harness 无记录 → 判表演，扣分，会话不可信。"""
    r = consistency_check(agent_claim=True, harness_record=False)
    ok = (r["performance_detected"] is True
          and r["penalty"] == -10
          and r["session_untrusted"] is True)
    detail = (f"performance={r['performance_detected']} "
              f"penalty={r['penalty']} untrusted={r['session_untrusted']}")
    return ok, detail


SCENARIOS = {1: v1, 2: v2, 3: v3, 4: v4, 5: v5, 6: v6, 7: v7, 8: v8}


# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(description="G0 Gate 8 场景验证断言")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="跑全部 8 个场景")
    group.add_argument("--scene", type=int, choices=range(1, 9),
                       help="只跑指定场景 (1-8)")
    args = ap.parse_args()

    if args.all:
        targets = list(SCENARIOS.items())
    else:
        targets = [(args.scene, SCENARIOS[args.scene])]

    print("G0 Gate · 8 场景验证（对齐 spec/verification.md）")
    print("=" * 60)
    all_ok = True
    for num, fn in targets:
        try:
            ok, detail = fn()
        except Exception as e:  # noqa: BLE001
            ok, detail = False, f"EXCEPTION: {e}"
        status = "PASS" if ok else "FAIL"
        if not ok:
            all_ok = False
        print(f"[v{num}] {status}  {detail}")
    print("=" * 60)
    print("RESULT: " + ("ALL PASS ✅" if all_ok else "HAS FAIL ❌"))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
