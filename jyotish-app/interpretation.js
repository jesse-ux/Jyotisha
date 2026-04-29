/**
 * Jyotish 解读文本数据层
 * 从 Skill 知识库移植的结构化中文解读数据
 */

// ============================================================================
// 宫位解读
// ============================================================================
export const HOUSE_MEANINGS = {
  1: { name: '自我宫', sanskrit: 'Lagna', themes: '外貌、性格、体质、生命力、自我认知', karaka: '太阳',
    strong: '强健体质、自我意识明确、领导气质、人生方向清晰',
    weak: '体质较弱、自我认知模糊、缺乏方向感、易受他人影响',
    lordInHouse: {
      1: '强健体质，自我意识强，人生方向明确',
      2: '财富靠自身努力，家庭意识强，口才佳',
      3: '沟通能力强，勇于冒险，兄弟姐妹缘好',
      4: '家庭幸福，内心平静，有房产运',
      5: '聪明有才，子女缘好，创造力强',
      6: '健康挑战，但有克服困难的毅力，善于服务',
      7: '婚姻重要，合伙运好，需注意自我妥协',
      8: '神秘色彩，有深层洞察力，经历重大转化',
      9: '幸运，有信仰追求，父亲关系重要',
      10: '事业成就突出，社会声誉好',
      11: '愿望易实现，财运好，人脉广',
      12: '灵性倾向，可能在外国生活，需注意损耗',
    }
  },
  2: { name: '财富宫', sanskrit: 'Dhana Bhava', themes: '积蓄、家族、语言、饮食、面部', karaka: '木星',
    strong: '财富积累能力强、口才好、家庭背景好',
    weak: '财务管理困难、言辞不当、家庭关系紧张',
  },
  3: { name: '兄弟宫', sanskrit: 'Sahaja Bhava', themes: '兄弟姐妹、勇气、短途旅行、沟通、写作', karaka: '火星',
    strong: '沟通能力强、勇气十足、兄弟姐妹关系好、写作天赋',
    weak: '表达困难、缺乏勇气、手足不和',
  },
  4: { name: '幸福宫', sanskrit: 'Sukha Bhava', themes: '母亲、家庭、房产、教育基础、内心平静', karaka: '月亮',
    strong: '家庭幸福、房产运好、与母亲关系亲密、内心安定',
    weak: '家庭不安、房产困难、与母亲关系复杂',
  },
  5: { name: '子女宫', sanskrit: 'Putra Bhava', themes: '子女、智慧、创造力、恋爱、投机、过去世积德', karaka: '木星',
    strong: '子女缘好、创造力旺盛、恋爱运佳、投机直觉准',
    weak: '子女缘弱、创造力受限、恋爱不顺',
  },
  6: { name: '敌人宫', sanskrit: 'Ripu Bhava', themes: '健康、债务、敌人、服务、诉讼', karaka: '火星/土星',
    strong: '战胜疾病和敌人能力强、竞争力强、服务精神好',
    weak: '健康挑战、债务压力、敌人多',
  },
  7: { name: '婚姻宫', sanskrit: 'Kalatra Bhava', themes: '配偶、婚姻、合伙、外交、商业伙伴', karaka: '金星/木星',
    strong: '婚姻美满、合伙成功、社交能力强',
    weak: '婚姻延迟或不顺、合伙有分歧、社交困难',
  },
  8: { name: '转化宫', sanskrit: 'Randhra Bhava', themes: '寿命、转化、神秘学、配偶财产、慢性病', karaka: '土星',
    strong: '有神秘学才能、能从危机中再生、配偶财运好',
    weak: '健康隐患、财务风险、心理压力大',
  },
  9: { name: '命运宫', sanskrit: 'Dharma Bhava', themes: '父亲、宗教、哲学、命运、长途旅行、导师', karaka: '木星/太阳',
    strong: '命运顺遂、信仰坚定、父亲关系好、导师运佳',
    weak: '信仰缺失、父亲关系紧张、远行不顺',
  },
  10: { name: '事业宫', sanskrit: 'Karma Bhava', themes: '职业、社会地位、权威、政府、成就', karaka: '太阳/土星/木星/火星',
    strong: '事业成就高、社会地位好、领导力强',
    weak: '职业发展受阻、社会地位不高、缺乏权威',
  },
  11: { name: '收益宫', sanskrit: 'Labha Bhava', themes: '收入、愿望实现、朋友、社交圈', karaka: '木星',
    strong: '愿望易实现、财运好、社交圈广、朋友支持',
    weak: '收入不稳、愿望难达成、社交受限',
  },
  12: { name: '损耗宫', sanskrit: 'Vyaya Bhava', themes: '支出、隐居、外国、灵性、睡眠、秘密', karaka: '土星/Ketu',
    strong: '灵性倾向、可能在海外发展、直觉能力强',
    weak: '支出过大、睡眠问题、内心不安',
  },
};

