/**
 * Jyotish Engine — JavaScript 版 v2.0
 * 从 Python jyotish_engine.py v3.7.1 移植 + 扩展
 * 底层天文计算使用 swisseph-wasm (Swiss Ephemeris WASM)
 *
 * v2.0: +Combustion, +MC, 支持高级计算模块导入
 */

// ============================================================================
// 常量（与Python引擎完全一致）
// ============================================================================

export const NAKSHATRA_LIST = [
  { name: "Ashwini", lord: "Ketu", years: 7 },
  { name: "Bharani", lord: "Venus", years: 20 },
  { name: "Krittika", lord: "Sun", years: 6 },
  { name: "Rohini", lord: "Moon", years: 10 },
  { name: "Mrigashira", lord: "Mars", years: 7 },
  { name: "Ardra", lord: "Rahu", years: 18 },
  { name: "Punarvasu", lord: "Jupiter", years: 16 },
  { name: "Pushya", lord: "Saturn", years: 19 },
  { name: "Ashlesha", lord: "Mercury", years: 17 },
  { name: "Magha", lord: "Ketu", years: 7 },
  { name: "Purva Phalguni", lord: "Venus", years: 20 },
  { name: "Uttara Phalguni", lord: "Sun", years: 6 },
  { name: "Hasta", lord: "Moon", years: 10 },
  { name: "Chitra", lord: "Mars", years: 7 },
  { name: "Swati", lord: "Rahu", years: 18 },
  { name: "Vishakha", lord: "Jupiter", years: 16 },
  { name: "Anuradha", lord: "Saturn", years: 19 },
  { name: "Jyeshtha", lord: "Mercury", years: 17 },
  { name: "Mula", lord: "Ketu", years: 7 },
  { name: "Purva Ashadha", lord: "Venus", years: 20 },
  { name: "Uttara Ashadha", lord: "Sun", years: 6 },
  { name: "Shravana", lord: "Moon", years: 10 },
  { name: "Dhanishta", lord: "Mars", years: 7 },
  { name: "Shatabhisha", lord: "Rahu", years: 18 },
  { name: "Purva Bhadrapada", lord: "Jupiter", years: 16 },
  { name: "Uttara Bhadrapada", lord: "Saturn", years: 19 },
  { name: "Revati", lord: "Mercury", years: 17 },
];

export const DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"];
export const DASHA_YEARS = { Ketu: 7, Venus: 20, Sun: 6, Moon: 10, Mars: 7, Rahu: 18, Jupiter: 16, Saturn: 19, Mercury: 17 };

export const SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces'];

export const SIGNS_CN = {
  Aries: '白羊座', Taurus: '金牛座', Gemini: '双子座', Cancer: '巨蟹座',
  Leo: '狮子座', Virgo: '处女座', Libra: '天秤座', Scorpio: '天蝎座',
  Sagittarius: '射手座', Capricorn: '摩羯座', Aquarius: '水瓶座', Pisces: '双鱼座'
};

export const SIGNS_EN_SHORT = {
  Aries: 'Ari', Taurus: 'Tau', Gemini: 'Gem', Cancer: 'Can',
  Leo: 'Leo', Virgo: 'Vir', Libra: 'Lib', Scorpio: 'Sco',
  Sagittarius: 'Sag', Capricorn: 'Cap', Aquarius: 'Aqu', Pisces: 'Pis'
};

export const SIGN_LORDS = {
  Aries: 'Mars', Taurus: 'Venus', Gemini: 'Mercury', Cancer: 'Moon',
  Leo: 'Sun', Virgo: 'Mercury', Libra: 'Venus', Scorpio: 'Mars',
  Sagittarius: 'Jupiter', Capricorn: 'Saturn', Aquarius: 'Saturn', Pisces: 'Jupiter'
};

export const EXALTATION = { Sun: 'Aries', Moon: 'Taurus', Mars: 'Capricorn', Mercury: 'Virgo', Jupiter: 'Cancer', Venus: 'Pisces', Saturn: 'Libra' };
export const DEBILITATION = { Sun: 'Libra', Moon: 'Scorpio', Mars: 'Cancer', Mercury: 'Pisces', Jupiter: 'Capricorn', Venus: 'Virgo', Saturn: 'Aries' };

export const PLANET_CN = {
  Sun: "太阳", Moon: "月亮", Mars: "火星", Mercury: "水星",
  Jupiter: "木星", Venus: "金星", Saturn: "土星", Rahu: "北交点", Ketu: "南交点"
};

export const PLANET_SYMBOLS = {
  Sun: '☉', Moon: '☽', Mars: '♂', Mercury: '☿',
  Jupiter: '♃', Venus: '♀', Saturn: '♄', Rahu: '☊', Ketu: '☋'
};

// 行星特殊相位规则（Graha Drishti）
export const PLANET_ASPECTS = {
  Sun: [7], Moon: [7], Mars: [4, 7, 8], Mercury: [7],
  Jupiter: [5, 7, 9], Venus: [7], Saturn: [3, 7, 10],
  Rahu: [5, 7, 9], Ketu: [5, 7, 9],
};

