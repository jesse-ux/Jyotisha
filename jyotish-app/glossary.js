/**
 * Jyotish Glossary v2.0 — "点读机"系统
 * 点击任何文本 → 自动匹配术语 → 弹出解释
 */
export const G = {
  Sun:{sk:'Surya',cn:'太阳',en:'Sun',cat:'graha',desc:'代表自我、灵魂、生命力、权威、父亲。强旺者自信、领导力强；受克则自我中心。'},
  Moon:{sk:'Chandra',cn:'月亮',en:'Moon',cat:'graha',desc:'代表心智、情感、直觉、母亲。月亮的星座揭示内在情感需求。强旺者善解人意；受克则情绪不稳。'},
  Mars:{sk:'Mangala',cn:'火星',en:'Mars',cat:'graha',desc:'代表行动力、勇气、竞争、体力。强旺者果断勇敢；受克则暴躁冲动。在婚姻匹配中至关重要。'},
  Mercury:{sk:'Budha',cn:'水星',en:'Mercury',cat:'graha',desc:'代表智力、沟通、商业、分析。最灵活的"王子"行星。强旺者口才好；受克则优柔寡断。'},
  Jupiter:{sk:'Guru',cn:'木星',en:'Jupiter',cat:'graha',desc:'最大吉星(Great Benefic)。代表智慧、信仰、子女、财富。女性盘中代表丈夫。强旺者慷慨乐观。'},
  Venus:{sk:'Shukra',cn:'金星',en:'Venus',cat:'graha',desc:'代表爱情、美感、艺术、婚姻。男性盘中代表妻子。强旺者有品味、浪漫；受克则虚荣。'},
  Saturn:{sk:'Shani',cn:'土星',en:'Saturn',cat:'graha',desc:'代表纪律、责任、考验、时间。"法官"行星，掌管因果业力。强旺者自律；受克则拖延悲观。'},
  Rahu:{sk:'Rahu',cn:'北交点/罗睺',en:'Rahu',cat:'graha',desc:'月亮北交点，代表欲望、执念、创新、跨领域突破。像放大镜放大触及的能量。'},
  Ketu:{sk:'Ketu',cn:'南交点/计都',en:'Ketu',cat:'graha',desc:'月亮南交点，代表解脱、灵性、直觉、前世课题。与Rahu相对——Rahu"想要"，Ketu"已拥有"。'},
  H1:{sk:'Lagna Bhava',cn:'第一宫·命宫',en:'1st House',cat:'bhava',desc:'代表自我、身体、性格、人生方向。整个星盘的"起点"，上升星座决定基础气质。'},
  H2:{sk:'Dhana Bhava',cn:'第二宫·财帛宫',en:'2nd House',cat:'bhava',desc:'代表财富、收入、家庭、语言能力。直接反映经济状况。也是Maraka(致命宫)。'},
  H3:{sk:'Sahaja Bhava',cn:'第三宫·兄弟宫',en:'3rd House',cat:'bhava',desc:'代表兄弟姐妹、短途旅行、沟通、勇气、努力。展示如何通过主动行动获得成就。'},
  H4:{sk:'Sukha Bhava',cn:'第四宫·田宅宫',en:'4th House',cat:'bhava',desc:'代表家庭、母亲、房产、教育、内心平静。"幸福宫"，反映内在安全感和归属感。'},
  H5:{sk:'Putra Bhava',cn:'第五宫·子女宫',en:'5th House',cat:'bhava',desc:'代表子女、创造力、恋爱、投资、智力。星盘中最"甜美"的宫位之一。'},
  H6:{sk:'Ripu Bhava',cn:'第六宫·奴仆宫',en:'6th House',cat:'bhava',desc:'代表疾病、敌人、债务、竞争。Dusthana凶宫，但也代表克服困难的能力。'},
  H7:{sk:'Kalatra Bhava',cn:'第七宫·夫妻宫',en:'7th House',cat:'bhava',desc:'代表婚姻、合作关系、配偶。"关系宫"，直接反映婚姻质量和配偶特质。'},
  H8:{sk:'Randhra Bhava',cn:'第八宫·疾厄宫',en:'8th House',cat:'bhava',desc:'代表长寿、遗产、神秘学、转化。最"神秘"的宫位，掌管人生重大转变。'},
  H9:{sk:'Dharma Bhava',cn:'第九宫·迁移宫',en:'9th House',cat:'bhava',desc:'代表宗教、哲学、长途旅行、导师、运气。最重要的三合宫(Trikona)之一。'},
  H10:{sk:'Karma Bhava',cn:'第十宫·官禄宫',en:'10th House',cat:'bhava',desc:'代表事业、社会地位、名声、成就。星盘中最"公共"的宫位。'},
  H11:{sk:'Labha Bhava',cn:'第十一宫·福德宫',en:'11th House',cat:'bhava',desc:'代表收入、愿望实现、朋友。"收入宫"，反映通过事业获得的回报。'},
  H12:{sk:'Vyaya Bhava',cn:'第十二宫·玄秘宫',en:'12th House',cat:'bhava',desc:'代表损失、支出、灵性修行、海外。Dusthana凶宫，但也代表灵性觉醒。'},
  Aries:{sk:'Mesha',cn:'白羊座',en:'Aries',cat:'rashi',desc:'火象星座，火星守护。代表新开始、勇气、行动力。太阳在此10°入旺，土星在此落陷。'},
  Taurus:{sk:'Vrishabha',cn:'金牛座',en:'Taurus',cat:'rashi',desc:'土象星座，金星守护。代表稳定、财富、感官享受。月亮在此3°入旺（最强月亮位置）。'},
  Gemini:{sk:'Mithuna',cn:'双子座',en:'Gemini',cat:'rashi',desc:'风象星座，水星守护。代表沟通、学习、多变。Rahu在此入旺。'},
  Cancer:{sk:'Karka',cn:'巨蟹座',en:'Cancer',cat:'rashi',desc:'水象星座，月亮守护。代表情感、家庭、安全感。木星在此入旺，火星在此落陷。'},
  Leo:{sk:'Simha',cn:'狮子座',en:'Leo',cat:'rashi',desc:'火象星座，太阳守护。代表创造力、领导力、王者风范。'},
  Virgo:{sk:'Kanya',cn:'处女座',en:'Virgo',cat:'rashi',desc:'土象星座，水星守护。代表分析、服务、健康。水星在此15°入旺，金星在此落陷。'},
  Libra:{sk:'Tula',cn:'天秤座',en:'Libra',cat:'rashi',desc:'风象星座，金星守护。代表平衡、关系、和谐。土星在此20°入旺，太阳在此落陷。'},
  Scorpio:{sk:'Vrischika',cn:'天蝎座',en:'Scorpio',cat:'rashi',desc:'水象星座，火星守护。代表深度转化、秘密、重生。月亮在此落陷。'},
  Sagittarius:{sk:'Dhanu',cn:'射手座',en:'Sagittarius',cat:'rashi',desc:'火象星座，木星守护。代表哲学、宗教、长途旅行、追求真理。'},
  Capricorn:{sk:'Makara',cn:'摩羯座',en:'Capricorn',cat:'rashi',desc:'土象星座，土星守护。代表纪律、事业、结构。火星在此28°入旺，木星在此落陷。'},
  Aquarius:{sk:'Kumbha',cn:'水瓶座',en:'Aquarius',cat:'rashi',desc:'风象星座，土星守护。代表创新、集体、人道主义、未来愿景。'},
  Pisces:{sk:'Meena',cn:'双鱼座',en:'Pisces',cat:'rashi',desc:'水象星座，木星守护。代表灵性、直觉、想象力。金星在此27°入旺，水星在此落陷。'},
  Exaltation:{sk:'Uccha',cn:'入旺',en:'Exaltation',cat:'status',desc:'行星最强位置。如太阳在白羊10°、月亮在金牛3°入旺。入旺行星赋予极强正面影响。'},
  Debilitation:{sk:'Neecha',cn:'落陷',en:'Debilitation',cat:'status',desc:'行星最弱位置。位于入旺星座的对冲位置。但也有"落陷取消"(Neecha Bhanga)的可能。'},
  OwnSign:{sk:'Swa Kshetra',cn:'入庙',en:'Own Sign',cat:'status',desc:'行星在守护的星座中。如火星在白羊或天蝎。能量稳定、正面，仅次于入旺。'},
  Combustion:{sk:'Asta',cn:'燃烧',en:'Combustion',cat:'status',desc:'行星距太阳太近被"灼烧"，功能被压制。水星和金星最容易被燃烧。'},
  Retrograde:{sk:'Vakri',cn:'逆行',en:'Retrograde',cat:'status',desc:'行星看似"倒退"。逆行行星力量更强(Chesta Bala)，但表达更内向反思。'},
  Nakshatra:{sk:'Nakshatra',cn:'星宿',en:'Lunar Mansion',cat:'concept',desc:'27个月亮星宿，每个跨13°20\'，由守护行星掌管。月亮所在Nakshatra决定思维模式，也是Dasha计算基础。'},
  Karaka:{sk:'Karaka',cn:'征象星',en:'Significator',cat:'concept',desc:'"指示者"。按度数排列：AK(灵魂目标)、AmK(事业)、BK(兄弟)、MK(母亲)、PK(子女)、GK(障碍)、DK(配偶)。'},
  Arudha:{sk:'Arudha',cn:'映像/表象',en:'Image',cat:'concept',desc:'Jaimini概念。Arudha Lagna代表世人眼中的形象（与真实Lagna不同）。'},
  Ashtakavarga:{sk:'Ashtakavarga',cn:'八分法',en:'Eight-fold Division',cat:'concept',desc:'Transit评估系统。7行星+上升的"吉星贡献"量化为Bindu分数。SAV总分337，≥30吉利，<20挑战。'},
  Shadbala:{sk:'Shadbala',cn:'六维力量',en:'Six-fold Strength',cat:'concept',desc:'行星综合力量评估：位置/方向/时间/运动/自然/相位六维度。达标率≥100%为强。'},
  Dasha:{sk:'Dasha',cn:'大运',en:'Planetary Period',cat:'concept',desc:'Jyotish独有时间系统。三级：Maha大运(数年)→Antar次运(数月)→Pratyantar三运(数天)。'},
  MahaDasha:{sk:'Maha Dasha',cn:'大运',en:'Major Period',cat:'concept',desc:'Vimshottari第一级。Ketu7/Venus20/Sun6/Moon10/Mars7/Rahu18/Jupiter16/Saturn19/Mercury17年。'},
  Antardasha:{sk:'Antardasha',cn:'次运',en:'Sub-period',cat:'concept',desc:'Dasha第二级。与大运行星的相互关系决定实际体验。'},
  Pratyantardasha:{sk:'Pratyantardasha',cn:'三运',en:'Sub-sub-period',cat:'concept',desc:'Dasha第三级。持续数天到数月，是事件定时的关键工具。'},
  Yoga:{sk:'Yoga',cn:'格局',en:'Combination',cat:'concept',desc:'特定行星排列产生的特殊影响。分吉Yoga(Raja/Dhana)和凶Yoga(Daridra/Kemadruma)。'},
  Yogakaraka:{sk:'Yogakaraka',cn:'王者行星',en:'Yoga-producing',cat:'concept',desc:'同时守护角宫(Kendra)和三合宫(Trikona)的行星。无论在哪都能带来极好结果。'},
  Vargottama:{sk:'Vargottama',cn:'同座(D1=D9)',en:'Same in D1 & D9',cat:'concept',desc:'行星在D1和D9同星座，能量放大。吉星加倍吉，凶星加倍凶。'},
  PACDARES:{sk:'PACDARES',cn:'八维分析',en:'8-dimension',cat:'concept',desc:'K.N.Rao体系：Position位置/Aspect相位/Conjunction合相/Dhana财富/Arishta凶象/Raja王者/Exchange互换/Special特殊。'},
  GrahaDrishti:{sk:'Graha Drishti',cn:'行星相位',en:'Planetary Aspect',cat:'concept',desc:'所有行星第7宫相位。Mars额外4/8宫，Jupiter 5/9宫，Saturn 3/10宫。'},
  SadeSati:{sk:'Sade Sati',cn:'土星七年半',en:'7.5yr Saturn Cycle',cat:'concept',desc:'Transit土星经过月亮星座及前后星座的7.5年。三阶段各2.5年，约每30年一次。'},
  Transit:{sk:'Gochara',cn:'行星过境/推运',en:'Transit',cat:'concept',desc:'当前天空行星实时位置对本命盘的影响。慢星(Saturn~2.5年/宫、Jupiter~1年/宫)影响最大。'},
  Panchanga:{sk:'Panchanga',cn:'五要素历法',en:'Five Elements',cat:'concept',desc:'Vara星期/Tithi月相/Nakshatra星宿/Yoga日月瑜伽/Karana半月相。用于择日和评估出生能量。'},
  Varga:{sk:'Varga',cn:'分盘',en:'Divisional Chart',cat:'concept',desc:'星座细分生成独立星盘。D1本命/D9婚姻/D10事业/D7子女/D12父母等。'},
  Ayanamsa:{sk:'Ayanamsa',cn:'岁差',en:'Precession',cat:'concept',desc:'恒星黄道与回归黄道差距(~24°)。Jyotish使用恒星黄道，最常用Lahiri Ayanamsa。'},
  Lagna:{sk:'Lagna',cn:'上升/命度',en:'Ascendant',cat:'concept',desc:'出生时刻东方地平线对应的黄道点。决定所有宫位划分。守护星Lagnesha是星盘最关键行星。'},
  Maraka:{sk:'Maraka',cn:'致命星',en:'Killer Planet',cat:'concept',desc:'第2/7宫守护星。在长寿和健康分析中需特别关注其Dasha和Transit。'},
  Trikona:{sk:'Trikona',cn:'三合宫(1/5/9)',en:'Trine',cat:'concept',desc:'第1/5/9宫，最吉祥三宫位，代表Dharma正道。守护星良好关系预示极大好运。'},
  Kendra:{sk:'Kendra',cn:'角宫(1/4/7/10)',en:'Angular',cat:'concept',desc:'最有力的四宫位，代表人生核心支柱。角宫+三合宫主星结合形成最强大Raja Yoga。'},
  Dusthana:{sk:'Dusthana',cn:'凶宫(6/8/12)',en:'Evil Houses',cat:'concept',desc:'带来挑战的宫位。6宫克服困难，8宫研究遗产，12宫灵性海外。'},
  BhavaBala:{sk:'Bhava Bala',cn:'宫位强度',en:'House Strength',cat:'concept',desc:'宫位综合强度评估：宫主星力量/方向力量/相位力量。'},
  Vimsopaka:{sk:'Vimsopaka Bala',cn:'二十分力量',en:'20-point Strength',cat:'concept',desc:'行星在不同分盘中综合尊严评分。满分20，入旺/入庙=20，大友=18，友=15。'},
  Avastha:{sk:'Avastha',cn:'行星状态',en:'Planet State',cat:'concept',desc:'行星状态维度：Activity(觉醒/梦境/沉睡)、Age(幼/青/成/老)、Mood(喜悦/愤怒/平静)。'},
  DoubleTransit:{sk:'Double Transit',cn:'双重过境锁定',en:'Double Transit Lock',cat:'concept',desc:'两颗慢星(Saturn+Jupiter)同时通过相位影响同一宫位，形成"锁定"，预示重大事件。'},
  Navamsa:{sk:'Navamsa (D9)',cn:'九分盘',en:'9th Division',cat:'concept',desc:'最重要分盘。D9反映婚姻、内在力量和后半生。"D1是树，D9是果实"。'},
  Dasamsa:{sk:'Dasamsa (D10)',cn:'十分盘',en:'10th Division',cat:'concept',desc:'事业分盘。D1显示事业潜力，D10揭示实际表现。'},
  Raman:{sk:'B.V. Raman',cn:'B.V. Raman 方法',en:'Raman Method',cat:'concept',desc:'20世纪最著名Jyotish大师。功能吉凶星表+宫位六步评级法(A-F)。'},
  SAV:{sk:'SAV',cn:'SAV 综合八分法',en:'Total AV Score',cat:'concept',desc:'所有BAV分数总和。每个星座最高56分，≥30吉利，<20挑战。'},
  Rashi:{sk:'Rashi',cn:'星座',en:'Zodiac Sign',cat:'concept',desc:'黄道12等分，每宫30°。分火/土/风/水四组。'},
  Conjunction:{sk:'Yuti',cn:'合相',en:'Conjunction',cat:'concept',desc:'两颗或多颗行星落在同一星座/宫位。能量交织融合，紧密合相影响力更大。'},
  Benefic:{sk:'Shubha',cn:'吉星',en:'Benefic',cat:'concept',desc:'天然吉星：Jupiter(大吉)、Venus(小吉)、饱满Moon、未受克Mercury。功能吉星取决于上升。'},
  Malefic:{sk:'Papa',cn:'凶星',en:'Malefic',cat:'concept',desc:'天然凶星：Saturn(大凶)、Mars(小凶)、Rahu、Ketu。功能凶星取决于上升。'},
  HouseLord:{sk:'Bhavesha',cn:'宫主星',en:'House Lord',cat:'concept',desc:'守护某宫对应星座的行星。宫主星位置和状态决定该宫事务的成败。'},
  Aspect:{sk:'Drishti',cn:'相位',en:'Aspect',cat:'concept',desc:'行星对特定宫位的"注视"。所有行星第7宫相位，Mars额外4/8，Jupiter 5/9，Saturn 3/10。'},
  Upachaya:{sk:'Upachaya',cn:'成长宫(3/6/10/11)',en:'Growth Houses',cat:'concept',desc:'随时间改善的宫位。凶星在此反而能发挥正面作用。'},
  D1:{sk:'Rasi Chart',cn:'本命盘(D1)',en:'Birth Chart',cat:'concept',desc:'最基础的星盘，显示出生时所有行星位置。是所有分析的根基。'},
  D9:{sk:'Navamsa',cn:'九分盘(D9)',en:'9th Division',cat:'concept',desc:'最重要分盘，反映婚姻和内在力量。'},
  D10:{sk:'Dasamsa',cn:'十分盘(D10)',en:'10th Division',cat:'concept',desc:'事业分盘，分析事业成就和职业方向。'},
  Tithi:{sk:'Tithi',cn:'月相',en:'Lunar Day',cat:'concept',desc:'月亮与太阳角距，每月30个。分盈月(Shukla)和亏月(Krishna)各15个。'},
  Vara:{sk:'Vara',cn:'星期',en:'Weekday',cat:'concept',desc:'每天由行星守护：周日Sun/周一Moon/周二Mars/周三Mercury/周四Jupiter/周五Venus/周六Saturn。'},
  Paksha:{sk:'Paksha',cn:'月相期',en:'Lunar Phase',cat:'concept',desc:'盈月(Shukla)代表增长开始，亏月(Krishna)代表减少完成。'},
  Bindu:{sk:'Bindu',cn:'分数点',en:'Point',cat:'concept',desc:'Ashtakavarga中的基本单位，代表行星对某星座的"吉星贡献"。'},
  BAV:{sk:'Bhinnashtakavarga',cn:'BAV 单星八分法',en:'Individual AV',cat:'concept',desc:'每颗行星各自的Ashtakavarga分数表(0-8)。'},
  RajaYoga:{sk:'Raja Yoga',cn:'王者格局',en:'Royal Combination',cat:'concept',desc:'角宫+三合宫主星关联时形成，预示权力、地位和重大成就。'},
  DhanaYoga:{sk:'Dhana Yoga',cn:'财富格局',en:'Wealth Combination',cat:'concept',desc:'2/11宫主星与1/5/9宫主星关联时形成，预示经济富裕。'},
  Lagnesha:{sk:'Lagnesha',cn:'命主星',en:'Ascendant Lord',cat:'concept',desc:'上升星座守护行星，星盘中最关键的行星，决定整体人生基调。'},
  Atmakaraka:{sk:'Atmakaraka',cn:'灵魂目标星(AK)',en:'Soul Planet',cat:'concept',desc:'度数最高的行星，代表此生灵魂的最高目标和课题。'},
  Darakaraka:{sk:'Darakaraka',cn:'配偶征象星(DK)',en:'Spouse Planet',cat:'concept',desc:'度数最低的行星(7K)，代表配偶的特质和关系模式。'},
  Amatyakaraka:{sk:'Amatyakaraka',cn:'事业征象星(AmK)',en:'Minister Planet',cat:'concept',desc:'度数第二高的行星，代表事业方向和职业路径。'},
  Mahapurusha:{sk:'Pancha Mahapurusha',cn:'五大伟人格局',en:'5 Great Yogas',cat:'concept',desc:'Hamsa/Malavya/Ruchaka/Bhadra/Shasha五种吉Yoga。入旺或入庙行星落角宫时形成。'},
  Neechabhanga:{sk:'Neechabhanga',cn:'落陷取消',en:'Cancellation of Debilitation',cat:'concept',desc:'落陷被特定条件取消反而形成强大Raja Yoga——"最黑暗处有最光明"。'},
  FunctionalBenefic:{sk:'Functional Benefic',cn:'功能吉星',en:'Functional Benefic',cat:'concept',desc:'守护角宫和三合宫的行星。每个上升的功能吉凶星不同。'},
  FunctionalMalefic:{sk:'Functional Malefic',cn:'功能凶星',en:'Functional Malefic',cat:'concept',desc:'守护凶宫(6/8/12)的行星。某些天然吉星可能成为功能凶星。'},
};

