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
  { name:'Ashwini', symbol:'马头', deity:'Ashwini双生子（天界神医）', lord:'Ketu', animal:'公马',
    keywords:'速度、治疗、先锋、独立行动、快速启动',
    career:'医疗急救、创业、体育、交通运输、新兴科技',
    relationship:'追求独立型伴侣，关系需要个人空间，不喜欢被束缚',
    modernMapping:'急诊医生、创业者、急救志愿者、赛车手、科技创新者',
    gana:'Deva', nadi:'Aadi' },
  { name:'Bharani', symbol:'女性生殖器（Yoni）', deity:'Yama（死神/审判之神）', lord:'Venus', animal:'大象',
    keywords:'转化、承受力、极端、重生、纪律',
    career:'法律、医疗、心理、危机管理、艺术创作',
    relationship:'深层情感连接，关系中的转化力量，需要经历考验',
    modernMapping:'心理咨询师、法官、殡葬行业、转型顾问、高强度训练师',
    gana:'Manushya', nadi:'Madhya' },
  { name:'Krittika', symbol:'剃刀/火焰', deity:'Agni（火神）', lord:'Sun', animal:'羊',
    keywords:'切割、净化、批评、烹饪、精确',
    career:'餐饮、医疗外科、编辑出版、质量管理、军工',
    relationship:'直接坦率，有时过于尖锐，需要学会柔和表达',
    modernMapping:'美食博主、外科医生、编辑/审稿人、品控专家、厨师',
    gana:'Rakshasa', nadi:'Antya' },
  { name:'Rohini', symbol:'牛车/战车', deity:'Brahma（创造之神）', lord:'Moon', animal:'蛇',
    keywords:'创造、丰饶、美、物质享受、艺术',
    career:'艺术、设计、房地产、农业、时尚、音乐',
    relationship:'重视物质舒适和感官享受，忠诚但占有欲强',
    modernMapping:'艺术家、设计师、房地产开发商、农业企业家、奢侈品行业',
    gana:'Manushya', nadi:'Aadi' },
  { name:'Mrigashira', symbol:'鹿头', deity:'Soma（月神/甘露之神）', lord:'Mars', animal:'蛇',
    keywords:'搜索、好奇、温柔、追寻、灵巧',
    career:'研究、调查、写作、旅行、教育、设计',
    relationship:'追寻理想伴侣，容易不满、总是寻找更好的',
    modernMapping:'研究员、调查记者、侦探、探险家、搜索引擎工程师',
    gana:'Deva', nadi:'Madhya' },
  { name:'Ardra', symbol:'泪滴/钻石', deity:'Rudra（暴风雨之神）', lord:'Rahu', animal:'狗',
    keywords:'风暴、净化、转化、情绪、破坏后重建',
    career:'工程、IT、研究、社会改革、医疗、物理学',
    relationship:'情绪波动大，关系中有强烈的风暴和重建周期',
    modernMapping:'危机公关、气象学家、社会活动家、改革者、灾难救援',
    gana:'Manushya', nadi:'Antya' },
  { name:'Punarvasu', symbol:'弓箭/箭袋', deity:'Aditi（宇宙之母）', lord:'Jupiter', animal:'猫',
    keywords:'回归、重建、哲学、乐观、无限可能',
    career:'教育、法律、宗教、旅行、外交、咨询',
    relationship:'乐观包容，关系中有回归和重修旧好的倾向',
    modernMapping:'哲学教授、NGO创始人、重启型创业者、国际关系、外交官',
    gana:'Deva', nadi:'Aadi' },
  { name:'Pushya', symbol:'牛乳房/箭头', deity:'Brihaspati（祭司之神）', lord:'Saturn', animal:'羊',
    keywords:'滋养、教导、传统、繁荣、宗教',
    career:'教育、宗教、社区管理、餐饮、护理、行政管理',
    relationship:'滋养型伴侣，重视家庭和传统，可能过于保护',
    modernMapping:'教师、导师、营养师、社区领袖、家庭教育专家',
    gana:'Deva', nadi:'Madhya' },
  { name:'Ashlesha', symbol:'蛇盘绕', deity:'Nagas（蛇神）', lord:'Mercury', animal:'猫',
    keywords:'洞察、秘密、直觉、缠绕、催眠',
    career:'心理学、情报、研究、医学、化学、法律',
    relationship:'深层洞察伴侣，有掌控欲，关系中有深层心理博弈',
    modernMapping:'心理学家、催眠师、间谍、密码学家、深度调查记者',
    gana:'Rakshasa', nadi:'Antya' },
  { name:'Magha', symbol:'王座/宫殿', deity:'Pitris（祖先之灵）', lord:'Ketu', animal:'雄鼠',
    keywords:'皇权、传承、祖先、领导力、尊严',
    career:'管理、政治、政府、传承产业、奢侈品、高端服务',
    relationship:'重视家族和社会地位，伴侣需要有尊严和荣誉感',
    modernMapping:'企业继承人、政治家、CEO、传统文化传承人、贵族学校校长',
    gana:'Rakshasa', nadi:'Aadi' },
  { name:'Purva Phalguni', symbol:'吊床/前腿床', deity:'Bhaga（命运之神/快乐之神）', lord:'Venus', animal:'雌鼠',
    keywords:'享乐、浪漫、创造性、慵懒、社交',
    career:'娱乐、艺术、时尚、酒店、公关、婚礼产业',
    relationship:'浪漫至上，享受恋爱的过程，可能回避深层承诺',
    modernMapping:'社交名流、娱乐产业、婚礼策划、度假村老板、网红',
    gana:'Manushya', nadi:'Madhya' },
  { name:'Uttara Phalguni', symbol:'后腿床', deity:'Aryaman（友谊之神）', lord:'Sun', animal:'牛',
    keywords:'承诺、友谊、服务、助人、持久',
    career:'服务行业、医疗、法律、教育、慈善、社会工作',
    relationship:'重视承诺和长期友谊，忠诚可靠，但可能过于自我牺牲',
    modernMapping:'社工、志愿者组织者、长期护理、婚姻顾问、公益律师',
    gana:'Manushya', nadi:'Antya' },
  { name:'Hasta', symbol:'手掌/拳头', deity:'Savitar（太阳神/创造力之神）', lord:'Moon', animal:'水牛',
    keywords:'手艺、技巧、治愈、勤劳、掌控',
    career:'手工艺、医疗、按摩、写作、会计、魔术',
    relationship:'务实可靠，通过实际行动表达爱意',
    modernMapping:'手工艺人、外科医生、按摩师、程序员、魔术师',
    gana:'Deva', nadi:'Aadi' },
  { name:'Chitra', symbol:'宝石/珍珠', deity:'Vishwakarma（宇宙建筑师）', lord:'Mars', animal:'虎',
    keywords:'设计、建筑、视觉美、创造力、独特',
    career:'建筑、设计、珠宝、摄影、电影、艺术',
    relationship:'被美和独特性吸引，重视伴侣的外表和品味',
    modernMapping:'建筑师、珠宝设计师、UI/UX设计师、电影导演、摄影师',
    gana:'Rakshasa', nadi:'Madhya' },
  { name:'Swati', symbol:'嫩芽/珊瑚', deity:'Vayu（风神）', lord:'Rahu', animal:'公牛',
    keywords:'独立、自由、贸易、外交、自我成长',
    career:'贸易、外交、咨询、航空、物流、独立创业',
    relationship:'极度重视个人自由，关系中需要空间，不喜欢依附',
    modernMapping:'自由贸易商、外交官、独立顾问、跨境电商、谈判专家',
    gana:'Deva', nadi:'Antya' },
  { name:'Vishakha', symbol:'凯旋门/树叉', deity:'Indra-Agni（雷火双神）', lord:'Jupiter', animal:'虎',
    keywords:'目标导向、双面性、决心、成功、持久',
    career:'军事、法律、宗教、政治、企业战略、项目管理',
    relationship:'有双重社交面孔，关系中有隐藏的一面',
    modernMapping:'项目经理、军事指挥官、目标达成教练、品牌双面策略师',
    gana:'Rakshasa', nadi:'Aadi' },
  { name:'Anuradha', symbol:'莲花/权杖', deity:'Mitra（友谊之神）', lord:'Saturn', animal:'鹿',
    keywords:'友谊、合作、探索、成功、纪律下的温暖',
    career:'国际合作、外交、科学、军事、石油、矿业',
    relationship:'善于建立深层友谊，关系从友情发展为爱情',
    modernMapping:'国际关系专家、联盟构建者、团队合作教练、跨文化顾问',
    gana:'Deva', nadi:'Madhya' },
  { name:'Jyeshtha', symbol:'圆形护符/耳环', deity:'Indra（众神之王）', lord:'Mercury', animal:'雄鹿',
    keywords:'权威、保护、孤独、智慧、隐忍',
    career:'管理、法律、安保、政府、学术研究',
    relationship:'保护型伴侣，内心孤独，不轻易展现脆弱',
    modernMapping:'高管、法官、安保专家、危机管理总监、最高领导人',
    gana:'Rakshasa', nadi:'Antya' },
  { name:'Mula', symbol:'象鼻/捆绑的根', deity:'Nirriti（毁灭女神）', lord:'Ketu', animal:'狗',
    keywords:'根、破坏、转化、真相、深层探索',
    career:'医学研究、考古、心理学、哲学、真相揭露',
    relationship:'深层连接，关系中有破坏-重建的循环，追求深层真相',
    modernMapping:'考古学家、心理分析师、医学研究者、拆除专家、破除迷思者',
    gana:'Rakshasa', nadi:'Aadi' },
  { name:'Purva Ashadha', symbol:'扇子/锤子', deity:'Apah（水神）', lord:'Venus', animal:'猴',
    keywords:'不可战胜、净化、旅程、激情、壮丽',
    career:'军事、体育、水利、旅行、艺术、医疗',
    relationship:'充满激情，关系中追求壮丽感，不喜欢平淡',
    modernMapping:'探险家、运动员、水利工程师、旅行博主、胜利型领导',
    gana:'Manushya', nadi:'Madhya' },
  { name:'Uttara Ashadha', symbol:'象牙/犁头', deity:'Vishvadevas（全体天神）', lord:'Sun', animal:'水獭',
    keywords:'最终胜利、领导、承诺、正直、不懈努力',
    career:'管理、政府、法律、教育、军事、工程',
    relationship:'正直忠诚，关系中追求共同成长和道德一致',
    modernMapping:'CEO、政治领袖、道德哲学家、终身学习者、马拉松跑者',
    gana:'Manushya', nadi:'Antya' },
  { name:'Shravana', symbol:'耳朵/三脚印', deity:'Vishnu（守护之神）', lord:'Moon', animal:'猴',
    keywords:'聆听、学习、名声、传统、沟通',
    career:'教育、翻译、咨询、媒体、医疗（耳鼻喉）、学术',
    relationship:'善于倾听，通过语言和沟通建立连接',
    modernMapping:'播客主持人、翻译、语言学家、听力学家、学术传承人',
    gana:'Deva', nadi:'Aadi' },
  { name:'Dhanishta', symbol:'鼓/长笛', deity:'Vasus（八位光明之神）', lord:'Mars', animal:'狮',
    keywords:'音乐、节奏、财富、群体、律动',
    career:'音乐、金融、社群管理、表演、军事、体育',
    relationship:'重视群体和谐，关系中需要节奏感和同步',
    modernMapping:'音乐家、乐队指挥、基金经理人、社群运营者、节奏型创业者',
    gana:'Rakshasa', nadi:'Madhya' },
  { name:'Shatabhisha', symbol:'圆圈/空圆', deity:'Varuna（宇宙秩序之神）', lord:'Rahu', animal:'马',
    keywords:'秘密、治疗、百药、独立、隐藏知识、探索未知',
    career:'科技、医疗、天文学、占星学、隐私保护、网络安全',
    relationship:'重视隐私和独立，需要深层理解，不喜欢表层的社交',
    modernMapping:'密码学家、量子物理学家、替代疗法医生、占星师、信息安全专家',
    gana:'Rakshasa', nadi:'Antya' },
  { name:'Purva Bhadrapada', symbol:'剑/双面人/棺材前端', deity:'Aja Ekapada（独脚山羊神）', lord:'Jupiter', animal:'狮',
    keywords:'转化之火、苦行、极端、升腾、灵性战士',
    career:'宗教、灵修、极限运动、金融风险管理、心理咨询',
    relationship:'有极端化的倾向——要么极度投入，要么彻底放手',
    modernMapping:'瑜伽大师、极限运动员、灵性导师、火葬场管理、炼金术研究者',
    gana:'Manushya', nadi:'Aadi' },
  { name:'Uttara Bhadrapada', symbol:'双鱼/双腿/棺材后端', deity:'Ahir Budhnya（深渊蛇神）', lord:'Saturn', animal:'牛',
    keywords:'深度、耐心、智慧、守护、内在力量',
    career:'深度研究、灵修、管理、地理、心理学、水利',
    relationship:'深层忠诚，关系中需要耐心和理解，不喜欢肤浅',
    modernMapping:'深度学习工程师、冥想导师、地下水文学家、监狱心理辅导员',
    gana:'Manushya', nadi:'Madhya' },
  { name:'Revati', symbol:'鱼群/鼓', deity:'Pushan（牧羊之神/道路守护者）', lord:'Mercury', animal:'大象',
    keywords:'旅程完成、守护、丰饶、和谐、道路指引',
    career:'旅行、物流、护理、教育、音乐、慈善、导航技术',
    relationship:'守护型伴侣，善于照顾和指引，关系中有一种圆满感',
    modernMapping:'旅行策划师、导游、物流专家、生命教练、新生儿护理',
    gana:'Deva', nadi:'Antya' },
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

