# Tajika Einstein 1905 Field Copy Template

目标 packet:
`references/oracle/artifacts/pending_packets/external_template_einstein_varshaphala_1905_lahiri.json`

已完成样板:
`references/oracle/artifacts/pending_packets/external_template_steve_jobs_varshaphala_1984_lahiri_pyjhora_20260627.json`

用途:
- 给你或副手直接照抄字段结构
- 只替换 Einstein 1905 对应的外部真值
- 尽量不思考格式, 只做复制和填空

---

## 1. 可直接照抄的整体填写顺序

1. 先复制 Steve Jobs packet 的 `metadata` 写法
2. 再填 Einstein 1905 的外部年盘真值
3. 最后把 `status` 改成 `external_verified`

---

## 2. 逐字段复制模板

把下面整段当作填空卡使用:

```json
{
  "status": "external_verified",
  "metadata": {
    "tool_name": "<JHora or PyJHora>",
    "tool_version_or_url": "<version string or citation>",
    "capture_date": "<YYYY-MM-DD>",
    "source_artifact": "references/oracle/artifacts/<artifact-file>",
    "ayanamsa": "lahiri",
    "node_mode": "mean",
    "timezone": "UTC+00:53",
    "annual_system": "Varshaphala/Tajika",
    "target_year": 1905,
    "operator_note": "<short note: source, solar-return convention, timezone/DST handling, workaround if any>"
  },
  "target_placeholders": {
    "target.solar_return_datetime": "<copy from annual chart header>",
    "target.varsha_lagna_deg": <absolute zodiac degree>,
    "target.muntha_sign": "<sign name>",
    "target.year_lord": "<planet name>",
    "target.mudda_dasha_first_lord": "<planet name>",
    "target.sahams.punya_saham": <absolute zodiac degree>,
    "target.sahams.rajya_saham": <absolute zodiac degree>,
    "target.sahams.vivah_saham": <absolute zodiac degree>,
    "target.tajika_yogas": "<copy exact yoga block structure from source>",
    "target.source_artifact": "references/oracle/artifacts/<artifact-file>"
  }
}
```

---

## 3. 哪些字段直接照 Steve Jobs 抄格式

这些字段只需要抄格式, 不需要重新想写法:

- `status`
- `metadata.tool_name`
- `metadata.tool_version_or_url`
- `metadata.capture_date`
- `metadata.source_artifact`
- `metadata.operator_note`
- `metadata.ayanamsa`
- `metadata.annual_system`
- `metadata.target_year`
- `target.source_artifact`

建议直接套这个写法:

```json
"metadata": {
  "tool_name": "PyJHora",
  "tool_version_or_url": "PyJHora <version> isolated /tmp black-box run",
  "capture_date": "<YYYY-MM-DD>",
  "source_artifact": "references/oracle/artifacts/<artifact-file>",
  "ayanamsa": "lahiri",
  "node_mode": "mean",
  "timezone": "UTC+00:53",
  "annual_system": "Varshaphala/Tajika",
  "target_year": 1905,
  "operator_note": "Black-box annual output from <tool/source>. External evidence only; local annual engine output not used. Solar-return convention: <fill>. Timezone/DST handling: <fill>. <optional workaround note>"
}
```

---

## 4. 哪些字段必须从外部源逐个抄

这些值禁止本地推断:

- `target.solar_return_datetime`
- `target.varsha_lagna_deg`
- `target.muntha_sign`
- `target.year_lord`
- `target.mudda_dasha_first_lord`
- `target.sahams.punya_saham`
- `target.sahams.rajya_saham`
- `target.sahams.vivah_saham`
- `target.tajika_yogas`

---

## 5. 逐字段抄写提示

### A. metadata

```json
"tool_name": "PyJHora"
```
- 填你实际使用的工具名

```json
"tool_version_or_url": "PyJHora <version> isolated /tmp black-box run"
```
- 直接抄 Steve Jobs 文风
- 如果是 JHora, 改成 JHora 对应版本说明

```json
"capture_date": "2026-06-29"
```
- 填今天真实采集日期

```json
"source_artifact": "references/oracle/artifacts/<artifact-file>"
```
- 填你保存的 stdout / 截图 / 引文文件

```json
"operator_note": "Black-box annual output from <tool/source>. External evidence only; local annual engine output not used. Solar-return convention: <fill>. Timezone/DST handling: <fill>. <optional workaround note>"
```
- 这句可以直接复制
- 只替换 `<fill>`

### B. annual header

```json
"target.solar_return_datetime": "<copy exact timestamp with offset>"
```
- 从年盘抬头直接抄

```json
"target.varsha_lagna_deg": <number>
```
- 抄绝对黄经
- 如果外部只给星座+度分秒, 先换算后再填

### C. annual rulership

```json
"target.muntha_sign": "<sign>"
"target.year_lord": "<planet>"
"target.mudda_dasha_first_lord": "<planet>"
```

### D. sahams

```json
"target.sahams.punya_saham": <number>
"target.sahams.rajya_saham": <number>
"target.sahams.vivah_saham": <number>
```
- 统一填绝对黄经

### E. tajika_yogas

```json
"target.tajika_yogas": {
  "<copy exact source structure here>": null
}
```
- 最省事方法:
  1. 直接照外部源标签抄
  2. 如果是 PyJHora stdout, 尽量保持与 Steve Jobs 样板同结构
  3. 不要翻译成我们本地解释层术语

### F. artifact echo

```json
"target.source_artifact": "references/oracle/artifacts/<artifact-file>"
```
- 与 `metadata.source_artifact` 保持一致

---

## 6. 最短实操法

最快方法不是从空模板填, 而是:

1. 打开 Steve Jobs packet
2. 复制它的 `metadata` 和 `target_placeholders` 结构
3. 仅替换 Einstein 1905 对应值
4. 保存到 Einstein packet

---

## 7. 填完后直接执行

```bash
python3 scripts/tajika_annual_oracle_queue.py \
  --oracle-file references/oracle/tajika_annual_oracle_cases.json \
  --apply-packet references/oracle/artifacts/pending_packets/external_template_einstein_varshaphala_1905_lahiri.json \
  --format json
```

```bash
python3 scripts/tajika_annual_benchmark_dashboard.py \
  --oracle-file references/oracle/tajika_annual_oracle_cases.json \
  --format json
```