// ===== 术语匹配表（长度降序，长优先） =====
export const TERM_BINDINGS = (() => {
  const raw = [
    ['北交点/罗睺','Rahu'],['南交点/计都','Ketu'],['北交点','Rahu'],['南交点','Ketu'],
    ['太阳','Sun'],['月亮','Moon'],['火星','Mars'],['水星','Mercury'],['木星','Jupiter'],['金星','Venus'],['土星','Saturn'],
    ['Jupiter','Jupiter'],['Mercury','Mercury'],['Saturn','Saturn'],['Venus','Venus'],
    ['Mars','Mars'],['Moon','Moon'],['Sun','Sun'],['Rahu','Rahu'],['Ketu','Ketu'],
    ['白羊座','Aries'],['金牛座','Taurus'],['双子座','Gemini'],['巨蟹座','Cancer'],
    ['狮子座','Leo'],['处女座','Virgo'],['天秤座','Libra'],['天蝎座','Scorpio'],
    ['射手座','Sagittarius'],['摩羯座','Capricorn'],['水瓶座','Aquarius'],['双鱼座','Pisces'],
    ['Sagittarius','Sagittarius'],['Capricorn','Capricorn'],['Aquarius','Aquarius'],['Pisces','Pisces'],
    ['Aries','Aries'],['Taurus','Taurus'],['Gemini','Gemini'],['Cancer','Cancer'],
    ['Leo','Leo'],['Virgo','Virgo'],['Libra','Libra'],['Scorpio','Scorpio'],
    ['入旺','Exaltation'],['落陷','Debilitation'],['入庙','OwnSign'],['燃烧','Combustion'],['逆行','Retrograde'],
    ['Nakshatra','Nakshatra'],['Ashtakavarga','Ashtakavarga'],['Shadbala','Shadbala'],
    ['Vargottama','Vargottama'],['PACDARES','PACDARES'],['Yogakaraka','Yogakaraka'],
    ['Double Transit','DoubleTransit'],['Graha Drishti','GrahaDrishti'],
    ['Sade Sati','SadeSati'],['Bhava Bala','BhavaBala'],
    ['Panchanga','Panchanga'],['Navamsa','Navamsa'],['Dasamsa','Dasamsa'],
    ['Vimsopaka','Vimsopaka'],['Avastha','Avastha'],['Ayanamsa','Ayanamsa'],
    ['Karaka','Karaka'],['Arudha','Arudha'],['Transit','Transit'],
    ['Dasha','Dasha'],['Yoga','Yoga'],['Maraka','Maraka'],['SAV','SAV'],['Raman','Raman'],
    ['Rashi','Rashi'],['星座','Rashi'],['合相','Conjunction'],['吉星','Benefic'],['凶星','Malefic'],
    ['宫主星','HouseLord'],['相位','Aspect'],['成长宫','Upachaya'],
    ['本命盘','D1'],['九分盘','D9'],['十分盘','D10'],['分盘','Varga'],
    ['月相期','Paksha'],['分数点','Bindu'],['BAV','BAV'],
    ['王者格局','RajaYoga'],['财富格局','DhanaYoga'],
    ['命主星','Lagnesha'],['灵魂目标','Atmakaraka'],['配偶征象','Darakaraka'],['事业征象','Amatyakaraka'],
    ['五大伟人','Mahapurusha'],['落陷取消','Neechabhanga'],
    ['功能吉星','FunctionalBenefic'],['功能凶星','FunctionalMalefic'],
    ['角宫','Kendra'],['三合宫','Trikona'],['凶宫','Dusthana'],
    ['宫位强度','BhavaBala'],['八维','PACDARES'],
    ['大运','MahaDasha'],['次运','Antardasha'],['三运','Pratyantardasha'],
    ['月相','Tithi'],['星期','Vara'],['五要素','Panchanga'],
    ['上升','Lagna'],['命度','Lagna'],['征象星','Karaka'],
    ['映像','Arudha'],['六维','Shadbala'],['八分法','Ashtakavarga'],
    ['过境','Transit'],['推运','Transit'],['格局','Yoga'],
    ['岁差','Ayanamsa'],['同座','Vargottama'],['致命星','Maraka'],
    ['王者行星','Yogakaraka'],
    // 星宿名（前6个最常见的）
    ['Ashwini','Nakshatra'],['Bharani','Nakshatra'],['Krittika','Nakshatra'],
    ['Rohini','Nakshatra'],['Mrigashira','Nakshatra'],['Ardra','Nakshatra'],
    ['Punarvasu','Nakshatra'],['Pushya','Nakshatra'],['Ashlesha','Nakshatra'],
    ['Magha','Nakshatra'],['Purva Phalguni','Nakshatra'],['Uttara Phalguni','Nakshatra'],
    ['Hasta','Nakshatra'],['Chitra','Nakshatra'],['Swati','Nakshatra'],
    ['Vishakha','Nakshatra'],['Anuradha','Nakshatra'],['Jyeshtha','Nakshatra'],
    ['Mula','Nakshatra'],['Purva Ashadha','Nakshatra'],['Uttara Ashadha','Nakshatra'],
    ['Shravana','Nakshatra'],['Dhanishta','Nakshatra'],['Shatabhisha','Nakshatra'],
    ['Purva Bhadrapada','Nakshatra'],['Uttara Bhadrapada','Nakshatra'],['Revati','Nakshatra'],
    // 宫位 H1-H12
    ...Array.from({length:12},(_,i)=>[`H${i+1}`,`H${i+1}`]),
    // 第N宫
    ...Array.from({length:12},(_,i)=>[`第${i+1}宫`,`H${i+1}`]),
  ];
  // 按长度降序排列（长的优先匹配）
  raw.sort((a,b) => b[0].length - a[0].length);
  return raw.map(([pattern,key]) => ({pattern,key}));
})();