// 行星关系
export const PLANET_RELATIONS = {
  Sun: { friends: ['Moon','Mars','Jupiter'], enemies: ['Venus','Saturn'] },
  Moon: { friends: ['Sun','Mercury'], enemies: [] },
  Mars: { friends: ['Sun','Moon','Jupiter'], enemies: ['Mercury'] },
  Mercury: { friends: ['Sun','Venus'], enemies: ['Moon'] },
  Jupiter: { friends: ['Sun','Moon','Mars'], enemies: ['Mercury','Venus'] },
  Venus: { friends: ['Mercury','Saturn'], enemies: ['Sun','Moon'] },
  Saturn: { friends: ['Mercury','Venus'], enemies: ['Sun','Moon','Mars'] },
};

// Swiss Ephemeris constants
const SE_SUN = 0, SE_MOON = 1, SE_MARS = 4, SE_MERCURY = 2, SE_JUPITER = 5, SE_VENUS = 3, SE_SATURN = 6, SE_MEAN_NODE = 10;
const SE_SIDM_LAHIRI = 1;
const SEFLG_SPEED = 256;

const PLANETS_SWE = {
  Sun: SE_SUN, Moon: SE_MOON, Mars: SE_MARS, Mercury: SE_MERCURY,
  Jupiter: SE_JUPITER, Venus: SE_VENUS, Saturn: SE_SATURN, Rahu: SE_MEAN_NODE
};

