/**
 * i18n.js — 国际化模块 v1.0
 * 支持中文(zh) / 英文(en) 切换
 * 使用方式: t('key') / signName('Aries') / planetName('Sun')
 */
const STORAGE_KEY = 'jyotish_lang';
const DEFAULT_LANG = 'zh';
let _lang = localStorage.getItem(STORAGE_KEY) || DEFAULT_LANG;
const _callbacks = [];

// ============================================================================
// 引擎常量（英文版）
// ============================================================================
export const SIGNS_EN = {
  Aries:'Aries', Taurus:'Taurus', Gemini:'Gemini', Cancer:'Cancer',
  Leo:'Leo', Virgo:'Virgo', Libra:'Libra', Scorpio:'Scorpio',
  Sagittarius:'Sagittarius', Capricorn:'Capricorn', Aquarius:'Aquarius', Pisces:'Pisces'
};

export const PLANET_EN = {
  Sun:'Sun', Moon:'Moon', Mars:'Mars', Mercury:'Mercury',
  Jupiter:'Jupiter', Venus:'Venus', Saturn:'Saturn', Rahu:'Rahu (North Node)', Ketu:'Ketu (South Node)'
};

export const STATUS_EN = {
  '入旺':'Exalted', '落陷':'Debilitated', '入庙':'Own Sign', '入友':'Friendly Sign',
  '入敌':'Enemy Sign', '中性':'Neutral', '燃烧':'Combust', '逆行':'Retrograde'
};

