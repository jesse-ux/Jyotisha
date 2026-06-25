# Antigravity AI 普通用户校准透明度黑盒审计 (Round 9)

## 审计范围
我们在本次审计中针对 `README.md`、`SKILL.md` 以及 `jyotish-app/` 下的前端呈现逻辑，检索了 `ready_for_calibration`、`Dasha/Shadbala` 校准等关键字，重点评估当前对普通用户的透明度。

## 检查结果

1. **README 是否说明 `ready_for_calibration: 0`**：
   - **通过**。目前的 `README.md` 在“质量门与验证”板块确实写明了：“当前队列有 5 个 `template_only` 任务、`ready_for_calibration: 0`、`production_tuning_allowed: false`，说明只能继续采集外部黑盒目标值”。这在工程层面上是透明的。
2. **SKILL 是否避免过度宣称**：
   - **通过**。在 `SKILL.md` 以及前端内置的 `skill-map.js` 中存在声明：“相对强弱已展示，外部绝对值校准仍需标注边界”。AI 也没有被赋予“系统已完全精准”的越权提示。
3. **Web/App 首屏或 Trust Center 是否展示 calibration status**：
   - **不通过（存在隐患）**。检索发现 `jyotish-app/` 没有任何直接向 C 端普通用户渲染输出 `ready_for_calibration` 大盘数据的视图逻辑。这意味着不读 README 的“纯净小白”用户根本不知道系统后台正卡在外部数据收集中。
4. **AI Chat 安全边界**：
   - **部分通过**。在结构化输出时 AI 不会吹嘘，但在纯自由对话时，如果缺乏强制系统注入的 calibration status，大模型有幻觉吹嘘其排盘（尤其是人生起步大运日期）为全球绝对真理的风险。
5. **用户能否区分高可信与待校准区域**：
   - **较差**。基础的 D1/D9、Ashtakavarga 拥有 100% 测试覆盖和天文学精度；而 Dasha 年月日漂移和 Shadbala 边缘值目前为相对参考。产品界面在呈现这些报表时，并没有使用明确的 UI 徽章（如“精确级” vs “外部校准中”）进行隔离提示。

## 结论
工程上（文档与测试）的防腐做得极其优秀，但是这些警示尚未穿透至普通产品的用户界面上。普通用户面临被高深且无声的排盘数据误导的真实风险。