// ============================================================================
// 行星在宫位的现代解读（精简版，每宫一句核心描述）
// ============================================================================
export const PLANET_IN_HOUSE = {
  Sun: {
    1: '个人品牌强、领导力出众、自信外向', 2: '政府相关收入、管理职位、家庭地位高', 3: '社交媒体影响力、沟通有力、兄弟姐妹有地位',
    4: '家庭地位高、父亲影响强、房产运好', 5: '子女优秀、创造力旺盛、投资眼光好', 6: '服务领导力、健康管理强、能战胜对手',
    7: '配偶有地位、婚姻有社会影响力', 8: '配偶财运好、危机中展现领导力', 9: '高等教育成功、父亲有地位、导师运佳',
    10: '事业巅峰、社会地位高、领导力被认可', 11: '社交圈有影响力、愿望实现、收入丰厚', 12: '灵性追求、海外发展、内在领导力',
  },
  Moon: {
    1: '情感丰富、直觉敏锐、有公众魅力', 2: '家庭理财好、情感消费、饮食相关收入', 3: '情感沟通、写作天赋、情感类短途旅行',
    4: '母亲影响强、家庭温馨、房产情感价值高', 5: '子女情感丰富、情感创作、浪漫恋爱', 6: '心理健康关注、情感服务、情绪健康管理',
    7: '配偶情感丰富、情感婚姻、社交有共鸣', 8: '情感深度洞察、心理研究、潜意识探索', 9: '情感教育、长途旅行、信仰中的情感',
    10: '公众情感事业、被大众喜爱、情感领导力', 11: '情感社交、朋友缘好、情感收入', 12: '潜意识探索、梦境分析、灵性冥想',
  },
  Mars: {
    1: '行动力强、健身达人、竞争意识强', 2: '技术收入、体育收入、创业收入', 3: '竞争性沟通、辩论高手、极限运动',
    4: '家庭竞争、房产争议、家庭创业', 5: '竞争性创作、激情恋爱、风险投资', 6: '运动健康、战胜疾病和对手、执行力强',
    7: '配偶活跃、激情婚姻、需注意冲突', 8: '风险投资、外科手术相关、危机中的战士', 9: '冒险旅行、竞争教育、体能挑战',
    10: '竞争事业、冒险创业、竞争领导力', 11: '竞争社交、风险收入、行动实现愿望', 12: '隐秘行动、远程合作、内在战斗',
  },
  Mercury: {
    1: '沟通能力强、聪明灵活、学习力强', 2: '知识付费收入、写作收入、商业收入', 3: '写作天赋、社交达人、多语言学习',
    4: '家庭沟通、家庭办公室、房产交易', 5: '智力创作、聪明子女、分析型投资', 6: '健康知识、沟通工作、数据服务',
    7: '配偶聪明、沟通婚姻、智力合作', 8: '数据分析、网络安全研究、隐秘沟通', 9: '智力教育、知识旅行、学术研究',
    10: '沟通事业、知识创业、技术领导力', 11: '智力社交、知识收入、技术社交网络', 12: '深度研究、隐秘写作、灵性学习',
  },
  Jupiter: {
    1: '教育家气质、导师风范、智慧外显', 2: '教育收入、投资收益、跨国收入', 3: '知识分享、教育沟通、学习型旅行',
    4: '家庭幸福、房产增值、家庭教育', 5: '子女优秀、教育创作、投资收益', 6: '教育服务、健康管理、债务管理',
    7: '配偶优秀、幸福婚姻、教育合作', 8: '配偶财运好、投资收益、深层智慧', 9: '教育成功、国际教育、灵性导师',
    10: '教育事业、知识领导力、社会尊敬', 11: '教育社交、知识愿望、投资收入', 12: '灵性投资、国际研究院、跨国研究',
  },
  Venus: {
    1: '审美能力强、社交魅力、艺术气质', 2: '艺术收入、美学收入、婚姻收入', 3: '美学沟通、艺术写作、浪漫旅行',
    4: '家居美学、家庭艺术、房产美学价值', 5: '艺术创作、浪漫恋爱、美学投资', 6: '美学服务、美学健康、美学工作',
    7: '配偶有艺术天赋、浪漫婚姻、美学合作', 8: '配偶美学财富、美学投资、深层情感', 9: '美学教育、美学旅行、美学导师',
    10: '艺术事业、美学领导力、审美事业', 11: '美学社交、美学愿望、艺术收入', 12: '国际艺术、在线创作、美学疗愈',
  },
  Saturn: {
    1: '责任感强、长期主义、成熟稳重', 2: '稳定收入、长期投资、延迟满足', 3: '专业沟通、技术写作、工作出差',
    4: '家庭责任、房产延迟但持久、家庭压力', 5: '子女延迟、责任创作、成熟恋爱', 6: '责任服务、长期健康、慢性病管理',
    7: '配偶成熟、稳定婚姻、长期合作', 8: '稳定投资、长期危机、慢性研究', 9: '长期教育、长期旅行、成熟导师',
    10: '长期事业、稳定地位、结构化领导力', 11: '长期朋友、长期愿望、稳定收入', 12: '长期灵性、隐秘工作、内在纪律',
  },
  Rahu: {
    1: '非传统路径、跨界创新、科技创业者', 2: '非传统收入、科技收入、网红收入', 3: '非传统沟通、匿名社交、跨界学习',
    4: '非传统家庭、海外房产、家庭变革', 5: '非传统创作、非传统恋爱、科技投资', 6: '非传统服务、非传统健康、科技工作',
    7: '非传统婚姻、跨文化伴侣、非传统合作', 8: '科技投资、非传统危机、深度研究', 9: '非传统教育、非传统旅行、非传统导师',
    10: '科技事业、非传统领导力、突破性职业', 11: '非传统社交、科技社交、突破性收入', 12: '非传统灵性、海外非传统成就',
  },
  Ketu: {
    1: '灵性追求者、深度工作者、内在探索', 2: '灵性收入、研究收入、隐秘收入', 3: '深度沟通、研究性写作、灵性旅行',
    4: '家庭灵性、家庭隐居、深度房产', 5: '灵性创作、灵性恋爱、深度投资', 6: '灵性服务、灵性健康、深度工作',
    7: '灵性婚姻、深度合作、灵魂伴侣', 8: '灵性投资、灵性危机、最深研究', 9: '灵性教育、灵性旅行、灵性导师',
    10: '灵性事业、深度事业、内在领导力', 11: '灵性社交、灵性愿望、灵性收入', 12: '灵性解脱、深度隐居、终极灵性',
  },
};

