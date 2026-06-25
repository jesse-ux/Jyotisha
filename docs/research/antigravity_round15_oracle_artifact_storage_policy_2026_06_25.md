# Antigravity AI 外部截图工件与隐私存档规范 (Round 15)

## 创建 `references/oracle/artifacts/`
**必须创建**。为防止图片污染根目录并降低代码仓库杂乱度，所有的真值证明图像必须被统一归拢至 `references/oracle/artifacts/` 路径下，并配套一个 `README.md` 说明。

## 截图命名规则
为了便于审查，截图必须含有可溯源要素：
`<case_id>_<tool_name>_v<tool_version>_<date>.png`
例如：`template_steve_jobs_dasha_lahiri_JHora_v8.0_20260625.png`

## 隐私遮挡与红线
1. **必须遮挡**：如果该星盘非公开名人，而是由真实志愿者贡献，**必须完全打码截图中的全名、具体经纬度（若非大城市）、医院等敏感信息**。
2. **不能入库**：带有明确个人全名、联络方式、非匿名化生辰信息的原件（如个人 PDF 报告、带有抬头指认的 JHora 界面等），在未打码前绝对不可进入 `.git` 追踪。

## Evidence Packet 引用方式
在 JSON Packet 的 `source_artifact` 字段，一律采用相对于仓库根目录的路径进行引用：
`"source_artifact": "references/oracle/artifacts/template_steve_jobs_dasha_lahiri_JHora_v8.0_20260625.png"`
验证器读取时将自动定位到该位置核实文件是否存在。