// ===== Tooltip DOM =====
let tooltipEl = null;
export function initTooltip() {
  tooltipEl = document.createElement('div');
  tooltipEl.className = 'jt-tooltip hidden';
  tooltipEl.innerHTML = `<div class="jt-overlay"></div><div class="jt-card">
    <div class="jt-header"><span class="jt-cat"></span><span class="jt-close">&times;</span></div>
    <div class="jt-title"></div><div class="jt-names"></div><div class="jt-desc"></div></div>`;
  document.body.appendChild(tooltipEl);
  tooltipEl.querySelector('.jt-overlay').addEventListener('click', hideTooltip);
  tooltipEl.querySelector('.jt-close').addEventListener('click', hideTooltip);
  // 核心改变：全局点击不再只依赖 data-term，而是扫描文本
  document.addEventListener('click', handleUniversalClick);
}

// ===== 通用点击处理器（"点读机"核心） =====
function handleUniversalClick(e) {
  // 1. 检查是否点击了 tooltip 自身
  if (tooltipEl && tooltipEl.contains(e.target)) return;
  // 2. 排除按钮/输入框/链接
  const tag = e.target.tagName;
  if (['BUTTON','INPUT','SELECT','TEXTAREA','A','SVG'].includes(tag)) return;
  // 3. 排除 AI 聊天面板
  if (e.target.closest('.ai-chat-panel') || e.target.closest('.ai-fab')) return;
  // 4. Fast path: 已有 data-term 的元素（含祖先）
  let el = e.target;
  while (el && el !== document.body) {
    if (el.dataset && el.dataset.term) {
      e.preventDefault();
      showTooltip(el.dataset.term);
      return;
    }
    el = el.parentElement;
  }
  // 5. Universal scan: 在 #page-chart 区域内，扫描点击元素的文本
  const chartPage = document.querySelector('#page-chart');
  if (!chartPage || !chartPage.contains(e.target)) return;
  const key = matchText(e.target);
  if (key) {
    e.preventDefault();
    showTooltip(key);
  }
}

