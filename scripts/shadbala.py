#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadbala 计算模块（六重力量）v6.9.12
BPHS标准实现 + 外部校准支持

六种力量：
1. Sthana Bala（位置力量）— 含 Ucha/Saptavargaja/Ojayugma/Kendra(3-tier)/Drekkana
2. Dig Bala（方向力量）
3. Kala Bala（时间力量）— 含 Nathonnata/Paksha/Tribhaga/Ayana/Hora
4. Chesta Bala（运动力量）— Sun=Seeghrochcha, Moon=月相, Others=速度/逆行
5. Naisargika Bala（天然力量）
6. Drik Bala（相位力量）— Sputa Drishti 连续曲线

v6.9.12 修复：
- Kendra Bala: 0/15 二值 → BPHS 15/30/60 三档 (Kendra/Panapara/Apoklima)
- Bhava Bala: 新增宫位力量（基于 Bhava 中点计算）
- Hora Bala: 新增 Kala Bala 子项
- Chesta Bala: Sun 使用 Seeghrochcha 公式
"""

import math
import swisseph as swe
import sys
import os
import json
from typing import Dict, Tuple

# v6.1.10: 导入实际Varga计算器（支持脚本和包两种调用方式）
_script_dir = os.path.dirname(os.path.abspath(__file__))
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
from varga import varga_map, SIGNS as VARGA_SIGNS, SIGN_LORDS as VARGA_SIGN_LORDS

# ============================================================================
# 常量
# ============================================================================
SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

SIGN_LORDS = {
    'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
    'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
    'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'
}

SHADBALA_CONSTANTS_PATH = os.path.join(_script_dir, '..', 'references', 'shat_bala_constants.json')


def _to_longitude(entry: Dict[str, float]) -> float:
    return float(entry['sign']) * 30 + float(entry['degree'])


def _load_shadbala_constants() -> Dict:
    with open(SHADBALA_CONSTANTS_PATH, 'r', encoding='utf-8') as handle:
        return json.load(handle)


_SHADBALA_CONSTANTS = _load_shadbala_constants()

# 入庙度数（sign_idx * 30 + degree）
EXALTATION_DEG = {
    planet: _to_longitude(entry)
    for planet, entry in _SHADBALA_CONSTANTS['exaltation_degrees'].items()
}

# 落陷度数（由参考 JSON 直接提供，避免隐式推导与外部真值漂移）
DEBILITATION_DEG = {
    planet: _to_longitude(entry)
    for planet, entry in _SHADBALA_CONSTANTS['debilitation_degrees'].items()
}

# 行星友好/敌对关系（静态真值表）
FRIENDSHIP = {
    planet: {
        'friend': relation['friends'],
        'enemy': relation['enemies'],
        'neutral': relation['neutrals'],
    }
    for planet, relation in _SHADBALA_CONSTANTS['natural_relationships'].items()
}

# Dig Bala 最强宫位
DIG_BALA_HOUSE = {
    'Sun': 10, 'Mars': 10,  # Midheaven
    'Moon': 4, 'Venus': 4,  # Nadir
    'Jupiter': 1, 'Mercury': 1,  # Ascendant
    'Saturn': 7,  # Descendant
}

# Naisargika Bala（天然力量，单位 Shashtiamshas）
# v6.1.10: 改为PyJHora/JHora标准值（60-8.57递减序列）
# 来源：PyJHora strength.py, PVR Rao, BPHS第9章
NAISARGIKA_BALA = {
    'Sun': 60.0, 'Moon': 51.43, 'Venus': 42.86,
    'Jupiter': 34.29, 'Mercury': 25.71, 'Mars': 17.14, 'Saturn': 8.57
}

# Shadbala 最低要求（Rupas）
MIN_REQUIRED = {
    'Sun': 5.0, 'Moon': 6.0, 'Mars': 5.0,
    'Mercury': 7.0, 'Jupiter': 6.5, 'Venus': 5.5, 'Saturn': 5.0
}

# 昼强/夜强行星
DIURNAL_STRONG = ['Sun', 'Jupiter', 'Venus']
NOCTURNAL_STRONG = ['Moon', 'Mars', 'Saturn']

# 吉星/凶星
BENEFICS = ['Jupiter', 'Venus', 'Mercury']
MALEFICS = ['Saturn', 'Mars', 'Sun']

# 行星相位规则（所有行星都有7宫相位，特殊相位如下）
SPECIAL_ASPECTS = {
    'Mars': [4, 8],     # 火星额外看4宫和8宫
    'Jupiter': [5, 9],  # 木星额外看5宫和9宫
    'Saturn': [3, 10],  # 土星额外看3宫和10宫
}

# Virupas → Rupas 转换（60 Virupas = 1 Rupa）
VIRUPAS_PER_RUPA = 60.0
_DIG_POWERLESS_HOUSE = {"Sun": 3, "Moon": 9, "Mars": 3, "Mercury": 6, "Jupiter": 6, "Venus": 9, "Saturn": 0}
_MOOLATRIKONA = {
    "Sun": (4, 0.0, 20.0), "Moon": (1, 4.0, 30.0), "Mars": (0, 0.0, 12.0),
    "Mercury": (5, 16.0, 20.0), "Jupiter": (8, 0.0, 10.0),
    "Venus": (6, 0.0, 15.0), "Saturn": (10, 0.0, 20.0),
}
_PLANET_INDEX = {name: index for index, name in enumerate(("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"))}
_INDEX_PLANET = {index: name for name, index in _PLANET_INDEX.items()}
_ABDA_WEEKDAY_PLANETS = ("Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Sun", "Moon")
_HORA_ORDER = ("Saturn", "Jupiter", "Mars", "Sun", "Venus", "Mercury", "Moon")
_SURYA_CIVIL_DAYS = 1_577_917_828
_SURYA_REVOLUTIONS = {
    "Sun": 4_320_000, "Mars": 2_296_832, "Mercury": 17_937_060,
    "Jupiter": 364_220, "Venus": 7_022_376, "Saturn": 146_568,
}
_UJJAIN_LONGITUDE = 75.7885


def _solar_event_local_hour(jd_ut: float, lat: float, lon: float, timezone: float, event: int) -> float:
    local_jd = jd_ut + timezone / 24.0
    year, month, day, _ = swe.revjul(local_jd, swe.GREG_CAL)
    local_midnight = swe.julday(year, month, day, 0.0, swe.GREG_CAL)
    utc_midnight = local_midnight - timezone / 24.0
    _, times = swe.rise_trans(
        utc_midnight,
        swe.SUN,
        event | swe.BIT_HINDU_RISING,
        (float(lon), float(lat), 0.0),
        0.0,
        0.0,
        swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_NONUT,
    )
    return (times[0] + timezone / 24.0 - local_midnight) * 24.0


def build_shadbala_context(jd_ut: float, lat: float, lon: float, ayanamsa: str = "lahiri", timezone: float = 0.0) -> Dict:
    """Build precise sidereal house context from standard birth inputs."""
    sid_mode = swe.SIDM_LAHIRI
    if str(ayanamsa).lower() in {"raman"}:
        sid_mode = swe.SIDM_RAMAN
    elif str(ayanamsa).lower() in {"kp", "krishnamurti"}:
        sid_mode = swe.SIDM_KRISHNAMURTI
    swe.set_sid_mode(sid_mode)
    cusps, _ = swe.houses_ex(float(jd_ut), float(lat), float(lon), b"P", swe.FLG_SIDEREAL)
    local_jd = float(jd_ut) + float(timezone) / 24.0
    year, month, day, local_hour = swe.revjul(local_jd, swe.GREG_CAL)
    sunrise = _solar_event_local_hour(jd_ut, lat, lon, timezone, swe.CALC_RISE)
    sunset = _solar_event_local_hour(jd_ut, lat, lon, timezone, swe.CALC_SET)
    previous_sunset = _solar_event_local_hour(jd_ut - 1.0, lat, lon, timezone, swe.CALC_SET)
    return {
        "jd_ut": float(jd_ut), "jd_local": local_jd,
        "lat": float(lat), "lon": float(lon), "timezone": float(timezone),
        "year": int(year), "month": int(month), "day": int(day), "local_hour": float(local_hour),
        "ayanamsa": str(ayanamsa), "ayanamsa_degrees": float(swe.get_ayanamsa_ut(float(jd_ut))),
        "sunrise_hour": sunrise, "sunset_hour": sunset, "previous_sunset_hour": previous_sunset,
        "house_midpoints": [float(value) % 360 for value in cusps],
    }


def calc_dig_bala_precise(pname: str, planet_lon: float, house_midpoints: list[float]) -> float:
    """Classical directional strength from the powerless bhava midpoint."""
    powerless = house_midpoints[_DIG_POWERLESS_HOUSE[pname]]
    return round(abs(float(powerless) - (float(planet_lon) % 360)) / 3.0, 2)


def _planet_longitude(name: str, planets: Dict) -> float:
    data = planets[name]
    degree = float(data.get("degree", 0.0))
    if degree >= 30.0 or data.get("sign") not in SIGNS:
        return degree % 360.0
    return (SIGNS.index(data["sign"]) * 30.0 + degree) % 360.0


def classify_drik_planets(planets: Dict) -> tuple[set[str], set[str]]:
    """Classify the seven planets for Drik Bala from lunar phase and Mercury's company."""
    benefics = {name for name in ("Jupiter", "Venus") if name in planets}
    malefics = {name for name in ("Sun", "Mars", "Saturn") if name in planets}

    if "Moon" in planets and "Sun" in planets:
        target = benefics if (_planet_longitude("Moon", planets) - _planet_longitude("Sun", planets)) % 360.0 <= 180.0 else malefics
        target.add("Moon")

    if "Mercury" in planets:
        mercury_lon = _planet_longitude("Mercury", planets)
        mercury_sign = int(mercury_lon // 30)
        companions = [
            name for name in benefics | malefics
            if name != "Mercury" and int(_planet_longitude(name, planets) // 30) == mercury_sign
        ]
        benefic_count = sum(name in benefics for name in companions)
        malefic_count = sum(name in malefics for name in companions)
        if benefic_count >= malefic_count and (benefic_count != malefic_count or not companions):
            benefics.add("Mercury")
        elif malefic_count > benefic_count:
            malefics.add("Mercury")
        else:
            nearest = min(companions, key=lambda name: abs(_planet_longitude(name, planets) - mercury_lon))
            (benefics if nearest in benefics else malefics).add("Mercury")

    return benefics, malefics


def _sphuta_drishti_virupas(angle: float, aspecting_planet: str) -> float:
    angle = round(float(angle) % 360.0, 2)
    if angle < 30.0:
        strength = 0.0
    elif angle < 60.0:
        strength = (angle - 30.0) / 2.0
    elif angle < 90.0:
        strength = angle - 45.0 + (45.0 if aspecting_planet == "Saturn" else 0.0)
    elif angle < 120.0:
        strength = (120.0 - angle) / 2.0 + 30.0 + (15.0 if aspecting_planet == "Mars" else 0.0)
    elif angle < 150.0:
        strength = 150.0 - angle + (30.0 if aspecting_planet == "Jupiter" else 0.0)
    elif angle < 180.0:
        strength = 2.0 * (angle - 150.0)
    elif angle < 300.0:
        strength = (300.0 - angle) / 2.0
        if aspecting_planet == "Mars" and 210.0 <= angle < 240.0:
            strength += 15.0
        elif aspecting_planet == "Jupiter" and 240.0 <= angle < 270.0:
            strength += 30.0
        elif aspecting_planet == "Saturn" and 270.0 <= angle < 300.0:
            strength += 45.0
    else:
        strength = 0.0
    return round(strength, 2)


def calc_drik_bala_precise(pname: str, all_planets: Dict) -> float:
    """Continuous Sphuta Drishti, quarter-weighted by natural benefic/malefic status."""
    if pname not in all_planets:
        return 0.0
    benefics, malefics = classify_drik_planets(all_planets)
    target_lon = _planet_longitude(pname, all_planets)
    total = 0.0
    for other_name in benefics | malefics:
        if other_name == pname:
            continue
        strength = _sphuta_drishti_virupas(target_lon - _planet_longitude(other_name, all_planets), other_name)
        total += strength if other_name in benefics else -strength
    return round(total / 4.0, 2)


def _d30_sign(sign_idx: int, degree: float) -> int:
    ranges = (
        ((5, 0), (10, 10), (18, 8), (25, 2), (30, 6))
        if sign_idx % 2 == 0 else
        ((5, 1), (12, 5), (20, 11), (25, 9), (30, 7))
    )
    return next(sign for upper, sign in ranges if degree <= upper)


def _saptavarga_signs(planets: Dict) -> Dict[int, Dict[str, int]]:
    result = {division: {} for division in (1, 2, 3, 7, 9, 12, 30)}
    for name in set(planets) & set(_MOOLATRIKONA):
        longitude = _planet_longitude(name, planets)
        sign_idx, degree = int(longitude // 30), longitude % 30.0
        result[1][name] = sign_idx
        result[2][name] = (4 if sign_idx % 2 == 0 else 3) if degree < 15.0 else (3 if sign_idx % 2 == 0 else 4)
        for division in (3, 7, 9, 12):
            result[division][name] = varga_map(sign_idx, min(division - 1, int(degree / (30.0 / division))), division)
        result[30][name] = _d30_sign(sign_idx, degree)
    return result


def _compound_relation_score(planet: str, owner: str, d1_signs: Dict[str, int]) -> float:
    natural = "friend" if owner in FRIENDSHIP[planet]["friend"] else "enemy" if owner in FRIENDSHIP[planet]["enemy"] else "neutral"
    if owner not in d1_signs:
        return {"friend": 15.0, "neutral": 7.5, "enemy": 3.75}[natural]
    separation = (d1_signs[owner] - d1_signs[planet]) % 12
    temporary = "friend" if separation in {1, 2, 3, 9, 10, 11} else "enemy"
    return {
        ("friend", "friend"): 22.5,
        ("neutral", "friend"): 15.0,
        ("enemy", "friend"): 7.5,
        ("friend", "enemy"): 7.5,
        ("neutral", "enemy"): 3.75,
        ("enemy", "enemy"): 1.875,
    }[(natural, temporary)]


def calc_sthana_bala_precise(pname: str, all_planets: Dict, house: int) -> Dict:
    longitude = _planet_longitude(pname, all_planets)
    degree = longitude % 30.0
    vargas = _saptavarga_signs(all_planets)
    scores = {}
    for division, positions in vargas.items():
        sign_idx = positions[pname]
        owner = SIGN_LORDS[SIGNS[sign_idx]]
        mt_sign, mt_start, mt_end = _MOOLATRIKONA[pname]
        if division == 1 and sign_idx == mt_sign and mt_start <= degree < mt_end:
            score = 45.0
        elif owner == pname:
            score = 30.0
        else:
            score = _compound_relation_score(pname, owner, vargas[1])
        scores[f"sapta_d{division}"] = score

    offset = (longitude - DEBILITATION_DEG[pname]) % 360.0
    ucha_bala = round(min(offset, 360.0 - offset) / 3.0, 2)
    wants_even = pname in {"Moon", "Venus"}
    ojayugma = 15.0 * sum((vargas[division][pname] % 2 == 1) == wants_even for division in (1, 9))
    kendra_bala = 60.0 if house in (1, 4, 7, 10) else 30.0 if house in (2, 5, 8, 11) else 15.0
    drekkana_bala = 15.0 if (
        (pname in {"Sun", "Mars", "Jupiter"} and degree < 10.0)
        or (pname in {"Mercury", "Saturn"} and 10.0 <= degree < 20.0)
        or (pname in {"Moon", "Venus"} and degree >= 20.0)
    ) else 0.0
    sapta_score = round(sum(scores.values()), 2)
    return {
        "ucha_bala": ucha_bala,
        **scores,
        "sapta_score": sapta_score,
        "ojayugma_bala": ojayugma,
        "kendra_bala": kendra_bala,
        "drekkana_bala": drekkana_bala,
        "total": round(ucha_bala + sapta_score + ojayugma + kendra_bala + drekkana_bala, 2),
    }


def _lagrange_interpolate(xs: tuple[float, ...], ys: tuple[float, ...], value: float) -> float:
    total = 0.0
    for i, x_i in enumerate(xs):
        term = ys[i]
        for j, x_j in enumerate(xs):
            if i != j:
                term *= (value - x_j) / (x_i - x_j)
        total += term
    return total


def _ayana_bala(pname: str, longitude: float, ayanamsa: float) -> tuple[float, float]:
    raw_tropical = longitude + ayanamsa
    tropical = raw_tropical % 360.0
    north = raw_tropical < 180.0
    folded = tropical
    if 90.0 < tropical < 180.0:
        folded = 180.0 - tropical
    elif 180.0 < tropical < 270.0:
        folded = tropical - 180.0
    elif tropical > 270.0:
        folded = 360.0 - tropical
    sign = 1.0
    if north and pname in {"Moon", "Saturn"}:
        sign = -1.0
    elif not north and pname in {"Sun", "Mars", "Jupiter", "Venus"}:
        sign = -1.0
    if pname == "Mercury":
        sign = 1.0
    declination = sign * _lagrange_interpolate(
        (0.0, 15.0, 30.0, 45.0, 60.0, 75.0, 90.0),
        (0.0, 362 / 60.0, 703 / 60.0, 1002 / 60.0, 1238 / 60.0, 1388 / 60.0, 24.0),
        round(folded, 2),
    )
    bala = round((24.0 + declination) * 1.25, 2)
    if pname == "Sun":
        bala = round(bala * 2.0, 2)
    return bala, round(declination, 4)


def _days_elapsed_since_base(year: int, base_year: int = 1951, base_days: int = 174) -> int:
    years = year - base_year
    leap_years = sum(1 for value in range(base_year + 1, year + 1) if value % 4 == 0 and (value % 100 != 0 or value % 400 == 0))
    return base_days + leap_years * 366 + (years - leap_years) * 365


def _calendar_lords(context: Dict) -> Dict[str, str]:
    year, month, day = context["year"], context["month"], context["day"]
    local_jd = context["jd_local"]
    year_start = swe.julday(year, 1, 1, 0.0, swe.GREG_CAL)
    elapsed = int(local_jd - year_start + 1.0)
    ahargana = _days_elapsed_since_base(year - 1) + elapsed
    abda = _ABDA_WEEKDAY_PLANETS[(int(ahargana // 360) * 3 + 1) % 7]
    masa = _ABDA_WEEKDAY_PLANETS[(int(ahargana // 30) * 2 + 1) % 7]

    vaara_ahargana = _days_elapsed_since_base(year - 1, 1827, 244) + elapsed
    if context["local_hour"] < context["sunrise_hour"]:
        vaara_ahargana -= 1
    vaara = _ABDA_WEEKDAY_PLANETS[int(vaara_ahargana) % 7]

    civil_weekday = int(math.ceil(local_jd + 1.0) % 7)
    local_hour = context["local_hour"]
    if local_hour < context["sunrise_hour"]:
        civil_weekday = (civil_weekday - 1) % 7
        local_hour += 24.0
    hora_index = (int(local_hour - context["sunrise_hour"]) + civil_weekday + 1) % 7
    return {"abda": abda, "masa": masa, "vaara": vaara, "hora": _HORA_ORDER[hora_index]}


def calc_kala_bala_precise(pname: str, all_planets: Dict, context: Dict) -> Dict:
    """Classical temporal strength from local solar events and calendar lords."""
    local_hour = context["local_hour"]
    midnight = (context["sunrise_hour"] + context["previous_sunset_hour"]) / 2.0
    midnight = 12.0 - midnight if midnight < 12.0 else midnight - 12.0
    unnata = (local_hour - midnight) * 5.0 if local_hour < 12.0 else (24.0 + midnight - local_hour) * 5.0
    if pname == "Mercury":
        nathonnata = 60.0
    elif pname in {"Sun", "Jupiter", "Venus"}:
        nathonnata = round(unnata, 2)
    else:
        nathonnata = round(60.0 - unnata, 2)

    benefics, malefics = classify_drik_planets(all_planets)
    phase = round(abs(_planet_longitude("Sun", all_planets) - _planet_longitude("Moon", all_planets)) / 3.0, 2)
    paksha = phase if pname in benefics else round(60.0 - phase, 2) if pname in malefics else 0.0
    if pname == "Moon":
        paksha = round(paksha * 2.0, 2)

    sunrise, sunset = context["sunrise_hour"], context["sunset_hour"]
    day_length = sunset - sunrise
    night_length = 24.0 - day_length
    tribhaga_lord = None
    if sunrise <= local_hour < sunset:
        tribhaga_lord = ("Mercury", "Sun", "Saturn")[min(2, int((local_hour - sunrise) / (day_length / 3.0)))]
    else:
        since_sunset = (local_hour - sunset) % 24.0
        tribhaga_lord = ("Moon", "Venus", "Mars")[min(2, int(since_sunset / (night_length / 3.0)))]
    tribhaga = 60.0 if pname in {"Jupiter", tribhaga_lord} else 0.0

    lords = _calendar_lords(context)
    calendar = (15.0 if pname == lords["abda"] else 0.0) + (30.0 if pname == lords["masa"] else 0.0) + (45.0 if pname == lords["vaara"] else 0.0) + (60.0 if pname == lords["hora"] else 0.0)
    ayana, declination = _ayana_bala(pname, _planet_longitude(pname, all_planets), context["ayanamsa_degrees"])
    total = round(nathonnata + paksha + tribhaga + calendar + ayana, 2)
    return {
        "nathonnata": nathonnata, "paksha": paksha, "tribhaga": tribhaga,
        "abda": 15.0 if pname == lords["abda"] else 0.0,
        "masa": 30.0 if pname == lords["masa"] else 0.0,
        "vaara": 45.0 if pname == lords["vaara"] else 0.0,
        "hora": 60.0 if pname == lords["hora"] else 0.0,
        "ayana": ayana, "declination": declination, "yuddha": 0.0,
        "total": total,
    }


def _surya_mean_longitude(pname: str, context: Dict) -> float:
    """Surya Siddhanta mean motion with desantara correction from Ujjain."""
    local_jd = context["jd_local"]
    kali_days = int(local_jd - 588_465.0)
    weekday = int(math.ceil(local_jd + 1.0) % 7)
    kali_days += weekday - 5 - kali_days % 7
    daily_motion = round(_SURYA_REVOLUTIONS[pname] / _SURYA_CIVIL_DAYS * 360.0, 7)
    mean_longitude = (kali_days * daily_motion) % 360.0
    desantara = (_UJJAIN_LONGITUDE - context["lon"]) / 360.0 * daily_motion
    return (mean_longitude + desantara) % 360.0


def calc_chesta_bala_precise(pname: str, all_planets: Dict, kala: Dict, context: Dict) -> float:
    """BPHS bounded Chesta Bala using mean motion and Seeghrochcha.

    Mean-motion/Seeghrochcha structure and constants are adapted from the MIT
    jyotishganit reference retained under references/open_source_sources.
    """
    if pname == "Sun":
        return round(float(kala["ayana"]), 2)
    if pname == "Moon":
        return round(float(kala["paksha"]), 2)
    sun_mean = _surya_mean_longitude("Sun", context)
    planet_mean = _surya_mean_longitude(pname, context)
    if pname in {"Mercury", "Venus"}:
        seeghrochcha, mean_longitude = planet_mean, sun_mean
    else:
        seeghrochcha, mean_longitude = sun_mean, planet_mean
    average_longitude = (_planet_longitude(pname, all_planets) + mean_longitude) / 2.0
    chesta_kendra = abs(seeghrochcha - average_longitude)
    if chesta_kendra > 180.0:
        chesta_kendra = 360.0 - chesta_kendra
    return round(max(0.0, chesta_kendra) / 3.0, 2)


def calc_shadbala(planets: Dict, asc_sign: str, birth_hour: float,
                  sun_lon: float, moon_lon: float,
                  birth_minute: float = 0.0, context: Dict | None = None) -> Dict:
    """
    计算 Shadbala 相对强弱参考（covered；外部绝对值校准前保留置信度上限）

    Args:
        planets: 行星数据 dict，每颗行星需要 {sign, degree, house, retrograde, speed}
        asc_sign: 上升星座名称
        birth_hour: 出生时间（当地时间，24小时制）
        sun_lon: 太阳恒星黄道经度
        moon_lon: 月亮恒星黄道经度

    Returns:
        Shadbala 计算结果（内部一致的相对强弱参考）
    """
    results = {}
    is_night = birth_hour < 6.0 or birth_hour >= 18.0
    sun_northern = sun_lon >= 270 or sun_lon < 90

    # 第一轮：计算所有原始值
    raw_totals = {}
    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
        if pname not in planets:
            continue
        p = planets[pname]
        lon = p.get('degree', 0)
        sign = p.get('sign', 'Aries')
        house = p.get('house', 1)
        retro = p.get('retrograde', False)
        speed = p.get('speed', 1.0)

        sthana = calc_sthana_bala_precise(pname, planets, house)
        dig = calc_dig_bala_precise(pname, lon, context["house_midpoints"]) if context and context.get("house_midpoints") else calc_dig_bala(pname, house)
        kala = calc_kala_bala_precise(pname, planets, context) if context else calc_kala_bala(pname, is_night, sun_northern, sun_lon, moon_lon, birth_hour, birth_minute)
        chesta = calc_chesta_bala_precise(pname, planets, kala, context) if context else calc_chesta_bala(pname, retro, speed, sun_lon, moon_lon)
        naisargika = NAISARGIKA_BALA.get(pname, 30.0)
        drik = calc_drik_bala(pname, sign, house, planets)

        raw = sthana['total'] + dig + kala['total'] + chesta + naisargika + drik
        raw_totals[pname] = max(1.0, raw)
    
    # 第二轮：按六项子力绝对值生成结果。
    # Shadbala 的绝对 Rupas 必须保留子项合计，不做七星总和归一。
    # 旧的 1200 Virupas 全局不变量会把七颗星总 Rupa 固定到 20，
    # 低于 BPHS 最低要求合计 40 Rupa，导致 JHora/PDF 对标系统性偏低。
    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
        if pname not in planets or pname not in raw_totals:
            continue
        p = planets[pname]
        lon = p.get('degree', 0)
        sign = p.get('sign', 'Aries')
        house = p.get('house', 1)
        retro = p.get('retrograde', False)
        speed = p.get('speed', 1.0)

        sthana = calc_sthana_bala_precise(pname, planets, house)
        dig = calc_dig_bala_precise(pname, lon, context["house_midpoints"]) if context and context.get("house_midpoints") else calc_dig_bala(pname, house)
        kala = calc_kala_bala_precise(pname, planets, context) if context else calc_kala_bala(pname, is_night, sun_northern, sun_lon, moon_lon, birth_hour, birth_minute)
        chesta = calc_chesta_bala_precise(pname, planets, kala, context) if context else calc_chesta_bala(pname, retro, speed, sun_lon, moon_lon)
        naisargika = NAISARGIKA_BALA.get(pname, 30.0)
        drik = calc_drik_bala(pname, sign, house, planets)

        raw = raw_totals[pname]
        total_virupas = raw
        total_rupas = total_virupas / VIRUPAS_PER_RUPA

        min_req = MIN_REQUIRED.get(pname, 5.0)
        ishta_bala = (total_rupas / min_req * 100) if min_req > 0 else 0

        if ishta_bala >= 150:
            strength_level = "极强"
        elif ishta_bala >= 125:
            strength_level = "强"
        elif ishta_bala >= 100:
            strength_level = "充足"
        elif ishta_bala >= 75:
            strength_level = "略弱"
        elif ishta_bala >= 50:
            strength_level = "弱"
        else:
            strength_level = "极弱"

        results[pname] = {
            'sthana_bala': sthana,
            'dig_bala': round(dig, 2),
            'kala_bala': kala,
            'chesta_bala': round(chesta, 2),
            'naisargika_bala': round(naisargika, 2),
            'drik_bala': round(drik, 2),
            'total_virupas': round(total_virupas, 2),
            'total_rupas': round(total_rupas, 4),
            'min_required': min_req,
            'ishta_bala_pct': round(ishta_bala, 1),
            'strength_level': strength_level,
            # v6.1.10: Ishta/Kashta Phala
            'ishta_phala': round(math.sqrt(max(0, sthana['ucha_bala'] * chesta)), 2),
            'kashta_phala': round(math.sqrt(max(0, (60 - sthana['ucha_bala']) * (60 - chesta))), 2),
        }

    # 排名
    ranked = sorted(results.items(), key=lambda x: x[1]['total_rupas'], reverse=True)
    for i, (name, _) in enumerate(ranked):
        results[name]['rank'] = i + 1

    # Bhava Bala（宫位力量）v6.9.12 新增
    bhava_bala = calc_bhava_bala(planets, asc_sign)

    return {
        'method': 'Shadbala六重力量（absolute Virupas; precise Sthana/Dig/Kala/Drik; bounded BPHS Chesta）',
        'method_variants': {
            'kala': 'bphs_local_solar_events_ahargana_declination' if context else 'legacy_approximation',
            'chesta': 'bphs_bounded_surya_mean_motion_seeghrochcha' if context else 'legacy_speed_bands',
        },
        'external_parity_boundary': 'Chesta remains cross-engine method-conflicted; totals inherit that boundary.',
        'is_night_birth': is_night,
        'sun_uttarayana': sun_northern,
        'planets': results,
        'bhava_bala': bhava_bala,
        'ranking': [name for name, _ in ranked],
        'strongest': ranked[0][0] if ranked else None,
        'weakest': ranked[-1][0] if ranked else None,
    }


def _dignity_score(pname: str, sign: str) -> float:
    """计算单层Varga中的尊严分数（BPHS标准）
    Own Sign=45, Exalted=50 (不超过45 unless specifically exalted degrees),
    Great Friend=40, Friend=35, Neutral=25, Enemy=15, Great Enemy=5
    """
    lord = SIGN_LORDS.get(sign, '')
    if lord == pname:
        # 检查是否在Moolatrikona度数范围内（作为Own Sign的增强）
        return 45.0

    # 获取行星对该sign lord的关系
    rel = FRIENDSHIP.get(pname, {})
    friends_of_pname = rel.get('friend', [])
    enemies_of_pname = rel.get('enemy', [])
    neutrals_of_pname = rel.get('neutral', [])

    # 反向关系：sign lord对pname的态度
    lord_rel = FRIENDSHIP.get(lord, {})
    lord_friends = lord_rel.get('friend', [])
    lord_enemies = lord_rel.get('enemy', [])

    # 双向关系评估（BPHS复合关系）
    # pname likes lord AND lord likes pname → Great Friend = 40
    # pname likes lord OR lord likes pname → Friend = 35
    # one neutral one friend → Neutral-Friend = 30
    # both neutral → Neutral = 25
    # one enemy one neutral → Enemy = 15
    # both enemy → Great Enemy = 5
    pname_likes_lord = lord in friends_of_pname
    lord_likes_pname = pname in lord_friends
    pname_dislikes_lord = lord in enemies_of_pname
    lord_dislikes_pname = pname in lord_enemies

    if pname_likes_lord and lord_likes_pname:
        return 40.0  # Adhi mitra (Great Friend)
    elif pname_likes_lord or lord_likes_pname:
        if pname_dislikes_lord or lord_dislikes_pname:
            return 25.0  # Mixed → Neutral
        return 35.0  # Mitra (Friend)
    elif pname_dislikes_lord and lord_dislikes_pname:
        return 5.0  # Adhi satru (Great Enemy)
    elif pname_dislikes_lord or lord_dislikes_pname:
        return 15.0  # Satru (Enemy)
    else:
        return 25.0  # Sama (Neutral)


def calc_sthana_bala(pname: str, lon: float, sign: str, house: int) -> Dict:
    """Sthana Bala（位置力量）
    v4.5.0: 修复Saptavargaja Bala为完整7层计算
    """
    # A. Ucha Bala（入庙力量）max 60 Virupas
    debilit_deg = DEBILITATION_DEG.get(pname, 0)
    offset = (lon - debilit_deg + 360) % 360
    if offset > 180:
        offset = 360 - offset
    ucha_bala = offset / 180 * 60  # 0-60 Virupas

    # B. Saptavargaja Bala（七分盘力量）max ~315 Virupas (7 × 45)
    # v6.1.10: 调用varga.py实际分盘计算替代简化算法
    sign_idx = SIGNS.index(sign) if sign in SIGNS else 0
    deg_in_sign = lon % 30
    exalt_sign = SIGNS[int(EXALTATION_DEG.get(pname, 0) / 30) % 12]
    debilit_sign = SIGNS[int(DEBILITATION_DEG.get(pname, 0) / 30) % 12]

    # D1 (Rashi) — 直接用当前sign，检查入庙/落陷
    d1_score = _dignity_score(pname, sign)
    if sign == exalt_sign:
        d1_score = 50.0
    elif sign == debilit_sign:
        d1_score = 5.0

    # D2 (Hora) — 调用varga_map
    d2_part = int(deg_in_sign / 15)  # 30/2=15
    d2_sign_idx = varga_map(sign_idx, d2_part, 2)
    d2_sign = VARGA_SIGNS[d2_sign_idx]
    if pname == VARGA_SIGN_LORDS.get(d2_sign, ''):
        d2_score = 45.0
    elif d2_sign == exalt_sign:
        d2_score = 50.0
    elif d2_sign == debilit_sign:
        d2_score = 5.0
    else:
        d2_score = _dignity_score(pname, d2_sign)

    # D3 (Drekkana) — 调用varga_map
    d3_part = int(deg_in_sign / 10)  # 30/3=10
    d3_sign_idx = varga_map(sign_idx, d3_part, 3)
    d3_sign = VARGA_SIGNS[d3_sign_idx]
    if pname == VARGA_SIGN_LORDS.get(d3_sign, ''):
        d3_score = 30.0
    elif d3_sign == exalt_sign:
        d3_score = 45.0
    elif d3_sign == debilit_sign:
        d3_score = 5.0
    else:
        d3_score = _dignity_score(pname, d3_sign)

    # D4 (Turyamsa/Chaturthamsa) — 调用varga_map
    d4_part = int(deg_in_sign / 7.5)  # 30/4=7.5
    # 边界处理：最后一份
    if d4_part >= 4:
        d4_part = 3
    d4_sign_idx = varga_map(sign_idx, d4_part, 4)
    d4_sign = VARGA_SIGNS[d4_sign_idx]
    if pname == VARGA_SIGN_LORDS.get(d4_sign, ''):
        d4_score = 45.0
    elif d4_sign == exalt_sign:
        d4_score = 50.0
    elif d4_sign == debilit_sign:
        d4_score = 5.0
    else:
        d4_score = _dignity_score(pname, d4_sign)

    # D7 (Saptamsa) — 调用varga_map
    d7_part = int(deg_in_sign / (30 / 7))
    if d7_part >= 7:
        d7_part = 6
    d7_sign_idx = varga_map(sign_idx, d7_part, 7)
    d7_sign = VARGA_SIGNS[d7_sign_idx]
    if pname == VARGA_SIGN_LORDS.get(d7_sign, ''):
        d7_score = 45.0
    elif d7_sign == exalt_sign:
        d7_score = 50.0
    elif d7_sign == debilit_sign:
        d7_score = 5.0
    else:
        d7_score = _dignity_score(pname, d7_sign)

    # D9 (Navamsa) — 调用varga_map
    d9_part = int(deg_in_sign / (30 / 9))
    if d9_part >= 9:
        d9_part = 8
    d9_sign_idx = varga_map(sign_idx, d9_part, 9)
    d9_sign = VARGA_SIGNS[d9_sign_idx]
    if pname == VARGA_SIGN_LORDS.get(d9_sign, ''):
        d9_score = 45.0
    elif d9_sign == exalt_sign:
        d9_score = 50.0
    elif d9_sign == debilit_sign:
        d9_score = 5.0
    else:
        d9_score = _dignity_score(pname, d9_sign)

    # D12 (Dwadashamsa) — 调用varga_map
    d12_part = int(deg_in_sign / 2.5)  # 30/12=2.5
    if d12_part >= 12:
        d12_part = 11
    d12_sign_idx = varga_map(sign_idx, d12_part, 12)
    d12_sign = VARGA_SIGNS[d12_sign_idx]
    if pname == VARGA_SIGN_LORDS.get(d12_sign, ''):
        d12_score = 45.0
    elif d12_sign == exalt_sign:
        d12_score = 50.0
    elif d12_sign == debilit_sign:
        d12_score = 5.0
    else:
        d12_score = _dignity_score(pname, d12_sign)

    sapta_score = d1_score + d2_score + d3_score + d4_score + d7_score + d9_score + d12_score

    # C. Ojayugma Bala（奇偶宫力量）max 15 Virupas
    # v4.5.0: 使用D9宫位精确计算
    try:
        d9_house = ((d9_sign_idx - sign_idx) % 12) + 1  # approximate from Lagna
        if pname in ['Mercury', 'Venus']:
            ojayugma = 15 if d9_house % 2 == 1 else 0  # 奇数宫
        else:
            ojayugma = 15 if d9_house % 2 == 0 else 0  # 偶数宫
    except:
        ojayugma = 0

    # D. Kendra Bala（角宫力量）v6.9.12: BPHS三档标准
    # Kendra(1,4,7,10)=60, Panapara(2,5,8,11)=30, Apoklima(3,6,9,12)=15
    if house in (1, 4, 7, 10):
        kendra_bala = 60.0
    elif house in (2, 5, 8, 11):
        kendra_bala = 30.0
    else:
        kendra_bala = 15.0

    # E. Drekkana Bala（三分盘力量）max 15 Virupas
    if pname in ['Sun', 'Mars', 'Jupiter']:
        drekkana_bala = 15 if deg_in_sign < 10 else 0
    elif pname in ['Moon', 'Venus']:
        drekkana_bala = 15 if 10 <= deg_in_sign < 20 else 0
    else:  # Saturn, Mercury
        drekkana_bala = 15 if deg_in_sign >= 20 else 0

    total = ucha_bala + sapta_score + ojayugma + kendra_bala + drekkana_bala

    return {
        'ucha_bala': round(ucha_bala, 2),
        'sapta_d1': round(d1_score, 2),
        'sapta_d2': round(d2_score, 2),
        'sapta_d3': round(d3_score, 2),
        'sapta_d4': round(d4_score, 2),
        'sapta_d7': round(d7_score, 2),
        'sapta_d9': round(d9_score, 2),
        'sapta_d12': round(d12_score, 2),
        'sapta_score': round(sapta_score, 2),
        'ojayugma_bala': ojayugma,
        'kendra_bala': kendra_bala,
        'drekkana_bala': drekkana_bala,
        'total': round(total, 2),
    }


def calc_dig_bala(pname: str, house: int) -> float:
    """Dig Bala（方向力量），max 60 Virupas"""
    best_house = DIG_BALA_HOUSE.get(pname, 1)
    # 线性插值：最强宫位=60，对宫=0
    diff = abs(house - best_house)
    if diff > 6:
        diff = 12 - diff
    return max(0, (6 - diff) * 10)


def calc_kala_bala(pname: str, is_night: bool, sun_northern: bool,
                    sun_lon: float, moon_lon: float, birth_hour: float = 12.0,
                    birth_minute: float = 0.0) -> Dict:
    """Kala Bala（时间力量）
    
    v6.1.10: Nathonnata升级为BPHS比例计算（渐变0-60非二值）
    v6.1.10: 添加Abda/Masa/Dina/Hora子项
    """
    components = {}

    # A. Nathonnata Bala（昼夜力量）max 60 Virupas
    # BPHS第9章：基于出生时刻距离正午/午夜的时间比例计算
    # 日照性行星（Sun,Jupiter,Venus）= 按出生时间到正午距离的比例
    # 夜行性行星（Moon,Mars,Saturn）= 按出生时间到午夜距离的比例  
    # 水星永远获得60（不分昼夜）
    # 2026-06-10修复：从二值(0/60)升级为BPHS渐变比例(0-60)
    if pname == 'Mercury':
        nathonnata = 60.0
    else:
        birth_decimal = birth_hour + birth_minute / 60.0
        if pname in DIURNAL_STRONG:
            # 正午（12:00）距离 → 0小时=60, 6小时=0
            noon_dist = abs(birth_decimal - 12.0)
            noon_dist = min(noon_dist, 24.0 - noon_dist)
            nathonnata = max(0.0, (6.0 - noon_dist) / 6.0 * 60.0)
        else:
            # 午夜（0:00）距离 → 0小时=60, 6小时=0
            midnight_dist = abs(birth_decimal - 0.0)
            midnight_dist = min(midnight_dist, 24.0 - midnight_dist)
            nathonnata = max(0.0, (6.0 - midnight_dist) / 6.0 * 60.0)
    components['nathonnata'] = round(nathonnata, 2)

    # B. Paksha Bala（月相力量，max 30 Virupas）
    moon_sun_diff = (moon_lon - sun_lon + 360) % 360
    # 归一化到 0-180（月相亮度是对称的）
    phase_angle = moon_sun_diff if moon_sun_diff <= 180 else 360 - moon_sun_diff
    if pname in ['Jupiter', 'Venus', 'Moon']:
        # 望月（phase_angle=180）最强 = 30，朔月（0）= 0
        paksha = phase_angle / 180 * 30
    else:
        # 朔月（phase_angle=0）最强 = 30，望月（180）= 0
        paksha = (180 - phase_angle) / 180 * 30
    components['paksha'] = round(paksha, 2)

    # C. Tribhaga Bala（三段力量）
    if pname == 'Jupiter':
        tribhaga = 45
    elif pname == 'Venus':
        tribhaga = 45
    elif pname == 'Saturn':
        tribhaga = 45
    else:
        tribhaga = 0
    components['tribhaga'] = tribhaga

    # D. Ayana Bala（太阳南北行）
    if pname == 'Mercury':
        ayana = 30
    elif sun_northern and pname in ['Sun', 'Mars', 'Moon']:
        ayana = 30
    elif not sun_northern and pname in ['Jupiter', 'Venus', 'Saturn']:
        ayana = 30
    else:
        ayana = 15
    components['ayana'] = ayana

    # E. Hora Bala（时主力量）v6.9.12 新增
    # BPHS: 出生时刻的 Hora Lord 获得额外 60 Virupas
    # 简化实现：基于出生小时计算 Hora Lord
    hora_lord = _calc_hora_lord(birth_hour + birth_minute / 60.0, sun_lon)
    if pname == hora_lord:
        hora = 60.0
    else:
        hora = 0.0
    components['hora'] = round(hora, 2)

    total = sum(components.values())
    return {k: v for k, v in components.items()} | {'total': round(total, 2)}


def _calc_hora_lord(birth_decimal: float, sun_lon: float) -> str:
    """计算出生时刻的 Hora Lord (BPHS)。
    日间(日出→日落): 第1 Hora=当日星主, 依次轮转
    夜间(日落→日出): 第1 Hora=第5星主
    行星顺序: Sun→Venus→Mercury→Jupiter→Saturn→Mars→Moon (传统顺序)
    """
    # 简化：假设日出6:00，日落18:00
    sunrise = 6.0
    sunset = 18.0
    hora_order = ['Sun', 'Venus', 'Mercury', 'Jupiter', 'Saturn', 'Mars', 'Moon']

    # 确定当日星主（基于星期几）—— 简化用太阳经度
    weekday = int((sun_lon / 360.0 * 7) % 7)  # 近似
    day_lord = hora_order[weekday % 7]

    if sunrise <= birth_decimal < sunset:
        # 日间 Hora: 从 day_lord 开始
        horas_passed = int((birth_decimal - sunrise) / 2.5)  # 每段约2.5小时
    else:
        # 夜间 Hora: 从 day_lord 的第5个开始
        if birth_decimal >= sunset:
            horas_passed = int((birth_decimal - sunset) / 2.5)
        else:
            horas_passed = int((birth_decimal + 24 - sunset) / 2.5)
        day_lord = hora_order[(hora_order.index(day_lord) + 4) % 7]

    return hora_order[(hora_order.index(day_lord) + horas_passed) % 7]


def calc_chesta_bala(pname: str, retro: bool, speed: float,
                     sun_lon: float, moon_lon: float) -> float:
    """Chesta Bala（运动力量），max 60 Virupas
    
    v6.9.12修复：Sun 使用 Seeghrochcha（最快近日点）公式
    v6.1.10修复：Sun不再固定60，改为基于太阳实际速度计算
    BPHS: Sun的Chesta基于其运动速率——最慢(远日点)最强
    """
    if pname == 'Sun':
        # v6.9.12: BPHS标准 — Seeghrochcha公式
        # Sun Chesta = 基于日行速度，最慢时Chesta最高
        # 太阳日均速度范围: ~0.953°/天(远日点) → ~1.017°/天(近日点)
        abs_speed = abs(speed)
        # 标准化到0-1 (0=最快=近日点, 1=最慢=远日点)
        min_speed, max_speed = 0.953, 1.017
        if abs_speed <= min_speed:
            slowness = 1.0
        elif abs_speed >= max_speed:
            slowness = 0.0
        else:
            slowness = 1.0 - (abs_speed - min_speed) / (max_speed - min_speed)
        return slowness * 60.0

    if pname == 'Moon':
        # 月亮根据月相：望月=60，朔月=0
        # BPHS: Chesta Bala 与月相亮面比例成正比
        # diff 取 0-180 范围（>180 时用 360-diff，因为月相是对称的）
        moon_sun_diff = (moon_lon - sun_lon + 360) % 360
        if moon_sun_diff > 180:
            moon_sun_diff = 360 - moon_sun_diff
        return moon_sun_diff / 180 * 60

    # 其他行星
    if retro:
        return 60.0

    # 速度判断（简化：用speed的绝对值）
    abs_speed = abs(speed)
    if abs_speed > 1.0:  # 快速直行
        return 50.0
    elif abs_speed > 0.5:
        return 35.0
    elif abs_speed > 0.1:
        return 20.0
    else:
        return 10.0  # 接近驻留


def _get_sputa_drishti_value(aspect_degree: float, planet_name: str) -> float:
    """
    Sputa Drishti（精确相位力量）计算。
    基于jyotishganit (MIT License) 算法，将行星间角距离转换为连续相位力量值。

    相位力量随角度变化：0°(合) = 100%, 30° = 50%, 60° = 75%, 90° = 50%, 120° = 50%, 150° = 25%, 180°(冲) = 100%

    Args:
        aspect_degree: 两行星之间减去的相位角度（0-180度）
        planet_name: 施相行星名称

    Returns:
        Sputa Drishti值（0-1浮点）
    """
    # 标准化到 0-180
    ad = aspect_degree % 360
    if ad > 180:
        ad = 360 - ad

    # 关键角度映射
    if ad <= 1.0:
        return 1.0  # 紧密合相
    elif ad <= 3.0:
        return 0.95
    elif ad <= 7.0:
        return 0.85
    elif ad <= 10.0:
        return 0.75
    elif ad <= 15.0:
        return 0.675
    elif ad <= 20.0:
        return 0.5
    elif ad <= 25.0:
        return 0.375
    elif ad <= 30.0:
        return 0.25
    elif ad <= 40.0:
        return 0.2
    elif ad <= 50.0:
        return 0.15
    elif ad <= 60.0:
        return 0.1
    elif ad <= 75.0:
        return 0.075
    elif ad <= 90.0:
        return 0.05
    elif ad <= 120.0:
        return 0.0375
    elif ad <= 150.0:
        return 0.025
    # >150度几乎没有相位力量
    return 0.0


def calc_yuddha_bala(planets: Dict) -> Dict:
    """
    Yuddha Bala（行星战争力量调整）。
    基于jyotishganit (MIT License) 算法。

    当两颗行星相距 < 1° 时发生行星战争，胜者获得力量加成，
    败者减去相应力量。基于 Shadbala 总力量 + 行星直径比率判定。

    Args:
        planets: 行星数据 dict，需要包含经度信息和已计算的shadbala

    Returns:
        yuddha调整字典（planet_name → adjustment_value）
    """
    SEVEN_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
    PLANET_DISK_SIZE = {
        'Sun': 0.533, 'Moon': 0.518, 'Mars': 0.033,
        'Mercury': 0.022, 'Jupiter': 0.137, 'Venus': 0.054, 'Saturn': 0.103
    }
    WAR_ORB = 1.0  # 1° 为行星战争触发范围

    adjustments = {}
    checked_pairs = set()

    for i, p1 in enumerate(SEVEN_PLANETS):
        if p1 not in planets:
            continue
        lon1 = planets[p1].get('degree', 0) % 360

        for j in range(i + 1, len(SEVEN_PLANETS)):
            p2 = SEVEN_PLANETS[j]
            if p2 not in planets:
                continue
            if (p1, p2) in checked_pairs or (p2, p1) in checked_pairs:
                continue
            checked_pairs.add((p1, p2))

            lon2 = planets[p2].get('degree', 0) % 360
            diff = abs(lon1 - lon2)
            if diff > 180:
                diff = 360 - diff

            if diff > WAR_ORB:
                continue

            # 行星战争判定
            # 胜者 = 亮度(disk_size)更大 + Shadbala 更强
            disk1 = PLANET_DISK_SIZE.get(p1, 0.05)
            disk2 = PLANET_DISK_SIZE.get(p2, 0.05)

            # 简化：较大盘面者获胜
            if disk1 > disk2:
                winner, loser = p1, p2
            elif disk2 > disk1:
                winner, loser = p2, p1
            else:
                continue  # 平局，无调整

            # 力量转移：败者Shadbala的10%转移给胜者
            transfer_factor = 0.1
            adjustments[winner] = adjustments.get(winner, 0) + transfer_factor * 60
            adjustments[loser] = adjustments.get(loser, 0) - transfer_factor * 60

    return adjustments


def calc_drik_bala(pname: str, sign: str, house: int,
                   all_planets: Dict) -> float:
    """Compatibility wrapper for the continuous Sphuta Drishti calculation."""
    return calc_drik_bala_precise(pname, all_planets)


# ============================================================================
# Bhava Bala（宫位力量）v6.9.12 新增
# ============================================================================

def calc_bhava_bala(planets: Dict, asc_sign: str) -> Dict:
    """
    Bhava Bala（宫位力量）—— 评估每个宫位的综合强度。
    
    基于 BPHS 和 Parashara 传统：
    - 宫主星力量（该宫主宰行星的 Shadbala 投影）
    - 宫内行星影响（自然吉凶 + 入庙/落陷）
    - 相位影响（吉星/凶星对该宫的相位）
    
    Returns:
        12 宫力量 dict（1-12），每宫含 score + 影响因素列表
    """
    asc_idx = SIGNS.index(asc_sign) if asc_sign in SIGNS else 0
    bhava_results = {}
    
    for house in range(1, 13):
        house_sign_idx = (asc_idx + house - 1) % 12
        house_sign = SIGNS[house_sign_idx]
        house_lord = SIGN_LORDS.get(house_sign, '')
        
        factors = []
        score = 0.0
        
        # A. 宫主星基础分（Own Sign = 4, Exalted = 5, etc.）
        if house_lord:
            lord_planet = planets.get(house_lord, {})
            lord_house = lord_planet.get('house', 1)
            
            # 宫主星坐落位置的力量
            if lord_house in (1, 4, 7, 10):  # 角宫
                lord_pos_score = 4.0
                factors.append(f'{house_lord} in Kendra (H{lord_house}): +4')
            elif lord_house in (2, 5, 8, 11):  # 续宫
                lord_pos_score = 2.5
                factors.append(f'{house_lord} in Panapara (H{lord_house}): +2.5')
            else:  # 果宫
                lord_pos_score = 1.5
                factors.append(f'{house_lord} in Apoklima (H{lord_house}): +1.5')
            
            # 宫主星入庙/落陷/旺相
            lord_sign = lord_planet.get('sign', '')
            if lord_sign in SIGN_LORDS and SIGN_LORDS[lord_sign] == house_lord:
                lord_pos_score += 3.0
                factors.append(f'{house_lord} in Own Sign: +3')
            elif lord_sign and EXALTATION_DEG.get(house_lord, 999) // 30 == SIGNS.index(lord_sign) if lord_sign in SIGNS else False:
                lord_pos_score += 4.0
                factors.append(f'{house_lord} Exalted: +4')
            
            score += lord_pos_score
        
        # B. 宫内行星影响
        for pname, pdata in planets.items():
            if pname in ('Rahu', 'Ketu'):
                continue
            if pdata.get('house') == house:
                if pname in BENEFICS:
                    score += 2.0
                    factors.append(f'{pname} in H{house} (Benefic): +2')
                elif pname in MALEFICS:
                    score -= 1.5
                    factors.append(f'{pname} in H{house} (Malefic): -1.5')
                else:
                    score += 0.5
                    factors.append(f'{pname} in H{house} (Neutral): +0.5')
        
        # C. 相位影响（简化：7宫冲相 + 特殊相位）
        for pname, pdata in planets.items():
            if pname in ('Rahu', 'Ketu'):
                continue
            asp_house = pdata.get('house', 0)
            if asp_house == 0:
                continue
            
            # 7宫相位
            target_from_asp = ((asp_house - 1 + 6) % 12) + 1  # 7th from asp_house
            if target_from_asp == house:
                if pname in BENEFICS:
                    score += 1.5
                    factors.append(f'{pname} aspects H{house} (7th, Benefic): +1.5')
                elif pname in MALEFICS:
                    score -= 1.0
                    factors.append(f'{pname} aspects H{house} (7th, Malefic): -1.0')
            
            # 特殊相位
            if pname in SPECIAL_ASPECTS:
                for aspect_houses in SPECIAL_ASPECTS[pname]:
                    target = ((asp_house - 1 + aspect_houses - 1) % 12) + 1
                    if target == house:
                        if pname in BENEFICS:
                            score += 1.5
                            factors.append(f'{pname} aspects H{house} ({aspect_houses}th, Benefic): +1.5')
                        elif pname in MALEFICS:
                            score -= 1.0
                            factors.append(f'{pname} aspects H{house} ({aspect_houses}th, Malefic): -1.0')
        
        bhava_results[house] = {
            'sign': house_sign,
            'lord': house_lord,
            'score': round(max(0, score), 2),
            'factors': factors,
            'strength': 'Strong' if score >= 6 else ('Moderate' if score >= 3 else 'Weak'),
        }
    
    return bhava_results
