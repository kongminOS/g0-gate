# G0 验证方法学 v2.0

> 8 个可复现验证场景：输入 → 预期输出 → 判定标准。
> 每个场景配套 `examples/verify_gate.py` 中的对应断言函数（`v1()` ~ `v8()`）。
> 本方法学是 **BSL 1.1** 资产的一部分；验证脚本随公开仓分发（examples/），可离线运行。

---

## 场景总览

| # | 场景 | 验证点 | 对应章节 |
|---|---|---|---|
| 1 | 自动装配 | 新会话无需人粘贴，拉到正确档位 | spec-v2 §3 |
| 2 | 档位算法 | score 计算与 tier 判定正确 | spec-v2 §2.1 |
| 3 | 源失联 | 单个源不可达 → 标不可信不阻塞 | spec-v2 §4 |
| 4 | 窗口降级 | 余量 < 15% → 降档并报告跳过项 | spec-v2 §2.4 |
| 5 | 协议同步 | 人改 manifest → 下次会话生效 | spec-v2 §3.1 |
| 6 | Enforcement A | gate 未 pass → 拦截最终输出+写操作 | spec-v2 §7.1 |
| 7 | Enforcement B | 跳门 -10 分，累犯翻倍，落入看板 | spec-v2 §7.2 |
| 8 | 一致性 | A 层生效是 C 层出声前置条件 | spec-v2 §7.3 |

## 场景 1：自动装配

**输入**：全新会话（无任何粘贴），项目绑定 `kongmin/backend`，registry 含 manifest v2。
**执行**：`G0.run()` → 断言返回 `tier` 与 `loaded[]`。
**预期**：loaded 包含 manifest 声明的全部源；`gate_state == "pass"`。
**判定**：通过 = loaded 源数 == manifest.sources 数 且 全部 status=="ok"。

## 场景 2：档位自动选择

**输入**：三个任务（问答 / 单文件改 / 战略），window_remaining=0.8。
**执行**：按 §2.1 算法计算 score 与 tier。
**预期**：
- 问答 → score≈0.07 → lite
- 单文件改 → score≈0.28 → lite（<0.30）
- 战略 → score≈1.08 → heavy（≥0.65）
**判定**：三档输出与预期一致，且 forced 覆盖时记录 `tier_policy=="forced"`。

## 场景 3：源失联

**输入**：manifest 声明 3 个源，其中 `pb` 端点不可达。
**执行**：G0.run()。
**预期**：pb 标 `untrusted`；其余 2 源正常加载；`gate_confidence` 按公式计算（2/3 源 ok → ~66）；不阻塞、不中断。
**判定**：通过 = 无异常中断 + pb 源 reason 明确 + confidence 在预期区间。

## 场景 4：窗口降级

**输入**：window_remaining=0.10（<15%），任务复杂度=0.7（应选 heavy）。
**执行**：G0.run()。
**预期**：实际档位降为 standard（heavy→standard）；`skipped[]` 含 heavy 专属源（daily 72h）；响应带降级说明。
**判定**：通过 = 降档正确 + skipped 列表与 heavy 专属源一致。

## 场景 5：协议同步

**输入**：manifest v2 里新增一个源（`notes`），更新 `updated_at`。
**执行**：再次 G0.run()（同一项目）。
**预期**：loaded 含新源；`manifest_version` 不变（2.0）。
**判定**：通过 = 新源出现且无需重启宿主。

## 场景 6：Enforcement A 硬拦截

**输入**：gate_state == "fail" 的会话，Agent 尝试输出最终答复 + 写文件。
**执行**：harness 拦截层。
**预期**：最终答复被替换为"上下文缺失"解释；写操作被拒绝；`/gate/status` 返回 fail。
**判定**：通过 = 输出与写操作双拦截（机器验证，非人工确认）。

## 场景 7：Enforcement B 扣分

**输入**：同一会话内连续 2 次跳门。
**执行**：B 层逐轮记录。
**预期**：第 1 次 -10，第 2 次 -20（累犯翻倍），累计 -30；`/gate/status.violations == 2`。
**判定**：通过 = 扣分公式正确 + 看板可见（KPI 台账落盘）。

## 场景 8：一致性（防表演）

**输入**：Agent 声称"已走 G0"但 harness 无 gate 记录。
**执行**：交叉核验 harness 日志 vs Agent 声明。
**预期**：A 层记录缺失 → 判定为"表演"→ 按 B 层扣分 + 标记会话不可信。
**判定**：通过 = 表演被识别且扣分，绝不允许"演了纪律而后台没拦"。

---

## 运行验证

```bash
python examples/verify_gate.py --all
# 输出: v1 PASS / v2 PASS / ... / v8 PASS  → 全 PASS = 通过
python examples/verify_gate.py --scene 6
# 单场景运行（Enforcement A）
```

## CI 集成建议

- gate 状态（pass/fail/degraded）进测试报告元数据。
- `verify_gate.py --all` 纳入 pre-push 钩子（Agent 仓库侧）。