// ===== 文本匹配引擎 =====
function matchText(el) {
  // 获取元素自身文本（不含子元素文本，更精确）
  const ownText = getOwnText(el);
  if (ownText) {
    const k = scanBindings(ownText);
    if (k) return k;
  }
  // 如果自身文本太短或没匹配，尝试包含子元素的完整文本
  const fullText = el.textContent || '';
  if (fullText.length <= 300) {
    return scanBindings(fullText);
  }
  return null;
}

function getOwnText(el) {
  let t = '';
  for (const n of el.childNodes) {
    if (n.nodeType === Node.TEXT_NODE) t += n.textContent;
  }
  return t.trim();
}

function scanBindings(text) {
  for (const {pattern, key} of TERM_BINDINGS) {
    if (text.includes(pattern) && G[key]) return key;
  }
  return null;
}

// ===== Tooltip 显示/隐藏 =====
const CAT_MAP = {graha:'行星 Graha',bhava:'宫位 Bhava',rashi:'星座 Rashi',status:'状态',concept:'概念 Concept'};
const TERMINOLOGY_MODE_LABELS = {
  balanced: '平衡模式',
  beginner: '入门解释',
  professional: '专业对照',
};
const TERMINOLOGY_MODES = Object.keys(TERMINOLOGY_MODE_LABELS);