// 城市数据库
export const CITIES = [
  // ═══ 中国（含港澳台）═══
  {name:"北京",en:"Beijing",lat:39.9,lon:116.4,tz:8},
  {name:"上海",en:"Shanghai",lat:31.2,lon:121.5,tz:8},
  {name:"广州",en:"Guangzhou",lat:23.1,lon:113.3,tz:8},
  {name:"深圳",en:"Shenzhen",lat:22.5,lon:114.1,tz:8},
  {name:"REDACTED_PLACE",en:"REDACTED_PLACE",lat:36.6,lon:114.5,tz:8},
  {name:"成都",en:"Chengdu",lat:30.6,lon:104.1,tz:8},
  {name:"杭州",en:"Hangzhou",lat:30.3,lon:120.2,tz:8},
  {name:"南京",en:"Nanjing",lat:32.1,lon:118.8,tz:8},
  {name:"武汉",en:"Wuhan",lat:30.6,lon:114.3,tz:8},
  {name:"西安",en:"Xian",lat:34.3,lon:108.9,tz:8},
  {name:"重庆",en:"Chongqing",lat:29.6,lon:106.5,tz:8},
  {name:"天津",en:"Tianjin",lat:39.1,lon:117.2,tz:8},
  {name:"苏州",en:"Suzhou",lat:31.3,lon:120.6,tz:8},
  {name:"长沙",en:"Changsha",lat:28.2,lon:113.0,tz:8},
  {name:"郑州",en:"Zhengzhou",lat:34.7,lon:113.7,tz:8},
  {name:"沈阳",en:"Shenyang",lat:41.8,lon:123.4,tz:8},
  {name:"大连",en:"Dalian",lat:38.9,lon:121.6,tz:8},
  {name:"哈尔滨",en:"Harbin",lat:45.8,lon:126.5,tz:8},
  {name:"长春",en:"Changchun",lat:43.9,lon:125.3,tz:8},
  {name:"济南",en:"Jinan",lat:36.7,lon:117.0,tz:8},
  {name:"青岛",en:"Qingdao",lat:36.1,lon:120.4,tz:8},
  {name:"福州",en:"Fuzhou",lat:26.1,lon:119.3,tz:8},
  {name:"厦门",en:"Xiamen",lat:24.5,lon:118.1,tz:8},
  {name:"昆明",en:"Kunming",lat:25.0,lon:102.7,tz:8},
  {name:"贵阳",en:"Guiyang",lat:26.6,lon:106.7,tz:8},
  {name:"南宁",en:"Nanning",lat:22.8,lon:108.3,tz:8},
  {name:"海口",en:"Haikou",lat:20.0,lon:110.3,tz:8},
  {name:"三亚",en:"Sanya",lat:18.3,lon:109.5,tz:8},
  {name:"兰州",en:"Lanzhou",lat:36.1,lon:103.8,tz:8},
  {name:"乌鲁木齐",en:"Urumqi",lat:43.8,lon:87.6,tz:8},
  {name:"拉萨",en:"Lhasa",lat:29.7,lon:91.1,tz:8},
  {name:"呼和浩特",en:"Hohhot",lat:40.8,lon:111.7,tz:8},
  {name:"石家庄",en:"Shijiazhuang",lat:38.0,lon:114.5,tz:8},
  {name:"太原",en:"Taiyuan",lat:37.9,lon:112.6,tz:8},
  {name:"合肥",en:"Hefei",lat:31.8,lon:117.3,tz:8},
  {name:"南昌",en:"Nanchang",lat:28.7,lon:115.9,tz:8},
  {name:"无锡",en:"Wuxi",lat:31.6,lon:120.3,tz:8},
  {name:"宁波",en:"Ningbo",lat:29.9,lon:121.6,tz:8},
  {name:"佛山",en:"Foshan",lat:23.0,lon:113.1,tz:8},
  {name:"东莞",en:"Dongguan",lat:23.0,lon:113.7,tz:8},
  {name:"珠海",en:"Zhuhai",lat:22.3,lon:113.6,tz:8},
  {name:"温州",en:"Wenzhou",lat:28.0,lon:120.7,tz:8},
  {name:"保定",en:"Baoding",lat:38.9,lon:115.5,tz:8},
  {name:"唐山",en:"Tangshan",lat:39.6,lon:118.2,tz:8},
  {name:"烟台",en:"Yantai",lat:37.5,lon:121.4,tz:8},
  {name:"洛阳",en:"Luoyang",lat:34.6,lon:112.5,tz:8},
  {name:"常州",en:"Changzhou",lat:31.8,lon:119.9,tz:8},
  {name:"徐州",en:"Xuzhou",lat:34.3,lon:117.2,tz:8},
  {name:"盐城",en:"Yancheng",lat:33.4,lon:120.1,tz:8},
  {name:"秦皇岛",en:"Qinhuangdao",lat:39.9,lon:119.6,tz:8},
  {name:"银川",en:"Yinchuan",lat:38.5,lon:106.3,tz:8},
  {name:"西宁",en:"Xining",lat:36.6,lon:101.8,tz:8},
  // 港澳台
  {name:"香港",en:"Hong Kong",lat:22.3,lon:114.2,tz:8},
  {name:"澳门",en:"Macau",lat:22.2,lon:113.5,tz:8},
  {name:"台北",en:"Taipei",lat:25.0,lon:121.5,tz:8},
  {name:"高雄",en:"Kaohsiung",lat:22.6,lon:120.3,tz:8},
  {name:"台中",en:"Taichung",lat:24.1,lon:120.7,tz:8},
  // ═══ 东亚 ═══
  {name:"东京",en:"Tokyo",lat:35.7,lon:139.7,tz:9},
  {name:"大阪",en:"Osaka",lat:34.7,lon:135.5,tz:9},
  {name:"京都",en:"Kyoto",lat:35.0,lon:135.8,tz:9},
  {name:"横滨",en:"Yokohama",lat:35.4,lon:139.6,tz:9},
  {name:"名古屋",en:"Nagoya",lat:35.2,lon:136.9,tz:9},
  {name:"札幌",en:"Sapporo",lat:43.1,lon:141.3,tz:9},
  {name:"福冈",en:"Fukuoka",lat:33.6,lon:130.4,tz:9},
  {name:"首尔",en:"Seoul",lat:37.6,lon:127.0,tz:9},
  {name:"釜山",en:"Busan",lat:35.2,lon:129.0,tz:9},
  {name:"仁川",en:"Incheon",lat:37.4,lon:126.7,tz:9},
  // ═══ 东南亚 ═══
  {name:"新加坡",en:"Singapore",lat:1.4,lon:103.8,tz:8},
  {name:"曼谷",en:"Bangkok",lat:13.8,lon:100.5,tz:7},
  {name:"吉隆坡",en:"Kuala Lumpur",lat:3.1,lon:101.7,tz:8},
  {name:"雅加达",en:"Jakarta",lat:-6.2,lon:106.8,tz:7},
  {name:"马尼拉",en:"Manila",lat:14.6,lon:121.0,tz:8},
  {name:"胡志明市",en:"Ho Chi Minh City",lat:10.8,lon:106.7,tz:7},
  {name:"河内",en:"Hanoi",lat:21.0,lon:105.9,tz:7},
  {name:"金边",en:"Phnom Penh",lat:11.6,lon:104.9,tz:7},
  // ═══ 南亚 ═══
  {name:"新德里",en:"New Delhi",lat:28.6,lon:77.2,tz:5.5},
  {name:"孟买",en:"Mumbai",lat:19.1,lon:72.9,tz:5.5},
  {name:"加尔各答",en:"Kolkata",lat:22.6,lon:88.4,tz:5.5},
  {name:"金奈",en:"Chennai",lat:13.1,lon:80.3,tz:5.5},
  {name:"班加罗尔",en:"Bangalore",lat:13.0,lon:77.6,tz:5.5},
  {name:"瓦拉纳西",en:"Varanasi",lat:25.3,lon:83.0,tz:5.5},
  // ═══ 中东 ═══
  {name:"迪拜",en:"Dubai",lat:25.2,lon:55.3,tz:4},
  {name:"阿布扎比",en:"Abu Dhabi",lat:24.5,lon:54.7,tz:4},
  {name:"多哈",en:"Doha",lat:25.3,lon:51.5,tz:3},
  {name:"利雅得",en:"Riyadh",lat:24.7,lon:46.7,tz:3},
  {name:"伊斯坦布尔",en:"Istanbul",lat:41.0,lon:29.0,tz:3},
  {name:"特拉维夫",en:"Tel Aviv",lat:32.1,lon:34.8,tz:2},
  {name:"德黑兰",en:"Tehran",lat:35.7,lon:51.4,tz:3.5},
  // ═══ 欧洲 ═══
  {name:"伦敦",en:"London",lat:51.5,lon:-0.1,tz:0},
  {name:"巴黎",en:"Paris",lat:48.9,lon:2.3,tz:1},
  {name:"柏林",en:"Berlin",lat:52.5,lon:13.4,tz:1},
  {name:"马德里",en:"Madrid",lat:40.4,lon:-3.7,tz:1},
  {name:"罗马",en:"Rome",lat:41.9,lon:12.5,tz:1},
  {name:"阿姆斯特丹",en:"Amsterdam",lat:52.4,lon:4.9,tz:1},
  {name:"布鲁塞尔",en:"Brussels",lat:50.9,lon:4.4,tz:1},
  {name:"维也纳",en:"Vienna",lat:48.2,lon:16.4,tz:1},
  {name:"苏黎世",en:"Zurich",lat:47.4,lon:8.5,tz:1},
  {name:"日内瓦",en:"Geneva",lat:46.2,lon:6.1,tz:1},
  {name:"慕尼黑",en:"Munich",lat:48.1,lon:11.6,tz:1},
  {name:"法兰克福",en:"Frankfurt",lat:50.1,lon:8.7,tz:1},
  {name:"巴塞罗那",en:"Barcelona",lat:41.4,lon:2.2,tz:1},
  {name:"里斯本",en:"Lisbon",lat:38.7,lon:-9.1,tz:0},
  {name:"雅典",en:"Athens",lat:37.98,lon:23.7,tz:2},
  {name:"莫斯科",en:"Moscow",lat:55.8,lon:37.6,tz:3},
  {name:"圣彼得堡",en:"Saint Petersburg",lat:59.9,lon:30.3,tz:3},
  {name:"华沙",en:"Warsaw",lat:52.2,lon:21.0,tz:1},
  {name:"布拉格",en:"Prague",lat:50.1,lon:14.4,tz:1},
  {name:"布达佩斯",en:"Budapest",lat:47.5,lon:19.0,tz:1},
  {name:"哥本哈根",en:"Copenhagen",lat:55.7,lon:12.6,tz:1},
  {name:"斯德哥尔摩",en:"Stockholm",lat:59.3,lon:18.1,tz:1},
  {name:"赫尔辛基",en:"Helsinki",lat:60.2,lon:24.9,tz:2},
  {name:"都柏林",en:"Dublin",lat:53.3,lon:-6.3,tz:0},
  {name:"爱丁堡",en:"Edinburgh",lat:55.9,lon:-3.2,tz:0},
  // ═══ 北美 ═══
  {name:"纽约",en:"New York",lat:40.7,lon:-74.0,tz:-5},
  {name:"洛杉矶",en:"Los Angeles",lat:34.1,lon:-118.2,tz:-8},
  {name:"旧金山",en:"San Francisco",lat:37.8,lon:-122.4,tz:-8},
  {name:"芝加哥",en:"Chicago",lat:41.9,lon:-87.6,tz:-6},
  {name:"华盛顿",en:"Washington DC",lat:38.9,lon:-77.0,tz:-5},
  {name:"西雅图",en:"Seattle",lat:47.6,lon:-122.3,tz:-8},
  {name:"波士顿",en:"Boston",lat:42.4,lon:-71.1,tz:-5},
  {name:"迈阿密",en:"Miami",lat:25.8,lon:-80.2,tz:-5},
  {name:"拉斯维加斯",en:"Las Vegas",lat:36.2,lon:-115.1,tz:-8},
  {name:"圣地亚哥",en:"San Diego",lat:32.7,lon:-117.2,tz:-8},
  {name:"休斯顿",en:"Houston",lat:29.8,lon:-95.4,tz:-6},
  {name:"达拉斯",en:"Dallas",lat:32.8,lon:-96.8,tz:-6},
  {name:"丹佛",en:"Denver",lat:39.7,lon:-105.0,tz:-7},
  {name:"亚特兰大",en:"Atlanta",lat:33.7,lon:-84.4,tz:-5},
  {name:"菲尼克斯",en:"Phoenix",lat:33.4,lon:-112.1,tz:-7},
  {name:"波特兰",en:"Portland",lat:45.5,lon:-122.7,tz:-8},
  {name:"多伦多",en:"Toronto",lat:43.7,lon:-79.4,tz:-5},
  {name:"温哥华",en:"Vancouver",lat:49.3,lon:-123.1,tz:-8},
  {name:"蒙特利尔",en:"Montreal",lat:45.5,lon:-73.6,tz:-5},
  {name:"渥太华",en:"Ottawa",lat:45.4,lon:-75.7,tz:-5},
  {name:"卡尔加里",en:"Calgary",lat:51.0,lon:-114.1,tz:-7},
  {name:"墨西哥城",en:"Mexico City",lat:19.4,lon:-99.1,tz:-6},
  // ═══ 南美 ═══
  {name:"圣保罗",en:"Sao Paulo",lat:-23.6,lon:-46.6,tz:-3},
  {name:"里约热内卢",en:"Rio de Janeiro",lat:-22.9,lon:-43.2,tz:-3},
  {name:"布宜诺斯艾利斯",en:"Buenos Aires",lat:-34.6,lon:-58.4,tz:-3},
  {name:"利马",en:"Lima",lat:-12.0,lon:-77.0,tz:-5},
  {name:"波哥大",en:"Bogota",lat:4.7,lon:-74.1,tz:-5},
  {name:"圣地亚哥",en:"Santiago",lat:-33.4,lon:-70.7,tz:-4},
  // ═══ 大洋洲 ═══
  {name:"悉尼",en:"Sydney",lat:-33.9,lon:151.2,tz:10},
  {name:"墨尔本",en:"Melbourne",lat:-37.8,lon:145.0,tz:10},
  {name:"布里斯班",en:"Brisbane",lat:-27.5,lon:153.0,tz:10},
  {name:"珀斯",en:"Perth",lat:-31.9,lon:115.9,tz:8},
  {name:"奥克兰",en:"Auckland",lat:-36.9,lon:174.8,tz:12},
  {name:"惠灵顿",en:"Wellington",lat:-41.3,lon:174.8,tz:12},
  // ═══ 非洲 ═══
  {name:"开罗",en:"Cairo",lat:30.0,lon:31.2,tz:2},
  {name:"约翰内斯堡",en:"Johannesburg",lat:-26.2,lon:28.0,tz:2},
  {name:"开普敦",en:"Cape Town",lat:-33.9,lon:18.4,tz:2},
  {name:"拉各斯",en:"Lagos",lat:6.5,lon:3.4,tz:1},
  {name:"内罗毕",en:"Nairobi",lat:-1.3,lon:36.8,tz:3},
  {name:"卡萨布兰卡",en:"Casablanca",lat:33.6,lon:-7.6,tz:1},
];

