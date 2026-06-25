# Antigravity AI Playwright 合盘 E2E 最小可执行计划 (Round 23)

建议编写以下核心 E2E 测试脚本以防御退化：

1. `goto('/synastry')` - 校验能正常载入。
2. `fill('#boy-moon-degree', '0')` - 男方填 0。
3. `fill('#girl-moon-degree', '10')` - 女方填 10。
4. `click('#btn-calculate-match')` - 点击计算按钮。
5. `waitForSelector('#match-results-table')` - 校验表格成功挂载。
6. `assert.textContains('#total-score', '/ 36')` - 校验总分文本是否包含满分格式。
7. `assert.elementCount('.kuta-row', 8)` - 校验必须有 8 行子评分。
8. `fill('#boy-moon-degree', '999')` - 测试超限输入。
9. `click('#btn-calculate-match')` - 再次点击计算。
10. `assert.isVisible('#error-toast')` - 断言提示框弹出“度数不合法”。
11. `goto('/trust-center')` - 跳转到 Trust Center。
12. `assert.textContains('.ashtakoot-progress', '0 / 5')` - 必须确认合婚 Oracle 进度暴露给了普通用户。
