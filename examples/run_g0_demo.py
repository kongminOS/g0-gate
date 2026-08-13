#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""G0 Gate · 30 秒模拟演示（v2 协议）

无运行时依赖，纯标准库。演示 G0 的核心流程：
  档位自动选择 → manifest 加载 → 自检评分 → gate 状态机

用法:
  python run_g0_demo.py            # 演示一次自动装配
  python run_g0_demo.py --scene 2  # 只演示档位算法（场景 2）
  python verify_gate.py --all      # 跑全部 8 个验证场景

License: BSL 1.1 (商用需授权) · (c) 2026 Wang Deyi (DeyiAI / Kongmin)
"""
import argparse
import json
import sys
import time


# ---------- 档位自动选择算法（spec-v2 §2.1） ----------

def choose_tier(task_complexity: float, domain_weight: float,
                window_remaining: float) -> tuple[str, float]:
    """返回 (tier, score)。公式见 spec-v2 §2.1。"""
    window_factor = max(0.2, min(1.0, window_remaining))
    score = task_complexity * domain_weight * window_factor
    if score < 0.30:
        tier = "lite"
    elif score < 0.65:
        tier = "standard"
    else:
        tier = "heavy"
    return tier, round(score, 3)


# ---------- 自检评分（spec-v2 §4.1） ----------

def freshness(age_hours: float, recency_hours: float) -> float:
    if age_hours <= recency_hours:
        return 1.0
    if age_hours <= 5 * recency_hours:
        return 1.0 - (age_hours - recency_hours) / (4 * recency_hours)
    return 0.0


def source_score(age_hours: float, recency_hours: float,
                 connected: bool, size: int, min_size: int) -> float:
    return freshness(age_hours, recency_hours) * (1.0 if connected else 0.0) * (1.0 if size >= min_size else 0.0)


# ---------- 演示 ----------

def demo_scene2():
    """场景 2：档位自动选择"""
    print("== 场景 2：档位自动选择（window_remaining=0.8）==")
    cases = [
        ("问答", 0.1, 0.9),
        ("单文件改", 0.4, 1.0),
        ("跨模块重构", 0.7, 1.0),
        ("战略规划", 0.9, 1.5),
    ]
    for name, comp, w in cases:
        tier, score = choose_tier(comp, w, 0.8)
        print(f"  {name:8s} complexity={comp} weight={w} -> score={score:.3f} tier={tier}")


def demo_full():
    """完整流程演示：自动装配 + 自检 + gate 状态"""
    print("G0 Gate v2 · 30 秒演示")
    print("=" * 50)

    # 1. 档位选择
    tier, score = choose_tier(0.6, 1.0, 0.75)
    print(f"[1] 档位选择: complexity=0.6 weight=1.0 window=0.75 -> {tier} (score={score})")

    # 2. manifest 加载（示例源）
    manifest = json.load(open("examples/g0_registry.example.json", encoding="utf-8"))
    print(f"[2] manifest v{manifest['version']} 加载: {len(manifest['sources'])} 个源")

    # 3. 自检评分（模拟：passport 新鲜、daily 过期、pb 不可达）
    sources = [
        ("passport", 2.0, 72, True, 2000, 100),
        ("daily", 200.0, 72, True, 500, 100),
        ("pb", 0.5, 24, False, 0, 100),
    ]
    scores = []
    for name, age, rec, conn, size, minsz in sources:
        s = source_score(age, rec, conn, size, minsz)
        scores.append(s)
        status = "ok" if s >= 0.6 else ("warn" if s > 0 else "untrusted")
        print(f"  - {name:10s} score={s:.2f} status={status}")

    # 4. gate 状态机
    conf = sum(scores) / len(scores) * 100
    gate = "pass" if conf >= 60 else ("degraded" if conf >= 30 else "fail")
    print(f"[4] gate_confidence={conf:.0f} -> gate_state={gate}")
    if gate == "fail":
        print("    > Enforcement A: 禁止最终答复 + 禁止写操作")
    print("=" * 50)
    print("30 秒演示完成。完整协议见 spec/G0-gate-spec-v2.md")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", type=int, choices=[2], help="只演示指定场景")
    args = ap.parse_args()
    if args.scene == 2:
        demo_scene2()
    else:
        demo_full()


if __name__ == "__main__":
    main()