// ============================================================================
// 核心引擎
// ============================================================================

let sweInstance = null;

/**
 * 等待 SwissEph 全局变量可用
 */
function waitForSwissEph(maxWait = 10000) {
  return new Promise((resolve, reject) => {
    if (window.SwissEph) { resolve(window.SwissEph); return; }
    const start = Date.now();
    const check = setInterval(() => {
      if (window.SwissEph) { clearInterval(check); resolve(window.SwissEph); }
      else if (Date.now() - start > maxWait) { clearInterval(check); reject(new Error('SwissEph not loaded after ' + maxWait + 'ms')); }
    }, 100);
  });
}

/**
 * 初始化 Swiss Ephemeris WASM (swisseph-wasm 版本)
 */
export async function initEngine() {
  if (sweInstance) return sweInstance;

  const SwissEph = await waitForSwissEph();
  
  sweInstance = new SwissEph();
  await sweInstance.initSwissEph();
  
  console.log('[Jyotish] Swiss Ephemeris initialized, version:', sweInstance.version());
  return sweInstance;
}

/**
 * 计算完整星盘 — 对应 Python compute_chart_data()
 */
export async function computeChart(birth) {
  const swe = await initEngine();
  const { year, month, day, hour, minute, lat, lon, tz } = birth;
  const hourDecimal = hour + minute / 60.0 - tz;

  // Julian Day (swe.julday 第5参数默认1=Gregorian)
  const jd = swe.julday(year, month, day, hourDecimal);
  console.log('[Jyotish] JD =', jd, 'hourUT =', hourDecimal);

  // Ayanamsa (Lahiri)
  swe.set_sid_mode(SE_SIDM_LAHIRI);
  const ayanamsa = swe.get_ayanamsa(jd);
  console.log('[Jyotish] Ayanamsa =', ayanamsa);

  // Houses — 'W' = Whole Sign houses
  const houseResult = swe.houses(jd, lat, lon, 'W');
  const cusps = houseResult.cusps;   // Float64Array[13], index 0 unused, 1-12 are cusps
  const ascmc = houseResult.ascmc;   // Float64Array[10], [0]=ASC, [1]=MC
  
  // Ascendant (tropical → sidereal)
  const ascTropical = ascmc[0];
  const ascSidereal = ((ascTropical - ayanamsa) % 360 + 360) % 360;
  const ascIdx = Math.floor(ascSidereal / 30);
  const ascSign = SIGNS[ascIdx];
  
  console.log('[Jyotish] ASC tropical =', ascTropical, 'sidereal =', ascSidereal, 'sign =', ascSign);

  // MC (Midheaven)
  const mcTropical = ascmc[1];
  const mcSidereal = ((mcTropical - ayanamsa) % 360 + 360) % 360;
  const mcIdx = Math.floor(mcSidereal / 30);

  const result = {
    birth_info: {
      date: `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`,
      time: `${String(hour).padStart(2,'0')}:${String(minute).padStart(2,'0')}`,
      tz: `UTC${tz >= 0 ? '+' : ''}${tz}`,
      lat, lon,
      julian_day: Math.round(jd * 1e6) / 1e6,
      ayanamsa: Math.round(ayanamsa * 1e4) / 1e4,
    },
    ascendant: {
      sign: ascSign,
      sign_cn: SIGNS_CN[ascSign],
      degree: Math.round(ascSidereal * 1e4) / 1e4,
      degree_in_sign: Math.round((ascSidereal - ascIdx * 30) * 1e4) / 1e4,
      lord: SIGN_LORDS[ascSign],
    },
    mc: {
      sign: SIGNS[mcIdx],
      sign_cn: SIGNS_CN[SIGNS[mcIdx]],
      degree: Math.round(mcSidereal * 1e4) / 1e4,
      degree_in_sign: Math.round((mcSidereal - mcIdx * 30) * 1e4) / 1e4,
    },
    planets: {},
    houses: {},
  };

  // House cusps (sidereal)
  for (let i = 0; i < 12; i++) {
    const cuspTropical = cusps[i + 1]; // cusps[1]..cusps[12]
    if (cuspTropical == null) continue;
    const cuspSidereal = ((cuspTropical - ayanamsa) % 360 + 360) % 360;
    const si = Math.floor(cuspSidereal / 30);
    result.houses[`house_${i + 1}`] = {
      cusp_sign: SIGNS[si],
      cusp_sign_cn: SIGNS_CN[SIGNS[si]],
      cusp_degree: Math.round(cuspSidereal * 1e4) / 1e4,
      lord: SIGN_LORDS[SIGNS[si]],
    };
  }

  // Planet positions
  // calc_ut 返回 Float64Array[6]: [longitude, latitude, distance, lonSpeed, latSpeed, distSpeed]
  const nakSpan = 360.0 / 27;
  const flags = SEFLG_SPEED;

  for (const [pname, pid] of Object.entries(PLANETS_SWE)) {
    try {
      const pos = swe.calc_ut(jd, pid, flags);
      // pos 是 Float64Array: [0]=lon, [1]=lat, [2]=dist, [3]=lonSpeed, [4]=latSpeed, [5]=distSpeed
      const lonTropical = pos[0];
      const lonSidereal = ((lonTropical - ayanamsa) % 360 + 360) % 360;
      const spd = pos[3];

      const si = Math.floor(lonSidereal / 30);
      const dInS = lonSidereal - si * 30;
      const sign = SIGNS[si];
      const retro = spd < 0;
      const house = ((si - ascIdx + 12) % 12) + 1;

      let status = "中性";
      if (EXALTATION[pname] === sign) status = "入旺";
      else if (DEBILITATION[pname] === sign) status = "落陷";
      else if (SIGN_LORDS[sign] === pname) status = "入庙";

      const ni = Math.floor(lonSidereal / nakSpan);
      const pada = Math.floor((lonSidereal % nakSpan) / (nakSpan / 4)) + 1;
      const nak = NAKSHATRA_LIST[ni % 27];

      result.planets[pname] = {
        sign, sign_cn: SIGNS_CN[sign],
        degree: Math.round(lonSidereal * 1e4) / 1e4,
        degree_in_sign: Math.round(dInS * 1e4) / 1e4,
        house, status, retrograde: retro,
        speed: Math.round(spd * 1e6) / 1e6,
        nakshatra: nak.name,
        nakshatra_pada: pada,
        nakshatra_lord: nak.lord,
        combust: false,
      };

      // Ketu = opposite Rahu
      if (pname === 'Rahu') {
        const klon = (lonSidereal + 180) % 360;
        const ksi = Math.floor(klon / 30);
        const kd = klon - ksi * 30;
        const kni = Math.floor(klon / nakSpan);
        const kp = Math.floor((klon % nakSpan) / (nakSpan / 4)) + 1;
        const kn = NAKSHATRA_LIST[kni % 27];

        result.planets['Ketu'] = {
          sign: SIGNS[ksi], sign_cn: SIGNS_CN[SIGNS[ksi]],
          degree: Math.round(klon * 1e4) / 1e4,
          degree_in_sign: Math.round(kd * 1e4) / 1e4,
          house: ((ksi - ascIdx + 12) % 12) + 1,
          status: "中性", retrograde: true,
          speed: Math.round(spd * 1e6) / 1e6,
          nakshatra: kn.name, nakshatra_pada: kp, nakshatra_lord: kn.lord,
          combust: false,
        };
      }
      
      console.log(`[Jyotish] ${pname}: ${sign} ${dInS.toFixed(2)}° (house ${house}, ${status})`);
    } catch (e) {
      console.error(`[Jyotish] Error computing ${pname}:`, e);
      result.planets[pname] = { error: e.message };
    }
  }

  return result;
}

