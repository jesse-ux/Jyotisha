"""Panchanga — 五支时间历法 (Five Limbs of Vedic Timekeeping).

Pure-arithmetic calculation of Tithi, Nakshatra, Nitya Yoga, Karana, and Vara
from Sun and Moon longitudes. No astronomical engine required — callers supply
pre-computed longitudes from ephemeris.py.

Reference: All 27 nakshatra lords follow the Vimshottari dasha cycle:
  Ketu → Venus → Sun → Moon → Mars → Rahu → Jupiter → Saturn → Mercury
"""

# ── Constants ──────────────────────────────────────────────────────────

# 15 Tithi names shared between Shukla and Krishna pakshas (0-14)
# Slot 14 = Purnima (Shukla) / Amavasya (Krishna), determined at runtime
TITHI_NAMES = [
    {"sanskrit": "Pratipada",  "chinese": "初日"},
    {"sanskrit": "Dwitiya",    "chinese": "二日"},
    {"sanskrit": "Tritiya",    "chinese": "三日"},
    {"sanskrit": "Chaturthi",  "chinese": "四日"},
    {"sanskrit": "Panchami",   "chinese": "五日"},
    {"sanskrit": "Shashti",    "chinese": "六日"},
    {"sanskrit": "Saptami",    "chinese": "七日"},
    {"sanskrit": "Ashtami",    "chinese": "八日"},
    {"sanskrit": "Navami",     "chinese": "九日"},
    {"sanskrit": "Dashami",    "chinese": "十日"},
    {"sanskrit": "Ekadashi",   "chinese": "十一日"},
    {"sanskrit": "Dwadashi",   "chinese": "十二日"},
    {"sanskrit": "Trayodashi", "chinese": "十三日"},
    {"sanskrit": "Chaturdashi","chinese": "十四日"},
    # Slot 14: Purnima (望月) for Shukla, Amavasya (朔月) for Krishna
]

# 27 Nakshatras: (index, sanskrit, chinese, lord, meaning)
NAKSHATRAS = [
    (0,  "Ashvini",          "阿说你",        "Ke", "马首星"),
    (1,  "Bharani",          "跋梨尼",        "Ve", "女阴星"),
    (2,  "Krittika",         "羯底迦",        "Su", "聚星"),
    (3,  "Rohini",           "卢醯尼",        "Mo", "红星"),
    (4,  "Mrigashira",       "密伽尸罗",      "Ma", "鹿首星"),
    (5,  "Ardra",            "阿陀罗",        "Ra", "泪星"),
    (6,  "Punarvasu",        "补那瓦苏",      "Ju", "双星"),
    (7,  "Pushya",           "布史也",        "Sa", "滋养星"),
    (8,  "Ashlesha",         "阿沙离沙",      "Me", "缠蛇星"),
    (9,  "Magha",            "摩伽",          "Ke", "权星"),
    (10, "Purva Phalguni",   "前弗勒艮尼",    "Ve", "前棕床星"),
    (11, "Uttara Phalguni",  "后弗勒艮尼",    "Su", "后棕床星"),
    (12, "Hasta",            "诃萨多",        "Mo", "手星"),
    (13, "Chitra",           "质多罗",        "Ma", "宝珠星"),
    (14, "Swati",            "萨缚帝",        "Ra", "珊瑚星"),
    (15, "Vishakha",         "吠舍祛",        "Ju", "叉星"),
    (16, "Anuradha",         "阿奴罗陀",      "Sa", "成功星"),
    (17, "Jyeshtha",         "折瑟多",        "Me", "长星"),
    (18, "Mula",             "牟罗",          "Ke", "根星"),
    (19, "Purva Ashadha",    "前沙他",        "Ve", "前胜星"),
    (20, "Uttara Ashadha",   "后沙他",        "Su", "后胜星"),
    (21, "Shravana",         "失罗婆拏",      "Mo", "耳星"),
    (22, "Dhanishtha",       "陀尼瑟吒",      "Ma", "福星"),
    (23, "Shatabhisha",      "设多毗沙",      "Ra", "百医星"),
    (24, "Purva Bhadrapada", "前跋陀罗",      "Ju", "前吉星"),
    (25, "Uttara Bhadrapada","后跋陀罗",      "Sa", "后吉星"),
    (26, "Revati",           "离婆底",        "Me", "丰裕星"),
]

