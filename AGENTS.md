# Jyotish Skill Agent Constraints

本文件是当前项目给协作代理、自动化助手与派生工作流的硬约束补充。它不替代 `SKILL.md`，而是把最容易被偷懒、省略、或在多窗口工作时遗失的高严谨规则单独钉死。

## 1. High-Rigor Override

当用户明确要求以下任一项时，必须进入高严谨模式：

- 不要凭经验泛谈
- 必须拉满三大开源参照引擎能力
- 必须提交底层原始数据
- 必须验证过去案例
- 必须避免偷工减料

进入该模式后，以下规则全部强制执行：

1. 必须尝试交叉参照 `PyJHora`、`VedAstro`、`jyotishganit`，并保持许可证边界。
2. 必须优先调用本仓原生实现，不得只用轻量包装脚本代替主链代码。
3. 涉及 timing / event / outcome，不得只看 `Vimshottari`，至少需要 `Vimshottari + Narayana Dasha` 双轨交叉。
4. 必须按问题域强制调取相关分盘：
   - 事业：`D10 + A10`
   - 财富：`D2 / D11`
   - 婚恋：`D9 + UL`
5. 必须交付原始数据依据：度数、Dasha 边界、Shadbala / Ashtakavarga、Yoga 名称、Ayanamsa / Node mode、外部证据路径。

## 2. Functional Benefic/Malefic Hard Constraint

**强制调取 Functional Benefic / Malefic 判定（功能性吉凶星判定）。**

这条约束与 Dasha / 分盘 / 原始数据交付同级，不得省略。

执行要求：

1. 每次进入高严谨模式，必须显式判定当前 Lagna 下的 `functional benefics` 与 `functional malefics`。
2. 任何关于事业、财富、婚恋、健康、障碍、回报、应期的结论，都不得只依据自然吉凶星（natural benefic/malefic）下判断，必须叠加功能性吉凶星层。
3. 若某颗星在自然属性与功能属性之间冲突，必须在输出中说明冲突来源，并降低置信度或标记 `blocked`。
4. 若未调用功能性吉凶星判定，不得声称该次解读完成了高严谨模式。
5. Technique Audit Table 中必须出现 `Functional Benefic/Malefic` 一行，说明：
   - `Used / not used / blocked`
   - 关键功能吉星
   - 关键功能凶星
   - 对结论置信度的影响

## 3. Existing MEVG Invocation Hard Constraint

**强制执行既有 MEVG 规则，不得把它当成可选增强项。**

本节不是新增一套验证系统，而是把 `SKILL.md` 与
`references/mandatory-verification-gate-protocol.md` 中已经存在的 MEVG
外部验证门控提升为协作代理硬约束。

执行要求：

1. 对用户提出的 **所有星盘运势类问题**、**所有有关印度占星推运的问题**，包括命盘解读、事业、财富、婚恋、健康、流年、流月、应期、事件预测、出生时间校正辅助和技法可靠性判断，必须执行 MEVG。
2. MEVG 必须包含：
   - 全球 / 全网外部资料采集
   - 真实案例参考
   - 来源分级
   - 冲突仲裁
   - 未验证声明降级
3. 输出的 Technique Audit Table 必须出现以下两行：
   - `MEVG / Global Web Evidence`
   - `Real Case Calibration`
4. 若无法完成外部资料采集、无法找到真实案例、网络/工具不可用、或来源之间出现重大冲突，必须写成 `blocked` 或降级置信度，不得静默跳过。
5. 只有 **纯计算 / 纯代码 / 纯项目维护** 可以豁免 MEVG，例如运行测试、检查 Git 状态、修复代码、输出未解释的原始度数或 Dasha 边界。一旦开始解释“这代表什么运势”，豁免立即失效。

## 4. Honesty Boundary

以下情况必须明确写成 `blocked` 或降级置信度：

- 外部 oracle 尚未闭环
- 三大外部参照引擎中有一层无法合法或稳定调用
- 缺少分盘、Ayanamsa、Node mode 或出生精度
- 功能性吉凶星层未完成
- 双重大运或多系统结果发生实质冲突
- MEVG / Global Web Evidence 或 Real Case Calibration 未完成

禁止把内部一致性伪装成“已经全球顶级精度”。

## 5. Pre-Work Error Ledger Hard Constraint

为避免多窗口、多应用、多文件夹碎片导致重复误判，开工前 / 进行任何实质项目工作前必须读取：

- `docs/research/pre_work_error_ledger.md`

若任务涉及运行入口、镜像边界、外部 oracle、远端同步、适配器、测试验收或大规模资料治理，还必须读取：

- `docs/research/whole_machine_fragment_sweep_2026_07_05.md`
- `docs/research/whole_machine_fragment_sweep_round25_2026_06_25.md`

同时必须运行：

- `python3 scripts/pre_work_check.py --remote-timeout 8 --command-timeout 45`

该预检必须包含：

- `scripts/diagnose_external_engine_adapters.py --json`

执行要求：

1. 不得把 `.workbuddy` 镜像当作运行主仓。
2. 不得在 `git ls-remote` / fetch / push 等远端验证失败时声称云端已同步。
3. 不得在未查看当前 `git status --short --branch` 时覆盖或重置本地变更。
4. 新发现的重复错误、阻塞、碎片目录、远端验证失败，必须追加到错误台账或当轮 sweep 文档。
