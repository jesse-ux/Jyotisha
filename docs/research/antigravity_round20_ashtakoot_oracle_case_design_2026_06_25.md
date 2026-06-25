# Antigravity AI Ashtakoot 外部 Oracle Cases 设计 (Round 20)

为验证我们的 Ashtakoot 实现，建议在 `references/oracle/` 新增合盘专用 JSON 校验文件，首批 5 个 Draft Cases：

### Case 1: The Perfect Match (满分标定)
- **case_id**: `template_ashtakoot_perfect_36`
- **privacy**: Synthetic
- **birth data**: Male Moon (0° Ashwini) vs Female Moon (0° Ashwini)
- **ayanamsa**: Lahiri
- **expected targets**: `total: 36`, `varna: 1`, `vashya: 2`, `tara: 3`, `yoni: 4`, `graha_maitri: 5`, `gana: 6`, `bhakoot: 7`, `nadi: 8`
- **preferred external sources**: VedAstro / AstroSage
- **artifact naming**: `astrosage_perfect_match_v1.png`

### Case 2: Severe Nadi Dosha (0分拦截)
- **case_id**: `template_ashtakoot_nadi_dosha`
- **privacy**: Synthetic
- **birth data**: 同一 Nakshatra 的不同 Pada。
- **expected targets**: `nadi: 0`, `total: 28`
- **preferred external sources**: JHora Matchmaking

### Case 3: Bhakoot Dosha Exception (异常豁免)
- **case_id**: `template_ashtakoot_bhakoot_exception`
- **privacy**: Synthetic
- **birth data**: 6-8 轴线，但主星同为木星（如射手-双鱼）。
- **expected targets**: `bhakoot: 7` (豁免后得满分) 或 `0` (严格派)。需标注派别。
- **preferred external sources**: AstroSage (观察其是否执行豁免)

### Case 4: Extreme Latitudes Match
- **case_id**: `template_ashtakoot_extreme_lat`
- **privacy**: Synthetic
- **birth data**: 北极圈内的两组出生数据。
- **expected targets**: 与赤道完全一致（因为合盘只看月亮）。
- **preferred external sources**: PyJHora CLI stdout

### Case 5: Public Celebrity Couple
- **case_id**: `celebrity_couple_victoria_david`
- **privacy**: Public Figure
- **expected targets**: 真实计算后的各项得分。
- **preferred external sources**: 任何权威网站的公开文章截屏。

**晋级标准**：只要提供截图并填平 JSON，即可晋级为 `external_verified`。