// ============================================================================
// Dasha 计算
// ============================================================================

export function computeDasha(moonLon, birthDate, referenceDate) {
  const nakSpan = 360.0 / 27;
  const nakIdx = Math.floor(moonLon / nakSpan);
  const progress = (moonLon % nakSpan) / nakSpan;
  const nak = NAKSHATRA_LIST[nakIdx % 27];

  const birthDt = new Date(birthDate);
  const elapsed = progress * nak.years;
  const startDt = new Date(birthDt.getTime() - elapsed * 365.25 * 24 * 3600000);
  const startIdx = DASHA_ORDER.indexOf(nak.lord);

  const remaining = nak.years - elapsed;

  const timeline = [];
  let dt = new Date(startDt.getTime());

  for (let i = 0; i < 9; i++) {
    const lord = DASHA_ORDER[(startIdx + i) % 9];
    const years = DASHA_YEARS[lord];
    const endDt = new Date(dt.getTime() + years * 365.25 * 24 * 3600000);
    const isBalance = i === 0;
    timeline.push({
      lord, lord_cn: PLANET_CN[lord],
      start: fmtDate(dt), end: fmtDate(endDt),
      years: isBalance ? Math.round(remaining * 100) / 100 : years,
      full_years: years,
      is_balance: isBalance,
      balance_years: isBalance ? Math.round(remaining * 100) / 100 : null,
      elapsed_at_birth: isBalance ? Math.round(elapsed * 100) / 100 : null,
      antardasha: null
    });
    dt = endDt;
  }

  const today = referenceDate ? new Date(referenceDate) : new Date();
  let current = null;

  for (const d of timeline) {
    const ds = new Date(d.start), de = new Date(d.end);
    if (ds <= today && today < de) {
      const totalDays = (de - ds) / (24 * 3600000);
      const li = DASHA_ORDER.indexOf(d.lord);
      const sub = [];
      let sdt = new Date(ds.getTime());
      for (let j = 0; j < 9; j++) {
        const sl = DASHA_ORDER[(li + j) % 9];
        const sd = totalDays * DASHA_YEARS[sl] / 120;
        const se = new Date(sdt.getTime() + sd * 24 * 3600000);
        sub.push({ lord: sl, lord_cn: PLANET_CN[sl], start: fmtDate(sdt), end: fmtDate(se), is_current: sdt <= today && today < se });
        sdt = se;
      }
      d.antardasha = sub;
      current = d;
      break;
    }
  }

  return { moon_nakshatra: nak.name, birth_date: birthDate, reference_date: fmtDate(today), timeline, current_dasha: current };
}

