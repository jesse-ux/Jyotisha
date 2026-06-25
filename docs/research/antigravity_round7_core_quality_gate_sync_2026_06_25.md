# Antigravity AI quick/release 质量门同步复核 (Round 7)

## 复核步骤与结果

我们审计了核心打包部署防御线 `scripts/run_quality_gate.py`，确认上游 Codex 已经修复了 Round 5 中发现的遗漏问题。

*   **`CORE_PYTEST_TARGETS`**: 代码中已经包含了 `tests/test_oracle_collection_queue.py` 与 `tests/test_oracle_evidence_validator.py`。
*   **`EXTRA_COMPILE_TARGETS`**: 已包含了 `ROOT / "scripts" / "oracle_collection_queue.py"` 和 `ROOT / "scripts" / "oracle_evidence_validator.py"`，确保其进入字节码编译检查。
*   **`RELEASE_CRITICAL_UNTRACKED_PATHS`**: 防患于未然，四个文件（两个业务逻辑，两个测试逻辑）都被纳入了文件路径的严格监控。
*   **质量门配置文件执行逻辑**: 我们检查了在 `--profile release` 或标准 profile 且 `--skip-oracle-audit=False` 的条件下，部署脚本能够正确执行 `run_oracle_collection_queue_and_validator()`。不仅如此，测试套件 `test_frontend_productization.py` 中的 `test_dasha_reference_audit_is_documented_and_gated` 现已完全通过，证实 `README.md` 与脚本均已记录闭环指令。

## Bug 跟踪表

| 严重程度 | 文件路径 | 行号 | 现象 | 复现步骤 | 修复建议 |
|---|---|---:|---|---|---|
| **P0/P1/P2** | `scripts/run_quality_gate.py` | N/A | 本次复检各项配置完善，`quick` 模式下尽管跳过耗时脚本但通过全量 `pytest` 实现了校验覆盖；`release` 模式下更是全线强校验。无任何质量门脱管漏跑现象。 | 运行 `python3 scripts/run_quality_gate.py --profile quick` | **无需修复**。Codex 对质量门的同步加固已经彻底完成。 |
