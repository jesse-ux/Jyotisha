# Antigravity / VedAstro 复核记录（2026-06-25）

## 范围

本记录复核 Antigravity 中临时安装 `vedastro` Python SDK 后得到的外部对照结果。样本使用用户提供的 PDF 参考盘：

- PDF：`/Users/wuyongnaren/Downloads/印度占星1.pdf`
- 出生资料：`REDACTED_DATE 14:45:20`，`UTC+8`，纬度 `36.466667`，经度 `114.2`
- 当前本地项目路径：`/Users/wuyongnaren/Documents/印度占星`

本记录只用于计算边界和外部 oracle 对照，不代表人生事件预测准确率。

## 对标结论

### VedAstro

- 参考：<https://github.com/VedAstro/VedAstro>
- 结论：Antigravity 报告中的 VedAstro D1 与 D9 结果可作为外部正向信号。当前项目在本样本上与 VedAstro 的 D1 落座、D9 落座保持一致，说明基础黄经、星座映射和 Navamsa 映射没有暴露结构性偏差。
- 限制：Antigravity 报告没有取得 VedAstro 的 Shadbala 与 Vimshottari Dasha 返回值；相关差异不能据此归因给当前项目。
- 产品判断：VedAstro 适合继续作为 MIT 产品/API/skill/MCP 生态对标和低频 oracle，不适合作为当前网页/app 高频实时后端的直接替换，因为外部 API 存在频控、超时和网络依赖。

### PyJHora / JHora 类参照

- 参考：<https://github.com/naturalstupid/PyJHora>
- 结论：PyJHora 更适合继续做高阶 Jyotish 行为 benchmark，尤其是 Dasha 口径、Shadbala 传统权重、Panchanga 与复杂分盘。
- 许可证边界：PyJHora 为 AGPL 生态参照，不能直接复制实现进当前项目；只能做独立 benchmark、结果对照和重新实现的验收 oracle。

## 已接受的外部反馈

1. D1/D9 与 VedAstro 对齐结果有效，已纳入信心判断：当前基础排盘和分盘映射没有发现结构性错误。
2. VedAstro 不宜直接作为生产主后端的判断有效：当前仍保留 Swiss Ephemeris 路线，并通过 adapter contract/parity gate 管理未来候选后端。
3. PDF Dasha 起点差异是真实边界，需要继续以 oracle 样本集方式审计，而不是靠单例常数调参。

## 已拒绝或已过期的外部反馈

1. “项目 CLI 不支持秒”已经过期。当前 `scripts/jyotish_engine.py`、`scripts/jyotish_api_server.py`、`jyotish_vedic/__init__.py` 与前端时间输入均已支持秒级出生时间。
2. “Shadbala 仍在 1.7-3.5 Rupas”已经过期。当前 Shadbala 主输出为 v6.9.15 absolute Rupas，按六大分量绝对求和，不再使用旧的 1200 总量归一化。
3. “加入全局 Scaling Factor 即可修复 Shadbala”不应直接采纳。全局缩放会掩盖六大分量的单项偏差；后续若要对齐 JHora/PDF，应按 Sthana/Dig/Kala/Chesta/Naisargika/Drik 分量分别建立 oracle 表。
4. “True Lahiri 开关可以解释 Dasha 差异”目前只是猜测。当前审计显示，秒级输入与年长常数都不足以单独解释 PDF 起点，下一步应直接比较外部 oracle 的 Moon sidereal longitude、ayanamsa 值、Nakshatra 边界和 Vimshottari 起算口径。

## 当前本地复验数据

命令：

```bash
python3 scripts/jyotish_engine.py chart \
  --year REDACTED_YEAR --month 4 --day 17 \
  --hour 14 --minute 45 --second 20 \
  --lat 36.466667 --lon 114.2 --tz 8

python3 scripts/jyotish_engine.py shadbala \
  --year REDACTED_YEAR --month 4 --day 17 \
  --hour 14 --minute 45 --second 20 \
  --lat 36.466667 --lon 114.2 --tz 8

python3 scripts/dasha_reference_audit.py \
  --year REDACTED_YEAR --month 4 --day 17 \
  --hour 14 --minute 45 --second 20 \
  --lat 36.466667 --lon 114.2 --tz 8 \
  --target-start-date 1986-05-18 \
  --target-source 印度占星1.pdf
```

关键结果：

- Moon sidereal longitude：`311.77867372`
- Moon nakshatra：`Shatabhisha`
- D1 Lagna：`Leo`
- D9 Lagna：`Cancer`
- Shadbala method：`v6.9.15 absolute Rupas`
- Shadbala total Rupas：`55.1437`
- Sun total Rupas：`9.7035`
- 当前 Vimshottari 起点：`1986-05-23T22:45:10`
- PDF 目标起点：`1986-05-18`
- 目标差异：约 `5.948032` 天
- 对齐目标所需 Moon 黄经偏移：约 `0.01206283°`，即约 `0.69-0.76` 角分

## 代码与质量门状态

- 秒级输入：`scripts/jyotish_engine.py` 的 `--second`、API server、wrapper 与前端输入已接通。
- Shadbala：`scripts/shadbala.py` 使用绝对 Rupa 分量求和；`tests/test_shadbala_complete.py` 和 benchmark invariant 已覆盖。
- Dasha：`scripts/dasha_reference_audit.py` 已作为诊断工具进入 release quality gate。
- 分盘稳定性：本轮发现并修复 `scripts/divisional_charts_extended.py` 在 D81/D108/D144/composite/custom varga 中可能出现大于 360 度中间黄经导致 sign index 越界的问题，新增回归测试。

## 下一步

1. 建立外部 oracle 样本矩阵：至少包含 VedAstro、JHora/PyJHora、用户 PDF 三类来源的 Moon sidereal longitude、ayanamsa、Dasha 起点。
2. 不直接调生产 Dasha 常数；先分离出“黄经差异”“ayanamsa 差异”“起算年长/日界口径差异”三类变量。
3. 对 Shadbala 建分量级 benchmark，而不是加入全局缩放系数。
4. 继续静态 demo/无 API 公开演示 polish，让普通用户在没有本地 API 时也知道哪些能力可用、哪些能力需要启动后端。