# Vimshottari dasha lord cycle (repeats every 9 nakshatras)
VIMSHOTTARI_LORDS = ['Ke', 'Ve', 'Su', 'Mo', 'Ma', 'Ra', 'Ju', 'Sa', 'Me']

# Full planet name mapping for lords
PLANET_FULL_NAMES = {
    'Su': 'Sun (太阳)',
    'Mo': 'Moon (月亮)',
    'Ma': 'Mars (火星)',
    'Me': 'Mercury (水星)',
    'Ju': 'Jupiter (木星)',
    'Ve': 'Venus (金星)',
    'Sa': 'Saturn (土星)',
    'Ra': 'Rahu (罗睺)',
    'Ke': 'Ketu (计都)',
}

# 27 Nitya Yogas: (index, sanskrit, chinese, meaning)
YOGA_NAMES = [
    (0,  "Vishkumbha",  "毗湿剑婆", "充满"),
    (1,  "Preeti",      "布利底",   "愉悦"),
    (2,  "Ayushman",    "阿由曼",   "长寿"),
    (3,  "Saubhagya",   "苏婆伽",   "吉祥"),
    (4,  "Shobhana",    "输婆那",   "光辉"),
    (5,  "Atiganda",    "阿底犍陀", "大障碍"),
    (6,  "Sukarma",     "苏羯摩",   "善业"),
    (7,  "Dhriti",      "底利提",   "坚定"),
    (8,  "Shoola",      "输罗",     "刺"),
    (9,  "Ganda",       "犍陀",     "结节"),
    (10, "Vriddhi",     "勿利提",   "增长"),
    (11, "Dhruva",      "陀留婆",   "固定"),
    (12, "Vyaghata",    "毗伽多",   "打击"),
    (13, "Harshana",    "诃沙那",   "喜悦"),
    (14, "Vajra",       "缚折罗",   "雷电"),
    (15, "Siddhi",      "悉提",     "成就"),
    (16, "Vyatipata",   "毗底波多", "灾难"),
    (17, "Variyana",    "婆利衍那", "舒适"),
    (18, "Parigha",     "波利伽",   "横木"),
    (19, "Shiva",       "湿婆",     "吉祥"),
    (20, "Siddha",      "悉陀",     "成就者"),
    (21, "Sadhya",      "萨提耶",   "可成就的"),
    (22, "Shubha",      "输婆",     "善"),
    (23, "Shukla",      "戌羯罗",   "明亮"),
    (24, "Brahma",      "梵摩",     "梵"),
    (25, "Indra",       "因陀罗",   "帝释天"),
    (26, "Vaidhriti",   "吠陀利提", "分离"),
]

# 7 repeating Karanas (cycle through the middle 56 of 60)
KARANA_REPEATING = [
    {"sanskrit": "Bava",    "chinese": "婆鞞"},
    {"sanskrit": "Balava",  "chinese": "婆罗鞞"},
    {"sanskrit": "Kaulava", "chinese": "拘罗婆"},
    {"sanskrit": "Taitila", "chinese": "太的罗"},
    {"sanskrit": "Gara",    "chinese": "伽罗"},
    {"sanskrit": "Vanija",  "chinese": "婆尼"},
    {"sanskrit": "Vishti",  "chinese": "毗湿提"},
]

# 4 fixed Karanas at specific index positions
KARANA_FIXED = [
    {"index": 0,  "sanskrit": "Kimstughni",   "chinese": "金土革尼"},
    {"index": 57, "sanskrit": "Shakuni",       "chinese": "夏俱尼"},
    {"index": 58, "sanskrit": "Chatushpada",   "chinese": "四足"},
    {"index": 59, "sanskrit": "Naga",          "chinese": "龙"},
]

# Weekday names
VARA_NAMES = [
    {"index": 0, "sanskrit": "Sunday",    "chinese": "星期日", "planet": "Su", "planet_cn": "太阳日"},
    {"index": 1, "sanskrit": "Monday",    "chinese": "星期一", "planet": "Mo", "planet_cn": "月亮日"},
    {"index": 2, "sanskrit": "Tuesday",   "chinese": "星期二", "planet": "Ma", "planet_cn": "火星日"},
    {"index": 3, "sanskrit": "Wednesday", "chinese": "星期三", "planet": "Me", "planet_cn": "水星日"},
    {"index": 4, "sanskrit": "Thursday",  "chinese": "星期四", "planet": "Ju", "planet_cn": "木星日"},
    {"index": 5, "sanskrit": "Friday",    "chinese": "星期五", "planet": "Ve", "planet_cn": "金星日"},
    {"index": 6, "sanskrit": "Saturday",  "chinese": "星期六", "planet": "Sa", "planet_cn": "土星日"},
]