// ============================================================================
// Nakshatra 深度解读（精简版）
// ============================================================================
export const NAKSHATRA_DATA = [
  { name: 'Ashwini', keywords: '速度、治疗、先锋、独立行动', career: '医疗急救、创业、体育、科技', relationship: '追求独立型伴侣，需要个人空间', gana: 'Deva', nadi: 'Aadi' },
  { name: 'Bharani', keywords: '转化、承受力、极端、重生', career: '法律、医疗、心理、危机管理', relationship: '深层情感连接，需要经历考验', gana: 'Manushya', nadi: 'Madhya' },
  { name: 'Krittika', keywords: '切割、净化、批评、精确', career: '餐饮、医疗外科、编辑出版、品控', relationship: '直接坦率，需学会柔和表达', gana: 'Rakshasa', nadi: 'Antya' },
  { name: 'Rohini', keywords: '创造、丰饶、美、物质享受', career: '艺术、设计、房地产、时尚、音乐', relationship: '重视物质舒适，忠诚但占有欲强', gana: 'Manushya', nadi: 'Aadi' },
  { name: 'Mrigashira', keywords: '搜索、好奇、温柔、追寻', career: '研究、调查、写作、旅行、教育', relationship: '追寻理想伴侣，容易不满', gana: 'Deva', nadi: 'Madhya' },
  { name: 'Ardra', keywords: '风暴、净化、转化、重建', career: '工程、IT、社会改革、医疗', relationship: '情绪波动大，关系中有风暴周期', gana: 'Manushya', nadi: 'Antya' },
  { name: 'Punarvasu', keywords: '回归、重建、哲学、乐观', career: '教育、法律、外交、咨询', relationship: '乐观包容，有回归和重修旧好的倾向', gana: 'Deva', nadi: 'Aadi' },
  { name: 'Pushya', keywords: '滋养、教导、传统、繁荣', career: '教育、宗教、社区管理、护理', relationship: '滋养型伴侣，重视家庭和传统', gana: 'Deva', nadi: 'Madhya' },
  { name: 'Ashlesha', keywords: '洞察、秘密、直觉、催眠', career: '心理学、情报、研究、医学', relationship: '深层洞察伴侣，有掌控欲', gana: 'Rakshasa', nadi: 'Antya' },
  { name: 'Magha', keywords: '皇权、传承、祖先、领导力', career: '管理、政治、政府、传承产业', relationship: '重视家族地位，伴侣需有尊严', gana: 'Rakshasa', nadi: 'Aadi' },
  { name: 'Purva Phalguni', keywords: '享乐、浪漫、创造性、社交', career: '娱乐、艺术、时尚、酒店、公关', relationship: '浪漫至上，享受恋爱，可能回避深层承诺', gana: 'Manushya', nadi: 'Madhya' },
  { name: 'Uttara Phalguni', keywords: '承诺、友谊、服务、持久', career: '服务行业、医疗、法律、教育', relationship: '重视承诺和长期友谊，忠诚可靠', gana: 'Manushya', nadi: 'Antya' },
  { name: 'Hasta', keywords: '手艺、技巧、治愈、勤劳', career: '手工艺、医疗、写作、会计', relationship: '务实可靠，通过实际行动表达爱', gana: 'Deva', nadi: 'Aadi' },
  { name: 'Chitra', keywords: '设计、建筑、视觉美、独特', career: '建筑、设计、珠宝、摄影、电影', relationship: '被美和独特性吸引，重视伴侣品味', gana: 'Rakshasa', nadi: 'Madhya' },
  { name: 'Swati', keywords: '独立、自由、贸易、外交', career: '贸易、外交、咨询、航空、独立创业', relationship: '极度重视自由，关系中需要空间', gana: 'Deva', nadi: 'Antya' },
  { name: 'Vishakha', keywords: '目标导向、双面性、决心', career: '军事、法律、宗教、企业战略', relationship: '有双重社交面孔，关系中有隐藏面', gana: 'Rakshasa', nadi: 'Aadi' },
  { name: 'Anuradha', keywords: '友谊、合作、探索、纪律下的温暖', career: '国际合作、外交、科学、军事', relationship: '善于建立深层友谊，从友情发展为爱情', gana: 'Deva', nadi: 'Madhya' },
  { name: 'Jyeshtha', keywords: '权威、保护、孤独、隐忍', career: '管理、法律、安保、政府、学术研究', relationship: '保护型伴侣，内心孤独，不轻易展现脆弱', gana: 'Rakshasa', nadi: 'Antya' },
  { name: 'Mula', keywords: '根基、破坏、转化、深层探索', career: '医学研究、考古、心理学、哲学', relationship: '深层连接，破坏-重建的循环', gana: 'Rakshasa', nadi: 'Aadi' },
  { name: 'Purva Ashadha', keywords: '不可战胜、净化、旅程、壮丽', career: '军事、体育、水利、旅行、艺术', relationship: '充满激情，追求壮丽感，不喜欢平淡', gana: 'Manushya', nadi: 'Madhya' },
  { name: 'Uttara Ashadha', keywords: '最终胜利、领导、承诺、正直', career: '管理、政府、法律、教育、军事', relationship: '正直忠诚，追求共同成长和道德一致', gana: 'Manushya', nadi: 'Antya' },
  { name: 'Shravana', keywords: '聆听、学习、名声、传统', career: '教育、翻译、咨询、媒体、学术', relationship: '善于倾听，通过语言和沟通建立连接', gana: 'Deva', nadi: 'Aadi' },
  { name: 'Dhanishta', keywords: '音乐、节奏、财富、群体', career: '音乐、金融、社群管理、表演', relationship: '重视群体和谐，需要节奏感和同步', gana: 'Rakshasa', nadi: 'Madhya' },
  { name: 'Shatabhisha', keywords: '秘密、治疗、独立、探索未知', career: '科技、医疗、天文学、占星学、网络安全', relationship: '重视隐私和独立，需深层理解', gana: 'Rakshasa', nadi: 'Antya' },
  { name: 'Purva Bhadrapada', keywords: '转化之火、苦行、极端、灵性战士', career: '宗教、灵修、极限运动、心理咨询', relationship: '极端化倾向——极度投入或彻底放手', gana: 'Manushya', nadi: 'Aadi' },
  { name: 'Uttara Bhadrapada', keywords: '深度、耐心、智慧、守护', career: '深度研究、灵修、管理、心理学', relationship: '深层忠诚，需要耐心和理解', gana: 'Manushya', nadi: 'Madhya' },
  { name: 'Revati', keywords: '旅程完成、守护、丰饶、道路指引', career: '旅行、物流、护理、教育、慈善', relationship: '守护型伴侣，关系中有圆满感', gana: 'Deva', nadi: 'Antya' },
];

