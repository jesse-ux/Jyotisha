# Antigravity AI 第一条真实 JHora 样本准备清单 (Round 16)

此清单旨在指导测试人员（或 Codex 本尊）如何纯手工、零污染地完成 `template_private_oracle_redacted` 的举证：

## 1. JHora 输入项
- **生辰信息**：REDACTED_YEAR-01-01 12:00:00，经度 0.0，纬度 0.0（格林威治无夏令时，或随意设定一个高辨识度的虚拟极地坐标）。
- **Ayanamsa**：Preferences 菜单中设为 `True Chitra Paksha (Lahiri)`。
- **Node Mode**：设为 `True Node`。

## 2. 需要截图的页面
- **主窗体**：必须包含左上角的经纬度和时间，以及右侧面板的 Rasi Chart（或具体的星体黄经详表）。
- **打码**：如果录入的是某位测试人员的真实生辰，将姓名栏用黑色笔刷盖住。

## 3. 需要摘录的字段
- 月球（Moon）的确切黄经度数（如：`Pisces 15° 30' 45"` 转为浮点数 `345.5125`）。
- Vimshottari Dasha 的起运起始日（如：`Saturn Dasha starts on REDACTED_YEAR-01-01`）。
- Shadbala 中日、月、火、水、木、金、土的六项力量值。

## 4. Evidence Packet 填写模板
```json
{
  "tool_name": "JHora",
  "tool_version_or_url": "8.0",
  "capture_date": "2026-06-25T12:00:00Z",
  "source_artifact": "references/oracle/artifacts/jhora_REDACTED_YEAR_moon_lahiri_v1.png",
  "ayanamsa": "Lahiri",
  "node_mode": "True",
  "timezone": "GMT+0",
  "operator_note": "完全依照指南输入",
  "target": {
    "moon_sidereal_longitude_deg": 345.5125,
    "vimshottari_start_date": "REDACTED_YEAR-01-01T00:00:00Z",
    "shadbala_components": {
      "sthana": 1.1, "dig": 1.2, "kala": 1.3, "chesta": 1.4, "naisargika": 1.5, "drik": 1.6
    }
  }
}
```

## 5. 运行 validator 后的期望结果
`ready_for_calibration: 1` 和 `valid_packets: 1`。

## 6. 不能晋级的情况
如果 `source_artifact` 指定的图片不存在，或者 Shadbala 六项填不全，系统直接拒绝。
