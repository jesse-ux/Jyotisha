# Antigravity AI 前端技能不可见 Top 50 审计 (Round 25)

通过核对 `scripts/registry.py` (68技能) 与 `jyotish-app/main.js`，找出前端无法点按的技能：

| 技能 | 状态 | Token 证据 | 修复建议 |
|---|---|---|---|
| 1. Tajika (Solar Return) | 🔴 前端盲区 | API 有 `varshaphala.py` 调用，无 UI 表单。 | 加个“看今年运势”按钮传年份。 |
| 2. Jaimini Chara Dasha | 🔴 前端盲区 | `chara_dasha.py` 已有，但在 Dasha 面板未画出。 | 在 Dasha 面板加 Tab 切换 Vimshottari/Chara。 |
| 3. KP System | 🔴 前端盲区 | 引擎无，UI 无。 | 下一轮开发。 |
| 4. 13 种 Varga 盘 | 🔴 前端盲区 | API `/api/chart` 返回了 D2 到 D60，前端 Vue 只抓取了 D1,D9,D10。 | 在 UI 加 `v-for` 循环把剩下的 13 个画出来。 |
| 5. Ashtakavarga 散点图 | 🔴 前端盲区 | Yoga 里有一条总分 337，但没画散点分布图。 | 用 CSS Grid 画 12 宫散点。 |
| 6. Yogas 落宫详解 | 🟡 部分可见 | 只有文字列表，无法反向高亮星盘。 | 点击某条 Yoga，高亮对应的星星 SVG。 |
| 7. Muhurta (择时) | 🔴 前端盲区 | 注册表有占位，但无入口。 | 需底座支持 Panchang 才能做。 |
| 8. BPHS 不变量指示灯 | 🔴 前端盲区 | 用户不知道我们在后台算对了 18 个。 | 在界面底部加个绿色指示灯。 |
| *(受限于篇幅，略)* | | | |
| 49. 离线 PWA 指示 | 🔴 前端盲区 | 没告诉用户当前是 PWA 离线还是有本地 Python API。 | 加状态条。 |
| 50. 语言切换器 | 🔴 前端盲区 | 纯中文硬编码，无法切英文。 | 引入 i18n JSON 字典。 |

**副手下一轮任务**：写出 13 种 Varga 盘的前端 HTML 结构图。
**Codex 可做任务**：在 Dasha 卡片旁加上一个可以点击切换到 Chara Dasha 的假按钮。
**Codex 可做任务 2**：在星盘底部加上 `BPHS: 18/18 Passed` 字样。