// ============================================================================
// Dasha 大运主题解读（来源: vimshottari_dasha_guide.md §3.2）
// ============================================================================
export const DASHA_THEMES = {
  Ketu: { years: 7, theme: '灵性觉醒、超脱、幻觉、内在探索',
    positive: '精神成长、解脱、直觉增强', negative: '迷惑、失去方向、孤立、幻灭' },
  Venus: { years: 20, theme: '爱情、婚姻、财富、艺术、享乐',
    positive: '美满婚姻、财富增长、艺术成就、享乐', negative: '感情纠葛、过度享乐、财务问题' },
  Sun: { years: 6, theme: '权力、权威、自我、父亲、政府',
    positive: '权威提升、事业成功、父亲健康', negative: '自我膨胀、与父亲冲突、健康问题' },
  Moon: { years: 10, theme: '情绪、家庭、母亲、心灵、公共关系',
    positive: '家庭和睦、情绪稳定、母亲健康', negative: '情绪波动、家庭问题、母亲健康' },
  Mars: { years: 7, theme: '行动、冲突、勇气、兄弟、土地',
    positive: '行动力强、勇气提升、兄弟相助', negative: '冲突、意外、健康问题、兄弟不和' },
  Rahu: { years: 18, theme: '欲望、幻想、突破、疯狂、物质追求',
    positive: '突破、物质成功、创新、冒险', negative: '成瘾、幻觉、失去方向、道德挑战' },
  Jupiter: { years: 16, theme: '智慧、财富、子息、运气、精神导师',
    positive: '智慧增长、财富增加、子女成才、贵人相助', negative: '过度乐观、财务膨胀、健康问题' },
  Saturn: { years: 19, theme: '业力、延迟、纪律、劳动、苦修',
    positive: '稳定、纪律、持久成功、精神成长', negative: '延迟、困难、健康问题、孤独' },
  Mercury: { years: 17, theme: '智力、沟通、商业、技巧、兄弟姐妹',
    positive: '智力提升、沟通能力、商业成功', negative: '焦虑、沟通问题、商业失败' },
};

