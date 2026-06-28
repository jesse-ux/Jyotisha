# Git Execution Card - Finance Yogi Boundary Only

日期：2026-06-28
目标：只提交 finance adjudicator 的外部真值 Yogi 边界修复，不混入其他工作树噪音。

## 目标文件

1. `mcp_server.py`
2. `tests/test_mcp_strict_workflow_finance.py`
3. `docs/research/wealth_adjudicator_fifth_pass_external_truth_boundary_2026_06_28.md`

## 执行顺序

### Step 1 - 确认暂存范围

```bash
git -C /Users/wuyongnaren/Documents/印度占星 reset
git -C /Users/wuyongnaren/Documents/印度占星 add -- \
  mcp_server.py \
  tests/test_mcp_strict_workflow_finance.py \
  docs/research/wealth_adjudicator_fifth_pass_external_truth_boundary_2026_06_28.md
```

### Step 2 - 检查暂存区

```bash
git -C /Users/wuyongnaren/Documents/印度占星 diff --cached --name-only
git -C /Users/wuyongnaren/Documents/印度占星 diff --cached --stat
git -C /Users/wuyongnaren/Documents/印度占星 diff --cached --check
```

预期：只看到上述 3 个文件。

### Step 3 - 回归验证

```bash
python3 -m pytest /Users/wuyongnaren/Documents/印度占星/tests/test_mcp_strict_workflow_finance.py -q
```

预期：

- `12 passed`

### Step 4 - 独立提交

建议提交语义：

```bash
git -C /Users/wuyongnaren/Documents/印度占星 commit -m "Enforce external-truth Yogi finance boundary"
```

### Step 5 - 推送当前分支

```bash
git -C /Users/wuyongnaren/Documents/印度占星 push origin codex/release-hygiene-ci
```

## 禁止事项

这次提交不要混入：

- `docs/research/public_benchmark_dashboard_latest.md`
- `references/oracle/artifacts/pyjhora_oracle_artifact_manifest.json`
- 任意 `patch_*.py`
- 任意本地试验脚本
- 未整理的 sidecar 研究包

## 一句话判断

**这是一张“只交 finance Yogi 真实性边界，不交别的”的推送卡。**