// ============================================================================
// Yoga 识别
// ============================================================================

export function detectYogas(planets, ascSign) {
  const ai = SIGNS.indexOf(ascSign);
  const kl = [...new Set([1, 4, 7, 10].map(h => SIGN_LORDS[SIGNS[(ai + h - 1) % 12]]))];
  const tl = [...new Set([1, 5, 9].map(h => SIGN_LORDS[SIGNS[(ai + h - 1) % 12]]))];
  const yogas = [];

  for (const k of kl) {
    for (const t of tl) {
      if (k !== t && planets[k] && planets[t] && planets[k].house === planets[t].house) {
        yogas.push({ name: "Raja Yoga", name_cn: "王者格局", combination: `${PLANET_CN[k]}+${PLANET_CN[t]}同在第${planets[k].house}宫`, effects: ["权力地位", "事业成功", "社会影响力"], strength: "强" });
      }
    }
  }

  const yogaNames = { Mars: 'Ruchaka', Mercury: 'Bhadra', Jupiter: 'Hamsa', Venus: 'Malavya', Saturn: 'Sasa' };
  for (const [p, info] of Object.entries(planets)) {
    if ([1, 4, 7, 10].includes(info.house) && yogaNames[p]) {
      if (EXALTATION[p] === info.sign || SIGN_LORDS[info.sign] === p) {
        const st = EXALTATION[p] === info.sign ? "入旺" : "入庙";
        yogas.push({ name: `${yogaNames[p]} Yoga`, name_cn: `${PLANET_CN[p]}${st}格局`, combination: `${PLANET_CN[p]}${st}在${SIGNS_CN[info.sign]}(第${info.house}宫)`, effects: ["卓越才能", "领域领军", "人格魅力"], strength: st === "入旺" ? "极强" : "强" });
      }
    }
  }

  if (planets.Jupiter && planets.Moon) {
    if ([1, 4, 7, 10].includes(planets.Jupiter.house) && [1, 4, 7, 10].includes(planets.Moon.house)) {
      yogas.push({ name: "Gajakesari Yoga", name_cn: "象狮格局", combination: `木星第${planets.Jupiter.house}宫+月亮第${planets.Moon.house}宫`, effects: ["智慧学识", "财富名声", "道德品质"], strength: "中" });
    }
  }

  for (const [p, info] of Object.entries(planets)) {
    if (DEBILITATION[p] === info.sign) {
      const dl = SIGN_LORDS[info.sign];
      if (planets[dl] && [1, 4, 7, 10].includes(planets[dl].house)) {
        yogas.push({ name: "Neechabhanga Raja Yoga", name_cn: "落陷取消格局", combination: `${PLANET_CN[p]}落陷在${SIGNS_CN[info.sign]}，${PLANET_CN[dl]}在角宫化解`, effects: ["克服困难", "逆境崛起", "转化能力"], strength: "中强" });
      }
    }
  }

  const wh = [2, 5, 9, 11];
  const wl = new Set(wh.map(h => SIGN_LORDS[SIGNS[(ai + h - 1) % 12]]));
  let wc = 0;
  for (const w of wl) { if (planets[w] && wh.includes(planets[w].house)) wc++; }
  if (wc >= 2) {
    yogas.push({ name: "Dhana Yoga", name_cn: "财富格局", combination: `${wc}个财富宫主星落入财富宫`, effects: ["财富积累", "物质成功", "投资收益"], strength: wc >= 3 ? "中强" : "中" });
  }

  return { ascendant: ascSign, yogas_detected: yogas.length, yogas };
}