// ============================================================================
// 翻译字典
// ============================================================================
const D = {
  // ---- index.html 静态文本 ----
  'app.title':           { zh:'Jyotish · 印度占星',        en:'Jyotish · Vedic Astrology' },
  'tagline':             { zh:'探索你的吠陀星盘 · 排盘 · 解盘 · 推运', en:'Explore Your Vedic Chart · Cast · Read · Predict' },
  'input.title':         { zh:'输入出生信息',              en:'Birth Information' },
  'label.date':          { zh:'出生日期',                  en:'Birth Date' },
  'label.time':          { zh:'出生时间',                  en:'Birth Time' },
  'date.year':           { zh:'年',                        en:'Year' },
  'date.month':          { zh:'月',                        en:'Month' },
  'date.day':            { zh:'日',                        en:'Day' },
  'label.city':          { zh:'出生城市',                  en:'Birth City' },
  'label.tz':            { zh:'时区',                      en:'Timezone' },
  'tz.auto':             { zh:'自动检测',                  en:'Auto Detect' },
  'city.placeholder':    { zh:'搜索城市...',               en:'Search city...' },
  'btn.calculate':       { zh:'生 成 星 盘',               en:'Generate Chart' },
  'btn.calculating':     { zh:'计算中...',                 en:'Calculating...' },
  'btn.export':          { zh:'⬇ 导出',                   en:'⬇ Export' },
  'btn.back':            { zh:'← 重新输入',                en:'← New Input' },
  'export.json':         { zh:'导出 JSON 数据',            en:'Export JSON Data' },
  'export.svg':          { zh:'导出星盘 SVG',              en:'Export Chart SVG' },
  'export.png':          { zh:'导出星盘 PNG',              en:'Export Chart PNG' },

  // ---- Tab 名称 ----
  'tab.chart':           { zh:'本命盘',                    en:'Rasi Chart' },
  'tab.karaka':          { zh:'Karaka',                    en:'Karaka' },
  'tab.houses':          { zh:'宫位分析',                  en:'House Analysis' },
  'tab.aspects':         { zh:'相位',                      en:'Aspects' },
  'tab.yogas':           { zh:'Yoga',                      en:'Yoga' },
  'tab.vargas':          { zh:'分盘',                      en:'Vargas' },
  'tab.ashtakavarga':    { zh:'Ashtakavarga',              en:'Ashtakavarga' },
  'tab.shadbala':        { zh:'Shadbala',                  en:'Shadbala' },
  'tab.dasha':           { zh:'Dasha',                     en:'Dasha' },
  'tab.transit':         { zh:'Transit',                   en:'Transit' },
  'tab.deep.full':       { zh:'Samagra Viveka 综合深度',    en:'Samagra Viveka Analysis' },
  'tab.deep.short':      { zh:'综合深度',                   en:'Deep Analysis' },
  'tab.extended.full':   { zh:'Vishesh Pariksha 扩展分析',  en:'Vishesh Pariksha Extended' },
  'tab.extended.short':  { zh:'扩展分析',                   en:'Extended' },
  'tab.rect.full':       { zh:'Janma Shuddhi 生时校正',     en:'Janma Shuddhi Rectification' },
  'tab.rect.short':      { zh:'生时校正',                   en:'Rectification' },

  // ---- 本命盘 Tab ----
  'chart.rasi':          { zh:'Rasi Chart 本命盘',         en:'Rasi Chart' },
  'chart.south':         { zh:'南印',                      en:'South' },
  'chart.north':         { zh:'北印',                      en:'North' },
  'planets.title':       { zh:'行星位置',                   en:'Planetary Positions' },
  'col.planet':          { zh:'行星',                      en:'Planet' },
  'col.sign':            { zh:'星座',                      en:'Sign' },
  'col.degree':          { zh:'度数',                      en:'Degree' },
  'col.house':           { zh:'宫位',                      en:'House' },
  'col.status':          { zh:'状态',                      en:'Status' },
  'col.nakshatra':       { zh:'星宿',                      en:'Nakshatra' },
  'col.d9':              { zh:'D9',                        en:'D9' },

  // ---- Karaka Tab ----
  'karaka.title':        { zh:'Jaimini Karaka 灵魂指针',    en:'Jaimini Karaka — Soul Pointers' },
  'karaka.7k':           { zh:'7-Karaka（古典系统）',       en:'7-Karaka (Classical)' },
  'karaka.8k':           { zh:'8-Karaka（含 Rahu）',       en:'8-Karaka (incl. Rahu)' },
  'karaka.note':         { zh:'Karaka 是 Jaimini 系统的核心概念。AK（Atmakaraka）代表灵魂目标，DK（Darakaraka）代表配偶征象星。7-Karaka 与 8-Karaka 是两种传承口径，Rahu 是否纳入会改变部分角色归属；实际解读需先固定所用体系。',
                           en:'Karaka is a core concept in the Jaimini system. AK (Atmakaraka) represents the soul purpose, and DK (Darakaraka) represents the spouse significator. 7-Karaka and 8-Karaka are two lineage conventions; including Rahu can change role assignments, so readings should first fix the chosen convention.' },

  // Karaka 标签
  'k.ak':    { zh:'AK 自我灵魂',    en:'AK Soul Self' },
  'k.amk':   { zh:'AmK 事业顾问',   en:'AmK Career Advisor' },
  'k.bk':    { zh:'BK 兄弟姐妹',    en:'BK Siblings' },
  'k.mk':    { zh:'MK 母亲',        en:'MK Mother' },
  'k.pk':    { zh:'PK 子女',        en:'PK Children' },
  'k.gk':    { zh:'GK 障碍冲突',    en:'GK Obstacles' },
  'k.dk':    { zh:'DK 配偶',        en:'DK Spouse' },
  'k.pik':   { zh:'PiK 父亲',       en:'PiK Father' },

  // ---- 宫位分析 Tab ----
  'houses.title':        { zh:'十二宫位综合解读',            en:'Twelve Houses Comprehensive Analysis' },
  'house.lord':          { zh:'宫主星',                     en:'Lord' },
  'house.inHouse':       { zh:'宫主星解读',                  en:'Lord Reading' },

  // ---- 相位 Tab ----
  'aspects.title':       { zh:'Graha Drishti 行星相位',     en:'Graha Drishti — Planetary Aspects' },
  'aspect.friendly':     { zh:'友方',                       en:'Friendly' },
  'aspect.neutral':      { zh:'中性',                       en:'Neutral' },
  'aspect.hostile':      { zh:'敌对',                       en:'Hostile' },
  'aspect.opposition':   { zh:'对冲',                       en:'Opposition' },
  'aspect.trine':        { zh:'三分',                       en:'Trine' },
  'aspect.special':      { zh:'特殊',                       en:'Special' },
  'aspect.none':         { zh:'未检测到行星间相位',          en:'No planetary aspects detected' },

  // ---- Yoga Tab ----
  'yoga.title':          { zh:'Yoga 格局识别',              en:'Yoga Pattern Detection' },
  'yoga.count':          { zh:'个格局',                     en:'yogas' },
  'yoga.bene':           { zh:'吉',                         en:'bene' },
  'yoga.male':           { zh:'凶',                         en:'malefic' },
  'yoga.none':           { zh:'未检测到显著的 Yoga 格局',    en:'No significant Yoga patterns detected' },
  'yoga.expand':         { zh:'▼ 点击展开详情',             en:'▼ Click to expand' },
  'yoga.collapse':       { zh:'▲ 点击收起',                 en:'▲ Click to collapse' },
  'yoga.formation':      { zh:'形成条件',                   en:'Formation' },
  'yoga.cancel':         { zh:'⚠️ 取消/削弱',              en:'⚠️ Cancellation/Weakening' },

  // ---- 分盘 Tab ----
  'varga.title':         { zh:'Varga 分盘系统',             en:'Varga Divisional Charts' },
  'varga.positions':     { zh:'行星位置',                   en:'Planetary Positions' },
  'col.vsign':           { zh:'分盘星座',                   en:'Varga Sign' },
  'col.nhouse':          { zh:'本命宫位',                   en:'Natal House' },

  // ---- Ashtakavarga Tab ----
  'av.title':            { zh:'Ashtakavarga 八分法',        en:'Ashtakavarga — Eightfold System' },
  'av.savtotal':         { zh:'SAV 总分',                   en:'SAV Total' },
  'arudha.title':        { zh:'Arudha Pada 完整列表',      en:'Arudha Pada Complete List' },
  'arudha.overview':     { zh:'Arudha Pada 概览',          en:'Arudha Pada Overview' },

  // ---- Shadbala Tab ----
  'sb.title':            { zh:'Shadbala 六维力量',          en:'Shadbala — Six-fold Strength' },
  'col.total':           { zh:'总力量',                     en:'Total' },
  'col.required':        { zh:'要求',                       en:'Required' },
  'col.pct':             { zh:'达标率',                     en:'Ratio' },
  'sb.note':             { zh:'Shadbala 是衡量行星综合力量的系统，包含6个维度：位置力量(Sthana)、方向力量(Dig)、时间力量(Kala)、运动力量(Chesta)、自然力量(Naisargika)、相位力量(Drik)。达标率≥100%为强，75-99%为中，<75%为弱。',
                           en:'Shadbala measures planetary strength across 6 dimensions: Positional (Sthana), Directional (Dig), Temporal (Kala), Motional (Chesta), Natural (Naisargika), and Aspectual (Drik) strength. Ratio ≥100% = strong, 75-99% = medium, <75% = weak.' },

  // ---- Dasha Tab ----
  'dasha.title':         { zh:'Dasha 大运系统',             en:'Dasha Systems' },
  'dasha.maha':          { zh:'大运',                       en:'Mahadasha' },
  'dasha.antar':         { zh:'次运',                       en:'Antardasha' },
  'dasha.praty':         { zh:'三运',                       en:'Pratyantardasha' },
  'dasha.years':         { zh:'年',                         en:'yrs' },

  // ---- Transit Tab ----
  'transit.title':       { zh:'Transit 行星过境分析',       en:'Transit — Planetary Passage' },
  'transit.date.label':  { zh:'日期（可选，默认当前）',     en:'Date (optional, defaults to now)' },
  'transit.time.label':  { zh:'时间',                       en:'Time' },
  'btn.transit.update':  { zh:'更新 Transit',               en:'Update Transit' },
  'transit.computing':   { zh:'正在计算行星位置...',         en:'Computing planetary positions...' },
  'transit.chart':       { zh:'Transit 星盘',               en:'Transit Chart' },
  'transit.slow':        { zh:'慢星过境详细分析',            en:'Slow Planet Transit Analysis' },
  'transit.alltable':    { zh:'全行星 Transit 对照表',       en:'All Planet Transit Table' },
  'col.tsign':           { zh:'Transit星座',                en:'Transit Sign' },
  'col.nsign':           { zh:'本命星座',                   en:'Natal Sign' },
  'col.retro':           { zh:'逆行',                       en:'Retro' },
  'col.change':          { zh:'换座',                       en:'Change' },
  'transit.conj':        { zh:'合相',                       en:'Conjunct' },
  'transit.asp':         { zh:'相位',                       en:'Aspect' },
  'dt.title':            { zh:'Double Transit 双重相位锁定', en:'Double Transit — Dual Aspect Lock' },
  'ss.detect':           { zh:'Sade Sati 检测',             en:'Sade Sati Detection' },
  'ss.active':           { zh:'当前不在 Sade Sati 期间',     en:'Not currently in Sade Sati' },
  'tav.title':           { zh:'Transit Ashtakavarga 评分',  en:'Transit Ashtakavarga Score' },
  'thi.title':           { zh:'宫位影响摘要',               en:'House Impact Summary' },

  // ---- 深度分析 Tab ----
  'deep.title':          { zh:'Samagra Viveka 综合深度分析', en:'Samagra Viveka — Comprehensive Analysis' },
  'deep.fn':             { zh:'Shubha Papa Lagna 功能吉凶星表 (B.V. Raman)', en:'Shubha Papa Lagna — Functional Benefics/Malefics (B.V. Raman)' },
  'deep.pacdares':       { zh:'PACDARES Ashtadasha 八维分析 (K.N. Rao)', en:'PACDARES Ashtadasha — Eight Dimension Analysis (K.N. Rao)' },
  'deep.grades':         { zh:'Bhava Sadhana 宫位六步评级 (A-F)', en:'Bhava Sadhana — House Grading (A-F)' },
  'deep.influence':      { zh:'Bhava Sambandha 宫位互影响矩阵', en:'Bhava Sambandha — House Influence Matrix' },
  'deep.vargottama':     { zh:'Vargottama 同座检测 (D1=D9)', en:'Vargottama Detection (D1=D9)' },
  'deep.triangle':       { zh:'Trikasiddhi D1 × D9 × D10 三角验证', en:'Trikasiddhi — D1 × D9 × D10 Triangle Verification' },
  'deep.freq':           { zh:'Graha Varga Sphuta 行星频率分析 (Shodashavarga 16分盘)', en:'Graha Varga Sphuta — Planetary Frequency (Shodashavarga)' },
  'deep.tk':             { zh:'Trikona-Kendra Sambandha 三方四正宫位映射', en:'Trikona-Kendra Sambandha — Trinal/Quadrant Mapping' },

  // ---- 扩展分析 Tab ----
  'ext.title':           { zh:'Vishesh Pariksha 扩展分析',  en:'Vishesh Pariksha — Extended Analysis' },
  'ext.bhava':           { zh:'Bhava Bala 宫位强度',        en:'Bhava Bala — House Strength' },
  'ext.vim':             { zh:'Vimsopaka Bala & Vaiseshikamsas 二十分力量评估', en:'Vimsopaka Bala & Vaiseshikamsas — 20-fold Strength' },
  'ext.states':          { zh:'Graha Avastha 行星状态 (活动·年龄·警觉·情绪)', en:'Graha Avastha — Planetary States (Activity·Age·Alertness·Mood)' },
  'ext.pinda':           { zh:'Ashtakavarga Pinda 八分法点数', en:'Ashtakavarga Pinda — Eightfold Points' },
  'ext.dasa':            { zh:'Ashtadasha Dasa 八种额外大运系统', en:'Ashtadasha Dasa — Eight Extra Dasa Systems' },

  // ---- 深度分析通用标签 ----
  'col.house':           { zh:'宫',                        en:'H' },
  'col.lord':            { zh:'主星',                      en:'Lord' },
  'col.rupas':           { zh:'Rupas',                     en:'Rupas' },
  'col.lordbala':        { zh:'主星强度',                   en:'Lord Bala' },
  'col.dig':             { zh:'Dig',                       en:'Dig' },
  'col.drig':            { zh:'Drig',                      en:'Drig' },
  'col.strength':        { zh:'强度',                      en:'Strength' },
  'col.dasa10':          { zh:'Dasa(10)',                   en:'Dasa(10)' },
  'col.shodasa':         { zh:'Shodasa(16)',               en:'Shodasa(16)' },
  'col.level':           { zh:'等级',                      en:'Level' },
  'col.activity':        { zh:'Activity 活动',             en:'Activity' },
  'col.age':             { zh:'Age 年龄',                  en:'Age' },
  'col.alertness':       { zh:'Alertness 警觉',            en:'Alertness' },
  'col.mood':            { zh:'Mood 情绪',                 en:'Mood' },

  // ---- 提示/警告 ----
  'alert.date':          { zh:'请填写出生日期和时间',       en:'Please fill in birth date and time' },
  'alert.city':          { zh:'请选择出生城市',             en:'Please select a birth city' },
  'alert.error':         { zh:'计算出错：',                 en:'Calculation error: ' },
  'alert.chart':         { zh:'请先生成星盘',               en:'Please generate a chart first' },

  // ---- 上升 Banner ----
  'asc.lord':            { zh:'宫主星',                     en:'Lord' },
  'asc.nakshatra':       { zh:'月亮星宿',                   en:'Moon Nakshatra' },

  // ---- Tithi/Panchanga ----
  'panch.title':         { zh:'Panchanga 五要素历法',       en:'Panchanga — Five Elements' },
  'panch.vara':          { zh:'Vara 星期',                  en:'Vara — Weekday' },
  'panch.tithi':         { zh:'Tithi 月相',                 en:'Tithi — Lunar Phase' },
  'panch.paksha':        { zh:'Paksha 半月',                en:'Paksha — Lunar Half' },
  'panch.karana':        { zh:'Karana 半月相',              en:'Karana — Half Tithi' },
  'panch.yoga':          { zh:'Yoga 日月瑜伽',              en:'Yoga — Sun-Moon Combination' },

  // ---- 宫位影响区域名 ----
  'houseArea.1':         { zh:'自我',    en:'Self' },
  'houseArea.2':         { zh:'财富',    en:'Wealth' },
  'houseArea.3':         { zh:'沟通',    en:'Communication' },
  'houseArea.4':         { zh:'家庭',    en:'Home' },
  'houseArea.5':         { zh:'创意',    en:'Creativity' },
  'houseArea.6':         { zh:'健康',    en:'Health' },
  'houseArea.7':         { zh:'关系',    en:'Relationship' },
  'houseArea.8':         { zh:'转化',    en:'Transformation' },
  'houseArea.9':         { zh:'远行',    en:'Travel' },
  'houseArea.10':        { zh:'事业',    en:'Career' },
  'houseArea.11':        { zh:'愿望',    en:'Aspirations' },
  'houseArea.12':        { zh:'灵性',    en:'Spirituality' },

  // ---- 行星详情标签 ----
  'detail.pos':          { zh:'✅ 正面',  en:'✅ Positive' },
  'detail.neg':          { zh:'⚠️ 负面',  en:'⚠️ Negative' },
  'detail.adv':          { zh:'💡 建议',  en:'💡 Advice' },
  'detail.special':      { zh:'🔮 特别',  en:'🔮 Special' },
  'detail.career':       { zh:'💼 事业',  en:'💼 Career' },
  'detail.wealth':       { zh:'💰 财富',  en:'💰 Wealth' },
  'detail.marriage':     { zh:'💑 婚姻',  en:'💑 Marriage' },
  'detail.health':       { zh:'🏥 健康',  en:'🏥 Health' },

  // ---- Transit 质量标签 ----
  'quality.fav':         { zh:'✓吉',     en:'✓ Fav' },
  'quality.chal':        { zh:'✗凶',     en:'✗ Chal' },
  'quality.neu':         { zh:'—中',     en:'— Neu' },

  // ---- Bhava Bala 说明 ----
  'bb.note':             { zh:'评估宫位综合强度：宫主星力量(Lord Bala) + 方向力量(Dig Bala) + 相位力量(Drig Bala)。Rupas 越高，该宫位代表的生活领域越强。',
                           en:'Evaluates house comprehensive strength: Lord Bala + Dig Bala + Drig Bala. Higher Rupas = stronger life area.' },
  'bb.strongest':        { zh:'最强',     en:'Strongest' },
  'bb.weakest':          { zh:'最弱',     en:'Weakest' },

  // ---- Extra Dasa ----
  'edasa.current':       { zh:'当前',     en:'Current' },

  // ---- Sade Sati ----
  'ss.moon':             { zh:'月亮',     en:'Moon' },
  'ss.saturn':           { zh:'土星',     en:'Saturn' },
  'ss.retro':            { zh:'(逆行)',   en:'(Retrograde)' },
  'ss.phase1':           { zh:'Sade Sati 第一阶段（Rising Phase）', en:'Sade Sati Phase 1 (Rising Phase)' },
  'ss.phase2':           { zh:'Sade Sati 第二阶段（Peak Phase）', en:'Sade Sati Phase 2 (Peak Phase)' },
  'ss.phase3':           { zh:'Sade Sati 第三阶段（Setting Phase）', en:'Sade Sati Phase 3 (Setting Phase)' },
  'ss.coming':           { zh:'Sade Sati 即将开始', en:'Sade Sati Approaching' },
  'ss.detail1':          { zh:'土星进入月亮前一宫，压力开始积蓄。此阶段影响财务和家庭关系。', en:'Saturn enters the sign before Moon — pressure builds. Affects finances and family relationships.' },
  'ss.detail2':          { zh:'土星直接经过月亮，最强烈的考验期。影响心理健康、事业和个人成长。', en:'Saturn transits over Moon — the most intense test period. Affects mental health, career, and personal growth.' },
  'ss.detail3':          { zh:'土星离开月亮进入下一宫，压力逐渐释放，转化收尾。', en:'Saturn leaves Moon\'s sign — pressure gradually releases, transformation concludes.' },
  'ss.detail.soon':      { zh:'土星距月亮星座仅一宫之差，Sade Sati 约在土星进入{0}时开始。', en:'Saturn is one sign away from Moon. Sade Sati begins when Saturn enters {0}.' },
  'ss.remaining':        { zh:'约剩 {0} 年', en:'~{0} years remaining' },
  'dt.locked':           { zh:'第{0}宫被双重相位锁定', en:'House {0} locked by dual aspect' },
  'transit.aspect.offset':{ zh:'{0}宫相位', en:'{0}-house aspect' },

  // ---- 语言切换 ----
  'lang.switch':         { zh:'EN',       en:'中文' },
  'lang.tooltip':        { zh:'Switch to English', en:'切换为中文' },

  // ---- 生时校正 Tab ----
  'rect.title':          { zh:'Janma Samaya Shuddhi 生时校正', en:'Janma Samaya Shuddhi — Birth Time Rectification' },
  'rect.subtitle':       { zh:'通过生命事件反推精确出生时间', en:'Reverse-engineer precise birth time from life events' },
  'rect.banner.title':   { zh:'不确定出生时间？',              en:'Uncertain about birth time?' },
  'rect.banner.desc':    { zh:'通过生命事件与分盘对比，精确校正到分钟', en:'Compare life events with divisional charts, accurate to the minute' },
  'rect.banner.btn':     { zh:'开始校正',                      en:'Start Rectification' },
  'rect.trigger':        { zh:'校正',                          en:'Rectify' },
  'rect.prompt.title':   { zh:'出生时间不确定？',                en:'Uncertain birth time?' },
  'rect.prompt.desc':    { zh:'通过生命事件反推精确出生时间，校正到分钟级', en:'Reverse-engineer precise birth time from life events, accurate to the minute' },
  'rect.prompt.btn':     { zh:'开始校正 →',                     en:'Start Rectification →' },
  'rect.config':         { zh:'校正参数', en:'Rectification Parameters' },
  'rect.range':          { zh:'搜索范围', en:'Search Range' },
  'rect.step':           { zh:'步长', en:'Step' },
  'rect.range.5':        { zh:'±5 分钟（精细）', en:'±5 min (Fine)' },
  'rect.range.10':       { zh:'±10 分钟', en:'±10 min' },
  'rect.range.15':       { zh:'±15 分钟（推荐）', en:'±15 min (Recommended)' },
  'rect.range.20':       { zh:'±20 分钟', en:'±20 min' },
  'rect.range.30':       { zh:'±30 分钟（宽范围）', en:'±30 min (Wide)' },
  'rect.step.30s':       { zh:'30 秒', en:'30 sec' },
  'rect.step.1m':        { zh:'1 分钟', en:'1 min' },
  'rect.step.2m':        { zh:'2 分钟', en:'2 min' },
  'rect.step.5m':        { zh:'5 分钟', en:'5 min' },
  'rect.events':         { zh:'生命事件', en:'Life Events' },
  'rect.events.hint':    { zh:'添加你确定日期的重要生命事件，至少5个效果最佳', en:'Add life events with known dates. At least 5 events recommended for best results' },
  'rect.event.date':     { zh:'事件日期', en:'Event Date' },
  'rect.event.cat':      { zh:'事件类别', en:'Event Category' },
  'rect.event.desc':     { zh:'备注（可选）', en:'Note (optional)' },
  'rect.event.add':      { zh:'+ 添加', en:'+ Add' },
  'rect.event.ph':       { zh:'如：第一次结婚...', en:'e.g., First marriage...' },
  'rect.event.count':    { zh:'个事件', en:'events' },
  'rect.no.events':      { zh:'尚未添加事件', en:'No events added yet' },
  'rect.run':            { zh:'🔍 开始校正', en:'🔍 Start Rectification' },
  'rect.computing':      { zh:'计算中...', en:'Computing...' },
  'rect.preparing':      { zh:'准备中...', en:'Preparing...' },
  'rect.calculating':    { zh:'正在计算...', en:'Computing...' },
  'rect.result':         { zh:'校正结果', en:'Rectification Result' },
  'rect.original.time':  { zh:'原始时间', en:'Original Time' },
  'rect.rec.time':       { zh:'推荐时间', en:'Recommended Time' },
  'rect.original.asc':   { zh:'原始上升', en:'Original Ascendant' },
  'rect.corrected.asc':  { zh:'校正后上升', en:'Corrected Ascendant' },
  'rect.confidence':     { zh:'置信度', en:'Confidence' },
  'rect.top.candidates': { zh:'Top 10 候选时间', en:'Top 10 Candidates' },
  'rect.rank':           { zh:'排名', en:'#' },
  'rect.time':           { zh:'时间', en:'Time' },
  'rect.offset':         { zh:'偏移', en:'Offset' },
  'rect.asc':            { zh:'上升', en:'Asc' },
  'rect.d9asc':          { zh:'D9上升', en:'D9 Asc' },
  'rect.score':          { zh:'评分', en:'Score' },
  'rect.match':          { zh:'匹配度', en:'Match' },
  'rect.event.detail':   { zh:'事件对齐详情（最佳匹配）', en:'Event Alignment Details (Best Match)' },
  'rect.event.col':      { zh:'事件', en:'Event' },
  'rect.date.col':       { zh:'日期', en:'Date' },
  'rect.maha.col':       { zh:'大运', en:'Mahadasha' },
  'rect.antar.col':      { zh:'次运', en:'Antardasha' },
  'rect.score.col':      { zh:'评分', en:'Score' },
  'rect.rel.col':        { zh:'关联性', en:'Relevance' },
  'rect.strong.match':   { zh:'✅ 强匹配', en:'✅ Strong Match' },
  'rect.maha.match':     { zh:'🟡 大运匹配', en:'🟡 Maha Match' },
  'rect.antar.match':    { zh:'🟡 次运匹配', en:'🟡 Antar Match' },
  'rect.no.match':       { zh:'⚪ 无直接关联', en:'⚪ No Direct Link' },
  'rect.conf.high':      { zh:'高', en:'High' },
  'rect.conf.medium':    { zh:'中', en:'Medium' },
  'rect.conf.low':       { zh:'低', en:'Low' },
  'rect.conf.unknown':   { zh:'不确定', en:'Uncertain' },
  'rect.baseline':       { zh:'基准', en:'Baseline' },
  'rect.alert.no.events':{ zh:'请至少添加一个生命事件', en:'Please add at least one life event' },
  'rect.alert.no.chart': { zh:'请先生成星盘', en:'Please generate a chart first' },
  'rect.offset.detail':  { zh:'偏移 {0} 详情 ({1})', en:'Offset {0} Details ({1})' },
  'rect.asc.label':      { zh:'上升：', en:'Ascendant: ' },
  'rect.d9.label':       { zh:'D9上升：', en:'D9 Ascendant: ' },
  'rect.moon.nak':       { zh:'月亮星宿：', en:'Moon Nakshatra: ' },
  'rect.total.score':    { zh:'总评分：', en:'Total Score: ' },
  'rect.house.changes':  { zh:'宫位变化', en:'House Changes' },
  'rect.no.change':      { zh:'行星宫位无变化', en:'No planetary house changes' },
  'rect.d9.changed':     { zh:' (已变更 ⚠️)', en:' (Changed ⚠️)' },
  'rect.best.desc':      { zh:'最佳匹配评分 {0}%，领先第二名 {1}%', en:'Best match score {0}%, leading runner-up by {1}%' },
  'rect.rec.adjust':     { zh:'建议出生时间校正 {0} 分钟', en:'Recommended birth time adjustment: {0} min' },
  'rect.d9.warn':        { zh:'⚠️ 此校正会改变Navamsa上升，影响重大，建议专业验证', en:'⚠️ This adjustment changes the Navamsa ascendant — significant impact, professional verification recommended' },
  'rect.more.events':    { zh:'建议提供至少5个以上生命事件以提高准确性', en:'Providing at least 5 life events is recommended for better accuracy' },
  'rect.high.conf':      { zh:'多个事件一致指向此时间，可信度较高', en:'Multiple events consistently point to this time — high reliability' },
  'rect.low.conf':       { zh:'事件对齐度较低，可能需要更多事件数据或尝试更大时间范围', en:'Low event alignment — more events or a wider search range may help' },

  // ---- 生时校正 v2.0 新增 ----
  'rect.method.info':       { zh:'基于 K.N. Rao 与 P.V.R. Narasimha Rao 方法：通过分盘上升变化（D9/D10/D24等）+ Dasha 事件对齐，多维交叉验证精确到分钟', en:'Based on K.N. Rao & P.V.R. Narasimha Rao methodology: cross-validate via varga ascendant changes (D9/D10/D24 etc.) + Dasha event alignment, accurate to the minute' },
  'rect.sensitivity.info':  { zh:'📋 分盘灵敏度参考（上升变更时间窗口）', en:'📋 Varga Sensitivity Reference (Ascendant change time window)' },
  'rect.time.window':       { zh:'变更窗口', en:'Change Window' },
  'rect.min.unit':          { zh:'分钟', en:'min' },
  'rect.varga.col':         { zh:'分盘', en:'Varga' },
  'rect.from.col':          { zh:'原始', en:'From' },
  'rect.to.col':            { zh:'校正后', en:'To' },
  'rect.varga.changes':     { zh:'分盘上升变化（最佳匹配 vs 基准）', en:'Varga Ascendant Changes (Best Match vs Baseline)' },
  'rect.scoring.title':     { zh:'评分维度', en:'Scoring Dimensions' },
  'rect.scoring.dasha':     { zh:'Dasha 对齐', en:'Dasha Alignment' },
  'rect.scoring.varga':     { zh:'分盘一致性', en:'Varga Consistency' },
  'rect.scoring.house':     { zh:'宫位变化', en:'House Changes' },
  'rect.scoring.nak':       { zh:'星宿 Pada', en:'Nakshatra Pada' },
  'rect.score.dasha':       { zh:'Dasha分', en:'Dasha' },
  'rect.score.varga':       { zh:'Varga分', en:'Varga' },

  // ---- AI Chat ----
  'ai.fab.text':         { zh:'问我', en:'Ask' },
  'ai.fab.title':        { zh:'AI 星盘咨询', en:'AI Chart Consultation' },
  'ai.fab.tip':          { zh:'有问题？点我解读星盘 ✨', en:'Questions? Tap me to read your chart ✨' },
  'ai.panel.title':      { zh:'☉ 星盘咨询', en:'☉ Chart Consultation' },
  'ai.select.chart':     { zh:'选择星盘', en:'Select Chart' },
  'ai.save.chart':       { zh:'保存当前星盘', en:'Save Current Chart' },
  'ai.delete':           { zh:'删除', en:'Delete' },
  'ai.welcome':          { zh:'选择一个星盘，开始与 AI 占星师对话', en:'Select a chart to start chatting with the AI astrologer' },
  'ai.placeholder':      { zh:'输入你的占星问题...', en:'Type your astrology question...' },
  'ai.send':             { zh:'发送', en:'Send' },
  'ai.select.saved':     { zh:'选择已保存的星盘', en:'Select a saved chart' },
  'ai.current':          { zh:'[当前]', en:'[Current]' },
  'ai.unknown.chart':    { zh:'未知星盘', en:'Unknown Chart' },
  'ai.no.chart.gen':     { zh:'请先生成一个星盘', en:'Please generate a chart first' },
  'ai.chart.saved':      { zh:'✓ 星盘已保存到星盘库', en:'✓ Chart saved to library' },
  'ai.chart.exists':     { zh:'该星盘已保存过', en:'Chart already saved' },
  'ai.chart.deleted':    { zh:'✓ 星盘已从库中删除', en:'✓ Chart removed from library' },
  'ai.select.first':     { zh:'请先选择一个星盘', en:'Please select a chart first' },
  'ai.no.chart.or.saved':{ zh:'请先生成一个星盘，或从星盘库中选择一个已保存的星盘。', en:'Please generate a chart or select one from the library.' },
  'ai.error.prefix':     { zh:'对话出错：', en:'Chat error: ' },
  'ai.no.data':          { zh:'无星盘数据', en:'No chart data' },
  'ai.no.reply':         { zh:'AI 未返回内容', en:'AI returned no content' },
  'ai.setup.title':      { zh:'配置 AI 后端可获得完整 AI 解读', en:'Configure an AI backend for full AI reading' },
  'ai.setup.server':     { zh:'请通过本地/服务端 API 代理连接模型，例如 /api/chat。', en:'Connect through a local or server-side API proxy, for example /api/chat.' },
  'ai.setup.secret':     { zh:'不要把 OpenAI API key 放进浏览器；在服务端环境变量 OPENAI_API_KEY 或密钥管理服务中读取。', en:'Do not put an OpenAI API key in the browser; load it from server-side OPENAI_API_KEY or a key management service.' },
  'ai.setup.trust':      { zh:'可在 Trust Center 先运行健康检查，确认本地 API 与能力目录可用。', en:'Run the Trust Center health check first to confirm the local API and capability catalog are available.' },

  // ---- Auth ----
  'auth.login':          { zh:'登录', en:'Login' },
  'auth.logout':         { zh:'退出', en:'Logout' },
  'auth.login.title':    { zh:'登录 Jyotish', en:'Login to Jyotish' },
  'auth.login.desc':     { zh:'登录后可使用 AI 占星师对话（每日 3 次免费）', en:'Login to use AI astrologer chat (3 free per day)' },
  'auth.email':          { zh:'邮箱', en:'Email' },
  'auth.password':       { zh:'密码', en:'Password' },
  'auth.pw.ph':          { zh:'输入密码', en:'Enter password' },
  'auth.login.btn':      { zh:'登 录', en:'Login' },
  'auth.logging.in':     { zh:'登录中...', en:'Logging in...' },
  'auth.login.failed':   { zh:'登录失败，请检查邮箱和密码', en:'Login failed. Check your email and password' },
  'auth.or':             { zh:'或', en:'or' },
  'auth.apple.login':    { zh:'通过 Apple 登录', en:'Sign in with Apple' },
  'auth.no.account':     { zh:'还没有账号？', en:'No account yet?' },
  'auth.register.link':  { zh:'注册', en:'Register' },
  'auth.register.title': { zh:'注册 Jyotish', en:'Register for Jyotish' },
  'auth.register.desc':  { zh:'免费注册，即可使用 AI 占星师对话', en:'Free registration unlocks AI astrologer chat' },
  'auth.pw2':            { zh:'确认密码', en:'Confirm Password' },
  'auth.pw2.ph':         { zh:'再次输入密码', en:'Re-enter password' },
  'auth.pw.min.ph':      { zh:'至少6位密码', en:'At least 6 characters' },
  'auth.register.btn':   { zh:'注 册', en:'Register' },
  'auth.registering':    { zh:'注册中...', en:'Registering...' },
  'auth.pw.mismatch':    { zh:'两次密码输入不一致', en:'Passwords do not match' },
  'auth.pw.short':       { zh:'密码至少需要6位', en:'Password must be at least 6 characters' },
  'auth.register.failed':{ zh:'注册失败，请稍后重试', en:'Registration failed. Please try again later' },
  'auth.has.account':    { zh:'已有账号？', en:'Already have an account?' },
  'auth.profile':        { zh:'用户', en:'User' },
  'auth.free.plan':      { zh:'免费版 · 今日已用 {0}/{1} 次', en:'Free · Today {0}/{1} used' },
  'auth.premium.plan':   { zh:'☉ 高级会员 · 无限对话', en:'☉ Premium · Unlimited Chat' },
  'auth.upgrade.title':  { zh:'升级到高级会员', en:'Upgrade to Premium' },
  'auth.upgrade.1':      { zh:'✦ 无限 AI 占星师对话', en:'✦ Unlimited AI astrologer chat' },
  'auth.upgrade.2':      { zh:'✦ 深度星盘解读', en:'✦ Deep chart interpretation' },
  'auth.upgrade.3':      { zh:'✦ 推运分析', en:'✦ Transit analysis' },
  'auth.upgrade.4':      { zh:'✦ 实时 Transit 咨询', en:'✦ Real-time transit consultation' },
  'auth.upgrade.btn':    { zh:'订阅高级会员', en:'Subscribe to Premium' },
  'auth.reset.title':    { zh:'重置密码', en:'Reset Password' },
  'auth.reset.desc':     { zh:'输入注册邮箱，我们将发送重置链接', en:'Enter your email to receive a reset link' },
  'auth.reset.btn':      { zh:'发送重置链接', en:'Send Reset Link' },
  'auth.back.login':     { zh:'返回登录', en:'Back to Login' },
  'auth.apple.failed':   { zh:'Apple 登录失败: ', en:'Apple Sign-In failed: ' },
  'auth.apple.device':   { zh:'Apple Sign-In 需要在 iOS 设备上使用，或加载 Apple JS SDK', en:'Apple Sign-In requires an iOS device or Apple JS SDK' },
  'auth.request.failed': { zh:'请求失败', en:'Request failed' },
  'auth.token.expired':  { zh:'Token 已过期', en:'Token expired' },
  'auth.error.unknown':  { zh:'未知错误', en:'Unknown error' },
  'auth.recovery.api':   { zh:'登录/注册需要本地或服务端 API 在线；请先到 Trust Center 运行健康检查。', en:'Login/register requires the local or server API to be online; run the Trust Center health check first.' },
  'auth.recovery.retry': { zh:'若未连接，请按 README 的普通用户启动路径启动网页服务和本地 API 服务后重试。', en:'If disconnected, follow the README first-use startup path to start the web service and local API service, then retry.' },

  // ---- Subscription ----
  'sub.iap.unavail':     { zh:'IAP 功能不可用，请在 iOS 设备上使用', en:'IAP unavailable. Please use on an iOS device' },
  'sub.no.product':      { zh:'暂无可用的订阅产品，请稍后重试', en:'No subscription products available. Please try again later' },
  'sub.success':         { zh:'🎉 订阅成功！已升级到高级会员', en:'🎉 Subscription successful! Upgraded to Premium' },
  'sub.failed':          { zh:'订阅失败: ', en:'Subscription failed: ' },
  'sub.restore.only':    { zh:'恢复购买功能仅在 iOS App 中可用', en:'Restore is only available in the iOS App' },
  'sub.restore.ok':      { zh:'✓ 已成功恢复订阅', en:'✓ Subscription restored successfully' },
  'sub.restore.none':    { zh:'未找到有效的订阅记录', en:'No valid subscription found' },
  'sub.restore.fail':    { zh:'恢复购买失败: ', en:'Restore failed: ' },
  'sub.free.name':       { zh:'免费版', en:'Free' },
  'sub.premium.name':    { zh:'高级会员', en:'Premium' },
  'sub.recommended':     { zh:'推荐', en:'Recommended' },
  'sub.free.price':      { zh:'¥0', en:'$0' },
  'sub.premium.price':   { zh:'¥18/月', en:'$2.99/mo' },
  'sub.f1':              { zh:'✓ 完整排盘功能', en:'✓ Full chart casting' },
  'sub.f2':              { zh:'✓ 12个分析模块', en:'✓ 12 analysis modules' },
  'sub.f3':              { zh:'✓ AI 对话 3次/天', en:'✓ AI chat 3x/day' },
  'sub.f4':              { zh:'✗ 无限 AI 对话', en:'✗ Unlimited AI chat' },
  'sub.f5':              { zh:'✓ 无限 AI 对话', en:'✓ Unlimited AI chat' },
  'sub.f6':              { zh:'✓ 深度推运分析', en:'✓ Deep transit analysis' },
  'sub.f7':              { zh:'✓ 优先新功能', en:'✓ Priority new features' },
  'sub.note':            { zh:'📱 订阅功能将在 iOS App 上线后开放。当前请使用免费版。', en:'📱 Subscription will be available when the iOS App launches. Please use the free version for now.' },
  'sub.contact':         { zh:'如有问题请联系: jyotish.app@proton.me', en:'Questions? Contact: jyotish.app@proton.me' },
  'sub.check.login':     { zh:'请先登录以使用 AI 对话', en:'Please login to use AI chat' },
  'sub.check.limit':     { zh:'今日免费对话已用完', en:'Daily free chat limit reached' },
  'sub.recovery.iap':    { zh:'订阅/恢复购买需要 iOS IAP 或后端验证服务；网页端可继续使用免费功能，并可先到 Trust Center 检查 API。', en:'Subscription/restore needs iOS IAP or backend receipt verification; on web you can keep using free features and check the API in Trust Center.' },

  // ---- Shadbala 状态 ----
  'sb.strong':           { zh:'强',       en:'Strong' },
  'sb.medium':           { zh:'中',       en:'Medium' },
  'sb.weak':             { zh:'弱',       en:'Weak' },
};

