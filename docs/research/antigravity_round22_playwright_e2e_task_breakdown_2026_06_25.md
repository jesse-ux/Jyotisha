# Antigravity AI Playwright E2E 伪代码任务拆解 (Round 22)

为了防止 Trust Center 和合盘因为重构崩塌，设计 20 条 Playwright 断言用例：

1. `test_nav_to_trust_center`：点击导航，断言 `#trust-center-page` 显示。
2. `test_dasha_card_render`：断言 `Dasha & Shadbala` 卡片存在。
3. `test_ashtakoot_card_render`：断言 `Ashtakoot` 卡片存在。
4. `test_dasha_progress_is_0`：断言红色的 `0 / 5` 进度条 DOM 存在。
5. `test_download_dasha_template`：点击下载，拦截并校验 Blob。
6. `test_upload_valid_dasha_json`：上传伪造的 1/5 成功数据，断言通过并刷新进度条。
7. `test_upload_invalid_dasha_json`：上传超额 Rupa 数字，断言红色的 `invalid_shadbala`。
8. `test_upload_sum_mismatch`：上传相加不对的数据，断言抛错。
9. `test_ashtakoot_progress_is_0`：断言合婚卡片初始进度也是 `0 / 5`。
10. `test_nav_to_synastry`：跳转合盘页面。
11. `test_synastry_form`：填写男女双方表单。
12. `test_synastry_submit`：点击匹配，断言转圈等待不超 2 秒。
13. `test_synastry_total_score`：断言表格里出现了总分。
14. `test_synastry_kuta_rows`：断言 Varna 到 Nadi 8 行全部呈现。
15. `test_synastry_kuja_warning`：如果是火星煞，断言出现了红色的🔥。
16. `test_synastry_missing_data`：空点击，断言 HTML5 Validation 或自定提示“缺月亮”。
17. `test_trust_center_mobile_stacking`：模拟宽度 375px，断言两个卡片处于上下层叠状态而非左右拥挤。
18. `test_privacy_mosaic_warning_visible`：断言上传框上方必须存在“打码提示”语。
19. `test_ai_prompt_shows_0_5`：点击大模型提示词拷贝按钮，剪贴板里包含“有效验证数: 0”。
20. `test_static_demo_blocks_upload`：如果是纯 PWA 静态模式，断言上传按钮变灰并提示连击。

**落地建议**：这些测试一旦全绿，我们的核心变现/信任功能将固若金汤。