# ── Calculation Functions ──────────────────────────────────────────────

def norm(deg):
    """Normalize angle to [0, 360)."""
    return deg % 360


def calc_tithi(sun_lon, moon_lon):
    """Calculate Tithi (lunar day) from Sun and Moon longitudes.

    Each tithi spans 12 degrees of the lunar-sidereal angle.
    30 tithis per lunar month: 15 Shukla (bright) + 15 Krishna (dark).

    Returns dict with name, paksha, progress (0-1), and angle details.
    """
    lunar_angle = norm(moon_lon - sun_lon)
    tithi_idx = min(int(lunar_angle / 12.0), 29)  # 0-29
    tithi_num = tithi_idx + 1  # 1-30

    paksha = "Shukla" if tithi_num <= 15 else "Krishna"
    paksha_cn = "白半月" if paksha == "Shukla" else "黑半月"
    paksha_tithi = tithi_num if tithi_num <= 15 else tithi_num - 15  # 1-15

    name_slot = tithi_idx % 15  # 0-14

    if name_slot == 14:
        name = "Purnima" if paksha == "Shukla" else "Amavasya"
        name_cn = "望月" if paksha == "Shukla" else "朔月"
    else:
        name = TITHI_NAMES[name_slot]["sanskrit"]
        name_cn = TITHI_NAMES[name_slot]["chinese"]

    progress = (lunar_angle - tithi_idx * 12.0) / 12.0

    return {
        "index": tithi_idx,
        "number": tithi_num,
        "paksha": paksha,
        "paksha_chinese": paksha_cn,
        "paksha_tithi": paksha_tithi,
        "name": name,
        "name_chinese": name_cn,
        "lunar_angle": round(lunar_angle, 6),
        "progress": round(progress, 6),
        "start_lon": round(tithi_idx * 12.0, 6),
        "end_lon": round(min((tithi_idx + 1) * 12.0, 360.0), 6),
    }


def calc_nakshatra(lon):
    """Calculate Nakshatra (lunar mansion) for a given longitude.

    The zodiac is divided into 27 equal spans of 13°20' (13.333...°).
    Each nakshatra is further divided into 4 padas of 3°20'.

    Returns dict with name, pada (1-4), lord, and progress.
    """
    lon = norm(lon)
    span = 360.0 / 27.0  # ~13.333...°
    idx = min(int(lon / span), 26)
    pada_span = span / 4.0
    progress_in_nak = (lon - idx * span) / span
    pada = min(int((lon - idx * span) / pada_span), 3) + 1  # 1-4

    lord = VIMSHOTTARI_LORDS[idx % 9]

    return {
        "index": idx,
        "name": NAKSHATRAS[idx][1],
        "name_chinese": NAKSHATRAS[idx][2],
        "meaning": NAKSHATRAS[idx][4],
        "pada": pada,
        "lord": lord,
        "lord_full": PLANET_FULL_NAMES.get(lord, lord),
        "longitude": round(lon, 6),
        "progress": round(progress_in_nak, 6),
        "span_start": round(idx * span, 6),
        "span_end": round((idx + 1) * span, 6),
    }


def calc_yoga(sun_lon, moon_lon):
    """Calculate Nitya Yoga from the sum of Sun and Moon longitudes.

    The sum is divided into 27 equal parts of 13°20' each.
    27 yogas total (Vishkumbha through Vaidhriti).

    Returns dict with name, meaning, and sum angle details.
    """
    combined = norm(sun_lon + moon_lon)
    span = 360.0 / 27.0
    idx = min(int(combined / span), 26)
    progress = (combined - idx * span) / span

    return {
        "index": idx,
        "name": YOGA_NAMES[idx][1],
        "name_chinese": YOGA_NAMES[idx][2],
        "meaning": YOGA_NAMES[idx][3],
        "combined_lon": round(combined, 6),
        "progress": round(progress, 6),
        "span_start": round(idx * span, 6),
        "span_end": round((idx + 1) * span, 6),
    }


