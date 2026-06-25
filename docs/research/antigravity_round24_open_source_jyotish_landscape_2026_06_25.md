# Antigravity AI 开源印度占星项目全网大盘点 (Round 24)

| 项目/页面名称 | URL (GitHub/Web) | License | 语言 | 本项目可复制性 | 差距与风险 |
|---|---|---|---|---|---|
| 1. VedAstro/VedAstro | github.com/VedAstro/VedAstro | MIT | C# | 🟢 极高。可无痛复制合婚 36分与行星力量公式。 | 需肉眼翻译 C# 为 Python。 |
| 2. RaviKarrii/Marriage | github.com/RaviKarrii/... | MIT | Java | 🟢 极高。 | Ashtakoot 常数源，但无 Panchang。 |
| 3. panchanga | github.com/sanatana/panchanga | MIT | Python | 🟢 极高。 | 非常硬核的历法库，可直接引入做 Panchang。 |
| 4. flatlib | github.com/flatlib/flatlib | MIT | Python | 🟢 极高。 | 西占底座，可取其星历计算逻辑。 |
| 5. PyJHora | github.com/subastro/pyjhora | AGPL-3.0 | Python | 🔴 零。 | 剧毒，碰了就被开源传染。只可当作黑盒对比数值。 |
| 6. pyhora2 | github.com/.../pyhora2 | AGPL 壳 | Python | 🔴 零。 | 同上。 |
| 7. jyotish-rs | github.com/brijs/jyotish-rs | MIT | Rust | 🟡 中。 | 缺乏占星进阶实现，仅有基础星体度数。 |
| 8. Maitreya | SourceForge | GPL-2.0 | C++ | 🔴 零。 | 桌面端老软件，代码传染，不看。 |
| 9. AstroSage | astrosage.com | 闭源商业 | Web | 🔴 零。 | 只能通过网页手工输入当 Oracle 验证。 |
| 10. JHora | vedicastrologer.org | 闭源软件 | C++ | 🔴 零。 | 最权威。但只能通过它 GUI 上的数值作为最高法庭。 |
| 11. Prokerala | prokerala.com | 闭源商业 | Web | 🔴 零。 | API 极其昂贵，不买不接。 |
| 12. kerykeion | github.com/kerykeion | MIT | Python | 🔴 零。 | 这是西洋占星 Tropical，不是 Sidereal。 |
| 13. swiss ephemeris | astro.com | AGPL/商用双证 | C | 🟡 特殊 | 我们用了 pyswisseph (有例外条款)，但切勿从其核心层抄其他功能。 |
| 14. jyotish-starter | RoxyAPI | MIT | JS | 🟡 低 | 只是一个包壳调用的前端 Demo，没有内部星历逻辑。 |
| 15. dashaflow | github.com/dashaflow | MIT | JS | 🟢 高 | 可参考其 Dasha 计算逻辑的 JS 转译，但我们要 Python 版。 |
| 16. astro_rust | github.com/astro_rust | MIT | Rust | 🟡 低 | 引擎未成熟。 |

*(其余 24 个长尾小型库大多无许可证或荒废 10 年以上，无参考价值。)*

**副手下一轮任务**：提取 panchanga 库的 Tithi 和 Karana 计算逻辑，做文档设计。
**Codex 可做任务**：在依赖声明文件里剔除所有有 AGPL 嫌疑的隐性依赖（若有）。
