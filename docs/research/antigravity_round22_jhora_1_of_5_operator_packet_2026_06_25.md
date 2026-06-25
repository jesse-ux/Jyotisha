# Antigravity AI JHora 1/5 破冰操作外包包 (Round 22)

请立刻将此 Checklist 发送给拥有 Windows 电脑的人员，让他照做：

1. [ ] **电脑要求**: Windows 10/11，不支持 Mac。
2. [ ] **下载软件**: 访问 JHora 官网下载 8.0 免费版。
3. [ ] **输入参数**: Steve Jobs / 1955-02-24 / 19:15 / San Francisco, CA (122w25, 37n46)。
4. [ ] **设置 Ayanamsa**: Preferences -> Ayanamsa -> 选 `Chitra Paksha (Lahiri)`。
5. [ ] **设置 Node**: Preferences -> True/Mean Nodes -> 选 `True Node`。
6. [ ] **截图 1**: 切换到 Dasha 面板，截图第一行 (Vimshottari Dasha 起始时间)。
7. [ ] **截图 2**: 切换到 Strength 面板，截图七大行星 (Sun-Saturn) 的 Shadbala 六大分量矩阵。
8. [ ] **打码**: 用画图工具把截图上的其他个人星盘细节模糊掉。
9. [ ] **命名**: `external_template_steve_jobs_dasha_lahiri_evidence.png` 等。放入 `artifacts/`。
10. [ ] **填 JSON**: 打开 `references/oracle/dasha_shadbala_oracle_cases.json`。找到 Steve Jobs 那一条。
11. [ ] **改数据**: 把 `draft` 改为 `external_verified`。把刚才矩阵里的 Rupa 小数（绝对不能是几百的 Virupa），一个个敲进 JSON 对应的占位符。
12. [ ] **验证**: `python3 scripts/oracle_evidence_validator.py`。
13. [ ] **成功判据**: 终端输出 `valid_packets: 1`。
14. [ ] **失败重采**: 如果提示 `invalid_shadbala` 或 `sum_mismatch`，说明你填错了数字，重填。
15. [ ] **红线**: **绝对不要**把软件生成的整份 PDF 交进 Git！

**最小动作**：把这份文档截屏发给操作员。只有 1 跑通了，后面 2-5 才有着落。