def calc_karana(sun_lon, moon_lon):
    """Calculate Karana (half-tithi) from Sun and Moon longitudes.

    Each karana spans 6 degrees (half a tithi). 60 karanas per lunar month.
    - Index 0: fixed "Kimstughni"
    - Indices 57-59: fixed "Shakuni", "Chatushpada", "Naga"
    - Indices 1-56: 7 repeating karanas (8 full cycles)

    Returns dict with name, type (fixed/repeating), and parent tithi.
    """
    lunar_angle = norm(moon_lon - sun_lon)
    idx = min(int(lunar_angle / 6.0), 59)
    tithi_idx = idx // 2
    half = (idx % 2) + 1  # 1 = first half, 2 = second half

    # Fixed karanas at specific indices
    fixed_map = {item["index"]: item for item in KARANA_FIXED}

    if idx in fixed_map:
        entry = fixed_map[idx]
        name, name_cn, karana_type = entry["sanskrit"], entry["chinese"], "fixed"
    else:
        # Repeating karana: skip index 0 (fixed), then cycle 1-56 through 7 names
        ri = (idx - 1) % 7
        entry = KARANA_REPEATING[ri]
        name, name_cn, karana_type = entry["sanskrit"], entry["chinese"], "repeating"

    progress = (lunar_angle - idx * 6.0) / 6.0

    return {
        "index": idx,
        "name": name,
        "name_chinese": name_cn,
        "type": karana_type,
        "tithi_index": tithi_idx,
        "half": half,
        "progress": round(progress, 6),
    }


def calc_vara(weekday):
    """Calculate Vara (weekday lord) from Python weekday index.

    Args:
        weekday: Python datetime.weekday() value (0=Monday..6=Sunday)

    Returns dict with Sanskrit name, Chinese name, and planetary lord.
    """
    # Convert Python weekday (0=Mon) to Vara index (0=Sun)
    vara_idx = (weekday + 1) % 7

    entry = VARA_NAMES[vara_idx]
    return {
        "index": vara_idx,
        "name": entry["sanskrit"],
        "name_chinese": entry["chinese"],
        "planet": entry["planet"],
        "planet_chinese": entry["planet_cn"],
    }


def calc_panchanga(sun_lon, moon_lon, weekday):
    """Calculate all 5 Panchanga limbs at once.

    Args:
        sun_lon: Sun's tropical longitude (0-360 degrees)
        moon_lon: Moon's tropical longitude (0-360 degrees)
        weekday: Python datetime.weekday() (0=Monday..6=Sunday)

    Returns:
        dict with keys 'tithi', 'nakshatra', 'yoga', 'karana', 'vara'.
    """
    return {
        "tithi": calc_tithi(sun_lon, moon_lon),
        "nakshatra": calc_nakshatra(moon_lon),
        "yoga": calc_yoga(sun_lon, moon_lon),
        "karana": calc_karana(sun_lon, moon_lon),
        "vara": calc_vara(weekday),
    }


def format_panchanga(panchanga):
    """Format Panchanga data as a human-readable multi-line string.

    Used by Chart.summary() for CLI output.
    """
    t = panchanga.get("tithi", {})
    n = panchanga.get("nakshatra", {})
    y = panchanga.get("yoga", {})
    k = panchanga.get("karana", {})
    v = panchanga.get("vara", {})

    lines = []
    if t:
        lines.append(f"  Tithi (月日):      {t['name']} ({t['name_chinese']})  "
                     f"{t['paksha_chinese']}第{t['paksha_tithi']}日  "
                     f"progress: {t['progress']*100:.1f}%")
    if n:
        lines.append(f"  Nakshatra (星宿):  {n['name']} ({n['name_chinese']})  "
                     f"Pada {n['pada']}/4  Lord: {n['lord']} ({n['lord_full']})  "
                     f"progress: {n['progress']*100:.1f}%")
    if y:
        lines.append(f"  Yoga (合朔):       {y['name']} ({y['name_chinese']} — {y['meaning']})")
    if k:
        lines.append(f"  Karana (半日):     {k['name']} ({k['name_chinese']})  {k['type']}")
    if v:
        lines.append(f"  Vara (曜日):       {v['name']} ({v['name_chinese']})  Lord: {v['planet_chinese']}")

    return "\n".join(lines)