// ============================================================================
// 核心函数
// ============================================================================

/** 翻译 key → 当前语言文本 */
export function t(key) {
  return D[key]?.[_lang] || D[key]?.zh || key;
}

/** 获取当前语言 */
export function getLang() { return _lang; }

/** 设置语言并触发回调 */
export function setLang(lang) {
  if (lang === _lang) return;
  _lang = lang;
  localStorage.setItem(STORAGE_KEY, lang);
  applyLocale();
  _callbacks.forEach(cb => { try { cb(lang); } catch(e) { console.error('[i18n] callback error:', e); } });
}

/** 注册语言变化回调 */
export function onLangChange(cb) { _callbacks.push(cb); }

/** 切换语言 */
export function toggleLang() { setLang(_lang === 'zh' ? 'en' : 'zh'); }

// ============================================================================
// 辅助函数
// ============================================================================

import { SIGNS_CN, PLANET_CN } from './jyotish-engine.js';

/** 获取本地化星座名 */
export function signName(sign) { return _lang === 'en' ? (SIGNS_EN[sign] || sign) : (SIGNS_CN[sign] || sign); }

/** 获取本地化行星名 */
export function planetName(planet) { return _lang === 'en' ? (PLANET_EN[planet] || planet) : (PLANET_CN[planet] || planet); }