// ============================================================================
// Yoga 扩展检测库
// ============================================================================
export const YOGA_DEFINITIONS = [
  // Moon-based Yogas
  { id: 'sunapha', name: 'Sunapha Yoga', name_cn: '自立格局', check: (p, asc) => {
    const moon = p.Moon; if (!moon) return null;
    const h2fromMoon = ((moon.house + 1) % 12) + 1;
    const planets2 = Object.entries(p).filter(([k,v]) => k !== 'Sun' && k !== 'Moon' && v.house === h2fromMoon);
    if (planets2.length > 0) return `月亮后第2宫有${planets2.map(([k]) => k).join('+')}`;
    return null;
  }, effects: '自力更生，凭自身努力获得成功', strength: '中' },

  { id: 'anapha', name: 'Anapha Yoga', name_cn: '魅力格局', check: (p, asc) => {
    const moon = p.Moon; if (!moon) return null;
    const h12fromMoon = ((moon.house + 11) % 12) + 1;
    const planets12 = Object.entries(p).filter(([k,v]) => k !== 'Sun' && k !== 'Moon' && v.house === h12fromMoon);
    if (planets12.length > 0) return `月亮后第12宫有${planets12.map(([k]) => k).join('+')}`;
    return null;
  }, effects: '有魅力、受人支持、幸运', strength: '中' },

  { id: 'durudhara', name: 'Durudhara Yoga', name_cn: '双围格局', check: (p, asc) => {
    const moon = p.Moon; if (!moon) return null;
    const h2 = ((moon.house + 1) % 12) + 1, h12 = ((moon.house + 11) % 12) + 1;
    const p2 = Object.entries(p).filter(([k,v]) => k !== 'Sun' && k !== 'Moon' && v.house === h2);
    const p12 = Object.entries(p).filter(([k,v]) => k !== 'Sun' && k !== 'Moon' && v.house === h12);
    if (p2.length > 0 && p12.length > 0) return `月亮两侧都有行星(${p2.map(([k])=>k).join(',')} | ${p12.map(([k])=>k).join(',')})`;
    return null;
  }, effects: '富有、有权势、有影响力', strength: '中强' },

  { id: 'kemadruma', name: 'Kemadruma Yoga', name_cn: '月亮孤立格局', check: (p, asc) => {
    const moon = p.Moon; if (!moon) return null;
    const h2 = ((moon.house + 1) % 12) + 1, h12 = ((moon.house + 11) % 12) + 1;
    const p2 = Object.entries(p).filter(([k,v]) => k !== 'Moon' && v.house === h2);
    const p12 = Object.entries(p).filter(([k,v]) => k !== 'Moon' && v.house === h12);
    if (p2.length === 0 && p12.length === 0) return '月亮前后两宫均无行星';
    return null;
  }, effects: '情感不安全感、孤立、早年奋斗', strength: '负面', negative: true },

  // Special Combination Yogas
  { id: 'budhaditya', name: 'Budhaditya Yoga', name_cn: '智阳格局', check: (p, asc) => {
    if (!p.Mercury || !p.Sun) return null;
    if (p.Mercury.house === p.Sun.house && Math.abs(p.Mercury.degree - p.Sun.degree) > 14) return '水星+太阳同宫且未燃烧';
    return null;
  }, effects: '智慧口才、写作能力、分析头脑', strength: '中' },

  { id: 'chandra_mangala', name: 'Chandra-Mangala Yoga', name_cn: '月火格局', check: (p, asc) => {
    if (!p.Moon || !p.Mars) return null;
    if (p.Moon.house === p.Mars.house) return '月亮+火星同宫';
    return null;
  }, effects: '财运强（但情感波动）、执行力强', strength: '中' },

  { id: 'guru_shukra', name: 'Guru-Shukra Yoga', name_cn: '木金格局', check: (p, asc) => {
    if (!p.Jupiter || !p.Venus) return null;
    if (p.Jupiter.house === p.Venus.house) return '木星+金星同宫';
    return null;
  }, effects: '财富、奢侈品、灵性智慧、艺术天赋', strength: '中强' },

  { id: 'guru_chandala', name: 'Guru-Chandala Yoga', name_cn: '木罗格局', check: (p, asc) => {
    if (!p.Jupiter || !p.Rahu) return null;
    if (p.Jupiter.house === p.Rahu.house) return '木星+Rahu同宫';
    return null;
  }, effects: '灵性挑战、非传统信仰、需注意道德边界', strength: '负面', negative: true },

  // Mangal Dosha
  { id: 'mangal_dosha', name: 'Mangal Dosha', name_cn: '火星煞', check: (p, asc) => {
    const mars = p.Mars; if (!mars) return null;
    if ([1, 2, 4, 7, 8, 12].includes(mars.house)) {
      // Check cancellation
      if (mars.status === '入庙' || mars.status === '入旺') return null;
      if (p.Jupiter && p.Jupiter.house === mars.house) return null;
      return `火星在第${mars.house}宫`;
    }
    return null;
  }, effects: '婚姻延迟或不顺、需注意配偶健康', strength: '负面', negative: true },

  // Kaal Sarpa Yoga
  { id: 'kaal_sarpa', name: 'Kaal Sarpa Yoga', name_cn: '蛇煞格局', check: (p, asc) => {
    if (!p.Rahu || !p.Ketu) return null;
    const rahuHouse = p.Rahu.house, ketuHouse = p.Ketu.house;
    const allBetween = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn'].every(name => {
      const h = p[name]?.house;
      if (!h) return true;
      const min = Math.min(rahuHouse, ketuHouse);
      const max = Math.max(rahuHouse, ketuHouse);
      return h >= min && h <= max;
    });
    if (allBetween) return `所有行星在Rahu(第${rahuHouse}宫)与Ketu(第${ketuHouse}宫)之间`;
    return null;
  }, effects: '业力挑战、祖辈模式、人生奋斗（但灵性潜力大）', strength: '负面', negative: true },

  // Lakshmi Yoga (5th + 9th lord connection)
  { id: 'lakshmi', name: 'Lakshmi Yoga', name_cn: '幸运女神格局', check: (p, asc) => {
    const ai = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'].indexOf(asc);
    const l5 = { Aries:'Leo', Taurus:'Virgo', Gemini:'Libra', Cancer:'Scorpio', Leo:'Sagittarius', Virgo:'Capricorn', Libra:'Aquarius', Scorpio:'Pisces', Sagittarius:'Aries', Capricorn:'Taurus', Aquarius:'Gemini', Pisces:'Cancer' };
    const l9 = { Aries:'Sagittarius', Taurus:'Capricorn', Gemini:'Aquarius', Cancer:'Pisces', Leo:'Aries', Virgo:'Taurus', Libra:'Gemini', Scorpio:'Cancer', Sagittarius:'Leo', Capricorn:'Virgo', Aquarius:'Libra', Pisces:'Scorpio' };
    const signs = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces'];
    const signIdx = (s) => signs.indexOf(s);
    const lordOf5 = { Aries:'Mars', Taurus:'Venus', Gemini:'Mercury', Cancer:'Moon', Leo:'Sun', Virgo:'Mercury', Libra:'Venus', Scorpio:'Mars', Sagittarius:'Jupiter', Capricorn:'Saturn', Aquarius:'Saturn', Pisces:'Jupiter' };
    const sign5 = signs[(ai + 4) % 12];
    const sign9 = signs[(ai + 8) % 12];
    const lord5 = lordOf5[sign5];
    const lord9 = lordOf5[sign9];
    if (lord5 !== lord9 && p[lord5] && p[lord9] && p[lord5].house === p[lord9].house) {
      return `5宫主(${lord5})+9宫主(${lord9})同宫`;
    }
    return null;
  }, effects: '好运连连、灵性财富、人生祝福', strength: '强' },
];

