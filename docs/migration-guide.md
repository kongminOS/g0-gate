# 从 v1.0（MIT）迁移到 v2.0（BSL 1.1）

> **v1.0 已过时声明**：本仓库早期版本（`docs/SPEC.md`，MIT 许可）已不再维护。
> 自 2026-08-13 起，G0 工程规格由 **v2.0（BSL 1.1）** 独占承载。使用 v1.0 文本的集成方将错过：
> 档位自动选择算法、manifest 协议 v2、自检评分公式、Wire Protocol 契约、验证方法学。

## 为什么迁移

| 项 | v1.0（MIT，已过时） | v2.0（BSL 1.1，现行） |
|---|---|---|
| 档位选择 | 人工判断 | 算法自动（§2.1） |
| manifest | 无版本概念 | 协议 v2 + 版本协商（§3.1） |
| 自检 | 原则描述 | 评分公式 + 阈值表（§4.1） |
| 集成 | 清单 | 完整 Wire Protocol 契约 |
| 验证 | 勾选清单 | 8 场景自动化断言 |
| 许可 | MIT | BSL 1.1（商用需授权） |

## 迁移步骤（集成方）

1. 拉取本仓库 `spec/G0-gate-spec-v2.md` + `spec/wire-protocol.md` + `spec/verification.md`
2. manifest 升级到 v2 schema（`examples/g0_registry.example.json` 为参考）
3. 接入 `/gate/init` + `/gate/run` + `/gate/status` 三端点（带 `Accept-Version: 2`）
4. 跑 `python examples/verify_gate.py --all` 确认 8 场景全 PASS
5. 商用前联系授权（LICENSE 条款）

## 兼容性

- v1.0 的 G1-G4 流程纪律不受影响（G1-G4 仍在 agent-gates 仓库，MIT 可自由使用）。
- G0 v2 协议向后兼容 v1 概念（分档/自检/路由），但 manifest schema 与端点契约不兼容——需按上表迁移。