/** 获取本地化状态名 */
export function statusName(status) {
  if (!status) return '';
  return _lang === 'en' ? (STATUS_EN[status] || status) : status;
}

/** 获取本地化宫位区域名 */
export function houseAreaName(house) { return t(`houseArea.${house}`); }

/** "第N宫" → localized */
export function houseLabel(house) { return _lang === 'en' ? `H${house}` : `第${house}宫`; }

/** "N年" → localized */
export function yearsLabel(years) { return _lang === 'en' ? `${years}yrs` : `${years}年`; }

// ============================================================================
// DOM 更新 — 应用翻译到所有 [data-i18n] 元素
// ============================================================================

export function applyLocale() {
  // 更新 html lang 属性
  document.documentElement.lang = _lang === 'zh' ? 'zh-CN' : 'en';
  // 更新 title
  document.title = t('app.title');

  // 遍历所有 data-i18n 元素
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    const text = t(key);
    if (text && text !== key) {
      el.textContent = text;
    }
  });

  // 遍历所有 data-i18n-placeholder 元素
  document.querySelectorAll('[data-i18n-ph]').forEach(el => {
    const key = el.getAttribute('data-i18n-ph');
    const text = t(key);
    if (text && text !== key) el.placeholder = text;
  });

  // 遍历所有 data-i18n-title 元素
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    const key = el.getAttribute('data-i18n-title');
    const text = t(key);
    if (text && text !== key) el.title = text;
  });

  // 更新语言切换按钮文本
  document.querySelectorAll('.lang-switch-btn').forEach(btn => {
    btn.textContent = t('lang.switch');
    btn.title = t('lang.tooltip');
  });
}

/**
 * 初始化语言系统
 * 在 DOMContentLoaded 时调用
 */
export function initI18N() {
  // 创建语言切换按钮（如果 header 中没有）
  ensureLangSwitcher();
  applyLocale();
}

function ensureLangSwitcher() {
  // 在两个 header 中添加语言切换按钮
  document.querySelectorAll('.header-right, .header-actions').forEach(container => {
    if (container.querySelector('.lang-switch-btn')) return;
    const btn = document.createElement('button');
    btn.className = 'lang-switch-btn';
    btn.textContent = t('lang.switch');
    btn.title = t('lang.tooltip');
    btn.addEventListener('click', () => toggleLang());
    // 插入到第一个子元素前面（或 [data-auth-header] 前面）
    const authEl = container.querySelector('[data-auth-header]');
    if (authEl) container.insertBefore(btn, authEl);
    else container.prepend(btn);
  });
}