// ============================================================================
// 12上升星座吉凶星表（来源: raman-house-judgment-methodology.md §1.2）
// ============================================================================
export const ASCENDANT_TABLE = {
  Aries:     { best: 'Jupiter', benefics: ['Mars','Sun'], malefics: ['Saturn','Mercury','Venus'], worst: 'Mercury(3+6主)', neutral: [], yogakaraka: null },
  Taurus:    { best: 'Saturn(9+10主)', benefics: ['Mercury','Mars','Sun'], malefics: ['Jupiter','Venus','Moon'], worst: null, neutral: ['Venus(Lagna主)'], yogakaraka: null },
  Gemini:    { best: 'Venus', benefics: [], malefics: ['Mars(6+11主)'], worst: null, neutral: ['Moon','Mercury'], yogakaraka: null },
  Cancer:    { best: 'Mars(5+10主)', benefics: ['Jupiter'], malefics: ['Saturn','Mercury'], worst: null, neutral: ['Venus'], yogakaraka: 'Mars' },
  Leo:       { best: 'Mars(4+9主)', benefics: ['Sun','Jupiter'], malefics: ['Venus','Saturn'], worst: null, neutral: ['Moon'], yogakaraka: 'Mars' },
  Virgo:     { best: 'Venus', benefics: [], malefics: ['Mars','Jupiter','Moon'], worst: 'Mars', neutral: ['Mercury(Lagna主)'], yogakaraka: null },
  Libra:     { best: 'Saturn(4+5主)', benefics: ['Mercury','Venus'], malefics: ['Jupiter','Sun','Mars'], worst: 'Jupiter', neutral: ['Moon'], yogakaraka: 'Saturn' },
  Scorpio:   { best: 'Jupiter(2+5主)', benefics: ['Moon','Sun','Mars'], malefics: ['Venus','Mercury'], worst: 'Venus', neutral: [], yogakaraka: null },
  Sagittarius:{ best: 'Mars, Sun', benefics: [], malefics: ['Venus','Saturn','Mercury'], worst: null, neutral: ['Jupiter','Moon'], yogakaraka: null },
  Capricorn: { best: 'Venus(5+10主)', benefics: ['Mercury','Saturn'], malefics: ['Mars','Jupiter','Moon'], worst: 'Mars', neutral: ['Sun(8主)'], yogakaraka: 'Venus' },
  Aquarius:  { best: 'Venus(4+9主)', benefics: ['Sun','Mars'], malefics: ['Jupiter','Moon'], worst: null, neutral: ['Mercury'], yogakaraka: 'Venus' },
  Pisces:    { best: 'Moon, Mars', benefics: [], malefics: ['Saturn','Sun','Venus','Mercury'], worst: null, neutral: ['Jupiter(Lagna主)'], yogakaraka: null },
};

