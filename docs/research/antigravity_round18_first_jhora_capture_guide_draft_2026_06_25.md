# Antigravity AI 第一条 JHora/PyJHora 真实样本公开教程草稿 (Round 18)

请直接复制以下内容发放给志愿者：

## 1. 案例选择
请优先使用公开人物（如 Steve Jobs）或我们的合成模板 `REDACTED_YEAR_moon_lahiri`，避免上传你真实的家人或个人星盘。

## 2. JHora 参数设置
- 顶部菜单：Preferences -> Related to Calculations -> Ayanamsa
- 确保选中 **Lahiri (Chitra Paksha)** （或者如果你选测 Raman/KP 模板，则对应切换）。
- 确保 Node 选用 True 或 Mean（请在截图内保留该设置）。

## 3. 时区与地点检查
出生地经纬度必须精确，尤其是 Timezone Offset。如果所在城市实行夏令时，请务必核对 JHora 自动推算的偏移是否正确。

## 4. 关键指标截图要求
请打开以下面板并分别截图（或者一屏包含）：
- **Moon sidereal longitude**: D1 盘中 Moon 的精确度数（精确到秒）。
- **Vimshottari 起点**: Dasha 面板中，起运的第一个 Mahadasha 的起始日期。
- **Shadbala 六分量表**: Strengths -> Shadbala 面板。请展开看到 `Sthana`, `Dig`, `Kala`, `Chesta`, `Naisargika`, `Drik`。

## 5. 打码与脱敏（非常重要）
- **必须打码**：截图中如果带入了真实姓名、具体城市名称、你的系统文件路径、浏览器标签页其它账号信息，请用马赛克涂抹。
- **不得提交**：不可提交整个 PDF 报告！不可提交浏览器 Scratch！

## 6. 保存路径规范
将打码好的截图保存为 PNG，例如 `jhora_REDACTED_YEAR_moon_lahiri_v1.png`。
若通过 PR 提交，请将其放入 `references/oracle/artifacts/` 目录。

## 7. 填写 packet 元数据
在 `dasha_shadbala_oracle_cases.json` 你的 task 下：
- `source_artifact`: 填入 `references/oracle/artifacts/jhora_REDACTED_YEAR_moon_lahiri_v1.png`
- `tool_name`: `JHora`
- `tool_version_or_url`: `8.0`
- 填好 `target` 里的各个空缺值。

## 8. Validator 本地验证与晋级
运行：`python3 scripts/oracle_evidence_validator.py`
若没出现红色的 `missing_shadbala_component` 或 `placeholder_unfilled`，则表示格式合格。
此时把 `"status": "draft"` 改为 `"status": "external_verified"`。

## 9. 拒收与重采红线
- 截图完全模糊看不清数字。
- 漏掉了 Shadbala 的 `kala` 等细分项。
- 携带了明显的个人真名、照片。