// ============================================================================
// 行星相位的中文描述
// ============================================================================
export const ASPECT_DESC = {
  '7': '对冲相位（第7宫）：直接影响力，带来对立面的能量',
  '5_Jupiter': '木星三分相位（第5/9宫）：智慧祝福、扩张性的正面影响',
  '9_Jupiter': '木星三分相位（第5/9宫）：智慧祝福、扩张性的正面影响',
  '3_Saturn': '土星特殊相位（第3/10宫）：结构性压力、持久性考验',
  '10_Saturn': '土星特殊相位（第3/10宫）：结构性压力、持久性考验',
  '4_Mars': '火星特殊相位（第4/8宫）：行动冲击、保护性或破坏性能量',
  '8_Mars': '火星特殊相位（第4/8宫）：行动冲击、保护性或破坏性能量',
};

// ============================================================================
// 宫位分组
// ============================================================================
export const HOUSE_GROUPS = {
  kendra: { name: '角宫 (Kendra)', houses: [1, 4, 7, 10], desc: '最强宫位，行星在此力量增强' },
  trikona: { name: '三角宫 (Trikona)', houses: [1, 5, 9], desc: '最吉祥的宫位，带来祝福' },
  upachaya: { name: '上升宫 (Upachaya)', houses: [3, 6, 10, 11], desc: '随时间增强的宫位' },
  dusthana: { name: '凶宫 (Dusthana)', houses: [6, 8, 12], desc: '挑战宫位，但也包含成长种子' },
  maraka: { name: '死亡指示宫 (Maraka)', houses: [2, 7], desc: '2宫主和7宫主是Maraka行星' },
};