// ============================================================================
// 行星旺衰与尊严数据（来源: planetary-dignity-complete-reference.md）
// ============================================================================
export const PLANET_DIGNITY = {
  Sun:    { exaltation: { sign:'Aries', degree:10 }, debilitation: { sign:'Libra', degree:10 },
    ownSigns: ['Leo'], moolatrikona: { sign:'Leo', start:0, end:20 },
    combustion: 0, // 太阳本身不燃烧
    exaltedModern: '领导力强、个人品牌成功、创业成功、自媒体影响力强',
    debilitatedModern: '合作成功、团队领导、非传统领导路径',
    friends: ['Moon','Mars','Jupiter'], enemies: ['Venus','Mercury','Saturn'] },
  Moon:   { exaltation: { sign:'Taurus', degree:3 }, debilitation: { sign:'Scorpio', degree:3 },
    ownSigns: ['Cancer'], moolatrikona: { sign:'Taurus', start:0, end:3 },
    combustion: 12,
    exaltedModern: '情绪稳定、公众吸引力强、配偶优秀、财富稳定',
    debilitatedModern: '情感深度、心理洞察、转化能力强、危机管理能力强',
    friends: ['Sun','Mercury'], enemies: [] },
  Mars:   { exaltation: { sign:'Capricorn', degree:28 }, debilitation: { sign:'Cancer', degree:28 },
    ownSigns: ['Aries','Scorpio'], moolatrikona: { sign:'Aries', start:0, end:12 },
    combustion: 17,
    exaltedModern: '行动力强、事业成功、管理能力强、长期目标达成',
    debilitatedModern: '情感驱动、家庭事业、非传统竞争路径',
    friends: ['Sun','Moon','Jupiter'], enemies: ['Mercury','Venus'] },
  Mercury:{ exaltation: { sign:'Virgo', degree:15 }, debilitation: { sign:'Pisces', degree:15 },
    ownSigns: ['Gemini','Virgo'], moolatrikona: { sign:'Virgo', start:16, end:20 },
    combustion: 14, combustionRetrograde: 8,
    exaltedModern: '分析能力强、写作能力强、沟通精准、逻辑思维强',
    debilitatedModern: '直觉强、艺术创作、灵性沟通、非传统智力路径',
    friends: ['Sun','Venus'], enemies: ['Moon'] },
  Jupiter:{ exaltation: { sign:'Cancer', degree:5 }, debilitation: { sign:'Capricorn', degree:5 },
    ownSigns: ['Sagittarius','Pisces'], moolatrikona: { sign:'Sagittarius', start:0, end:10 },
    combustion: 11,
    exaltedModern: '教育成功、家庭幸福、财富丰厚、智慧深厚',
    debilitatedModern: '长期成功、稳定扩张、非传统教育路径',
    friends: ['Sun','Moon','Mars'], enemies: ['Mercury','Venus'] },
  Venus:  { exaltation: { sign:'Pisces', degree:27 }, debilitation: { sign:'Virgo', degree:27 },
    ownSigns: ['Taurus','Libra'], moolatrikona: { sign:'Libra', start:0, end:15 },
    combustion: 10, combustionRetrograde: 8,
    exaltedModern: '艺术天赋强、爱情浪漫、美学品味高、财富转化能力强',
    debilitatedModern: '服务型爱情、美学服务、非传统美学路径',
    friends: ['Mercury','Saturn'], enemies: ['Sun','Moon'] },
  Saturn: { exaltation: { sign:'Libra', degree:20 }, debilitation: { sign:'Aries', degree:20 },
    ownSigns: ['Capricorn','Aquarius'], moolatrikona: { sign:'Capricorn', start:0, end:20 },
    combustion: 15,
    exaltedModern: '责任感强、合作关系好、长期成功、社会地位高',
    debilitatedModern: '快速成功、短期责任、非传统长期路径',
    friends: ['Venus','Mercury'], enemies: ['Sun','Moon','Mars'] },
};

// Neecha Bhanga（落陷取消）五大条件
export const NEECHA_BHANGA_RULES = [
  { id: 1, name: '定位星在角宫', desc: '落陷行星所在星座的守护星，位于命宫的角宫（1/4/7/10）' },
  { id: 2, name: '定位星相对月亮在角宫', desc: '落陷行星的定位星，位于月亮的角宫' },
  { id: 3, name: '互补入庙星在角宫', desc: '在该星座入庙的行星，位于命宫或月亮的角宫' },
  { id: 4, name: '与定位星产生关联', desc: '落陷行星与定位星合相或被定位星注视（产生相位）' },
  { id: 5, name: '星座互换/互容', desc: '落陷行星与定位星之间发生星座互换' },
];