export function setGlossaryTerminologyMode(mode = 'balanced') {
  window.__jyotishTerminologyMode = normalizeGlossaryTerminologyMode(mode);
  if (tooltipEl) tooltipEl.dataset.mode = window.__jyotishTerminologyMode;
  const visibleKey = tooltipEl?.dataset?.termKey;
  if (visibleKey && tooltipEl && !tooltipEl.classList.contains('hidden')) showTooltip(visibleKey);
  return window.__jyotishTerminologyMode;
}

export function getGlossaryTerminologyMode() {
  return normalizeGlossaryTerminologyMode(window.__jyotishTerminologyMode);
}

function normalizeGlossaryTerminologyMode(mode) {
  return TERMINOLOGY_MODES.includes(mode) ? mode : 'balanced';
}

function buildTerminologyDisplay(entry, mode) {
  if (mode === 'professional') {
    return {
      title: `${entry.cn} · ${entry.en}`,
      names: [entry.sk, entry.cat].filter(Boolean),
      desc: `${entry.desc} 专业模式保留中文、英文与 Sanskrit 名称，方便和 API、报告及古典术语交叉核对。`,
    };
  }
  if (mode === 'beginner') {
    return {
      title: entry.cn,
      names: [entry.en, '初学解释'].filter(Boolean),
      desc: modernizeGlossaryDescription(entry.desc),
    };
  }
  return {
    title: entry.cn,
    names: [entry.sk, entry.en].filter(Boolean),
    desc: entry.desc,
  };
}