/**
 * 扩展 Yoga 检测 — 使用 interpretation.js 的 YOGA_DEFINITIONS
 */
export function detectExtendedYogas(planets, ascSign) {
  const base = detectYogas(planets, ascSign);
  // YOGA_DEFINITIONS 由 interpretation.js 动态导入
  return base;
}

// ============================================================================
// Graha Drishti 行星相位
// ============================================================================

export function computeAspects(planets) {
  const aspects = [];
  const names = ['Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'];
  for (const from of names) {
    const fp = planets[from]; if (!fp || fp.error) continue;
    const asp = PLANET_ASPECTS[from] || [7];
    for (const offset of asp) {
      const toHouse = ((fp.house - 1 + offset) % 12) + 1;
      const targets = names.filter(t => t !== from && planets[t] && !planets[t].error && planets[t].house === toHouse);
      for (const to of targets) {
        let type = offset === 7 ? 'opposition' : (offset === 5 || offset === 9) ? 'trine' : 'special';
        let friendly = 'neutral';
        const rel = PLANET_RELATIONS[from];
        if (rel) {
          if (rel.friends.includes(to)) friendly = 'friendly';
          else if (rel.enemies.includes(to)) friendly = 'hostile';
        }
        aspects.push({ from, to, from_cn: PLANET_CN[from], to_cn: PLANET_CN[to], type, offset, toHouse, friendly });
      }
    }
  }
  return aspects;
}