// ============================================================================
// Transit 行星过境影响速查
// ============================================================================
export const TRANSIT_EFFECTS = {
  Saturn: {
    1: '个人压力与转化期，关注健康', 2: '财务压力、家庭矛盾', 3: '勇气增长、短途旅行增多',
    4: '家庭不安、房产问题、母亲健康', 5: '子女挑战、创造力受限', 6: '战胜敌人、健康改善（6宫好）',
    7: '婚姻压力、合作考验', 8: '慢性疾病、深层转化（Ashtama Shani）', 9: '信仰考验、远行受阻',
    10: '事业阻碍、上级冲突（Kantaka Shani）', 11: '社交重组、收入稳定化', 12: '灵性觉醒、支出增加（Sade Sati起始）',
  },
  Jupiter: {
    1: '自我提升、贵人运、健康改善', 2: '财务增长、家庭和谐', 3: '沟通提升、短途旅行顺利',
    4: '家庭幸福、房产运好', 5: '子女喜讯、创造力爆发、投资收益', 6: '健康改善、战胜困难',
    7: '婚姻机遇、合作顺利', 8: '深层转化、配偶财运好', 9: '贵人相助、出国运、信仰转变',
    10: '事业突破、社会地位提升', 11: '愿望实现、社交扩张、收入增长', 12: '灵性成长、海外机遇',
  },
  Rahu: {
    1: '自我形象重塑、非传统路径', 2: '非传统收入、家庭变革', 3: '沟通创新、非传统学习',
    4: '家庭变革、非传统居住', 5: '创新创作、非传统恋爱', 6: '非传统服务、科技工作',
    7: '跨文化伴侣、非传统婚姻', 8: '深层欲望、隐秘研究', 9: '非传统信仰、海外探索',
    10: '科技事业、突破性职业', 11: '非传统社交、网络收入', 12: '灵性突破、海外隐居',
  },
  Ketu: {
    1: '灵性觉醒、内在探索', 2: '财务分离、价值观转变', 3: '深度沟通、灵性学习',
    4: '家庭简化、内在安宁', 5: '创作分离、灵性恋爱', 6: '健康解放、服务简化',
    7: '灵性伴侣、关系简化', 8: '深层解脱、秘密揭露', 9: '灵性旅行、信仰深化',
    10: '事业转型、内在领导力', 11: '愿望净化、社交简化', 12: '灵性解脱、终极自由',
  },
};