function modernizeGlossaryDescription(text) {
  return String(text || '')
    .replace(/业力/g, '长期模式')
    .replace(/前世课题/g, '深层习惯与未完成议题')
    .replace(/凶宫/g, '压力宫')
    .replace(/致命/g, '高风险')
    .replace(/凶星/g, '压力星')
    .replace(/吉星/g, '支持星')
    .replace(/最黑暗处有最光明/g, '困难条件中可能出现反转机会');
}

function showTooltip(key) {
  const entry = G[key];
  if (!entry) return;
  const mode = getGlossaryTerminologyMode();
  const display = buildTerminologyDisplay(entry, mode);
  tooltipEl.dataset.termKey = key;
  tooltipEl.dataset.mode = mode;
  tooltipEl.querySelector('.jt-cat').textContent = `${CAT_MAP[entry.cat] || entry.cat} · ${TERMINOLOGY_MODE_LABELS[mode]}`;
  tooltipEl.querySelector('.jt-title').textContent = display.title;
  tooltipEl.querySelector('.jt-names').innerHTML = display.names.map((name, index) => (
    `<span class="${index === 0 ? 'jt-sk' : 'jt-en'}">${escapeHtml(String(name))}</span>`
  )).join('');
  tooltipEl.querySelector('.jt-desc').textContent = display.desc;
  tooltipEl.classList.remove('hidden');
}