// ============================================================================
// Navamsa (D9) 分盘
// ============================================================================

export function computeNavamsa(planets) {
  const d9 = {};
  for (const [pn, pi] of Object.entries(planets)) {
    if (pi.error) continue;
    const degInSign = pi.degree_in_sign;
    const nw = 30 / 9;
    const ni = Math.floor(degInSign / nw);
    const si = SIGNS.indexOf(pi.sign);
    let start;
    if ([0,3,6,9].includes(si)) start = si;           // Movable
    else if ([1,4,7,10].includes(si)) start = (si+8)%12; // Fixed
    else start = (si+4)%12;                              // Dual
    const d9si = (start + ni) % 12;
    d9[pn] = { sign: SIGNS[d9si], sign_cn: SIGNS_CN[SIGNS[d9si]], house: pi.house };
  }
  return { type: 'D9', name: 'Navamsa', name_cn: '九分盘', planets: d9 };
}

// ============================================================================
// 宫位综合分析
// ============================================================================

export function computeHouseAnalysis(planets, ascSign) {
  const ai = SIGNS.indexOf(ascSign);
  const houses = [];
  for (let h = 1; h <= 12; h++) {
    const si = (ai + h - 1) % 12;
    const sign = SIGNS[si];
    const lord = SIGN_LORDS[sign];
    const lordPlanet = planets[lord];
    const occupants = Object.entries(planets).filter(([_,p]) => p.house === h && !p.error).map(([n,p]) => ({name:n,...p}));
    const aspecting = [];
    for (const [pn, pp] of Object.entries(planets)) {
      if (pp.error) continue;
      for (const offset of (PLANET_ASPECTS[pn]||[7])) {
        if (((pp.house-1+offset)%12)+1 === h) aspecting.push({name:pn, offset});
      }
    }
    houses.push({ house:h, sign, sign_cn: SIGNS_CN[sign], lord, lord_cn: PLANET_CN[lord]||lord, lordHouse: lordPlanet?lordPlanet.house:null, occupants, aspecting });
  }
  return houses;
}

// ============================================================================
// 工具
// ============================================================================

function fmtDate(d) {
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

export function searchCities(query) {
  if (!query || query.length < 1) return [];
  const fullQ = query.toLowerCase();
  // 拆分关键词：空格/逗号/中文逗号分隔
  const words = fullQ.split(/[\s,，;；]+/).filter(w => w.length > 0);

  return CITIES.filter(c => {
    const nameLow = c.name.toLowerCase();
    const enLow = (c.en || '').toLowerCase();
    const combined = nameLow + ' ' + enLow;

    // 1. 整体包含（如输入"REDACTED_PLACE"直接匹配）
    if (nameLow.includes(fullQ) || enLow.includes(fullQ)) return true;

    // 2. 拆词 AND 匹配（如"中国 REDACTED_PLACE"→每个词都须命中）
    if (words.length > 1 && words.every(w => combined.includes(w))) return true;

    // 3. 模糊匹配：城市名包含输入的子串，或输入包含城市名
    //    支持"中国REDACTED_PLACE"匹配"REDACTED_PLACE"、"REDACTED_PLACE市"匹配"REDACTED_PLACE"等
    if (nameLow.length >= 2 && (fullQ.includes(nameLow) || nameLow.includes(fullQ))) return true;
    if (enLow.length >= 2 && (fullQ.includes(enLow) || enLow.includes(fullQ))) return true;

    return false;
  }).slice(0, 10);
}
