# Antigravity AI 下一轮（Round 21）副手任务建议 (Round 20)

下一轮可继续指派给副手处理的 10 项繁重任务：

1. **VedAstro (MIT) Ashtakoot JSON 提取**：跑一趟 VedAstro C# 库，把里头的 Nakshatra Nadi/Gana 等映射表格式化为一个纯净的 `ashtakoot_constants.json` 文件供本地取用。
2. **Kuja Dosha 叠加消除法则**：调研 AstroSage 上的“当一方有火星煞，另一方也有时，双方煞气互相抵消”的规则边界，整理规则草案。
3. **Playwright E2E 安装测试**：在隔离环境跑一下 `npm init playwright@latest`，确保我们在 Node 20+ 环境的依赖支持，并给出安装命令清单。
4. **Shadbala 极限值阻拦测试草稿**：写一段 pytest 用例，专门测试传给 validator `"sthana": 1000` 会怎样，并补充 `> 20.0` 的警告设计。
5. **Ayanamsa 脱轨侦测**：调研如果 `pyswisseph` 返回的 Lahiri 和 KP 之间差值大于某个容差（比如 1.5 度）时的异常捕获机制。
6. **多语言 UI 词典（第二批）**：继续映射 Dasha 和 Yoga 等梵文到中文的专业名词。
7. **JHora 精度极限对标**：人工截取 1950 以前和 2050 以后两个极远年代的 JHora 行星落点，用于极限浮点验证。
8. **Ashtakoot `female` API Payload 规范**：设计 `/api/synastry` 接收两份星盘数据的嵌套 JSON 结构，输出 Schema。
9. **K.P. Horary (1-249) 切表提取**：从 `KP Astrology (MIT)` 中提取 1 到 249 的 Sublord 切片角度，做成 JSON。
10. **Tauri 桌面端应用图标设计**：准备一套 macOS 规范的 `.icns` 和 Windows `.ico` 的资源规格建议。

**落地建议**：这些费时费力的找常数、测边界、提 JSON 的活儿，全部让副手去干，千万别占用 Codex 主线的宝贵算力。