function hideTooltip() {
  if (tooltipEl) {
    tooltipEl.classList.add('hidden');
    delete tooltipEl.dataset.termKey;
  }
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;',
  }[ch]));
}

// ===== 视觉标记：bindTerms 仍然用于添加高亮样式 =====
export function bindTerms(root) {
  if (!root) return;
  const selMap = [
    ['.planets-table td:first-child', mapPlanetTd],
    ['.planets-table td:nth-child(4)', mapHouseEl],
    ['.planets-table td:nth-child(5)', mapStatusTd],
    ['.planets-table td:nth-child(6)', () => 'Nakshatra'],
    ['.av-house-num', mapHouseEl], ['.hi-num', mapHouseEl],
    ['.hi-house', mapHouseEl], ['.house-card-num', mapHouseCard],
    ['.rg-num', mapHouseEl], ['.transit-house-badge', mapHouseEl],
    ['.sub-title', mapSubtitle], ['.section-title', mapSubtitle],
    ['.planet-symbol', mapPlanetSymbol],
    ['.k-label', mapKaraka], ['.k-planet', mapPlanetTd],
    ['.status-exalted', () => 'Exaltation'], ['.status-debilitated', () => 'Debilitation'],
    ['.status-own', () => 'OwnSign'],
    ['.yoga-name', () => 'Yoga'], ['.yoga-strength', () => 'Yoga'],
    ['.dasha-planet', mapPlanetText], ['.ad-planet', mapPlanetText],
    ['.praty-planet', mapPlanetText], ['.dasha-name', mapPlanetText],
    ['.av-planet', mapPlanetText],
    ['.transit-planet-name', mapTransitPlanetName],
    ['*', mapCombust],
  ];
  for (const [sel, fn] of selMap) {
    try {
      root.querySelectorAll(sel).forEach(el => {
        if (el.dataset.term) return;
        const key = fn(el);
        if (key) { el.dataset.term = key; el.classList.add('jt-clickable'); }
      });
    } catch(_) {}
  }
}

