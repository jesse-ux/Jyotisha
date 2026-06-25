# Antigravity AI Panchanga 商业级 UI 规格 (Round 27)

| 规格说明 | 设计要求 |
|---|---|
| 1. 入口位置 | 前端顶部导航栏加一个独立的 `Panchang & Muhurta` Tab。 |
| 2. 日历表格 | 默认展示本月的 `<table>`。 |
| 3. 表格格子信息 | 顶部大字：公历日期。右上小字：星期几。中部居中：Tithi 数字 (如 4/15)。底部：节假日标志 (若有)。 |
| 4. 每日详情展开 | 点击某个格子，弹出一个 Modal 或侧边栏，显示当天的 5 大要素 (Tithi, Vara, Nakshatra, Yoga, Karana) 及起止时间。 |
| 5. 凶时标红 (Rahu Kala) | 每日详情里，把 Rahu Kala, Yamaganda, Gulika 用红色高亮标出具体时间段。 |
| 6. 活动筛选器 | 顶部有一个 `<select>` (如 `Marriage`, `Business`, `Travel`)。选完后，日历格子里的吉日打绿勾，凶日打红叉。 |
| 7. 经纬度感知 | 提供一个基于 `navigator.geolocation` 的按钮，自动获取当地经纬度发给后端。默认用新德里。 |
| 8. 导出 ICS 入口 | 右上角放一个 `Export to Apple/Google Calendar` 按钮。 |
| 9. Choghadiya 视图 | 详情页加一个 Tab 显示当天的昼夜 Choghadiya 表格（红绿灯色块表示吉凶）。 |
| 10. 移动端自适应 | 月历在手机上太挤的话，变成一个纵向无限滚动的 List，每天占一张卡片。 |
| 11. Codex 任务 1 | 🟢 Codex可做 | 在 `jyotish-app/main.js` 新开辟一片渲染月历的 DOM 区域。 |
| 12. Codex 任务 2 | 🟢 Codex可做 | 去调用已有的 `/api/panchanga_range` 获取三十天数据并拼装 `<table>`。 |
| 13. Codex 任务 3 | 🟢 Codex可做 | 把 Rahu Kala 的红条用 CSS 画出来。 |
| 14. 副手下轮 1 | 🟢 副手可做 | 为那个 `<select>` 提供精确的梵文/英文对照活动词表。 |
| 15. 副手下轮 2 | 🟢 副手可做 | 撰写 ICS 生成的测试用例。 |
| 16. 需要人工 | 🔴 否 | |
| 17. API 准备情况 | 后端全部就绪。 |
| 18. CSS 框架 | 使用现成的 Tailwind 实用类即可。 |
| 19. 没有借口 | 既然算法早写好了，不把它展示出来简直是犯罪。 |
| 20. 竞品情况 | 竞品靠这个模块就能每天获取几万 DAU。 |
| 21. Vrata (斋戒日) | 目前可以先不管，之后补充。 |
| 22. 时间格式 | 必须使用本地时区的 hh:mm AM/PM 格式渲染。 |
| 23. Ayanamsa | 也要受全局 Ayanamsa 配置控制。 |
| 24. Sunrise | 日历的起止计算必须严格以当地日出为界，而不是午夜 0 点。 |
| 25. 总结 | 这是让用户每天都会打开 App 的核心法宝。 |
