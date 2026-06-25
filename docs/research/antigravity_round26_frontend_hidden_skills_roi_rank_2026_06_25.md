# Antigravity AI 前端隐藏高级技能 ROI 排序 (Round 26)

基于 Round 25，剔除掉目前已经在 `jyotish-app/main.js` 里能看到的东西（D1,D9,D10,Vimshottari,Shadbala,Yoga），按投入产出比重排其余隐藏技能：

| 排名 | 隐藏技能名称 | 为什么重要 (ROI分析) | UI 落地难度 |
|---|---|---|---|
| **1** | Panchanga / Muhurta | C 端用户黏性极强，每天看黄历。 | 难 (需造月历控件)。 |
| **2** | Chara Dasha (Jaimini) | 高级占星师的刚需，和 Vimshottari 互参。 | 易 (和现有运势树共用组件，加个 Tab)。 |
| **3** | D7 (子息盘) & D60 | 最常看的特殊分盘，看后代和前世。 | 极易 (现成的 SVG 生成器 `draw_d1_chart` 就能复用)。 |
| **4** | Tajika 年盘 (太阳返照) | 想看“今年运势”的用户必点。 | 中 (需在表单加个年份输入框，重新调接口)。 |
| **5** | Ashtakavarga 散点图 | Yoga 里的总分不够看，大师要看 12 宫分。 | 中 (需用 CSS Grid 拼个 12 格数字)。 |
| **6** | 剩余 11 种 Varga | 给极客查数用。 | 极易 (塞进 `More Vargas` 下拉框)。 |
| **7** | KP System (若有) | KP 是另一个大流派。 | 难 (完全不同的 UI 展示法)。 |
| 8. 语言切换 | | | |
| 9. AI 打分板 | | | |
| 10. 离线 PWA 指示器 | | | |
| 11. Codex 任务 1 | 🟢 Codex可做 | 在 Dasha 面板旁边加个 `Chara Dasha` 的按钮，把 API 返回的该数据灌进树形图。 |
| 12. Codex 任务 2 | 🟢 Codex可做 | 在 SVG 盘上方做个 `Select Varga` 的下拉框，默认 D1，选了 D7 就重绘 SVG。 |
| 13. Codex 任务 3 | 🟢 Codex可做 | 在表单底部加个按钮 `Calculate Solar Return`。 |
| 14. 副手下轮 1 | 🟢 副手继续做 | 去画这套“一键切换不同 Varga”的 Figma / Tailwind 伪代码草图。 |
| 15. 副手下轮 2 | 🟢 副手继续做 | 调研 Tajika 年盘在 AstroSage 里长什么样。 |
| 16. 需要人工 | 🔴 否 | |
| 17. 总结 1 | 我们底层算的东西太多，前端漏出来的太少。 |
| 18. 总结 2 | 复用现有的 SVG 画图器是解锁 Varga 的最快路径。 |
| 19. 总结 3 | 不做日历就是暴殄天物。 |
| 20. 总结 4 | 按 ROI 行事，先做 D7/D60，再做 Chara Dasha。 |