// ===== 映射辅助函数 =====
const PM = {'太阳':'Sun','月亮':'Moon','火星':'Mars','水星':'Mercury','木星':'Jupiter','金星':'Venus','土星':'Saturn','北交点':'Rahu','南交点':'Ketu'};
const PSM = {'☉':'Sun','☽':'Moon','♂':'Mars','☿':'Mercury','♃':'Jupiter','♀':'Venus','♄':'Saturn','☊':'Rahu','☋':'Ketu'};

function mapPlanetTd(el) {
  const t = el.textContent.trim();
  for (const [s,k] of Object.entries(PSM)) if (t.includes(s)) return k;
  for (const [c,k] of Object.entries(PM)) if (t.includes(c)) return k;
  for (const en of ['Jupiter','Mercury','Saturn','Venus','Mars','Moon','Sun','Rahu','Ketu'])
    if (t.includes(en)) return en;
  return null;
}
function mapPlanetText(el) {
  const t = el.textContent.trim().replace(' ◀','').replace(' ℞','');
  return PM[t] || (G[t] ? t : null);
}
function mapPlanetSymbol(el) { const t=el.textContent.trim(); return PSM[t]||PM[t]||null; }
function mapHouseEl(el) { const m=el.textContent.match(/H(\d+)/); return m?`H${m[1]}`:null; }
function mapHouseCard(el) { const m=el.textContent.match(/第(\d+)宫/); return m?`H${m[1]}`:null; }
function mapStatusTd(el) {
  const t=el.textContent.trim();
  if(t==='入旺')return'Exaltation';if(t==='落陷')return'Debilitation';if(t==='入庙')return'OwnSign';
  if(t.includes('逆行'))return'Retrograde';if(t.includes('燃烧')||t.includes('[燃]'))return'Combustion';return null;
}
function mapTransitPlanetName(el) {
  const t=el.textContent.trim().replace(' ℞','');
  for(const[c,k]of Object.entries(PM))if(t.includes(c))return k;
  for(const en of['Jupiter','Mercury','Saturn','Venus','Mars','Moon','Sun','Rahu','Ketu'])if(t.includes(en))return en;
  return null;
}
function mapSubtitle(el) {
  const t=el.textContent;
  const m=[['Ashtakavarga','Ashtakavarga'],['Shadbala','Shadbala'],['Nakshatra','Nakshatra'],['Vargottama','Vargottama'],
    ['PACDARES','PACDARES'],['Karaka','Karaka'],['Arudha','Arudha'],['Panchanga','Panchanga'],['Sade Sati','SadeSati'],
    ['Double Transit','DoubleTransit'],['Graha Drishti','GrahaDrishti'],['Transit','Transit'],['Dasha','Dasha'],
    ['Navamsa','Navamsa'],['Dasamsa','Dasamsa'],['Yogakaraka','Yogakaraka'],['Vimsopaka','Vimsopaka'],['Avastha','Avastha'],
    ['Bhava Bala','BhavaBala'],['Raman','Raman'],['Maraka','Maraka'],['分盘','Varga'],['大运','Dasha'],
    ['相位','GrahaDrishti'],['Yoga','Yoga'],['SAV','SAV'],['Ayanamsa','Ayanamsa'],
    ['星座','Rashi'],['八维','PACDARES'],['六维','Shadbala'],['八分法','Ashtakavarga'],
    ['月相','Tithi'],['月相期','Paksha'],['星期','Vara'],['五要素','Panchanga'],
    ['上升','Lagna'],['命度','Lagna'],['角宫','Kendra'],['三合宫','Trikona'],['凶宫','Dusthana'],
    ['王者格局','RajaYoga'],['财富格局','DhanaYoga'],['命主星','Lagnesha'],
    ['功能吉星','FunctionalBenefic'],['功能凶星','FunctionalMalefic']];
  for(const[p,k]of m)if(t.includes(p))return k;
  return null;
}
function mapKaraka() { return 'Karaka'; }
function mapCombust(el) {
  if(el.textContent.includes('[燃]')){el.dataset.term='Combustion';el.classList.add('jt-clickable');}
  return null;
}
