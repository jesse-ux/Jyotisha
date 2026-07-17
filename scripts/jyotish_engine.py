#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
印度占星统一引擎 v3.7.1 (Jyotish Unified Engine)
整合所有计算能力为单一CLI入口，供Skill调用

子命令:
  chart        计算完整星盘（基于Swiss Ephemeris）
  dasha        计算Vimshottari Dasha大运时间线
  yoga         Yoga格局识别
  predict      三层验证法事件预测（优先EventPredictionModel规则引擎）
  varga        分盘计算（D9/D10）
  varga-full   BPHS十六分盘完整计算（D2-D60）（v3.7新增）
  aspects      度数精确相位系统（v3.7新增）
  jaimini      Jaimini系统（Chara Karaka/Karakamsha；Chara Dasha timing covered）（v3.7新增）
  nakshatra-adv 高级Nakshatra分析（Tara Bala/Sub-Lord/兼容性）（v3.7新增）
  argala       Argala门闩系统（v3.7新增）
  tajika       Tajika/Varshaphala年运盘（v3.7新增）
  synastry     合盘分析（Ashta Koota 36分制+Mangal Dosha）（v3.7新增）
  full-reading 全自动综合解盘（出生信息→全链路计算→完整报告）（v3.7.1新增）
  celebrity    名人案例查询（15,807条数据+SQLite验证库）
  db-stats     验证数据库统计
  transit      行星过境查询
  shadbala     六重力量计算（covered；外部绝对值校准前保留置信度上限）（v3.4新增）
  ashtakavarga 八分法计算（v3.5升级BPHS完整表，SAV=337）
  memory       Hermes记忆系统（v3.4新增）
  validate     R1-R10数学验证（v3.5新增，含R2b BAV列→SAV校验）
  audit        P1-P12行星审计管线（v3.6升级含P3仓库耦合+P8年龄状态+冲突仲裁）
  report       MD→HTML报告生成（v3.6新增，羊皮纸主题）

用法示例:
  python3 jyotish_engine.py chart --year 1990 --month 1 --day 1 --hour 12 --minute 0 --lat 39.9 --lon 116.4 --tz 8
  python3 jyotish_engine.py shadbala --year 1990 --month 1 --day 1 --hour 12 --minute 0 --lat 39.9 --lon 116.4 --tz 8
  python3 jyotish_engine.py ashtakavarga --year 1990 --month 1 --day 1 --hour 12 --minute 0 --lat 39.9 --lon 116.4 --tz 8
  python3 jyotish_engine.py memory --action store --content "测试记忆"
"""

import argparse
import json
import sys
import os
import csv
import math
import time
import sqlite3
import importlib.util
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List
try:
    from tabulate import tabulate
except ModuleNotFoundError:  # pragma: no cover - minimal environments
    def tabulate(rows, headers=(), tablefmt=None):
        lines = []
        if headers:
            lines.append(" | ".join(str(item) for item in headers))
        lines.extend(" | ".join(str(item) for item in row) for row in rows)
        return "\n".join(lines)
from life_stage_hook import generate_life_stage_hooks
from capability_evidence_pool import build_capability_evidence_pool_summary
from guided_topic_discovery import build_guided_topics

from ayanamsa_utils import (
    AYANAMSA_DISPLAY_NAMES,
    AYANAMSA_MODES,
    apply_ayanamsa,
    ayanamsa_display_name,
    current_ayanamsa_name,
)

# ============================================================================
# 路径常量
# ============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR)
HOME_DIR = os.path.expanduser('~')
CLAW_DIR = os.path.join(HOME_DIR, 'WorkBuddy', 'Claw')
DB_PATH = os.path.join(CLAW_DIR, 'vedic_astrology_validation.db')
PERSON_CSV = os.path.join(CLAW_DIR, 'vedastro_data', 'PersonList-15k.csv')
TRANSIT_JSON = os.path.join(CLAW_DIR, '月运过境配置-2026-2028.json')

try:
    from local_env import load_local_env
except ModuleNotFoundError:  # pragma: no cover - compatibility when imported as package
    from scripts.local_env import load_local_env

load_local_env(ROOT_DIR)

try:
    import swisseph as swe
    apply_ayanamsa('lahiri', swe)  # P0修复：必须设置Lahiri恒星黄道模式
    HAS_SWE = True
except ImportError:
    HAS_SWE = False

from cmd_solar_return import cmd_solar_return  # v6.0.18
from cmd_narayana_dasha import cmd_narayana_dasha as _cmd_narayana_dasha_impl  # v6.0.20
from cmd_muhurta import cmd_muhurta  # v6.0.21
from yoga_engine import detect_yogas  # v6.0.26: data-driven Yoga engine
from kp_system import calc_kp_analysis, get_kp_lords  # v6.9.10: KP完整系统
from bhava_chalit import cmd_bhava_chalit  # v6.9.13: Bhava Chalit 不等宫边界调整
from sudarshana_chakra import calc_sudarshana_chakra, generate_sudarshana_report  # v6.9.14: Sudarshana Chakra 三参考点盘

# ============================================================================
# 常量
# ============================================================================
NAKSHATRA_LIST = [
    ("Ashwini", "Ketu", 7), ("Bharani", "Venus", 20), ("Krittika", "Sun", 6),
    ("Rohini", "Moon", 10), ("Mrigashira", "Mars", 7), ("Ardra", "Rahu", 18),
    ("Punarvasu", "Jupiter", 16), ("Pushya", "Saturn", 19), ("Ashlesha", "Mercury", 17),
    ("Magha", "Ketu", 7), ("Purva Phalguni", "Venus", 20), ("Uttara Phalguni", "Sun", 6),
    ("Hasta", "Moon", 10), ("Chitra", "Mars", 7), ("Swati", "Rahu", 18),
    ("Vishakha", "Jupiter", 16), ("Anuradha", "Saturn", 19), ("Jyeshtha", "Mercury", 17),
    ("Mula", "Ketu", 7), ("Purva Ashadha", "Venus", 20), ("Uttara Ashadha", "Sun", 6),
    ("Shravana", "Moon", 10), ("Dhanishta", "Mars", 7), ("Shatabhisha", "Rahu", 18),
    ("Purva Bhadrapada", "Jupiter", 16), ("Uttara Bhadrapada", "Saturn", 19), ("Revati", "Mercury", 17),
]
DASHA_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {"Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17}
SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
SIGNS_CN = {'Aries': '白羊座', 'Taurus': '金牛座', 'Gemini': '双子座', 'Cancer': '巨蟹座', 'Leo': '狮子座', 'Virgo': '处女座', 'Libra': '天秤座', 'Scorpio': '天蝎座', 'Sagittarius': '射手座', 'Capricorn': '摩羯座', 'Aquarius': '水瓶座', 'Pisces': '双鱼座'}
SIGN_LORDS = {'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon', 'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars', 'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'}
EXALTATION = {'Sun': 'Aries', 'Moon': 'Taurus', 'Mars': 'Capricorn', 'Mercury': 'Virgo', 'Jupiter': 'Cancer', 'Venus': 'Pisces', 'Saturn': 'Libra'}
DEBILITATION = {'Sun': 'Libra', 'Moon': 'Scorpio', 'Mars': 'Cancer', 'Mercury': 'Pisces', 'Jupiter': 'Capricorn', 'Venus': 'Virgo', 'Saturn': 'Aries'}
# Moolatrikona（三方本宫）: 行星 → (星座, 度数范围起始)
MOOLATRIKONA = {'Sun': ('Leo', 0, 20), 'Moon': ('Taurus', 0, 3), 'Mars': ('Aries', 0, 12), 'Mercury': ('Virgo', 16, 20), 'Jupiter': ('Sagittarius', 0, 10), 'Venus': ('Libra', 0, 15), 'Saturn': ('Aquarius', 0, 20)}
# BPHS 永久友好关系表 (Naisargika Mitra)
PERMANENT_FRIENDS = {
    'Sun': ['Moon', 'Mars', 'Jupiter'],
    'Moon': ['Sun', 'Mercury'],
    'Mars': ['Sun', 'Moon', 'Jupiter'],
    'Mercury': ['Sun', 'Venus'],
    'Jupiter': ['Sun', 'Moon', 'Mars'],
    'Venus': ['Mercury', 'Saturn'],
    'Saturn': ['Mercury', 'Venus'],
    'Rahu': ['Venus', 'Saturn'],
    'Ketu': ['Mars', 'Saturn'],
}
PERMANENT_ENEMIES = {
    'Sun': ['Saturn', 'Venus'],
    'Moon': [],
    'Mars': ['Mercury'],
    'Mercury': ['Moon'],
    'Jupiter': ['Mercury', 'Venus'],
    'Venus': ['Sun', 'Moon'],
    'Saturn': ['Sun', 'Moon', 'Mars'],
    'Rahu': ['Sun', 'Moon', 'Jupiter'],
    'Ketu': ['Sun', 'Moon'],
}
DIGNITY_LABELS = {
    'EXALTED': '入旺(Exalted)',
    'MOOLATRIKONA': '本垣(Moolatrikona)',
    'OWN_SIGN': '入庙(Own Sign)',
    'GREAT_FRIEND': '极友(Great Friend)',
    'FRIEND': '入友(Friendly Sign)',
    'NEUTRAL': '中性(Neutral)',
    'ENEMY': '入敌(Enemy Sign)',
    'GREAT_ENEMY': '极敌(Great Enemy)',
    'DEBILITATED': '落陷(Debilitated)',
    'NEECHA_BHANGA': '落陷取消(Neecha Bhanga)',
}


def _build_vimsopaka_semantic_summary(vimsopaka: dict | None) -> dict:
    if not isinstance(vimsopaka, dict):
        return {"status": "blocked", "highlights": [], "warnings": []}

    highlights = []
    warnings = []
    for planet, payload in vimsopaka.items():
        if not isinstance(payload, dict):
            continue
        dignity = payload.get('dignity')
        label = DIGNITY_LABELS.get(dignity)
        if dignity in {'GREAT_FRIEND', 'NEECHA_BHANGA'} and label:
            highlights.append(f"{planet}: {label}")
        elif dignity == 'GREAT_ENEMY' and label:
            warnings.append(f"{planet}: {label}")

    return {
        "status": "used",
        "highlights": highlights,
        "warnings": warnings,
    }
PUSHKARA_NAVAMSA_RANGES = {
    'fire': [(6 + 40/60, 10), (23 + 20/60, 26 + 40/60)],
    'earth': [(3 + 20/60, 6 + 40/60), (16 + 40/60, 20)],
    'air': [(13 + 20/60, 16 + 40/60), (26 + 40/60, 30)],
    'water': [(0, 3 + 20/60), (10, 13 + 20/60)],
}
PUSHKARA_BHAGA_DEGREES = {'fire': 21, 'earth': 14, 'air': 24, 'water': 7}
SIGN_ELEMENTS = {
    'Aries': 'fire', 'Leo': 'fire', 'Sagittarius': 'fire',
    'Taurus': 'earth', 'Virgo': 'earth', 'Capricorn': 'earth',
    'Gemini': 'air', 'Libra': 'air', 'Aquarius': 'air',
    'Cancer': 'water', 'Scorpio': 'water', 'Pisces': 'water',
}


def _element_key(sign):
    return SIGN_ELEMENTS.get(sign)


def _is_pushkara_navamsa(sign, deg_in_sign):
    element = _element_key(sign)
    if element is None or deg_in_sign is None:
        return False, None
    for start, end in PUSHKARA_NAVAMSA_RANGES[element]:
        if start <= deg_in_sign < end:
            return True, {"element": element, "range": [round(start, 4), round(end, 4)]}
    return False, None


def _is_pushkara_bhaga(sign, deg_in_sign, orb=1.0):
    element = _element_key(sign)
    if element is None or deg_in_sign is None:
        return False, None
    target = PUSHKARA_BHAGA_DEGREES[element]
    delta = abs(deg_in_sign - target)
    return delta <= orb, {"element": element, "target_degree": target, "orb": orb, "delta": round(delta, 4)}


def _calc_vargottama(planets, varga_full):
    d9 = varga_full.get('D9_Navamsa', {}) if isinstance(varga_full, dict) else {}
    result = {}
    for pn, pd in planets.items():
        if not isinstance(pd, dict) or 'sign' not in pd:
            continue
        d9_pd = d9.get(pn, {}) if isinstance(d9, dict) else {}
        d9_sign = d9_pd.get('sign') if isinstance(d9_pd, dict) else None
        result[pn] = {
            'd1_sign': pd.get('sign'),
            'd9_sign': d9_sign,
            'is_vargottama': bool(d9_sign and pd.get('sign') == d9_sign),
        }
    return result


def _calc_pushkara_flags(planets):
    result = {}
    for pn, pd in planets.items():
        if not isinstance(pd, dict) or 'sign' not in pd:
            continue
        sign = pd.get('sign')
        deg = pd.get('degree_in_sign', pd.get('degree', 0) % 30)
        in_pna, pna_meta = _is_pushkara_navamsa(sign, deg)
        in_pb, pb_meta = _is_pushkara_bhaga(sign, deg)
        result[pn] = {
            'sign': sign,
            'sign_cn': SIGNS_CN.get(sign, ''),
            'degree_in_sign': round(deg, 4),
            'pushkara_navamsa': in_pna,
            'pushkara_navamsa_meta': pna_meta,
            'pushkara_bhaga': in_pb,
            'pushkara_bhaga_meta': pb_meta,
        }
    return result


def _calc_sensitive_points(planets):
    result = {}
    try:
        from varga import calc_bhrigu_bindu, calc_sarpa_drekkana
    except Exception:
        return result

    moon = planets.get('Moon', {}) if isinstance(planets, dict) else {}
    rahu = planets.get('Rahu', {}) if isinstance(planets, dict) else {}
    moon_lon = moon.get('degree_raw', moon.get('degree'))
    rahu_lon = rahu.get('degree_raw', rahu.get('degree'))
    if moon_lon is not None and rahu_lon is not None:
        result['bhrigu_bindu'] = calc_bhrigu_bindu(moon_lon, rahu_lon)

    sarpa = {}
    for planet_name, pdata in planets.items():
        if not isinstance(pdata, dict):
            continue
        lon = pdata.get('degree_raw', pdata.get('degree'))
        if lon is None:
            continue
        payload = calc_sarpa_drekkana(lon)
        if payload.get('is_sarpa_drekkana'):
            sarpa[planet_name] = payload
    result['sarpa_drekkana'] = sarpa
    return result


def _calc_dasha_sandhi(dasha_result, reference_date=None, orb_days=90):
    ref = datetime.strptime(reference_date, "%Y-%m-%d") if reference_date else datetime.now()
    sandhi = []
    timeline = dasha_result.get('timeline', []) if isinstance(dasha_result, dict) else []
    for md in timeline:
        for boundary_key in ['start', 'end']:
            if boundary_key not in md:
                continue
            bdt = datetime.strptime(md[boundary_key], "%Y-%m-%d")
            delta = (bdt - ref).days
            if abs(delta) <= orb_days:
                sandhi.append({
                    'level': 'mahadasha',
                    'lord': md.get('lord'),
                    'boundary': boundary_key,
                    'date': md.get(boundary_key),
                    'days_from_reference': delta,
                    'within_orb': True,
                })
        for ad in md.get('antardasha_timeline', []):
            for boundary_key in ['start', 'end']:
                if boundary_key not in ad:
                    continue
                bdt = datetime.strptime(ad[boundary_key], "%Y-%m-%d")
                delta = (bdt - ref).days
                if abs(delta) <= orb_days:
                    sandhi.append({
                        'level': 'antardasha',
                        'mahadasha_lord': md.get('lord'),
                        'lord': ad.get('lord'),
                        'boundary': boundary_key,
                        'date': ad.get(boundary_key),
                        'days_from_reference': delta,
                        'within_orb': True,
                    })
    return {'reference_date': ref.strftime('%Y-%m-%d'), 'orb_days': orb_days, 'sandhi_windows': sandhi}



# ============================================================================
# 新增：Dispositor Chain + Inter-chart Linkage (v6.0.12)
# ============================================================================

def calc_dispositor_chain(planet_name, planets_data, max_depth=12):
    """
    计算行星的定位星链（dispositor chain）。
    返回列表：[{planet, sign, dispositor, dispositor_sign}, ...]
    直到循环或达到 max_depth。
    """
    chain = []
    current_planet = planet_name
    visited = set()
    for _ in range(max_depth):
        if current_planet in visited:
            break
        visited.add(current_planet)
        pdata = planets_data.get(current_planet, {})
        if not isinstance(pdata, dict) or 'sign' not in pdata:
            break
        sign = pdata['sign']
        dispositor = SIGN_LORDS.get(sign, '')
        chain.append({
            'planet': current_planet,
            'sign': sign,
            'sign_cn': SIGNS_CN.get(sign, ''),
            'dispositor': dispositor,
            'dispositor_sign': sign,  # 定位星所在的星座（即当前行星所在星座）
        })
        if not dispositor:
            break
        current_planet = dispositor
    return chain


def calc_inter_chart_linkage(planet_name, d1_data, d9_data, d10_data, d12_data=None, d1_asc_idx=None, d9_asc_idx=None, d10_asc_idx=None):
    """
    计算行星在 D1/D9/D10 分盘之间的飞星落宫。
    返回 {chart_type: {sign, house_in_chart, lord_of_sign_in_chart}}
    """
    result = {}
    charts = [
        ('D1', d1_data, d1_asc_idx),
        ('D9', d9_data, d9_asc_idx),
        ('D10', d10_data, d10_asc_idx),
    ]
    if d12_data:
        charts.append(('D12', d12_data, None))

    for chart_name, chart_data, asc_idx in charts:
        if not isinstance(chart_data, dict):
            continue
        pdata = chart_data.get(planet_name, {})
        if not isinstance(pdata, dict) or 'sign' not in pdata:
            continue
        sign = pdata['sign']
        sign_idx = SIGNS.index(sign) if sign in SIGNS else 0
        house = None
        if asc_idx is not None:
            house = ((sign_idx - asc_idx) % 12) + 1
        lord = SIGN_LORDS.get(sign, '')
        result[chart_name] = {
            'planet': planet_name,
            'sign': sign,
            'sign_cn': SIGNS_CN.get(sign, ''),
            'house': house,
            'lord': lord,
        }
    return result


def calc_all_dispositor_chains(planets_data):
    """为所有行星计算定位星链"""
    result = {}
    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
        if pname in planets_data:
            result[pname] = calc_dispositor_chain(pname, planets_data)
    return result


def calc_all_inter_chart_linkages(d1_data, d9_data, d10_data, d12_data=None, d1_asc_idx=None, d9_asc_idx=None, d10_asc_idx=None):
    """
    为所有行星计算 D1/D9/D10 分盘间飞星。
    需要各分盘的 asc_idx 来正确计算落宫。
    """
    result = {}
    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
        result[pname] = calc_inter_chart_linkage(
            pname, d1_data, d9_data, d10_data, d12_data,
            d1_asc_idx, d9_asc_idx, d10_asc_idx
        )
    return result



def _get_temporary_relationship(planet1, planet2, planets_data):
    """Calculate Temporary Friendship (Tatkalika Maitri)."""
    if not planets_data or planet1 not in planets_data or planet2 not in planets_data:
        return 'NEUTRAL'

    p1_sign = planets_data[planet1].get('sign')
    p2_sign = planets_data[planet2].get('sign')
    if not p1_sign or not p2_sign:
        return 'NEUTRAL'
        
    idx1 = SIGNS.index(p1_sign)
    idx2 = SIGNS.index(p2_sign)
    distance = (idx2 - idx1) % 12 + 1

    # 2, 3, 4, 10, 11, 12 from planet are temporary friends
    if distance in [2, 3, 4, 10, 11, 12]:
        return 'FRIEND'
    # 1 (conjunct), 5, 6, 7, 8, 9 are temporary enemies
    else:
        return 'ENEMY'

def _check_neecha_bhanga(planet, sign, planets_data):
    """Check for Cancellation of Debilitation."""
    if not planets_data:
        return False
        
    sign_lord = SIGN_LORDS.get(sign)
    
    # Condition 1: Dispositor is exalted.
    if sign_lord and sign_lord in planets_data:
        lord_sign = planets_data[sign_lord].get('sign')
        if lord_sign and EXALTATION.get(sign_lord) == lord_sign:
            return True
            
    # Condition 2: Planet exalted in this sign is conjunct.
    exalted_planet = None
    for p, ex_sign in EXALTATION.items():
        if ex_sign == sign:
            exalted_planet = p
            break
            
    if exalted_planet and exalted_planet in planets_data:
        ex_p_sign = planets_data[exalted_planet].get('sign')
        if ex_p_sign == sign:
            return True
            
    return False


def _build_dignity_context(chart_data):
    """Normalize a chart/varga payload into the per-planet context used by dignity checks."""
    context = {}
    if not isinstance(chart_data, dict):
        return context

    for pn, pd in chart_data.items():
        if pn in ('_meta', 'Ascendant') or not isinstance(pd, dict) or 'sign' not in pd:
            continue
        context[pn] = {
            'sign': pd.get('sign'),
            'degree_in_sign': pd.get('degree_in_sign', pd.get('degree', 0) % 30),
        }
    return context

def _get_dignity_level(planet, sign, deg_in_sign=None, planets_data=None):
    """判断行星在某星座的尊严等级 (用于 Vimsopaka 映射), 包含五重敌友和落陷取消"""
    if EXALTATION.get(planet) == sign:
        return 'EXALTED'
    
    mt = MOOLATRIKONA.get(planet)
    if mt and mt[0] == sign:
        if deg_in_sign is not None and mt[1] <= deg_in_sign < mt[2]:
            return 'MOOLATRIKONA'
            
    if SIGN_LORDS.get(sign) == planet:
        return 'OWN_SIGN'
        
    if DEBILITATION.get(planet) == sign:
        if _check_neecha_bhanga(planet, sign, planets_data):
            return 'NEECHA_BHANGA'
        return 'DEBILITATED'
        
    sign_lord = SIGN_LORDS.get(sign, '')
    if not sign_lord:
        return 'NEUTRAL'
        
    # Naisargika (Permanent)
    perm = 'NEUTRAL'
    if sign_lord in PERMANENT_FRIENDS.get(planet, []):
        perm = 'FRIEND'
    elif sign_lord in PERMANENT_ENEMIES.get(planet, []):
        perm = 'ENEMY'
        
    if not planets_data:
        return perm
        
    # Tatkalika (Temporary)
    temp = _get_temporary_relationship(planet, sign_lord, planets_data)
    
    # Panchadha Maitri (Compound)
    if perm == 'FRIEND' and temp == 'FRIEND':
        return 'GREAT_FRIEND'
    elif perm == 'ENEMY' and temp == 'ENEMY':
        return 'GREAT_ENEMY'
    elif perm == 'FRIEND' and temp == 'ENEMY':
        return 'NEUTRAL'
    elif perm == 'NEUTRAL' and temp == 'FRIEND':
        return 'FRIEND'
    elif perm == 'NEUTRAL' and temp == 'ENEMY':
        return 'ENEMY'
    elif perm == 'ENEMY' and temp == 'FRIEND':
        return 'NEUTRAL'
        
    return 'NEUTRAL'


def _get_planet_status_label(planet, sign, deg_in_sign=None, planets_data=None):
    """Return the user-facing D1 dignity label for chart output."""
    return DIGNITY_LABELS.get(_get_dignity_level(planet, sign, deg_in_sign, planets_data), '中性')
PLANET_CN = {"Ketu": "南交点Ketu", "Venus": "金星Venus", "Sun": "太阳Sun", "Moon": "月亮Moon", "Mars": "火星Mars", "Rahu": "北交点Rahu", "Jupiter": "木星Jupiter", "Saturn": "土星Saturn", "Mercury": "水星Mercury"}
BASE_PLANETS_SWE = {'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS, 'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER, 'Venus': swe.VENUS, 'Saturn': swe.SATURN} if HAS_SWE else {}
PLANETS_SWE = {**BASE_PLANETS_SWE, 'Rahu': swe.MEAN_NODE} if HAS_SWE else {}


def _node_pid(node_mode='mean'):
    """返回 Rahu/Ketu 节点计算口径对应的 Swiss Ephemeris id。"""
    if not HAS_SWE:
        return None
    return swe.TRUE_NODE if (node_mode or 'mean').lower() == 'true' else swe.MEAN_NODE


def _planet_map_for_node_mode(node_mode='mean'):
    """返回七曜+Rahu 的行星映射，Rahu 口径由 node_mode 决定。"""
    if not HAS_SWE:
        return {}
    return {**BASE_PLANETS_SWE, 'Rahu': _node_pid(node_mode)}


def _calc_sidereal_planets_for_jd(jd, node_mode='mean', include_ketu=True):
    """使用 Swiss Ephemeris 计算指定 Julian Day 的恒星黄道行星位置。"""
    if not HAS_SWE:
        return {}, None
    ayanamsa = swe.get_ayanamsa(jd)
    data = {}
    for pname, pid in _planet_map_for_node_mode(node_mode).items():
        pos, ret = swe.calc_ut(jd, pid)
        if ret < 0:
            continue
        lon = (pos[0] - ayanamsa) % 360
        sign_idx = int(lon / 30) % 12
        speed = pos[3] if len(pos) > 3 else 0
        data[pname] = {
            'sign': SIGNS[sign_idx],
            'sign_cn': SIGNS_CN[SIGNS[sign_idx]],
            'degree': round(lon, 4),
            'degree_raw': lon,
            'degree_in_sign': round(lon % 30, 2),
            'degree_in_sign_raw': lon % 30,
            'speed': round(speed, 4),
            'retrograde': speed < 0,
        }
    if include_ketu and 'Rahu' in data:
        rahu_lon = data['Rahu']['degree_raw']
        ketu_lon = (rahu_lon + 180) % 360
        ketu_idx = int(ketu_lon / 30) % 12
        data['Ketu'] = {
            'sign': SIGNS[ketu_idx],
            'sign_cn': SIGNS_CN[SIGNS[ketu_idx]],
            'degree': round(ketu_lon, 4),
            'degree_raw': ketu_lon,
            'degree_in_sign': round(ketu_lon % 30, 2),
            'degree_in_sign_raw': ketu_lon % 30,
            'speed': data['Rahu'].get('speed', 0),
            'retrograde': data['Rahu'].get('retrograde', True),
        }
    return data, ayanamsa


def output_json(data):
    """统一JSON输出"""
    print(json.dumps(data, ensure_ascii=False, indent=2, default=str))


def output_table(command, data):
    """Human-readable ASCII table output for selected commands."""
    if command == 'chart':
        birth_info = data.get('birth_info', {}) if isinstance(data, dict) else {}
        ascendant = data.get('ascendant', {}) if isinstance(data, dict) else {}
        planets = data.get('planets', {}) if isinstance(data, dict) else {}
        rows = []
        for planet_name, planet_data in planets.items():
            if not isinstance(planet_data, dict):
                continue
            rows.append([
                planet_name,
                planet_data.get('sign', ''),
                planet_data.get('house', ''),
                planet_data.get('nakshatra', ''),
                planet_data.get('status', ''),
            ])
        print(f"Birth: {birth_info.get('date', '')} {birth_info.get('time', '')}")
        print(f"Ascendant: {ascendant.get('sign', '')} {ascendant.get('degree', '')}")
        print(tabulate(rows, headers=['Planet', 'Sign', 'House', 'Nakshatra', 'Status'], tablefmt='github'))
        return
    if command == 'dasha':
        timeline = data.get('timeline', []) if isinstance(data, dict) else []
        current = data.get('current_dasha') if isinstance(data, dict) else {}
        rows = []
        for item in timeline:
            rows.append([
                item.get('lord', ''),
                item.get('start', ''),
                item.get('end', ''),
                item.get('years', ''),
                'yes' if item.get('is_current') else '',
            ])
        print(f"Moon Nakshatra: {data.get('moon_nakshatra', '')}")
        print(f"Birth Date: {data.get('birth_date', '')}")
        print(f"Reference Date: {data.get('reference_date', '')}")
        if isinstance(current, dict) and current:
            print(
                "Current: "
                f"{current.get('lord', '')}"
                f" ({current.get('start', '')} -> {current.get('end', '')})"
            )
        print(tabulate(rows, headers=['Mahadasha', 'Start', 'End', 'Years', 'Current'], tablefmt='github'))
        return
    if command == 'shadbala':
        planets = data.get('planets', {}) if isinstance(data, dict) else {}
        rows = []
        for planet_name, planet_data in planets.items():
            if not isinstance(planet_data, dict):
                continue
            rows.append([
                planet_name,
                planet_data.get('total_rupas', ''),
                planet_data.get('min_required', ''),
                planet_data.get('strength_level', ''),
                planet_data.get('rank', ''),
            ])
        print(f"Shadbala Method: {data.get('method', '')}")
        print(tabulate(rows, headers=['Planet', 'Rupas', 'Min Required', 'Strength', 'Rank'], tablefmt='github'))
        return
    if command == 'ashtakoot':
        scores = data.get('scores', {}) if isinstance(data, dict) else {}
        rows = [[kuta, score] for kuta, score in scores.items()]
        print(f"Ashtakoot Method: {data.get('method', '')}")
        print(
            f"Total Score: {data.get('total_score', '')}/{data.get('max_score', '')} | "
            f"Match Approved: {data.get('is_match_approved', '')}"
        )
        print(tabulate(rows, headers=['Kuta', 'Score'], tablefmt='github'))
        return
    if command == 'ashtakavarga':
        sav = data.get('sav', {}) if isinstance(data, dict) else {}
        assessment = sav.get('assessment', []) if isinstance(sav, dict) else []
        bav_validation = data.get('bav_validation', []) if isinstance(data, dict) else []
        sign_rows = []
        for item in assessment:
            sign_rows.append([
                item.get('sign', ''),
                item.get('score', ''),
                item.get('level', ''),
            ])
        validation_rows = []
        for item in bav_validation:
            validation_rows.append([
                item.get('planet', ''),
                item.get('actual', ''),
                item.get('expected', ''),
                item.get('status', ''),
            ])
        print(f"Ashtakavarga Method: {data.get('method', '')}")
        print(
            f"SAV Total: {sav.get('total', '')}/{sav.get('expected_total', '')} | "
            f"Valid: {sav.get('valid', '')} | "
            f"Strongest Signs: {', '.join(data.get('strongest_signs', []))}"
        )
        print(tabulate(sign_rows, headers=['Sign', 'Score', 'Level'], tablefmt='github'))
        if validation_rows:
            print()
            print("BAV Validation:")
            print(tabulate(validation_rows, headers=['Planet', 'Actual', 'Expected', 'Status'], tablefmt='github'))
        return
    output_json(data)


def _second_arg(value):
    """Validate CLI birth second values."""
    second = int(value)
    if second < 0 or second > 59:
        raise argparse.ArgumentTypeError("second must be between 0 and 59")
    return second


def _arg_second(args):
    """Return an argparse namespace's optional birth second."""
    return int(getattr(args, 'second', 0) or 0)


def _birth_hour_decimal(hour, minute, second=0):
    return hour + minute / 60.0 + second / 3600.0


def _birth_time_string(hour, minute, second=0):
    second = int(second or 0)
    if second:
        return f"{int(hour):02d}:{int(minute):02d}:{second:02d}"
    return f"{int(hour):02d}:{int(minute):02d}"


def _birth_datetime_from_args(args):
    return datetime(args.year, args.month, args.day, args.hour, args.minute, _arg_second(args))


def _compute_chart_from_args(args):
    from domain_calculation_service import compute_chart

    result = compute_chart({
        'year': args.year,
        'month': args.month,
        'day': args.day,
        'hour': args.hour,
        'minute': args.minute,
        'second': _arg_second(args),
        'lat': args.lat,
        'lon': args.lon,
        'tz': args.tz,
        'node_mode': getattr(args, 'node_mode', 'mean'),
        'ayanamsa': _current_ayanamsa_name(args),
    })
    asc_idx = SIGNS.index(result['ascendant']['sign'])
    birth = result['birth_info']
    return result, asc_idx, birth['julian_day'], birth['ayanamsa']


def _current_ayanamsa_name(args=None):
    return current_ayanamsa_name(args)


def _ayanamsa_display_name(name):
    return ayanamsa_display_name(name)


def _add_chart_args(p):
    """为需要出生数据的子命令添加公共参数"""
    p.add_argument('--year', type=int, required=True)
    p.add_argument('--month', type=int, required=True)
    p.add_argument('--day', type=int, required=True)
    p.add_argument('--hour', type=int, required=True)
    p.add_argument('--minute', type=int, required=True)
    p.add_argument('--second', type=_second_arg, default=0)
    p.add_argument('--lat', type=float, required=True)
    p.add_argument('--lon', type=float, required=True)
    p.add_argument('--tz', type=float, default=None)
    p.add_argument('--node-mode', default='mean', choices=['mean', 'true'], help='Rahu/Ketu节点口径：mean=Mean Node（默认，JHora常用/Swiss direct baseline），true=True Node（PyJHora默认）')
    p.add_argument('--ayanamsa', default='lahiri', choices=list(AYANAMSA_MODES.keys()),
                   help='恒星黄道系统（默认lahiri）。可选: raman, kp(krishnamurti), fagan_bradley, djwhal_khul, sassanian, true_citra')


def _apply_ayanamsa(ayanamsa_name):
    """应用指定的 Ayanamsa 系统到全局 swissph 设置。新增 v6.9.9"""
    return bool(HAS_SWE and apply_ayanamsa(ayanamsa_name, swe))


def _varga_chart_to_yoga_context(varga_chart):
    """Convert varga.py output into yoga_engine context chart shape."""
    if not isinstance(varga_chart, dict):
        return {}
    asc = varga_chart.get('Ascendant', {})
    asc_sign = asc.get('sign') if isinstance(asc, dict) else None
    asc_idx = SIGNS.index(asc_sign) if asc_sign in SIGNS else None
    planets_ctx = {}
    for pn, pd in varga_chart.items():
        if pn in ('Ascendant', '_meta', '_dignity', '_d9_analysis', '_d60_analysis'):
            continue
        if not isinstance(pd, dict) or 'sign' not in pd:
            continue
        sign = pd.get('sign')
        sign_idx = pd.get('sign_idx')
        if sign_idx is None and sign in SIGNS:
            sign_idx = SIGNS.index(sign)
        house = None
        if asc_idx is not None and sign_idx is not None:
            house = ((int(sign_idx) - asc_idx) % 12) + 1
        planets_ctx[pn] = {
            'sign': sign,
            'house': house,
            'degree': pd.get('degree_in_sign', pd.get('degree')),
            'degree_in_sign': pd.get('degree_in_sign', pd.get('degree')),
            'sign_idx': sign_idx,
        }
    return {
        'ascendant': asc_sign,
        'ascendant_degree': asc.get('degree_in_sign') if isinstance(asc, dict) else None,
        'planets': planets_ctx,
    }


def _build_yoga_context_from_vargas(varga_result, planet_lons=None):
    """Build optional YogaContext payload with D9/D60 and basic panchanga."""
    context = {}
    if isinstance(varga_result, dict):
        d9 = varga_result.get('D9_Navamsa') or {}
        d60 = varga_result.get('D60_Shashtiamsa') or varga_result.get('D60_Shashtyamsa') or {}
        if d9:
            context['d9'] = _varga_chart_to_yoga_context(d9)
        if d60:
            context['d60'] = _varga_chart_to_yoga_context(d60)
    if isinstance(planet_lons, dict) and 'Moon' in planet_lons and 'Sun' in planet_lons:
        tithi_no = int(((planet_lons.get('Moon', 0) - planet_lons.get('Sun', 0)) % 360) / 12) + 1
        context['panchanga'] = {
            'tithi': tithi_no,
            'paksha': 'waxing' if 1 <= tithi_no <= 15 else 'waning',
            'is_waning_moon': tithi_no > 15,
        }
    return context


def _planet_snapshot(planets, planet_name):
    pdata = planets.get(planet_name, {}) if isinstance(planets, dict) else {}
    if not isinstance(pdata, dict):
        return {}
    return {
        'source': pdata.get('source'),
        'sign': pdata.get('sign'),
        'sign_cn': pdata.get('sign_cn'),
        'house': pdata.get('house'),
        'degree': pdata.get('degree'),
        'lon': pdata.get('lon'),
        'degree_in_sign': pdata.get('degree_in_sign'),
        'vargas': pdata.get('vargas'),
        'nakshatra': pdata.get('nakshatra'),
        'nakshatra_pada': pdata.get('nakshatra_pada'),
        'status': pdata.get('status'),
        'retrograde': pdata.get('retrograde'),
    }


def _oracle_progress_snapshot():
    try:
        import json
        import subprocess
        import sys
        import tempfile
        from pathlib import Path

        root = Path(__file__).resolve().parents[1]
        oracle_file = root / 'references' / 'oracle' / 'dasha_shadbala_oracle_cases.json'
        with tempfile.NamedTemporaryFile('w+', suffix='.json', delete=True, encoding='utf-8') as handle:
            queue = subprocess.run(
                [sys.executable, 'scripts/oracle_collection_queue.py', '--oracle-file', str(oracle_file), '--format', 'json'],
                cwd=root,
                text=True,
                capture_output=True,
                timeout=90,
                check=False,
            )
            if queue.returncode != 0:
                raise RuntimeError(queue.stderr.strip() or queue.stdout.strip())
            handle.write(queue.stdout)
            handle.flush()
            validation = subprocess.run(
                [sys.executable, 'scripts/oracle_evidence_validator.py', '--queue-file', handle.name],
                cwd=root,
                text=True,
                capture_output=True,
                timeout=90,
                check=False,
            )
            if validation.returncode != 0:
                raise RuntimeError(validation.stderr.strip() or validation.stdout.strip())
            report = json.loads(validation.stdout)
        summary = report.get('summary', {})
        return {
            'scope': 'external_oracle_evidence_validation',
            'collection_queue': 'external_oracle_collection_queue',
            'total_packets': summary.get('total_packets', 0),
            'valid_packets': summary.get('valid_packets', 0),
            'ready_for_calibration': summary.get('ready_for_calibration', 0),
            'production_tuning_allowed': summary.get('production_tuning_allowed', False),
            'artifact_policy': 'references/oracle/artifacts/',
            'promotion_rule': 'external_verified requires source_artifact, filled target values, and non-local-engine external evidence.',
            'boundary': report.get('boundary', 'Dasha/Shadbala absolute values are not externally calibrated until enough packets pass validation.'),
        }
    except Exception as exc:
        return {
            'scope': 'external_oracle_evidence_validation',
            'collection_queue': 'external_oracle_collection_queue',
            'total_packets': 0,
            'valid_packets': 0,
            'ready_for_calibration': 0,
            'production_tuning_allowed': False,
            'artifact_policy': 'references/oracle/artifacts/',
            'promotion_rule': 'external_verified requires source_artifact, filled target values, and non-local-engine external evidence.',
            'boundary': f'Oracle progress unavailable: {exc}',
        }


def _functional_benefic_malefic_snapshot(planets, ascendant):
    try:
        from functional_benefics import derive_functional_benefic_malefic
        asc_sign = ascendant.get('sign') if isinstance(ascendant, dict) else None
        return derive_functional_benefic_malefic(asc_sign)
    except Exception as exc:
        return {
            'status': 'blocked',
            'ascendant': ascendant.get('sign') if isinstance(ascendant, dict) else None,
            'functional_benefics': [],
            'functional_malefics': [],
            'functional_neutrals': [],
            'yogakarakas': [],
            'owned_houses': {},
            'effect_on_confidence': f'未完成功能性吉凶星判定，需降低高严谨结论置信度: {exc}',
            'source': 'strict_functional_benefic_malefic_v1',
        }


def _build_technique_audit_table(functional_layer, oracle_progress, modules):
    dasha = modules.get('dasha') if isinstance(modules, dict) else {}
    narayana = modules.get('narayana_dasha') if isinstance(modules, dict) else {}
    d9 = modules.get('d9_navamsa_expanded') if isinstance(modules, dict) else {}
    shadbala = modules.get('shadbala') if isinstance(modules, dict) else {}
    ashtakavarga = modules.get('ashtakavarga') if isinstance(modules, dict) else {}
    vimsopaka = modules.get('vimsopaka') if isinstance(modules, dict) else {}
    dasa_convergence = modules.get('dasa_convergence') if isinstance(modules, dict) else {}
    relationship = modules.get('relationship_strict_evidence') if isinstance(modules, dict) else {}
    vedastro_overview = modules.get('vedastro_range_scan_result') if isinstance(modules, dict) else {}

    rows = [
        {
            'technique': 'Functional Benefic/Malefic',
            'status': functional_layer.get('status', 'blocked'),
            'source': 'scripts/yoga_engine.py::YogaContext',
            'note': (
                f"关键功能吉星={functional_layer.get('functional_benefics', [])}; "
                f"关键功能凶星={functional_layer.get('functional_malefics', [])}; "
                f"功能中性星={functional_layer.get('functional_neutrals', [])}; "
                f"Yogakaraka={functional_layer.get('yogakarakas', [])}; "
                f"{functional_layer.get('effect_on_confidence', '高严谨模式缺少功能性吉凶星判定。')}"
            ),
        },
        {
            'technique': 'External Oracle Progress',
            'status': 'used' if oracle_progress.get('total_packets', 0) else 'blocked',
            'source': 'scripts/oracle_collection_queue.py + scripts/oracle_evidence_validator.py',
            'note': (
                f"当前 external oracle 进度 {oracle_progress.get('ready_for_calibration', 0)}/"
                f"{oracle_progress.get('total_packets', 0)} ready，"
                f"production_tuning_allowed={oracle_progress.get('production_tuning_allowed', False)}。"
            ),
        },
        {
            'technique': 'Interpretation Source Pack',
            'status': 'used',
            'source': 'repo_existing_interpretation_sources',
            'note': (
                '已显式索引 interpretation_template_registry、P1-P12、house_framework、'
                'Raman/BPHS 与前端 planet-house-details；这些资料只作为本地解释源，'
                '不替代 MEVG 外部采集和真实案例校正。'
            ),
        },
        {
            'technique': 'MEVG / Global Web Evidence',
            'status': 'blocked',
            'source': 'references/mandatory-verification-gate-protocol.md',
            'note': '所有星盘运势/推运解释必须执行全球/全网外部资料采集；未执行时解释声明需降级。',
        },
        {
            'technique': 'Real Case Calibration',
            'status': 'blocked',
            'source': 'references/real-reading-quality-checklist.md',
            'note': '所有星盘运势/推运解释必须参考真实案例或公开 benchmark；无匹配案例时置信度封顶。',
        },
    ]

    rows.append({
        'technique': 'Vimshottari + Narayana Cross-check',
        'status': 'used' if isinstance(dasha, dict) and isinstance(narayana, dict) and dasha and narayana else 'blocked',
        'source': 'modules.dasha + modules.narayana_dasha + modules.dasa_convergence',
        'note': (
            f"Vimshottari 当前主运={((dasha.get('current_dasha') or {}).get('lord')) if isinstance(dasha, dict) else None}; "
            f"Narayana 当前主运={narayana.get('current_dasha') if isinstance(narayana, dict) else None}; "
            f"多系统收敛摘要={dasa_convergence.get('top_convergent_domains') if isinstance(dasa_convergence, dict) else None}。"
        ),
    })
    rows.append({
        'technique': 'Relevant Vargas',
        'status': 'used' if isinstance(d9, dict) and d9 else 'blocked',
        'source': 'modules.d9_navamsa_expanded',
        'note': (
            f"D9 已接入；可见键={list(d9.keys())[:5] if isinstance(d9, dict) else []}。"
            "高严谨解读至少应交叉 D1 + D9，婚姻/关系主题不得跳过 D9。"
        ),
    })
    rows.append({
        'technique': 'Strength Layers',
        'status': 'used' if isinstance(shadbala, dict) and isinstance(ashtakavarga, dict) and isinstance(vimsopaka, dict) else 'blocked',
        'source': 'modules.shadbala + modules.ashtakavarga + modules.vimsopaka',
        'note': (
            f"Shadbala status={shadbala.get('status') if isinstance(shadbala, dict) else None}; "
            f"Ashtakavarga SAV={((ashtakavarga.get('sav') or {}).get('total')) if isinstance(ashtakavarga, dict) else None}; "
            f"Vimsopaka status={vimsopaka.get('status') if isinstance(vimsopaka, dict) else None}。"
        ),
    })

    event_judgement = relationship.get('event_judgement') if isinstance(relationship, dict) else {}
    secondary_context = event_judgement.get('secondary_context') if isinstance(event_judgement, dict) else []
    synastry_context = [item for item in (secondary_context or []) if isinstance(item, str) and item.startswith('synastry_')]
    rows.append({
        'technique': 'Relationship Synastry Taxonomy',
        'status': 'used' if synastry_context else 'blocked',
        'source': 'relationship strict workflow + synastry_relationship_bridge_v1',
        'note': (
            f"relationship secondary_context 中的 synastry 语义={synastry_context}; "
            "compatibility support 表示匹配/延续性支持；"
            "protective kuta support 表示防护型 Kuta 清洁度支持；"
            "若 dual dasha / external timing / marriage convergence 冲突，"
            "不得把这些支持越权解释成 legal marriage 的高置信度落地。"
        ),
    })
    vedastro_meta = vedastro_overview.get('source_metadata') if isinstance(vedastro_overview, dict) else {}
    rows.append({
        'technique': 'VedAstro Main Entry Overview',
        'status': 'used' if isinstance(vedastro_overview, dict) and vedastro_overview.get('status') == 'ok' else 'blocked',
        'source': 'modules.vedastro_range_scan_result',
        'note': (
            f"overview only; status={vedastro_overview.get('status') if isinstance(vedastro_overview, dict) else None}; "
            f"domain_statuses={vedastro_meta.get('domain_statuses') if isinstance(vedastro_meta, dict) else None}; "
            f"reference_date={vedastro_meta.get('reference_date') if isinstance(vedastro_meta, dict) else None}."
        ),
    })
    return rows


def _build_relationship_narrative_payload(relationship_strict):
    if not isinstance(relationship_strict, dict) or not relationship_strict:
        return {
            'headline': '婚恋严格裁决证据尚未完成，当前不能生成高严谨关系叙事。',
            'strengths': [],
            'risks': ['缺少 relationship strict workflow 的核心证据，婚恋正文需降级。'],
            'boundaries': [
                '未完成 D1 + D9 + UL + dual dasha 交叉前，不得把单一关系信号写成高置信度婚姻结论。',
            ],
            'monthly_frame': {
                'primary_state': {'value': 'blocked'},
                'manifestation_mode': {'value': 'blocked'},
                'friction_source': {'value': 'blocked'},
                'time_confidence': {'value': 'blocked'},
            },
            'markdown': (
                "### 婚恋严格裁决\n"
                "- 当前缺少 relationship strict evidence，无法生成高严谨婚恋 narrative。\n"
                "- 在 D1、D9、UL、Vimshottari 与 Narayana 未齐备前，应标记为 blocked 或降低置信度。"
            ),
        }

    event_judgement = relationship_strict.get('event_judgement') if isinstance(relationship_strict, dict) else {}
    adjudication = relationship_strict.get('adjudication_stages') if isinstance(relationship_strict, dict) else {}
    boundary_contract = relationship_strict.get('prediction_boundary_contract') if isinstance(relationship_strict, dict) else {}
    confidence_boundary = boundary_contract.get('confidence_boundary') if isinstance(boundary_contract, dict) else {}
    present = relationship_strict.get('present_evidence') if isinstance(relationship_strict, dict) else {}
    missing = relationship_strict.get('missing_evidence') or []
    secondary_context = event_judgement.get('secondary_context') if isinstance(event_judgement, dict) else []
    secondary_context = secondary_context if isinstance(secondary_context, list) else []
    confidence_cap = relationship_strict.get('confidence_cap') or event_judgement.get('confidence_cap') or 'unknown'
    dominant_label = event_judgement.get('dominant_label') if isinstance(event_judgement, dict) else None
    monthly_frame = relationship_strict.get('monthly_adjudication_summary') if isinstance(relationship_strict, dict) else {}
    monthly_frame = monthly_frame if isinstance(monthly_frame, dict) else {}
    synastry = present.get('synastry_relationship_support') if isinstance(present, dict) else {}
    synastry_signals = synastry.get('signals') if isinstance(synastry, dict) else []
    synastry_signals = synastry_signals if isinstance(synastry_signals, list) else []

    strengths = []
    risks = []
    boundaries = []

    if dominant_label == 'legal_marriage':
        strengths.append('本轮严格裁决已把婚恋主标签抬到 legal_marriage，但仍需尊重时机与现实承诺层。')
    elif dominant_label == 'public_formalization':
        strengths.append('当前更偏向 public_formalization，表示关系可见度/公开化支持强于法律婚姻落地。')
    elif 'public_formalization_candidate' in secondary_context:
        strengths.append('当前更接近 public_formalization_candidate，表示公开化/关系可见度候选正在增强，但仍未达到法律婚姻落地。')

    if 'jaimini_support' in secondary_context:
        strengths.append('Jaimini 桥接已提供配偶征象支持，DK/UL 线索可用于补强婚恋叙事。')
    if 'ul_support' in secondary_context:
        strengths.append('Upapada Lagna 已进入严格证据，可作为关系承诺与婚姻叙事的辅助锚点。')
    if 'synastry_support' in secondary_context:
        strengths.append('合盘支持已进入婚恋主链，但它只说明关系兼容度有帮助，不能单独决定婚姻落地。')
    if 'synastry_compatibility_support' in secondary_context:
        strengths.append('protective kuta / compatibility support 说明部分 Kuta 与关系延续性维度较干净。')
    if 'synastry_protective_kuta_support' in secondary_context:
        strengths.append('protective kuta support 已被识别，可作为关系稳定性的次级支持语义。')
    if 'synastry_exception_mitigated' in secondary_context:
        strengths.append('存在 exception mitigation，说明部分 Dosha/不利匹配在传统规则里有缓解条件。')
    if monthly_frame.get('primary_state', {}).get('value'):
        strengths.append(f"月度主状态：{monthly_frame.get('primary_state', {}).get('value')}。")
    if monthly_frame.get('manifestation_mode', {}).get('value'):
        strengths.append(f"落地形式：{monthly_frame.get('manifestation_mode', {}).get('value')}。")

    if confidence_cap in {'low', 'blocked'}:
        risks.append('当前 confidence cap 偏低，dual dasha / external timing / marriage convergence 至少有一层存在冲突或不足。')
        if 'public_formalization_candidate' in secondary_context:
            risks.append('当前虽更接近 public_formalization_candidate，但在 timing conflict 未解除前，不能误读成接近结婚。')
    if missing:
        risks.append(f"仍缺少关键层：{', '.join(str(item) for item in missing[:4])}。")
    if 'virodhargala_obstruction' in secondary_context:
        risks.append('第七宫 Argala 出现阻滞，关系推进可能伴随现实阻力或时间延后。')
    if 'dignity_high_friction' in secondary_context:
        risks.append('相关婚恋行星尊贵度摩擦较高，关系推进时更容易出现磨损与反复确认。')
    if 'shadbala_component_gap' in secondary_context:
        risks.append('Shadbala 六分量还存在缺口，关系强弱结论需继续保守处理。')
    if monthly_frame.get('friction_source', {}).get('value'):
        risks.append(f"阻力来源：{monthly_frame.get('friction_source', {}).get('value')}。")

    boundaries.append('婚恋高严谨模式至少需要 D1、D9、UL、Vimshottari 与 Narayana dual dasha 同时在场。')
    boundaries.append('protective kuta support、Mahendra、Stree Deergha 等合盘细信号只能辅助，不得越权抬升 legal_marriage。')
    boundaries.append('若 dual dasha、external timing 或 marriage convergence 冲突，必须明确降置信度，而不是把关系窗口包装成婚姻必然落地。')
    if monthly_frame.get('time_confidence', {}).get('value'):
        boundaries.append(f"时间置信度：{monthly_frame.get('time_confidence', {}).get('value')}。")
    if 'public_formalization_candidate' in secondary_context:
        boundaries.append('public_formalization_candidate 只表示公开化候选，不等于法律婚姻，不能越权替代 legal_marriage。')
    if synastry_signals:
        boundaries.append(f"当前 synastry taxonomy 已命中 {', '.join(synastry_signals[:5])}，但这些信号仍从属于 secondary-context。")

    if not strengths:
        strengths.append('当前婚恋 strict workflow 主要提供边界与缺口提示，尚未形成足够稳定的正向落地支持。')
    if not risks:
        risks.append('未见强烈负面冲突，但仍需用现实事件、D9 和 dual dasha 做最后复核。')

    headline = (
        '婚恋严格裁决已接入 synastry taxonomy，可把合盘支持翻译成次级关系语义。'
        if 'synastry_support' in secondary_context
        else '婚恋严格裁决已接入主链，但当前更依赖本命、D9 与时机层，而非合盘辅助。'
    )

    markdown_lines = [
        '### 婚恋严格裁决',
        f"- headline: {headline}",
        f"- promise: {(adjudication.get('promise') or {}).get('status') or 'missing'} / drivers={(adjudication.get('promise') or {}).get('drivers') or []}",
        f"- activation: {(adjudication.get('activation') or {}).get('status') or 'missing'} / drivers={(adjudication.get('activation') or {}).get('drivers') or []}",
        f"- manifestation: {(adjudication.get('manifestation') or {}).get('status') or 'missing'} / drivers={(adjudication.get('manifestation') or {}).get('drivers') or []}",
        f"- label: {(adjudication.get('label') or {}).get('value') or dominant_label or 'none'}",
        f"- confidence_boundary: MEVG={confidence_boundary.get('mevg_status') or 'blocked'}; Real Case Calibration={confidence_boundary.get('real_case_calibration_status') or 'blocked'}; policy={confidence_boundary.get('unverified_claim_policy') or 'downgrade_or_block'}",
        f"- dominant_label: {dominant_label or 'none'}",
        f"- confidence_cap: {confidence_cap}",
        f"- secondary_context: {secondary_context}",
        f"- 月度主状态: {monthly_frame.get('primary_state', {}).get('value') or 'blocked'}",
        f"- 落地形式: {monthly_frame.get('manifestation_mode', {}).get('value') or 'blocked'}",
        f"- 阻力来源: {monthly_frame.get('friction_source', {}).get('value') or 'blocked'}",
        f"- 时间置信度: {monthly_frame.get('time_confidence', {}).get('value') or 'blocked'}",
        '- strengths:',
        *[f"  - {item}" for item in strengths],
        '- risks:',
        *[f"  - {item}" for item in risks],
        '- boundaries:',
        *[f"  - {item}" for item in boundaries],
    ]

    return {
        'headline': headline,
        'strengths': strengths,
        'risks': risks,
        'boundaries': boundaries,
        'monthly_frame': {
            'primary_state': monthly_frame.get('primary_state') or {'value': 'blocked'},
            'manifestation_mode': monthly_frame.get('manifestation_mode') or {'value': 'blocked'},
            'friction_source': monthly_frame.get('friction_source') or {'value': 'blocked'},
            'time_confidence': monthly_frame.get('time_confidence') or {'value': 'blocked'},
        },
        'markdown': "\n".join(markdown_lines),
        'output_template_status': 'used',
        'required_sections': ['promise', 'activation', 'manifestation', 'label', 'confidence_boundary'],
    }


def _base_strict_narrative_payload(route_label, strict, *, fallback_headline, strengths, risks, boundaries):
    monthly_frame = strict.get('monthly_adjudication_summary') if isinstance(strict, dict) else {}
    monthly_frame = monthly_frame if isinstance(monthly_frame, dict) else {}
    event_judgement = strict.get('event_judgement') if isinstance(strict, dict) else {}
    event_judgement = event_judgement if isinstance(event_judgement, dict) else {}
    adjudication = strict.get('adjudication_stages') if isinstance(strict, dict) else {}
    adjudication = adjudication if isinstance(adjudication, dict) else {}
    boundary_contract = strict.get('prediction_boundary_contract') if isinstance(strict, dict) else {}
    boundary_contract = boundary_contract if isinstance(boundary_contract, dict) else {}
    confidence_boundary = boundary_contract.get('confidence_boundary') if isinstance(boundary_contract, dict) else {}
    confidence_boundary = confidence_boundary if isinstance(confidence_boundary, dict) else {}
    confidence_cap = strict.get('confidence_cap') or event_judgement.get('confidence_cap') or 'unknown'
    dominant_label = event_judgement.get('dominant_label') if isinstance(event_judgement, dict) else None

    if monthly_frame.get('primary_state', {}).get('value'):
        strengths = list(strengths) + [f"月度主状态：{monthly_frame.get('primary_state', {}).get('value')}。"]
    if monthly_frame.get('manifestation_mode', {}).get('value'):
        strengths = list(strengths) + [f"落地形式：{monthly_frame.get('manifestation_mode', {}).get('value')}。"]
    if monthly_frame.get('friction_source', {}).get('value'):
        risks = list(risks) + [f"阻力来源：{monthly_frame.get('friction_source', {}).get('value')}。"]
    if monthly_frame.get('time_confidence', {}).get('value'):
        boundaries = list(boundaries) + [f"时间置信度：{monthly_frame.get('time_confidence', {}).get('value')}。"]

    markdown_lines = [
        f"### {route_label}严格裁决",
        f"- headline: {fallback_headline}",
        f"- promise: {(adjudication.get('promise') or {}).get('status') or 'missing'} / drivers={(adjudication.get('promise') or {}).get('drivers') or []}",
        f"- activation: {(adjudication.get('activation') or {}).get('status') or 'missing'} / drivers={(adjudication.get('activation') or {}).get('drivers') or []}",
        f"- manifestation: {(adjudication.get('manifestation') or {}).get('status') or 'missing'} / drivers={(adjudication.get('manifestation') or {}).get('drivers') or []}",
        f"- label: {(adjudication.get('label') or {}).get('value') or dominant_label or 'none'}",
        f"- confidence_boundary: MEVG={confidence_boundary.get('mevg_status') or 'blocked'}; Real Case Calibration={confidence_boundary.get('real_case_calibration_status') or 'blocked'}; policy={confidence_boundary.get('unverified_claim_policy') or 'downgrade_or_block'}",
        f"- dominant_label: {dominant_label or 'none'}",
        f"- confidence_cap: {confidence_cap}",
        f"- 月度主状态: {monthly_frame.get('primary_state', {}).get('value') or 'blocked'}",
        f"- 落地形式: {monthly_frame.get('manifestation_mode', {}).get('value') or 'blocked'}",
        f"- 阻力来源: {monthly_frame.get('friction_source', {}).get('value') or 'blocked'}",
        f"- 时间置信度: {monthly_frame.get('time_confidence', {}).get('value') or 'blocked'}",
        '- strengths:',
        *[f"  - {item}" for item in strengths],
        '- risks:',
        *[f"  - {item}" for item in risks],
        '- boundaries:',
        *[f"  - {item}" for item in boundaries],
    ]
    return {
        'headline': fallback_headline,
        'strengths': list(strengths),
        'risks': list(risks),
        'boundaries': list(boundaries),
        'monthly_frame': {
            'primary_state': monthly_frame.get('primary_state') or {'value': 'blocked'},
            'manifestation_mode': monthly_frame.get('manifestation_mode') or {'value': 'blocked'},
            'friction_source': monthly_frame.get('friction_source') or {'value': 'blocked'},
            'time_confidence': monthly_frame.get('time_confidence') or {'value': 'blocked'},
        },
        'markdown': "\n".join(markdown_lines),
        'output_template_status': 'used',
        'required_sections': ['promise', 'activation', 'manifestation', 'label', 'confidence_boundary'],
    }


def _build_career_narrative_payload(career_strict):
    if not isinstance(career_strict, dict) or not career_strict:
        return _base_strict_narrative_payload(
            '事业',
            {},
            fallback_headline='事业严格裁决证据尚未完成，当前不能生成高严谨事业叙事。',
            strengths=[],
            risks=['缺少 career strict workflow 的核心证据，事业正文需降级。'],
            boundaries=['未完成 D1、D10、A10、Vimshottari 与 Narayana 交叉前，不得把单一事业信号写成高置信度结论。'],
        )
    event_judgement = career_strict.get('event_judgement') if isinstance(career_strict, dict) else {}
    secondary_context = event_judgement.get('secondary_context') if isinstance(event_judgement, dict) else []
    secondary_context = secondary_context if isinstance(secondary_context, list) else []
    missing = career_strict.get('missing_evidence') or []
    strengths = []
    risks = []
    boundaries = [
        '事业高严谨模式至少需要 D1、D10、A10、Functional Benefic/Malefic、Vimshottari 与 Narayana dual dasha 同时在场。',
        'VedAstro 官方事件日可以给时间支撑，但不得越权改写本命 promise 与 strict workflow 的边界。',
    ]
    if event_judgement.get('dominant_label') == 'career_status':
        strengths.append('事业 strict workflow 已形成主裁决标签，说明职业主题不是泛泛活跃，而是进入可判读窗口。')
    if 'a10_active' in secondary_context:
        strengths.append('A10/Karma Pada 已进入主链，说明事业结果会更偏向社会角色、职责承接或可见产出。')
    if 'amk_active' in secondary_context:
        strengths.append('Amatyakaraka 已进入主链，说明职业能力、上级关系或专业角色承担被明显放大。')
    if 'karakamsha_context' in secondary_context:
        strengths.append('Karakamsha 已提供职业志向语义，适合用来判断方向感而不只是短期机会。')
    if missing:
        risks.append(f"仍缺少关键层：{', '.join(str(item) for item in missing[:4])}。")
    if 'virodhargala_obstruction' in secondary_context:
        risks.append('事业主轴存在 Argala 阻滞，推进通常伴随现实牵制、流程卡顿或资源不顺。')
    if 'dignity_high_friction' in secondary_context:
        risks.append('相关事业行星尊贵度摩擦较高，机会不一定消失，但落地成本会明显上升。')
    if 'shadbala_component_gap' in secondary_context:
        risks.append('Shadbala 六分量仍有缺口，强弱结论需继续保守。')
    headline = '事业严格裁决已接入主链，当前结论将强制引用本命 promise、双重大运、官方时间窗与结构阻力。'
    return _base_strict_narrative_payload(
        '事业',
        career_strict,
        fallback_headline=headline,
        strengths=strengths,
        risks=risks,
        boundaries=boundaries,
    )


def _build_finance_narrative_payload(finance_strict):
    if not isinstance(finance_strict, dict) or not finance_strict:
        return _base_strict_narrative_payload(
            '财富',
            {},
            fallback_headline='财富严格裁决证据尚未完成，当前不能生成高严谨财富叙事。',
            strengths=[],
            risks=['缺少 finance strict workflow 的核心证据，财富正文需降级。'],
            boundaries=['未完成 D2/D11、财富 promise、Vimshottari 与 Narayana 交叉前，不得把单一财富信号写成高置信度结论。'],
        )
    event_judgement = finance_strict.get('event_judgement') if isinstance(finance_strict, dict) else {}
    secondary_context = event_judgement.get('secondary_context') if isinstance(event_judgement, dict) else []
    secondary_context = secondary_context if isinstance(secondary_context, list) else []
    missing = finance_strict.get('missing_evidence') or []
    strengths = []
    risks = []
    boundaries = [
        '财富高严谨模式至少需要 D2/D11 或等价财富 promise 层、Functional Benefic/Malefic、Vimshottari 与 Narayana dual dasha 同时在场。',
        '官方财富日窗口只能帮助判断回款/交易/现金流节奏，不能单独替代本命财富 promise。',
    ]
    if event_judgement.get('dominant_label') == 'income_growth':
        strengths.append('财富 strict workflow 已判到 income_growth，说明更偏向真实入账增长，而不是空泛的财运变好。')
    if event_judgement.get('dominant_label') == 'public_wealth_status':
        strengths.append('财富 strict workflow 已判到 public_wealth_status，说明更像项目回款、公开收入状态或外部可见的收益变化。')
    if 'ashtakavarga_wealth_support' in secondary_context:
        strengths.append('Ashtakavarga 财富桥接已进入主链，可作为兑现能力的次级支持。')
    if missing:
        risks.append(f"仍缺少关键层：{', '.join(str(item) for item in missing[:4])}。")
    if 'avayogi_active' in secondary_context:
        risks.append('Avayogi 风险已触发，说明某些看似有钱流动的窗口也可能伴随高代价或错误决策。')
    if 'sodhita_wealth_friction' in secondary_context or 'ashtakavarga_wealth_friction' in secondary_context:
        risks.append('财富桥接层已提示兑现摩擦，现金流并不等于可自由留存。')
    if 'shadbala_component_gap' in secondary_context:
        risks.append('Shadbala 六分量仍有缺口，财富强弱结论需继续保守。')
    headline = '财富严格裁决已接入主链，当前结论会强制区分收入兑现、现金流动作与风险摩擦。'
    return _base_strict_narrative_payload(
        '财富',
        finance_strict,
        fallback_headline=headline,
        strengths=strengths,
        risks=risks,
        boundaries=boundaries,
    )


def _build_vedastro_overview_payload(modules):
    overview = modules.get('vedastro_range_scan_result') if isinstance(modules, dict) else {}
    if not isinstance(overview, dict):
        return {
            'status': 'blocked',
            'source': 'vedastro_service_adapter_candidate',
            'ingestion_profile': None,
            'search_scope': None,
            'reference_date': None,
            'event_count': 0,
            'domain_statuses': {},
            'top_events_by_domain': {},
            'boundary_note': 'VedAstro main-entry overview was not attached.',
            'visibility': 'user_visible_overview_only',
        }
    metadata = overview.get('source_metadata') if isinstance(overview.get('source_metadata'), dict) else {}
    return {
        'status': overview.get('status') or 'blocked',
        'source': overview.get('backend') or 'vedastro_service_adapter_candidate',
        'ingestion_profile': metadata.get('ingestion_profile'),
        'search_scope': metadata.get('search_scope'),
        'reference_date': metadata.get('reference_date'),
        'event_count': int(overview.get('event_count', 0) or 0),
        'domain_statuses': metadata.get('domain_statuses') or {},
        'top_events_by_domain': overview.get('top_events_by_domain') or {},
        'boundary_note': (
            overview.get('reason')
            or 'This is overview only and does not replace explicit long-range VedAstro scans.'
        ),
        'visibility': 'user_visible_overview_only',
    }


def _full_reading_profiler_enabled(args) -> bool:
    if bool(getattr(args, 'profile_stages', False)):
        return True
    env_value = os.environ.get('JYOTISH_PROFILE_STAGES', '').strip().lower()
    return env_value in {'1', 'true', 'yes', 'on'}


def _record_stage_timing(stage_timings, stage, started_at, *, enabled=False, status='ok', details=None):
    elapsed = round(time.perf_counter() - started_at, 4)
    entry = {
        'stage': stage,
        'elapsed_seconds': elapsed,
        'status': status,
    }
    if details:
        entry['details'] = details
    stage_timings.append(entry)
    if enabled:
        print(f"[full-reading stage] {stage}: {elapsed:.4f}s ({status})", file=sys.stderr)
    return entry


def _build_unified_stage_contract(stage_timings):
    groups = {
        'local_core': [
            'core_chart_and_setup',
            'dasha_and_core_varga_stack',
            'advanced_interpretation_and_timing_layers',
            'dynamic_hooks',
        ],
        'official_evidence': [
            'vedastro_official_snapshot',
            'vedastro_main_entry_overview',
        ],
        'contract_and_prompt': [
            'strict_contracts',
            'guided_topics',
            'ai_prompt_pack',
        ],
    }
    grouped_rows = []
    for group_name, stage_names in groups.items():
        matched = [row for row in stage_timings if row.get('stage') in stage_names]
        grouped_rows.append({
            'group': group_name,
            'stages': [row.get('stage') for row in matched],
            'elapsed_seconds': round(
                sum(float(row.get('elapsed_seconds', 0) or 0) for row in matched),
                4,
            ),
            'execution_mode': (
                'sync_remote_heavy' if group_name == 'official_evidence'
                else 'sync_structuring' if group_name == 'contract_and_prompt'
                else 'sync_local'
            ),
        })
    return {
        'stage_contract_version': 1,
        'stage_groups': grouped_rows,
        'cache_recommendations': {
            'api_chart_response': 'recommended',
            'official_full_snapshot_semantic': 'recommended',
        },
        'async_recommendations': {
            'chart_async_optional': True,
            'high_rigor_async_recommended': True,
        },
    }


STRICT_WORKFLOW_MODULE_MAP = {
    'relationship': 'relationship_strict_evidence',
    'career': 'career_strict_evidence',
    'finance': 'finance_strict_evidence',
}


def _compact_strict_workflow_contract(strict):
    if not isinstance(strict, dict) or not strict:
        return None
    return {
        'question_type': strict.get('question_type'),
        'confidence_cap': strict.get('confidence_cap'),
        'blocked': bool(strict.get('blocked')),
        'reason': strict.get('reason'),
        'required_evidence': strict.get('required_evidence') or [],
        'missing_evidence': strict.get('missing_evidence') or [],
        'official_primary_evidence': strict.get('official_primary_evidence') or {},
        'local_supplemental_evidence': strict.get('local_supplemental_evidence') or {},
        'fallback_used': strict.get('fallback_used') or [],
        'blocked_items': strict.get('blocked_items') or [],
        'conflicts': strict.get('conflicts') or [],
        'technique_audit_summary': strict.get('technique_audit_summary') or {},
        'adjudication_stages': strict.get('adjudication_stages') or {},
        'prediction_boundary_contract': strict.get('prediction_boundary_contract') or {},
        'domain_invocation_contract': strict.get('domain_invocation_contract') or {},
        'output_template_contract': strict.get('output_template_contract') or {},
        'mevg_collection_queue': strict.get('mevg_collection_queue') or {},
        'real_case_calibration_layer': strict.get('real_case_calibration_layer') or {},
        'technical_debt_contract': strict.get('technical_debt_contract') or {},
        'remaining_priority1_batch_queue': strict.get('remaining_priority1_batch_queue') or {},
        'oracle_parity_queue': strict.get('oracle_parity_queue') or {},
        'release_hygiene_plan': strict.get('release_hygiene_plan') or {},
        'multi_reference_reading_summary': strict.get('multi_reference_reading_summary') or {},
        'monthly_adjudication_summary': strict.get('monthly_adjudication_summary') or {},
        'official_day_signal_summary': strict.get('official_day_signal_summary') or {},
        'strict_adjudication_bundle': strict.get('strict_adjudication_bundle') or {},
        'verdict': strict.get('verdict'),
        'dominant_label': strict.get('dominant_label'),
        'main_conflicts': strict.get('main_conflicts') or [],
    }


def _extract_strict_workflow_contracts(modules):
    contracts = {}
    if not isinstance(modules, dict):
        return contracts
    for route, module_name in STRICT_WORKFLOW_MODULE_MAP.items():
        contract = _compact_strict_workflow_contract(modules.get(module_name))
        if contract:
            contracts[route] = contract
    return contracts


def _preferred_strict_workflow_contract(contracts):
    if not isinstance(contracts, dict):
        return None, {}
    for route in ('relationship', 'career', 'finance'):
        contract = contracts.get(route)
        if isinstance(contract, dict) and contract:
            return route, contract
    return None, {}


def _build_vedastro_official_full_snapshot_payload(modules):
    snapshot = modules.get('vedastro_official_full_snapshot') if isinstance(modules, dict) else {}
    strict_workflow_contracts = _extract_strict_workflow_contracts(modules)
    primary_route, primary_contract = _preferred_strict_workflow_contract(strict_workflow_contracts)
    official_primary_evidence = primary_contract.get('official_primary_evidence') if isinstance(primary_contract, dict) else {}
    local_supplemental_evidence = primary_contract.get('local_supplemental_evidence') if isinstance(primary_contract, dict) else {}
    fallback_used = primary_contract.get('fallback_used') if isinstance(primary_contract, dict) else []
    blocked_items = primary_contract.get('blocked_items') if isinstance(primary_contract, dict) else []
    conflicts = primary_contract.get('conflicts') if isinstance(primary_contract, dict) else []
    if not isinstance(snapshot, dict) or not snapshot:
        return {
            'status': 'blocked',
            'available': False,
            'operation': 'official_full_snapshot',
            'primary_source': 'vedastro_official',
            'strict_workflow_primary_route': primary_route,
            'strict_workflow_routes_available': list(strict_workflow_contracts.keys()),
            'strict_workflow_contracts': strict_workflow_contracts,
            'official_primary_evidence': official_primary_evidence or {},
            'local_supplemental_evidence': local_supplemental_evidence or {},
            'fallback_used': fallback_used or [],
            'blocked_items': blocked_items or [],
            'conflicts': conflicts or [],
            'boundary_note': 'VedAstro official full snapshot is not attached.',
        }
    manifest = snapshot.get('request_manifest') if isinstance(snapshot.get('request_manifest'), dict) else {}
    requests = manifest.get('requests') if isinstance(manifest.get('requests'), list) else []
    snapshot_sections = snapshot.get('snapshot_sections') if isinstance(snapshot.get('snapshot_sections'), dict) else {}
    metadata = snapshot.get('source_metadata') if isinstance(snapshot.get('source_metadata'), dict) else {}
    full_catalog = metadata.get('official_full_capability_catalog') if isinstance(metadata.get('official_full_capability_catalog'), dict) else {}
    dynamic_selection = full_catalog.get('dynamic_selection') if isinstance(full_catalog.get('dynamic_selection'), dict) else {}
    report_references = {
        theme: selection.get('report_reference')
        for theme, selection in dynamic_selection.items()
        if isinstance(selection, dict) and isinstance(selection.get('report_reference'), dict)
    }
    return {
        'status': snapshot.get('status') or 'blocked',
        'available': bool(snapshot.get('available')),
        'operation': snapshot.get('operation') or 'official_full_snapshot',
        'primary_source': snapshot.get('primary_source') or 'vedastro_official',
        'section_statuses': snapshot.get('section_statuses') or {},
        'snapshot_section_keys': sorted(snapshot_sections.keys()),
        'request_section_count': len(requests),
        'request_sections': [item.get('section') for item in requests if isinstance(item, dict)],
        'method_catalog': manifest.get('method_catalog') or {},
        'official_full_capability_catalog_status': full_catalog.get('status'),
        'official_full_capability_catalog_summary': full_catalog.get('summary') or {},
        'official_full_capability_catalog_coverage': full_catalog.get('coverage') or {},
        'official_full_capability_domain_routing': full_catalog.get('domain_routing') or {},
        'official_full_capability_dynamic_selection': dynamic_selection,
        'official_report_references': report_references,
        'user_visibility': snapshot.get('user_visibility') or 'backend_raw_evidence_not_direct_user_report',
        'source_metadata': snapshot.get('source_metadata') or {},
        'strict_workflow_primary_route': primary_route,
        'strict_workflow_routes_available': list(strict_workflow_contracts.keys()),
        'strict_workflow_contracts': strict_workflow_contracts,
        'official_primary_evidence': official_primary_evidence or {},
        'local_supplemental_evidence': local_supplemental_evidence or {},
        'fallback_used': fallback_used or [],
        'blocked_items': blocked_items or [],
        'conflicts': conflicts or [],
        'boundary_note': (
            snapshot.get('reason')
            or 'VedAstro official full snapshot is the primary raw evidence layer; user reports consume selected slices only.'
        ),
    }


def _build_ai_prompt_pack(report):
    """Build a compact, evidence-first prompt pack for downstream AI/RAG reading."""
    modules = report.get('modules', {}) if isinstance(report, dict) else {}
    chart = report.get('chart') or modules.get('chart') or {}
    planets = chart.get('planets', {}) if isinstance(chart, dict) else {}
    birth_info = chart.get('birth_info', {}) if isinstance(chart, dict) else {}
    dasha = modules.get('dasha') or {}
    current_dasha = dasha.get('current_dasha') if isinstance(dasha, dict) else {}
    narayana = modules.get('narayana_dasha') or {}
    dasa_convergence = modules.get('dasa_convergence') or {}
    shadbala = modules.get('shadbala') or {}
    shadbala_planets = shadbala.get('planets', {}) if isinstance(shadbala, dict) else {}
    ashtakavarga = modules.get('ashtakavarga') or {}
    sav = ashtakavarga.get('sav') if isinstance(ashtakavarga, dict) else {}
    d9 = modules.get('d9_navamsa_expanded') or {}
    functional_layer = _functional_benefic_malefic_snapshot(planets, chart.get('ascendant', {}))
    oracle_progress = _oracle_progress_snapshot()
    technique_audit_table = _build_technique_audit_table(functional_layer, oracle_progress, modules)
    relationship_narrative = _build_relationship_narrative_payload(modules.get('relationship_strict_evidence'))
    career_narrative = _build_career_narrative_payload(modules.get('career_strict_evidence'))
    finance_narrative = _build_finance_narrative_payload(modules.get('finance_strict_evidence'))
    vimsopaka_semantic_summary = _build_vimsopaka_semantic_summary(modules.get('vimsopaka'))
    vedastro_overview = _build_vedastro_overview_payload(modules)
    vedastro_official_full_snapshot = _build_vedastro_official_full_snapshot_payload(modules)
    strict_workflow_contracts = _extract_strict_workflow_contracts(modules)
    strict_workflow_primary_route, primary_strict_contract = _preferred_strict_workflow_contract(strict_workflow_contracts)
    primary_prediction_boundary_contract = (
        primary_strict_contract.get('prediction_boundary_contract')
        if isinstance(primary_strict_contract, dict)
        else {}
    )
    primary_domain_invocation_layers = (
        primary_strict_contract.get('domain_invocation_contract')
        if isinstance(primary_strict_contract, dict)
        else {}
    )
    primary_output_template_contract = (
        primary_strict_contract.get('output_template_contract')
        if isinstance(primary_strict_contract, dict)
        else {}
    )
    primary_mevg_collection_queue = (
        primary_strict_contract.get('mevg_collection_queue')
        if isinstance(primary_strict_contract, dict)
        else {}
    )
    primary_real_case_calibration_layer = (
        primary_strict_contract.get('real_case_calibration_layer')
        if isinstance(primary_strict_contract, dict)
        else {}
    )
    primary_technical_debt_contract = (
        primary_strict_contract.get('technical_debt_contract')
        if isinstance(primary_strict_contract, dict)
        else {}
    )
    primary_remaining_priority1_batch_queue = (
        primary_strict_contract.get('remaining_priority1_batch_queue')
        if isinstance(primary_strict_contract, dict)
        else {}
    )
    primary_oracle_parity_queue = (
        primary_strict_contract.get('oracle_parity_queue')
        if isinstance(primary_strict_contract, dict)
        else {}
    )
    primary_release_hygiene_plan = (
        primary_strict_contract.get('release_hygiene_plan')
        if isinstance(primary_strict_contract, dict)
        else {}
    )
    primary_audit = (
        primary_strict_contract.get('technique_audit_summary')
        if isinstance(primary_strict_contract, dict)
        else {}
    )
    try:
        from strict_evidence_service import existing_interpretation_source_pack
        fallback_source_pack = existing_interpretation_source_pack()
    except Exception:
        fallback_source_pack = {}
    interpretation_source_audit = (
        primary_audit.get('interpretation_source_pack')
        if isinstance(primary_audit, dict) and isinstance(primary_audit.get('interpretation_source_pack'), dict)
        else {}
    )
    fallback_domain_layers = (
        fallback_source_pack.get('domain_invocation_layers')
        if isinstance(fallback_source_pack, dict) and isinstance(fallback_source_pack.get('domain_invocation_layers'), dict)
        else {}
    )
    guided_topics = modules.get('guided_topics') if isinstance(modules.get('guided_topics'), list) else build_guided_topics(report)
    capability_evidence_pool = build_capability_evidence_pool_summary()

    shadbala_ranking = []
    for planet_name, pdata in sorted(
        shadbala_planets.items(),
        key=lambda item: item[1].get('rank', 99) if isinstance(item[1], dict) else 99,
    ):
        if isinstance(pdata, dict):
            shadbala_ranking.append({
                'planet': planet_name,
                'rank': pdata.get('rank'),
                'total_rupas': pdata.get('total_rupas'),
                'min_required': pdata.get('min_required'),
                'strength_level': pdata.get('strength_level'),
            })

    current_ad = current_dasha.get('antardasha') if isinstance(current_dasha, dict) else {}
    evidence_snapshot = {
        'birth': report.get('birth_info', {}),
        'ayanamsa': {
            'name': birth_info.get('ayanamsa_name', 'lahiri'),
            'display': birth_info.get('ayanamsa_display', 'Lahiri'),
            'value': birth_info.get('ayanamsa'),
            'node_mode': birth_info.get('node_mode'),
        },
        'core': {
            'ascendant': chart.get('ascendant', {}),
            'Sun': _planet_snapshot(planets, 'Sun'),
            'Moon': _planet_snapshot(planets, 'Moon'),
            'Mars': _planet_snapshot(planets, 'Mars'),
            'Jupiter': _planet_snapshot(planets, 'Jupiter'),
            'Venus': _planet_snapshot(planets, 'Venus'),
            'Saturn': _planet_snapshot(planets, 'Saturn'),
            'Rahu': _planet_snapshot(planets, 'Rahu'),
            'Ketu': _planet_snapshot(planets, 'Ketu'),
        },
        'timing': {
            'vimshottari': {
                'mahadasha': current_dasha.get('lord') if isinstance(current_dasha, dict) else None,
                'antardasha': current_ad.get('lord') if isinstance(current_ad, dict) else None,
                'start': current_dasha.get('start') if isinstance(current_dasha, dict) else None,
                'end': current_dasha.get('end') if isinstance(current_dasha, dict) else None,
            },
            'narayana': {
                'current_dasha': narayana.get('current_dasha') if isinstance(narayana, dict) else None,
                'current_year': narayana.get('current_year') if isinstance(narayana, dict) else None,
                'current_age': narayana.get('current_age') if isinstance(narayana, dict) else None,
            },
            'convergence_top_domains': dasa_convergence.get('top_convergent_domains', []) if isinstance(dasa_convergence, dict) else [],
        },
        'strength': {
            'shadbala_ranking': shadbala_ranking[:7],
            'sav_total': sav.get('total') if isinstance(sav, dict) else None,
            'sav_scores': sav.get('scores') if isinstance(sav, dict) else None,
        },
        'varga_focus': {
            'd9': {
                'Ascendant': d9.get('Ascendant') if isinstance(d9, dict) else None,
                'Venus': d9.get('Venus') if isinstance(d9, dict) else None,
                'Jupiter': d9.get('Jupiter') if isinstance(d9, dict) else None,
                'Mars': d9.get('Mars') if isinstance(d9, dict) else None,
                'Saturn': d9.get('Saturn') if isinstance(d9, dict) else None,
            }
        },
        'quality_boundary': {
            'errors': report.get('errors', []),
            'warnings': report.get('warnings', []),
            'external_oracle_status': 'D1/D9/VedAstro longitude boundary covered; Dasha/Shadbala external absolute calibration still requires multi-source oracle expansion.',
        },
        'oracle_progress': oracle_progress,
        'functional_benefic_malefic': functional_layer,
        'interpretation_source_pack': {
            'status': interpretation_source_audit.get('status') or 'blocked',
            'source': interpretation_source_audit.get('source') or 'repo_existing_interpretation_sources',
            'core_rule_source_refs': interpretation_source_audit.get('core_rule_source_refs') or [],
            'promote_batch2_source_refs': interpretation_source_audit.get('promote_batch2_source_refs') or [],
            'reference_only_source_refs': interpretation_source_audit.get('reference_only_source_refs') or [],
            'missing_refs': interpretation_source_audit.get('missing_refs') or [],
        },
        'prediction_boundary_contract': primary_prediction_boundary_contract or {},
        'domain_invocation_layers': primary_domain_invocation_layers or fallback_domain_layers or {},
        'output_template_contract': primary_output_template_contract or {},
        'mevg_collection_queue': primary_mevg_collection_queue or {},
        'real_case_calibration_layer': primary_real_case_calibration_layer or {},
        'technical_debt_contract': primary_technical_debt_contract or {},
        'remaining_priority1_batch_queue': primary_remaining_priority1_batch_queue or {},
        'oracle_parity_queue': primary_oracle_parity_queue or {},
        'release_hygiene_plan': primary_release_hygiene_plan or {},
        'strict_workflow_primary_route': strict_workflow_primary_route,
        'strict_workflow_routes_available': list(strict_workflow_contracts.keys()),
        'strict_workflow_contracts': strict_workflow_contracts,
        'official_primary_evidence': primary_strict_contract.get('official_primary_evidence') if isinstance(primary_strict_contract, dict) else {},
        'local_supplemental_evidence': primary_strict_contract.get('local_supplemental_evidence') if isinstance(primary_strict_contract, dict) else {},
        'fallback_used': primary_strict_contract.get('fallback_used') if isinstance(primary_strict_contract, dict) else [],
        'blocked_items': primary_strict_contract.get('blocked_items') if isinstance(primary_strict_contract, dict) else [],
        'conflicts': primary_strict_contract.get('conflicts') if isinstance(primary_strict_contract, dict) else [],
        'vedastro_official_full_snapshot': vedastro_official_full_snapshot,
        'vedastro_overview': vedastro_overview,
        'guided_topics': guided_topics,
        'capability_evidence_pool': capability_evidence_pool,
        'technique_audit_table': technique_audit_table,
        'career_narrative': career_narrative,
        'relationship_narrative': relationship_narrative,
        'finance_narrative': finance_narrative,
        'vimsopaka_semantic_summary': vimsopaka_semantic_summary,
    }

    prompt_lines = [
        "你是一个审慎的 AI Native 印度/吠陀占星分析助手。",
        "请只基于 evidence_snapshot 中的计算证据生成解读，不要编造星盘不存在的配置。",
        f"本盘使用 {evidence_snapshot['ayanamsa']['display']} ayanamsa，节点口径为 {evidence_snapshot['ayanamsa']['node_mode']}。",
        "必须遵守：不要仅凭单一配置下结论；每个核心判断至少交叉 D1、D9、Dasha、Shadbala/Ashtakavarga 或 Transit 中的两个证据层。",
        "必须显式标注置信度和边界：Dasha/PDF 起点差异、Shadbala 外部绝对值 oracle 尚未完成时，不得声称已经完全校准。",
        "输出结构建议：参数声明、核心星盘、关系/事业/财富/健康分主题、当前时机、证据表、风险边界、可行动建议。",
        "若引用经典法则，请优先检索 retrieval_plan.local_reference_docs；需要外部断语时再做 web/source verification。",
        "若 evidence_snapshot.vedastro_overview.status 为 ok，请把它作为用户可见外部概览证据明确写出，但不要把 overview-only 结果误当作长周期精扫结论。",
        "VedAstro 官方全量快照是第一原始证据层；若 evidence_snapshot.vedastro_official_full_snapshot.status 不是 ok/partial，必须说明官方全量资料 blocked，并把本地结果标记为 fallback。",
        "若 evidence_snapshot.capability_evidence_pool 存在，请把 89 项视为后台备选证据池；不要把所有能力条目平铺成结论，也不要让 audit_only/alias 条目影响占星判断。",
        "必须按 promise → activation → manifestation → label 输出；每个判断都要说明属于承诺、激活、落地形式还是标签层。",
        "未完成 MEVG / Real Case Calibration 时必须降级或标 blocked，不得把内部一致性写成已验证结论。",
    ]

    return {
        'schema_version': 1,
        'mode': 'jyotish_structured_prompt_pack',
        'prompt_zh': "\n".join(prompt_lines),
        'evidence_snapshot': evidence_snapshot,
        'retrieval_plan': {
            'local_reference_docs': [
                'references/ai-reading-workflow-prompt.md',
                'references/comprehensive-reading-workflow.md',
                'references/prediction-boundary-protocol.md',
                'references/event_judgment_skeleton.md',
                'references/planetary-dignity-complete-reference.md',
                'references/retrograde-combustion-war-guide.md',
                'references/transit-multi-reference-guide.md',
                'references/vimshottari_dasha_guide.md',
                'references/pratyantar-calculation-guide.md',
                'references/divisional-chart-deep-reading.md',
                'references/shadbala-complete-methodology.md',
                'references/ashtakavarga-complete-system.md',
                'references/tajika-yoga-complete-guide.md',
                'references/jaimini-complete-system.md',
                'references/kp-astrology-complete-system.md',
                'references/argala-complete-guide.md',
                'references/badhaka-obstacle-planet-guide.md',
                'references/condition-dasha-complete.md',
                'references/dasa-convergence-methodology.md',
                'references/multi-dasha-convergence-protocol.md',
                'references/yoga-strength-scoring-system.md',
                'references/shadbala-interpretation-methodology.md',
                'references/navamsa-d9-interpretation-template.md',
                'references/interpretation_template_registry.json',
                'references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/p1_p12.md',
                'references/open_source_sources/vedic-astro-skills/codex/skills/vedic-core/resources/house_framework.md',
                'references/raman-house-judgment-methodology.md',
                'references/mandatory-verification-gate-protocol.md',
                'references/real-reading-quality-checklist.md',
                'jyotish-app/planet-house-details-a.js',
                'jyotish-app/planet-house-details-b.js',
                'jyotish-app/planet-house-details-c.js',
            ],
            'retrieval_tags': [
                'no_single_factor_conclusion',
                'd1_d9_dasha_cross_validation',
                'oracle_boundary_visible',
                'external_oracle_evidence_validation',
                'confidence_labeled_reading',
                'interpretation_source_pack',
                'mevg_global_web_evidence_required',
                'real_case_calibration_required',
            ],
        },
    }


def _overview_vedastro_reference_date(args) -> str:
    candidate = (
        getattr(args, 'transit_date', None)
        or getattr(args, 'today', None)
        or datetime.now().strftime('%Y-%m-%d')
    )
    return str(candidate)[:10]


def _overview_vedastro_scan_window(reference_date: str) -> tuple[str, str]:
    start = datetime.strptime(reference_date, '%Y-%m-%d').date()
    return start.isoformat(), start.isoformat()


def _attach_vedastro_main_entry_overview(report, args):
    if not isinstance(report, dict):
        return report
    modules = report.setdefault('modules', {})
    if not isinstance(modules, dict):
        return report
    if modules.get('vedastro_range_scan_result'):
        return report

    try:
        from vedastro_service_adapter import run_range_scan_for_case
    except Exception as exc:  # pragma: no cover - import guard
        report.setdefault('warnings', []).append(f"vedastro-main-entry-import: {exc}")
        return report

    reference_date = _overview_vedastro_reference_date(args)
    start_date, end_date = _overview_vedastro_scan_window(reference_date)
    case = {
        'year': getattr(args, 'year', None),
        'month': getattr(args, 'month', None),
        'day': getattr(args, 'day', None),
        'hour': getattr(args, 'hour', None),
        'minute': getattr(args, 'minute', None),
        'second': _arg_second(args),
        'lat': getattr(args, 'lat', None),
        'lon': getattr(args, 'lon', None),
        'tz': getattr(args, 'tz', None),
        'ayanamsa_policy': getattr(args, 'ayanamsa', None) or _current_ayanamsa_name(args),
        'node_policy': getattr(args, 'node_mode', 'mean'),
        'reference_date': (
            getattr(args, 'transit_date', None)
            or getattr(args, 'today', None)
            or datetime.now().strftime('%Y-%m-%d')
        ),
    }

    def _scan_domain(domain: str):
        return domain, run_range_scan_for_case(
            case,
            domain=domain,
            start_date=start_date,
            end_date=end_date,
            case_id=f"main_entry_{domain}",
        )

    domain_reports = {}
    combined_events = []
    domain_statuses = {}
    top_events = {}
    daily_windows_by_domain = {}
    top_daily_window_by_domain = {}
    failure_reason = None
    availability = True

    with ThreadPoolExecutor(max_workers=3) as executor:
        for domain, domain_report in executor.map(_scan_domain, ('career', 'marriage', 'wealth')):
            domain_reports[domain] = domain_report
    for domain in ('career', 'marriage', 'wealth'):
        domain_report = domain_reports[domain]
        domain_statuses[domain] = domain_report.get('status')
        availability = availability and bool(domain_report.get('available', False))
        if domain_report.get('status') != 'ok' and failure_reason is None:
            failure_reason = domain_report.get('reason')
        for event in domain_report.get('evidence_ledger') or []:
            if isinstance(event, dict):
                combined_events.append(event)
        top_event = domain_report.get('top_event')
        if isinstance(top_event, dict):
            top_events[domain] = top_event
        daily_windows = domain_report.get('daily_windows')
        if isinstance(daily_windows, list):
            daily_windows_by_domain[domain] = daily_windows
        top_daily_window = domain_report.get('top_daily_window')
        if isinstance(top_daily_window, dict):
            top_daily_window_by_domain[domain] = top_daily_window

    primary_status = next(
        (
            domain_reports[domain].get('status')
            for domain in ('career', 'marriage', 'wealth')
            if domain_reports.get(domain, {}).get('status') == 'ok'
        ),
        domain_reports.get('marriage', {}).get('status') or 'blocked',
    )
    source_metadata = {
        'ingestion_profile': 'main_entry_overview',
        'search_scope': 'single_day_overview',
        'reference_date': reference_date,
        'scan_window': {'start': start_date, 'end': end_date},
        'domain_statuses': domain_statuses,
        'domain_event_counts': {
            domain: int((domain_reports.get(domain, {}) or {}).get('event_count', 0) or 0)
            for domain in ('career', 'marriage', 'wealth')
        },
    }
    for domain in ('career', 'marriage', 'wealth'):
        metadata = domain_reports.get(domain, {}).get('source_metadata')
        if isinstance(metadata, dict):
            for key in (
                'endpoint',
                'endpoint_host',
                'transport',
                'provenance_mode',
                'timeout_seconds',
                'retry_policy',
            ):
                if key in metadata and key not in source_metadata:
                    source_metadata[key] = metadata[key]

    modules['vedastro_range_scan_result'] = {
        'backend': 'vedastro_service_adapter_candidate',
        'available': availability,
        'status': primary_status,
        'operation': 'range_scan',
        'domain': 'overview',
        'event_count': len(combined_events),
        'top_event': top_events.get('marriage') or next(iter(top_events.values()), None),
        'top_events_by_domain': top_events,
        'daily_windows': [
            item
            for domain in ('career', 'marriage', 'wealth')
            for item in (daily_windows_by_domain.get(domain) or [])
            if isinstance(item, dict)
        ],
        'top_daily_window': (
            top_daily_window_by_domain.get('marriage')
            or next(iter(top_daily_window_by_domain.values()), None)
        ),
        'daily_windows_by_domain': daily_windows_by_domain,
        'top_daily_window_by_domain': top_daily_window_by_domain,
        'evidence_ledger': combined_events,
        'source_metadata': source_metadata,
        'reason': failure_reason,
        'domain_reports': domain_reports,
    }
    return report


def _attach_vedastro_official_full_snapshot(report, args):
    if not isinstance(report, dict):
        return report
    modules = report.setdefault('modules', {})
    if not isinstance(modules, dict):
        return report
    if modules.get('vedastro_official_full_snapshot'):
        return report

    try:
        from vedastro_service_adapter import run_official_full_snapshot_for_case
        from vedastro_priority import apply_vedastro_source_priority
    except Exception as exc:  # pragma: no cover - import guard
        report.setdefault('warnings', []).append(f"vedastro-official-full-snapshot-import: {exc}")
        return report

    case = {
        'year': getattr(args, 'year', None),
        'month': getattr(args, 'month', None),
        'day': getattr(args, 'day', None),
        'hour': getattr(args, 'hour', None),
        'minute': getattr(args, 'minute', None),
        'second': _arg_second(args),
        'lat': getattr(args, 'lat', None),
        'lon': getattr(args, 'lon', None),
        'tz': getattr(args, 'tz', None),
        'ayanamsa_policy': getattr(args, 'ayanamsa', None) or _current_ayanamsa_name(args),
        'node_policy': getattr(args, 'node_mode', 'mean'),
        'reference_date': (
            getattr(args, 'transit_date', None)
            or getattr(args, 'today', None)
            or datetime.now().strftime('%Y-%m-%d')
        ),
    }
    modules['vedastro_official_full_snapshot'] = run_official_full_snapshot_for_case(
        case,
        case_id='full_reading_official_primary',
    )
    apply_vedastro_source_priority(
        report,
        official_snapshot=modules['vedastro_official_full_snapshot'],
    )
    return report


def _load_strict_evidence_collector():
    try:
        from strict_evidence_service import collect_strict_evidence as collector
        return collector
    except Exception:
        service_path = os.path.join(SCRIPT_DIR, 'strict_evidence_service.py')
        if not os.path.exists(service_path):
            raise
        spec = importlib.util.spec_from_file_location("jyotish_strict_evidence_service", service_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Unable to load strict_evidence_service from {service_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        collector = getattr(module, "collect_strict_evidence", None)
        if collector is None:
            raise ImportError("strict_evidence_service.collect_strict_evidence not found")
        return collector


# ============================================================================
# 公共星盘计算（供 chart/shadbala/ashtakavarga 共用，v3.4提取）
# ============================================================================
def compute_chart_data(year, month, day, hour, minute, lat, lon, tz, node_mode='mean', second=0, ayanamsa_name=None):
    """计算星盘核心数据，返回 (result_dict, asc_idx, jd, ayanamsa)。node_mode: mean|true。"""
    if not HAS_SWE:
        return None, None, None, None
    swe.set_ephe_path('')
    if ayanamsa_name:
        _apply_ayanamsa(ayanamsa_name)
    ayanamsa_name = _current_ayanamsa_name(type('Args', (), {'ayanamsa': ayanamsa_name})())
    second = int(second or 0)
    hour_decimal = _birth_hour_decimal(hour, minute, second) - tz
    jd = swe.julday(year, month, day, hour_decimal)
    ayanamsa = swe.get_ayanamsa(jd)

    node_mode = (node_mode or 'mean').lower()
    if node_mode not in ('mean', 'true'):
        node_mode = 'mean'
    node_pid = _node_pid(node_mode)
    result = {"birth_info": {
        "date": f"{year}-{month:02d}-{day:02d}", "time": _birth_time_string(hour, minute, second),
        "hour": int(hour), "minute": int(minute), "second": second,
        "tz": f"UTC{'+' if tz >= 0 else ''}{tz}", "lat": lat, "lon": lon,
        "julian_day": round(jd, 6), "ayanamsa": round(ayanamsa, 4),
        "ayanamsa_name": ayanamsa_name,
        "ayanamsa_display": _ayanamsa_display_name(ayanamsa_name),
        "node_mode": node_mode, "node_mode_note": "mean=Mean Node; true=True Node. PyJHora默认true，本skill默认mean。"
    }, "ascendant": None, "planets": {}, "houses": {}}

    asc_lon, _ = swe.houses(jd, lat, lon, b'A')
    asc_deg = (asc_lon[0] - ayanamsa) % 360
    asc_idx = int(asc_deg / 30)
    asc_sign = SIGNS[asc_idx]
    deg_in_sign = asc_deg - asc_idx * 30
    result["ascendant"] = {"sign": asc_sign, "sign_cn": SIGNS_CN[asc_sign],
        "degree": round(deg_in_sign, 4), "degree_raw": round(asc_deg, 4),
        "degree_in_sign": round(deg_in_sign, 4),
        "degree_in_sign_raw": asc_deg,
        "lon": round(asc_deg, 4),
        "lord": SIGN_LORDS[asc_sign]}

    for i in range(12):
        c = (asc_lon[i] - ayanamsa) % 360
        si = int(c / 30)
        result["houses"][f"house_{i+1}"] = {"cusp_sign": SIGNS[si],
            "cusp_sign_cn": SIGNS_CN[SIGNS[si]], "cusp_degree": round(c, 4),
            "lord": SIGN_LORDS[SIGNS[si]]}

    nak_span = 360.0 / 27
    planets_swe = {**BASE_PLANETS_SWE, 'Rahu': node_pid}
    for pname, pid in planets_swe.items():
        try:
            pos, _ = swe.calc_ut(jd, pid)
            lon_p = (pos[0] - ayanamsa) % 360; lat_p = pos[1]; spd = pos[3]
            si = int(lon_p / 30); d_in_s = lon_p - si * 30; sign = SIGNS[si]
            retro = spd < 0
            house = ((si - asc_idx) % 12) + 1
            ni = int(lon_p / nak_span); pada = int((lon_p % nak_span) / (nak_span / 4)) + 1
            nak_n, nak_l, _ = NAKSHATRA_LIST[ni % 27]
            result["planets"][pname] = {
                "sign": sign, "sign_cn": SIGNS_CN[sign], "degree": round(lon_p, 4),
                "degree_raw": lon_p,
                "degree_in_sign": round(d_in_s, 4), "degree_in_sign_raw": d_in_s,
                "house": house, "status": "",
                "retrograde": retro, "speed": round(spd, 6),
                "nakshatra": nak_n, "nakshatra_pada": pada, "nakshatra_lord": nak_l}
            if pname == 'Rahu':
                klon = (lon_p + 180) % 360; ksi = int(klon / 30); kd = klon - ksi * 30
                kni = int(klon / nak_span); kp = int((klon % nak_span) / (nak_span / 4)) + 1
                kn, kl, _ = NAKSHATRA_LIST[kni % 27]
                result["planets"]["Ketu"] = {
                    "sign": SIGNS[ksi], "sign_cn": SIGNS_CN[SIGNS[ksi]],
                    "degree": round(klon, 4), "degree_raw": klon,
                    "degree_in_sign": round(kd, 4), "degree_in_sign_raw": kd,
                    "house": ((ksi - asc_idx) % 12) + 1, "status": "",
                    "retrograde": True, "speed": round(spd, 6),
                    "nakshatra": kn, "nakshatra_pada": kp, "nakshatra_lord": kl}
        except Exception as e:
            result["planets"][pname] = {"error": str(e)}
            
    for pn, p_data in result["planets"].items():
        if "error" not in p_data and pn != "Lagna":
            p_data["status"] = _get_planet_status_label(pn, p_data["sign"], p_data["degree_in_sign"], result["planets"])
            
    return result, asc_idx, jd, ayanamsa


# ============================================================================
# 1. 星盘计算
# ============================================================================
def cmd_chart(args):
    result, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if result is None:
        return {"error": "swisseph未安装"}
    # v3.5: --validate 触发 R1-R10 校验
    if getattr(args, 'validate', False):
        try:
            sys.path.insert(0, SCRIPT_DIR)
            from ashtakavarga import calc_ashtakavarga
            asht_result = calc_ashtakavarga(result.get('planets', {}), asc_idx)
            from validate import validate_chart
            validation = validate_chart(result, asht_result)
            result['validation'] = validation
        except Exception as e:
            result['validation'] = {"error": str(e), "valid": False}
    return result


# ============================================================================
# 2. Dasha计算
# ============================================================================
def cmd_dasha(args):
    nak_info = None; progress = 0.5
    if args.moon_lon is not None:
        ns = 360.0 / 27; idx = int(args.moon_lon / ns); progress = (args.moon_lon % ns) / ns
        nak_info = NAKSHATRA_LIST[idx % 27]
    elif args.nakshatra:
        nl = args.nakshatra.lower().replace(" ", "").replace("-", "")
        for n in NAKSHATRA_LIST:
            if nl in n[0].lower().replace(" ", "") or n[0].lower().replace(" ", "").startswith(nl[:5]):
                nak_info = n; break
        if not nak_info: return {"error": f"未找到Nakshatra: {args.nakshatra}"}
        if args.pada: progress = (max(1, min(4, args.pada)) - 1) / 4 + 0.125
    else:
        # v6.0.27: Auto-calculate Moon's Nakshatra from birth datetime
        chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
        if chart is None:
            return {"error": "swisseph未安装，无法自动计算Nakshatra"}
        moon = chart.get("planets", {}).get("Moon", {})
        moon_lon = moon.get("degree_raw")
        if moon_lon is None:
            return {"error": "无法计算Moon位置"}
        ns = 360.0 / 27; idx = int(moon_lon / ns); progress = (moon_lon % ns) / ns
        nak_info = NAKSHATRA_LIST[idx % 27]

    nak_name, start_lord, start_years = nak_info
    birthdate = args.birthdate or f"{args.year}-{args.month:02d}-{args.day:02d}"
    has_birth_clock = all(getattr(args, field, None) is not None for field in ("year", "month", "day", "hour", "minute"))
    birth_time = _birth_time_string(args.hour, args.minute, _arg_second(args)) if has_birth_clock else None
    birth_dt = _birth_datetime_from_args(args) if has_birth_clock else datetime.strptime(birthdate, "%Y-%m-%d")
    elapsed = progress * start_years; remaining = start_years - elapsed
    dt = birth_dt - timedelta(days=elapsed * 365.25)
    si = DASHA_ORDER.index(start_lord)
    timeline = []
    for i in range(9):
        lord = DASHA_ORDER[(si + i) % 9]; years = DASHA_YEARS[lord]
        end_dt = dt + timedelta(days=years * 365.25)
        # 第一个 MD 的展示 years 用 balance，实际日期计算用完整年数（数学等价）
        display_years = round(remaining, 2) if i == 0 else years
        timeline.append({
            "lord": lord,
            "lord_cn": PLANET_CN[lord],
            "start": dt.strftime("%Y-%m-%d"),
            "end": end_dt.strftime("%Y-%m-%d"),
            "start_datetime": dt.isoformat(timespec="seconds"),
            "end_datetime": end_dt.isoformat(timespec="seconds"),
            "years": display_years,
            "full_years": years,
            "is_current": False,
            "is_balance": i == 0,
            "balance_years": round(remaining, 2) if i == 0 else None,
            "elapsed_at_birth": round(elapsed, 2) if i == 0 else None,
        })
        dt = end_dt

    today = datetime.strptime(args.today, "%Y-%m-%d") if args.today else datetime.now()
    current = None
    for d in timeline:
        ds = datetime.strptime(d["start"], "%Y-%m-%d"); de = datetime.strptime(d["end"], "%Y-%m-%d")
        total_days = (de - ds).days; li = DASHA_ORDER.index(d["lord"])
        # v3.7.2: 为所有 Mahadasha 计算 Antardasha（不仅当前大运）
        sub = []; sdt = ds
        for j in range(9):
            sl = DASHA_ORDER[(li + j) % 9]; sd = total_days * DASHA_YEARS[sl] / 120
            se = sdt + timedelta(days=sd)
            is_cur = sdt <= today < se
            sub.append({"lord": sl, "lord_cn": PLANET_CN[sl], "start": sdt.strftime("%Y-%m-%d"), "end": se.strftime("%Y-%m-%d"), "is_current": is_cur})
            sdt = se
        d["antardasha_timeline"] = sub
        if ds <= today < de:
            d["is_current"] = True
            # 从 antardasha 列表中提取当前正在运行的 antardasha
            current_ad = None
            for ad in sub:
                if ad.get("is_current"):
                    current_ad = ad
                    break
            d["mahadasha"] = d.get("lord", "")
            d["mahadasha_cn"] = d.get("lord_cn", "")
            d["antardasha"] = current_ad or (sub[0] if sub else None)
            current = d

    result = {"moon_nakshatra": nak_name, "birth_date": birthdate, "reference_date": today.strftime("%Y-%m-%d"), "timeline": timeline, "current_dasha": current}
    if birth_time:
        result["birth_time"] = birth_time
        result["birth_datetime"] = f"{birthdate} {birth_time}"
    return result


# ============================================================================
# 3. Yoga识别
# ============================================================================
def cmd_yoga(args):
    """
    Yoga 识别 —— v6.0.26 数据驱动引擎。

    支持两种输入：
    1. 兼容旧接口：--ascendant + --planets "Sun:Aries:1[:10.5],Moon:Cancer:4[:15]"
    2. 出生信息直算：--year --month --day --hour --minute --lat --lon --tz [--node-mode]
    """
    planets = {}
    asc = args.ascendant or "Aries"

    yoga_context = None

    if args.planets:
        for item in args.planets.split(','):
            parts = item.strip().split(':')
            if len(parts) >= 3:
                pdata = {"sign": parts[1].strip(), "house": int(parts[2].strip())}
                if len(parts) >= 4 and parts[3].strip() != "":
                    try:
                        pdata["degree"] = float(parts[3].strip())
                    except ValueError:
                        pass
                planets[parts[0].strip()] = pdata
        context_json = getattr(args, 'context_json', None)
        if context_json:
            try:
                yoga_context = json.loads(context_json)
            except Exception:
                yoga_context = None
    else:
        required_birth_fields = ["year", "month", "day", "hour", "minute", "lat", "lon"]
        has_birth_input = all(getattr(args, field, None) is not None for field in required_birth_fields)
        if has_birth_input:
            chart, asc_idx, jd, ayanamsa = compute_chart_data(
                args.year, args.month, args.day, args.hour, args.minute,
                args.lat, args.lon, getattr(args, 'tz', 0), getattr(args, 'node_mode', 'mean'),
                second=_arg_second(args),
            )
            if chart is None:
                return {"error": "swisseph未安装"}
            asc = chart.get("ascendant", {}).get("sign", asc)
            planet_lons_for_varga = {}
            for pname, pd in chart.get("planets", {}).items():
                if isinstance(pd, dict) and "sign" in pd and "house" in pd:
                    planets[pname] = {
                        "sign": pd["sign"],
                        "house": pd["house"],
                        "degree": pd.get("degree_in_sign", pd.get("degree")),
                    }
                    if pd.get("degree_raw") is not None:
                        planet_lons_for_varga[pname] = pd.get("degree_raw")
            try:
                from varga import calc_all_vargas
                asc_deg_raw = chart.get("ascendant", {}).get("degree_raw")
                if asc_deg_raw is not None and planet_lons_for_varga:
                    yoga_context = _build_yoga_context_from_vargas(
                        calc_all_vargas(planet_lons_for_varga, asc_deg_raw, [9, 60]),
                        planet_lons_for_varga,
                    )
            except Exception:
                yoga_context = None

    ai = SIGNS.index(asc) if asc in SIGNS else 0
    kl = list(set([SIGN_LORDS[SIGNS[(ai + h - 1) % 12]] for h in [1, 4, 7, 10]]))
    tl = list(set([SIGN_LORDS[SIGNS[(ai + h - 1) % 12]] for h in [1, 5, 9]]))

    # 调用数据驱动引擎（yoga_engine.py）
    yogas = detect_yogas(planets, asc, context=yoga_context)

    return {
        "ascendant": asc,
        "planets_analyzed": len(planets),
        "kendra_lords": kl,
        "trikona_lords": tl,
        "yogas_detected": len(yogas),
        "yogas": yogas,
        "detected_yogas": yogas,
    }


# ============================================================================
# 4. 三层验证法事件预测（v3.4增强：优先EventPredictionModel规则引擎）
# ============================================================================
def cmd_predict(args):
    # 验前事模式（v3.5新增）
    if getattr(args, 'past_verify', False) and args.year:
        chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
        if chart is None:
            return {"error": "swisseph未安装"}
        return _past_event_verify(chart, asc_idx, args)

    chart = json.loads(args.chart) if args.chart else {}
    evt = args.event_type or "all"

    # 尝试加载 EventPredictionModel（替代LAM神经网络）
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from event_prediction_model import EventPredictionModel
        # 直接传完整chart数据给EventPredictionModel（v5.0需要ascendant dict和planets dict）
        # 同时从 full-reading 输出中提取所有模块数据传入（v5.1修复：之前丢失dasha/congregation等）
        modules = chart.get("modules", {})
        model = EventPredictionModel(
            chart_data={
                "ascendant": chart.get("ascendant", {}),
                "planets": chart.get("planets", {}),
            },
            dasha_data=modules.get("dasha"),
            congregation_data=modules.get("congregation"),
            vivah_saham_data=modules.get("vivah_saham"),
            chara_dasha_data=modules.get("jaimini", {}).get("chara_dasha"),
        )
        raw_preds = model.predict_all_events()
        # 将 Prediction dataclass 转为可序列化 dict（v5.1补充缺失字段）
        predictions = []
        for p in raw_preds:
            predictions.append({
                "event_type": str(p.event_type.value) if hasattr(p.event_type, 'value') else str(p.event_type),
                "description": p.description,
                "probability": p.probability,
                "risk_level": str(p.risk_level.value) if hasattr(p.risk_level, 'value') else str(p.risk_level),
                "confidence": str(p.confidence.value) if hasattr(p.confidence, 'value') else str(p.confidence),
                "timing": p.timing,
                "key_factors": p.key_factors,
                "recommendations": p.recommendations,
                "dasha_signals": p.dasha_signals,
                "transit_signals": p.transit_signals,
                "timing_windows": p.timing_windows,
            })
        return {
            "method": "三层验证法（EventPredictionModel规则引擎）",
            "engine": "event_prediction_model.py",
            "event_type": evt,
            "predictions": predictions,
            "note": "基于规则引擎的三层验证法，替代LAM神经网络（准确率从0.17%大幅提升）"
        }
    except Exception as e:
        # 降级到简化版
        result = {"method": "三层验证法（简化版）", "fallback_reason": str(e),
                  "event_type": evt, "predictions": []}
        planets = chart.get("planets", {})
        indicators_map = {
            "marriage": {"houses": [7], "karaka": "Venus", "cn": "婚姻"},
            "career": {"houses": [10, 6], "karaka": "Sun", "cn": "职业"},
            "wealth": {"houses": [2, 11], "karaka": "Jupiter", "cn": "财富"},
            "health": {"houses": [6, 8, 12], "karaka": "Saturn", "cn": "健康"},
        }
        for ek, ei in indicators_map.items():
            if evt != "all" and evt != ek: continue
            found = []
            for hn in ei["houses"]:
                for pn, pd in planets.items():
                    if isinstance(pd, dict) and pd.get("house") == hn:
                        found.append({"planet": pn, "house": hn, "sign": pd.get("sign", ""), "status": pd.get("status", "中性")})
            if found:
                result["predictions"].append({"event": ei["cn"], "key": ek, "static_indicators": found, "note": "需要结合Dasha和Transit进行精确预测"})
        return result


# ============================================================================
# 验前事模式（v3.5新增，避免冷读效应）
# ============================================================================
def _past_event_verify(chart: Dict, asc_idx: int, args) -> Dict:
    """
    验前事：从星盘数据推断 2-4 个高信号历史时段，供用户确认。
    AI 先推断，用户后确认——避免冷读效应。
    """
    planets = chart.get('planets', {})
    asc_sign = chart.get('ascendant', {}).get('sign', 'Unknown')
    birth_year = args.year

    signals = []

    # 1. 土星回归（约29.5年一次）
    saturn_sign = planets.get('Saturn', {}).get('sign', '')
    saturn_house = planets.get('Saturn', {}).get('house', 0)
    # 土星绕黄道一圈约29.5年
    for cycle_age in [29, 58]:
        event_year = birth_year + cycle_age
        signals.append({
            'type': '土星回归',
            'age': cycle_age,
            'year': event_year,
            'description': f'约{event_year}年（{cycle_age}岁），土星回归周期',
            'confidence': '高',
            'indicators': [f'土星在{saturn_sign}（第{saturn_house}宫）'],
        })

    # 2. 木星回归（约12年一次）
    jupiter_sign = planets.get('Jupiter', {}).get('sign', '')
    jupiter_house = planets.get('Jupiter', {}).get('house', 0)
    for cycle_age in [12, 24, 36, 48]:
        event_year = birth_year + cycle_age
        signals.append({
            'type': '木星回归',
            'age': cycle_age,
            'year': event_year,
            'description': f'约{event_year}年（{cycle_age}岁），木星回归周期',
            'confidence': '中高',
            'indicators': [f'木星在{jupiter_sign}（第{jupiter_house}宫）'],
        })

    # 3. Rahu-Ketu 对冲过境（约18.6年半周期）
    rahu_sign = planets.get('Rahu', {}).get('sign', '')
    for half_cycle in [9, 18, 27, 36]:
        event_year = birth_year + half_cycle
        signals.append({
            'type': 'Rahu-Ketu半周期',
            'age': half_cycle,
            'year': event_year,
            'description': f'约{event_year}年（{half_cycle}岁），Rahu-Ketu对冲轴变化',
            'confidence': '中',
            'indicators': [f'本命Rahu在{rahu_sign}'],
        })

    # 4. 关键宫位激活（基于 Dasha 可能性）
    # 7宫主星相关 → 婚姻/合作时间窗
    libra_idx = SIGNS.index('Libra') if 'Libra' in SIGNS else 6
    sign_7 = SIGNS[(asc_idx + 6) % 12]
    lord_7 = SIGN_LORDS.get(sign_7, 'Unknown')
    lord_7_info = planets.get(lord_7, {})
    if lord_7_info:
        signals.append({
            'type': '7宫主星活跃期',
            'age_range': '24-32',
            'year_range': f'{birth_year + 24}-{birth_year + 32}',
            'description': f'{lord_7}（7宫主星，7宫={sign_7}）活跃期，可能涉及婚姻/重要合作',
            'confidence': '中',
            'indicators': [f'{lord_7}在{lord_7_info.get("sign", "")}（第{lord_7_info.get("house", 0)}宫）'],
        })

    # 5. 10宫主星相关 → 事业突破
    sign_10 = SIGNS[(asc_idx + 9) % 12]
    lord_10 = SIGN_LORDS.get(sign_10, 'Unknown')
    lord_10_info = planets.get(lord_10, {})
    if lord_10_info:
        signals.append({
            'type': '10宫主星活跃期',
            'age_range': '28-40',
            'year_range': f'{birth_year + 28}-{birth_year + 40}',
            'description': f'{lord_10}（10宫主星，10宫={sign_10}）活跃期，可能涉及事业突破',
            'confidence': '中',
            'indicators': [f'{lord_10}在{lord_10_info.get("sign", "")}（第{lord_10_info.get("house", 0)}宫）'],
        })

    # 按置信度排序，取前4
    priority = {'高': 3, '中高': 2, '中': 1, '低': 0}
    signals.sort(key=lambda s: priority.get(s.get('confidence', '低'), 0), reverse=True)
    top_signals = signals[:4]

    return {
        'method': '验前事（Past Event Reverse Verification）',
        'version': '3.5',
        'note': 'AI从星盘推断的高信号历史时段，请用户确认——避免冷读效应',
        'birth_year': birth_year,
        'ascendant': asc_sign,
        'inferred_periods': top_signals,
        'disclaimer': '这些是基于星盘结构推断的可能时段，需要用户确认是否实际发生了相关事件。',
    }


# ============================================================================
# 5. 分盘计算
# ============================================================================
def cmd_varga(args):
    if not HAS_SWE: return {"error": "swisseph未安装"}
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from varga import calc_varga
    except ImportError as e:
        return {"error": f"varga模块导入失败: {e}"}

    swe.set_ephe_path('')
    hd = _birth_hour_decimal(args.hour, args.minute, _arg_second(args)) - args.tz
    jd = swe.julday(args.year, args.month, args.day, hd)

    # Lahiri Ayanamsa（恒星黄道修正，与cmd_chart一致）
    ayanamsa = swe.get_ayanamsa(jd)

    natal = {}
    for pn, pid in PLANETS_SWE.items():
        pos, _ = swe.calc_ut(jd, pid); natal[pn] = (pos[0] - ayanamsa) % 360  # 恒星黄道
    if 'Rahu' in natal: natal['Ketu'] = (natal['Rahu'] + 180) % 360
    asc_lon, _ = swe.houses(jd, args.lat, args.lon, b'A'); asc_deg = (asc_lon[0] - ayanamsa) % 360  # 恒星黄道

    def short_varga_row(lon, div):
        row = calc_varga(lon, div)
        return {"sign": row["sign"], "sign_cn": SIGNS_CN[row["sign"]]}

    result = {"birth_info": f"{args.year}-{args.month:02d}-{args.day:02d} {_birth_time_string(args.hour, args.minute, _arg_second(args))}", "divisional_charts": {}}
    if args.d9 or args.all:
        d9 = {"ascendant": calc_varga(asc_deg, 9)["sign"]}
        for p, l in natal.items(): d9[p] = short_varga_row(l, 9)
        result["divisional_charts"]["D9_Navamsa"] = d9
    if args.d10 or args.all:
        d10 = {"ascendant": calc_varga(asc_deg, 10)["sign"]}
        for p, l in natal.items(): d10[p] = short_varga_row(l, 10)
        result["divisional_charts"]["D10_Dasamsa"] = d10
    if not result["divisional_charts"]: result["note"] = "请指定 --d9, --d10 或 --all"
    return result


# ============================================================================
# 6. 名人案例查询
# ============================================================================
def cmd_celebrity(args):
    result = {"query": args.name or "all", "results": []}
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            if args.name: c.execute("SELECT * FROM cases WHERE name LIKE ?", (f'%{args.name}%',))
            else: c.execute("SELECT * FROM cases LIMIT ?", (args.limit or 20,))
            cols = [d[0] for d in c.description]
            for r in c.fetchall(): result["results"].append(dict(zip(cols, r)))
            conn.close()
        except Exception as e: result["db_error"] = str(e)

    if os.path.exists(PERSON_CSV) and args.name:
        try:
            matches = []
            with open(PERSON_CSV, 'r', encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    if args.name.lower() in row.get('Name', '').lower():
                        matches.append({"name": row.get('Name', ''), "birth_time": row.get('BirthTime', ''), "gender": row.get('Gender', '')})
                        if len(matches) >= 10: break
            result["person_list_matches"] = matches; result["person_list_total"] = 15807
        except Exception as e: result["csv_error"] = str(e)
    return result


# ============================================================================
# 7. 数据库统计
# ============================================================================
def cmd_db_stats(args):
    result = {}
    if os.path.exists(DB_PATH):
        try:
            conn = sqlite3.connect(DB_PATH); c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM cases"); result["total_cases"] = c.fetchone()[0]
            c.execute("SELECT case_type, COUNT(*) FROM cases GROUP BY case_type"); result["by_type"] = dict(c.fetchall())
            c.execute("SELECT difficulty, COUNT(*) FROM cases GROUP BY difficulty"); result["by_difficulty"] = dict(c.fetchall())
            c.execute("SELECT name, accuracy_rate, sample_size, correct_predictions FROM techniques"); result["techniques"] = [{"name": r[0], "accuracy": r[1], "samples": r[2], "correct": r[3]} for r in c.fetchall()]
            conn.close()
        except Exception as e: result["error"] = str(e)
    else:
        result["error"] = f"数据库不存在: {DB_PATH}"
    return result


# ============================================================================
# 8. 过境查询
# ============================================================================
def cmd_transit(args):
    """
    实时 Transit 行星过境计算（v3.7.2 改用 Swiss Ephemeris）
    不再依赖静态 JSON，直接用 swe 计算任意日期的行星位置。
    支持指定日期范围（--year/--month）和目标行星（--planet）。
    """
    if not HAS_SWE:
        return {"error": "swisseph未安装，无法计算实时Transit"}

    swe.set_ephe_path('')

    # --- 参数解析 ---
    t_year = args.year
    t_month = args.month
    # 可选：指定某日（默认取月中15号做代表）
    t_day = getattr(args, 'day', 15) or 15
    # 可选：指定目标行星（默认全部七曜+Rahu/Ketu）
    target_planets_str = getattr(args, 'planet', None)
    target_planets = [p.strip() for p in target_planets_str.split(',')] if target_planets_str else None

    # --- 计算该月月中行星位置 ---
    try:
        hd = 12.0 - (getattr(args, 'tz', 8) or 8)  # 默认UTC+8中午
        jd_mid = swe.julday(t_year, t_month, t_day, hd)
    except Exception as e:
        return {"error": f"日期计算失败: {e}"}

    ayanamsa = swe.get_ayanamsa(jd_mid)

    # --- 计算行星位置 ---
    node_mode = getattr(args, 'node_mode', 'mean')
    transit_data, ayanamsa = _calc_sidereal_planets_for_jd(jd_mid, node_mode=node_mode, include_ketu=True)
    if target_planets:
        target_set = set(target_planets)
        transit_data = {p: d for p, d in transit_data.items() if p in target_set}

    # --- 计算行星间相位（互相在对方星座的宫位关系）---
    aspects_found = []
    planet_names = list(transit_data.keys())
    for i, p1 in enumerate(planet_names):
        for p2 in planet_names[i+1:]:
            if p1 == 'Ketu' or p2 == 'Ketu':
                continue
            d1 = transit_data[p1]['degree']
            d2 = transit_data[p2]['degree']
            diff = abs(d1 - d2) % 360
            if diff > 180:
                diff = 360 - diff
            # 合相（≤10°）
            if diff <= 10:
                aspects_found.append({
                    'type': 'conjunction',
                    'planets': [p1, p2],
                    'degree_diff': round(diff, 2),
                    'description': f'{p1}与{p2}合相（{diff:.1f}°）'
                })
            # 对冲（180°±8°）
            elif 172 <= diff <= 188:
                aspects_found.append({
                    'type': 'opposition',
                    'planets': [p1, p2],
                    'degree_diff': round(diff, 2),
                    'description': f'{p1}与{p2}对冲（{diff:.1f}°）'
                })
            # 三方（120°±6°）
            elif 114 <= diff <= 126:
                aspects_found.append({
                    'type': 'trine',
                    'planets': [p1, p2],
                    'degree_diff': round(diff, 2),
                    'description': f'{p1}与{p2}三方相位（{diff:.1f}°）'
                })
            # 四分（90°±6°）
            elif 84 <= diff <= 96:
                aspects_found.append({
                    'type': 'square',
                    'planets': [p1, p2],
                    'degree_diff': round(diff, 2),
                    'description': f'{p1}与{p2}四分相位（{diff:.1f}°）'
                })

    # --- 构建结果 ---
    result = {
        'method': 'Swiss Ephemeris 实时计算（v3.7.2）',
        'target_date': f'{t_year}-{t_month:02d}-{t_day:02d}',
        'ayanamsa': round(ayanamsa, 4),
        'node_mode': node_mode,
        'data_layer': 'true_transit_positions',
        'planets': transit_data,
        'aspects': aspects_found,
        'note': f'使用Swiss Ephemeris实时计算{t_year}年{t_month}月行星过境位置，不再依赖静态JSON'
    }

    return result


# ============================================================================
# 8b. Double Transit PAC + D9 层（KN Rao 完整实现 v3.9新增）
#
# 核心逻辑:
# 1. D1 层: Saturn/Jupiter 通过 PAC 关联事件宫/宫主/LL/对宫主
# 2. D9 层: Saturn/Jupiter 通过 PAC 关联 D9 宫主/D9 Asc/宫主D9星座/LL D9星座
# 3. 两者必须同时激活同一目标 -> Double Transit 确认
#
# 精度: KN Rao 体系 110-115 星盘测试 97% 准确率（使用 D9 Navamsa）
# ============================================================================
def _navamsa_idx(lon):
    """Navamsa 星座索引"""
    lon = lon % 360
    si = int(lon / 30)
    d = lon - si * 30
    ni = int(d / (30 / 9))
    el_starts = [0, 9, 6, 3]  # Aries/Fire=0, Taurus/Earth=9, Gemini/Air=6, Cancer/Water=3
    return (el_starts[si % 4] + ni) % 12


def _calc_planetary_congregation(planets: Dict, asc_idx: int) -> Dict:
    """
    本命盘行星聚集检测（供 cmd_full_reading 调用）
    检测 3+ 行星同宫的聚集效应，返回聚集宫位、行星列表、影响领域
    """
    houses = {}
    for pn, pd in planets.items():
        if not isinstance(pd, dict) or 'sign' not in pd:
            continue
        if pn in ['Rahu', 'Ketu']:
            continue  # Rahu/Ketu 不计入聚集
        si = SIGNS.index(pd['sign']) if pd['sign'] in SIGNS else 0
        h = ((si - asc_idx) % 12) + 1
        houses.setdefault(h, []).append(pn)

    congregations = []
    for h, plist in houses.items():
        if len(plist) >= 3:
            h_sign = SIGNS[(asc_idx + h - 1) % 12]
            # 判断影响领域
            impact = _house_theme(h)
            # 判断聚集力量（有无吉星/凶星）
            benefics = [p for p in plist if p in ['Jupiter', 'Venus', 'Mercury', 'Moon']]
            malefics = [p for p in plist if p in ['Saturn', 'Mars', 'Sun', 'Rahu']]
            strength = 'strong' if len(benefics) > len(malefics) else 'mixed'
            if len(malefics) >= 3:
                strength = 'malefic_heavy'
            congregations.append({
                'house': h,
                'sign': h_sign,
                'planets': plist,
                'count': len(plist),
                'benefics': benefics,
                'malefics': malefics,
                'strength': strength,
                'impact': impact,
                'description': f'{",".join(plist)} 聚集于{h}宫({h_sign})',
            })

    return {
        'congregations': congregations,
        'total': len(congregations),
        'note': '3+ 行星同宫为显著聚集，影响该宫主题领域',
    }


def _house_theme(house: int) -> List[str]:
    """返回宫位影响领域"""
    themes = {
        1: ['自我', '健康', '性格'],
        2: ['财富', '家庭', '言语'],
        3: ['沟通', '旅行', '兄弟'],
        4: ['母亲', '房产', '情感'],
        5: ['子女', '投资', '创意'],
        6: ['疾病', '敌人', '债务'],
        7: ['婚姻', '合作', '伴侣'],
        8: ['转型', '意外', '遗产'],
        9: ['命运', '父亲', '灵性'],
        10: ['事业', '声望', '成就'],
        11: ['收益', '社交', '愿望'],
        12: ['损失', '外迁', '解脱'],
    }
    return themes.get(house, ['未知'])


def _calc_vivah_saham(planets: Dict, asc_deg: float) -> Dict:
    """
    计算本命 Vivah Saham 婚姻敏感点（供 cmd_full_reading 调用）
    公式: Saham = (Venus_lon - Saturn_lon + Asc_deg) % 360
    """
    venus_lon = planets.get('Venus', {}).get('degree', 0)
    saturn_lon = planets.get('Saturn', {}).get('degree', 0)
    if venus_lon == 0 or saturn_lon == 0:
        return {'error': '缺少金星或土星数据', 'saham': None}

    sahams_lon = (venus_lon - saturn_lon + asc_deg) % 360
    sahams_sign = SIGNS[int(sahams_lon / 30) % 12]
    sahams_deg_in_sign = sahams_lon % 30
    sahams_si = int(sahams_lon / 30) % 12

    # 检查哪些本命行星与 Saham 同宫/合相
    conjuncts = []
    for pn, pd in planets.items():
        if pn in ['Rahu', 'Ketu']:
            continue
        if not isinstance(pd, dict) or 'degree' not in pd:
            continue
        p_lon = pd['degree']
        diff = abs(p_lon - sahams_lon) % 360
        if diff > 180:
            diff = 360 - diff
        if diff <= 5:
            conjuncts.append({'planet': pn, 'diff_deg': round(diff, 2)})

    # 从 Saham 位置反推婚姻相关宫位
    asc_si = int(asc_deg / 30) % 12
    sahams_house = ((sahams_si - asc_si) % 12) + 1

    return {
        'saham_lon': round(sahams_lon, 4),
        'saham_sign': sahams_sign,
        'saham_deg_in_sign': round(sahams_deg_in_sign, 2),
        'saham_house': sahams_house,
        'formula': f'Venus({venus_lon:.2f}°) - Saturn({saturn_lon:.2f}°) + Asc({asc_deg:.2f}°)',
        'natal_conjuncts': conjuncts,
        'marriage_relevance': 'high' if sahams_house in [7, 1, 5, 9] else 'moderate',
        'note': 'Vivah Saham 是度数级婚姻敏感点，Transit 木星/土星过境此点时触发婚姻事件窗',
    }


def _check_pac(planet_name, planet_lon, target_lon, asc_idx):
    """PAC检查: Position(同宫)/Aspect(相位)/Conjunction(合相<=10度)"""
    results = []
    p_si = int((planet_lon % 360) / 30)
    t_si = int((target_lon % 360) / 30)
    p_house = ((p_si - asc_idx) % 12) + 1
    t_house = ((t_si - asc_idx) % 12) + 1

    # P: Position - 同宫
    if p_house == t_house:
        results.append({'type': 'Position', 'desc': f'同宫({t_house}宫)'})

    # C: Conjunction - 合相 <=10度
    diff = abs(planet_lon - target_lon) % 360
    if diff > 180:
        diff = 360 - diff
    if diff <= 10:
        results.append({'type': 'Conjunction', 'desc': f'合相({diff:.2f}\u00b0)'})

    # A: Aspect - Graha Drishti
    planet_aspects = {
        'Sun': [7], 'Moon': [7], 'Mars': [4, 7, 8], 'Mercury': [7],
        'Jupiter': [5, 7, 9], 'Venus': [7], 'Saturn': [3, 7, 10],
        'Rahu': [5, 7, 9], 'Ketu': [5, 7, 9],
    }
    aspects = planet_aspects.get(planet_name, [7])
    for offset in aspects:
        if ((t_house - p_house + 12) % 12) == offset:
            results.append({'type': 'Aspect', 'offset': offset, 'desc': f'{offset}宫相位'})

    return results


def cmd_double_transit_pac(args):
    """Double Transit PAC + D9 层计算"""
    # 1. 计算本命星盘
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}

    natal = chart.get('planets', {})
    asc_sign = chart.get('ascendant', {}).get('sign', 'Aries')
    asc_deg = chart.get('ascendant', {}).get('lon', chart.get('ascendant', {}).get('degree', 0))
    event_house = args.house or 7

    # 2. 计算过境行星位置
    if not HAS_SWE:
        return {"error": "swisseph未安装"}

    transit_year, transit_month, transit_day = map(int, args.date.split('-'))
    transit_hour = 12.0 - args.tz  # 正午 UT
    transit_jd = swe.julday(transit_year, transit_month, transit_day, transit_hour)
    transit_ayanamsa = swe.get_ayanamsa(transit_jd)

    transit_planets = {}
    for pname, pid in PLANETS_SWE.items():
        try:
            pos, _ = swe.calc_ut(transit_jd, pid)
            lon_p = (pos[0] - transit_ayanamsa) % 360
            transit_planets[pname] = {'lon': lon_p, 'sign': SIGNS[int(lon_p / 30)]}
            if pname == 'Rahu':
                klon = (lon_p + 180) % 360
                transit_planets['Ketu'] = {'lon': klon, 'sign': SIGNS[int(klon / 30)]}
        except Exception as e:
            transit_planets[pname] = {'error': str(e)}

    # 3. D1 层敏感点
    event_si = (asc_idx + event_house - 1) % 12
    event_sign = SIGNS[event_si]
    event_lord = SIGN_LORDS[event_sign]
    ll_name = SIGN_LORDS[asc_sign]
    opposite_si = (asc_idx + 6) % 12
    opposite_lord = SIGN_LORDS[SIGNS[opposite_si]]

    event_house_lon = (event_si * 30) + 15  # 宫位中点
    ll_lon = natal.get(ll_name, {}).get('degree', 0)
    event_lord_lon = natal.get(event_lord, {}).get('degree', 0)
    opp_lord_lon = natal.get(opposite_lord, {}).get('degree', 0)

    d1_targets = {
        f'{event_house}宫({event_sign})': event_house_lon,
        f'{event_lord}(宫主)': event_lord_lon,
        f'{ll_name}(LL)': ll_lon,
        f'{opposite_lord}(对宫主)': opp_lord_lon,
    }

    # 4. D9 层敏感点
    d9_asc_idx = _navamsa_idx(asc_deg)
    d9_asc_sign = SIGNS[d9_asc_idx]
    d9_event_si = (d9_asc_idx + event_house - 1) % 12
    d9_event_sign = SIGNS[d9_event_si]
    d9_event_lord = SIGN_LORDS[d9_event_sign]
    # 宫主的 D9 星座（KN Rao 关键）
    event_lord_d9_si = _navamsa_idx(event_lord_lon)
    event_lord_d9_sign = SIGNS[event_lord_d9_si]
    ll_d9_si = _navamsa_idx(ll_lon)
    ll_d9_sign = SIGNS[ll_d9_si]

    d9_event_house_lon = (d9_asc_idx * 30) + 15
    d9_event_lord_lon = natal.get(d9_event_lord, {}).get('degree', 0)

    d9_targets = {
        f'D9_{event_house}宫({d9_event_sign})': d9_event_house_lon,
        f'D9_{d9_event_lord}(宫主)': d9_event_lord_lon,
        f'{event_lord}_D9({event_lord_d9_sign})': event_lord_d9_si * 30 + 15,
        f'{ll_name}_D9({ll_d9_sign})': ll_d9_si * 30 + 15,
    }

    # 5. PAC 检查
    results = {
        'transit_date': args.date,
        'event_house': event_house,
        'd1': {'jupiter': {}, 'saturn': {}},
        'd9': {'jupiter': {}, 'saturn': {}},
        'cl': {'jupiter': {}, 'saturn': {}},
        'double_transit': [],
        'summary': '',
    }

    # Chandra Lagna 层敏感点
    moon_lon = natal.get('Moon', {}).get('degree', 0)
    moon_idx = int((moon_lon % 360) / 30)
    cl_event_sign = SIGNS[(moon_idx + event_house - 1) % 12]
    cl_event_lord = SIGN_LORDS[cl_event_sign]
    cl_event_house_lon = ((moon_idx + event_house - 1) % 12) * 30 + 15
    cl_event_lord_lon = natal.get(cl_event_lord, {}).get('degree', 0)
    cl_targets = {
        f'CL_{event_house}宫({cl_event_sign})': cl_event_house_lon,
        f'CL_{cl_event_lord}(宫主)': cl_event_lord_lon,
    }

    for tp_name in ['Jupiter', 'Saturn']:
        tp = transit_planets.get(tp_name, {})
        if 'error' in tp:
            continue
        tp_lon = tp['lon']
        layer = tp_name.lower()

        for t_name, t_lon in d1_targets.items():
            pac = _check_pac(tp_name, tp_lon, t_lon, asc_idx)
            if pac:
                results['d1'][layer][t_name] = pac

        for t_name, t_lon in d9_targets.items():
            pac = _check_pac(tp_name, tp_lon, t_lon, d9_asc_idx)
            if pac:
                results['d9'][layer][t_name] = pac

        for t_name, t_lon in cl_targets.items():
            pac = _check_pac(tp_name, tp_lon, t_lon, moon_idx)
            if pac:
                results['cl'][layer][t_name] = pac

    # 6. Double Transit 判定
    jup_d1 = set(results['d1']['jupiter'].keys())
    sat_d1 = set(results['d1']['saturn'].keys())
    jup_d9 = set(results['d9']['jupiter'].keys())
    sat_d9 = set(results['d9']['saturn'].keys())
    jup_cl = set(results['cl']['jupiter'].keys())
    sat_cl = set(results['cl']['saturn'].keys())

    # D1 层 overlap
    d1_overlap = jup_d1 & sat_d1
    for t in d1_overlap:
        results['double_transit'].append({
            'layer': 'D1', 'target': t,
            'jupiter_pac': results['d1']['jupiter'][t],
            'saturn_pac': results['d1']['saturn'][t],
            'strength': 'strong',
        })

    # D9 层 overlap
    d9_overlap = jup_d9 & sat_d9
    for t in d9_overlap:
        results['double_transit'].append({
            'layer': 'D9', 'target': t,
            'jupiter_pac': results['d9']['jupiter'][t],
            'saturn_pac': results['d9']['saturn'][t],
            'strength': 'strong',
        })

    # Chandra Lagna 层 overlap
    cl_overlap = jup_cl & sat_cl
    for t in cl_overlap:
        results['double_transit'].append({
            'layer': 'CL', 'target': t,
            'jupiter_pac': results['cl']['jupiter'][t],
            'saturn_pac': results['cl']['saturn'][t],
            'strength': 'strong',
        })

    # 跨层 Double Transit
    for d1t in jup_d1:
        for d9t in sat_d9:
            d1_nums = ''.join(c for c in d1t if c.isdigit())
            d9_nums = ''.join(c for c in d9t if c.isdigit())
            if d1_nums == d9_nums or (event_lord in d1t and event_lord in d9t):
                results['double_transit'].append({
                    'layer': 'D1+D9', 'target': f'Jupiter(D1){d1t} + Saturn(D9){d9t}',
                    'jupiter_pac': results['d1']['jupiter'][d1t],
                    'saturn_pac': results['d9']['saturn'][d9t],
                    'strength': 'moderate',
                })
    for d1t in sat_d1:
        for d9t in jup_d9:
            d1_nums = ''.join(c for c in d1t if c.isdigit())
            d9_nums = ''.join(c for c in d9t if c.isdigit())
            if d1_nums == d9_nums or (event_lord in d1t and event_lord in d9t):
                results['double_transit'].append({
                    'layer': 'D1+D9', 'target': f'Saturn(D1){d1t} + Jupiter(D9){d9t}',
                    'jupiter_pac': results['d9']['jupiter'][d9t],
                    'saturn_pac': results['d1']['saturn'][d1t],
                    'strength': 'moderate',
                })

    # Summary
    d1_active = len(d1_overlap) > 0
    d9_active = len(d9_overlap) > 0
    cl_active = len(cl_overlap) > 0
    cross_active = any(d['layer'] == 'D1+D9' for d in results['double_transit'])

    active_layers = []
    if d1_active: active_layers.append('D1')
    if d9_active: active_layers.append('D9')
    if cl_active: active_layers.append('CL')

    if len(active_layers) >= 2:
        results['summary'] = f'✅ Double Transit PAC 确认: {"+".join(active_layers)} 多层激活{event_house}宫主题'
    elif d1_active:
        results['summary'] = f'⚠️ D1 层 Double Transit 激活，D9/CL 层未确认'
    elif d9_active:
        results['summary'] = f'⚠️ D9 层 Double Transit 激活，D1/CL 层未确认'
    elif cl_active:
        results['summary'] = f'⚠️ Chandra Lagna 层 Double Transit 激活，D1/D9 未确认'
    elif cross_active:
        results['summary'] = f'⚠️ 跨层间接 Double Transit (D1+D9)，需结合 Dasha 确认'
    else:
        results['summary'] = f'❌ 无 Double Transit PAC 激活'

    results['stats'] = {
        'd1_jupiter_targets': sorted(jup_d1),
        'd1_saturn_targets': sorted(sat_d1),
        'd9_jupiter_targets': sorted(jup_d9),
        'd9_saturn_targets': sorted(sat_d9),
        'cl_jupiter_targets': sorted(jup_cl),
        'cl_saturn_targets': sorted(sat_cl),
        'd1_overlap': sorted(d1_overlap),
        'd9_overlap': sorted(d9_overlap),
        'cl_overlap': sorted(cl_overlap),
        'd9_ascendant': d9_asc_sign,
        'event_lord_d9_sign': event_lord_d9_sign,
        'chandra_lagna': SIGNS[moon_idx],
    }

    return results


# ============================================================================
# 8c. Transit LL/7L 连接 + 互换（Parivartana）（v3.9新增）
#
# P5: Transit LL PAC natal 7L / Transit 7L PAC natal LL (98%命中率)
# P8: Transit LL 过 7H 或 Transit 7L 过 Lagna (59%命中率)
# + Parivartana 互换检测
# ============================================================================
def _calc_transit_lon(jd, planet_name):
    """计算指定 Julian Day 的行星恒星黄经"""
    pid_map = {'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS, 'Mercury': swe.MERCURY,
               'Jupiter': swe.JUPITER, 'Venus': swe.VENUS, 'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE}
    pid = pid_map.get(planet_name)
    if pid is None:
        return None
    pos, _ = swe.calc_ut(jd, pid)
    aya = swe.get_ayanamsa_ut(jd)
    return (pos[0] - aya) % 360


def cmd_transit_ll7l(args):
    """Transit LL/7L 连接 + 互换检测"""
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}

    natal = chart.get('planets', {})
    asc_sign = chart.get('ascendant', {}).get('sign', 'Aries')
    asc_deg = chart.get('ascendant', {}).get('lon', chart.get('ascendant', {}).get('degree', 0))

    ll_name = SIGN_LORDS[asc_sign]
    seven_sign = SIGNS[(SIGNS.index(asc_sign) + 6) % 12]
    seven_lord = SIGN_LORDS[seven_sign]

    # Transit 日期
    t_year, t_month, t_day = map(int, args.date.split('-'))
    transit_jd = swe.julday(t_year, t_month, t_day, 12.0 - args.tz)

    # Transit LL/7L 位置
    t_ll_lon = _calc_transit_lon(transit_jd, ll_name)
    t_7l_lon = _calc_transit_lon(transit_jd, seven_lord)
    if t_ll_lon is None or t_7l_lon is None:
        return {"error": f"无法计算 Transit 位置: LL={ll_name}, 7L={seven_lord}"}

    n_ll_lon = natal.get(ll_name, {}).get('degree', 0)
    n_7l_lon = natal.get(seven_lord, {}).get('degree', 0)
    asc_lon = asc_deg

    result = {
        'transit_date': args.date,
        'lagna_lord': ll_name,
        'seventh_lord': seven_lord,
        'p5': {'hit': False, 'details': []},
        'p8': {'hit': False, 'details': []},
        'parivartana': {'hit': False, 'details': []},
    }

    # P5: Transit LL PAC natal 7L / Transit 7L PAC natal LL
    pac1 = _check_pac(ll_name, t_ll_lon, n_7l_lon, asc_idx)
    if pac1:
        result['p5']['hit'] = True
        result['p5']['details'].append({
            'direction': f'Transit {ll_name} → natal {seven_lord}',
            'connections': pac1,
        })
    pac2 = _check_pac(seven_lord, t_7l_lon, n_ll_lon, asc_idx)
    if pac2:
        result['p5']['hit'] = True
        result['p5']['details'].append({
            'direction': f'Transit {seven_lord} → natal {ll_name}',
            'connections': pac2,
        })

    # P8: Transit LL 过 7H 或 Transit 7L 过 Lagna
    t_ll_house = ((int((t_ll_lon % 360) / 30) - asc_idx) % 12) + 1
    t_7l_house = ((int((t_7l_lon % 360) / 30) - asc_idx) % 12) + 1
    if t_ll_house == 7:
        result['p8']['hit'] = True
        result['p8']['details'].append(f'Transit {ll_name}({SIGNS[int(t_ll_lon/30)]})在7H')
    if t_7l_house == 1:
        result['p8']['hit'] = True
        result['p8']['details'].append(f'Transit {seven_lord}({SIGNS[int(t_7l_lon/30)]})在Lagna')

    # Parivartana 互换
    n_ll_sign = SIGNS[int((n_ll_lon % 360) / 30)]
    n_7l_sign = SIGNS[int((n_7l_lon % 360) / 30)]
    t_ll_in_7l = SIGNS[int((t_ll_lon % 360) / 30)] == n_7l_sign
    t_7l_in_ll = SIGNS[int((t_7l_lon % 360) / 30)] == n_ll_sign
    if t_ll_in_7l and t_7l_in_ll:
        result['parivartana']['hit'] = True
        result['parivartana']['details'].append(
            f'完整互换: Transit {ll_name}在{n_7l_sign}(natal {seven_lord}) + Transit {seven_lord}在{n_ll_sign}(natal {ll_name})')
    elif t_ll_in_7l:
        result['parivartana']['details'].append(f'部分: Transit {ll_name}在{n_7l_sign}')
    elif t_7l_in_ll:
        result['parivartana']['details'].append(f'部分: Transit {seven_lord}在{n_ll_sign}')

    return result


# ============================================================================
# 8d. 行星聚集检测（Lagna/7H + Transit 聚集）（v3.9新增）
# ============================================================================
def cmd_planetary_congregation(args):
    """行星聚集检测"""
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}

    natal = chart.get('planets', {})
    asc_sign = chart.get('ascendant', {}).get('sign', 'Aries')
    event_house = args.house or 7

    result = {
        'natal': {'lagna': [], 'house_7': [], f'house_{event_house}': []},
        'transit': None,
        'summary': '',
    }

    # 本命盘聚集
    for pname, pdata in natal.items():
        if 'error' in pdata or 'sign' not in pdata:
            continue
        p_si = SIGNS.index(pdata['sign'])
        house = ((p_si - asc_idx) % 12) + 1
        if house == 1:
            result['natal']['lagna'].append(pname)
        if house == 7:
            result['natal']['house_7'].append(pname)
        if house == event_house:
            result['natal'][f'house_{event_house}'].append(pname)

    # Transit 聚集
    if args.transit_date:
        t_year, t_month, t_day = map(int, args.transit_date.split('-'))
        transit_jd = swe.julday(t_year, t_month, t_day, 12.0 - args.tz)
        transit_aya = swe.get_ayanamsa(transit_jd)
        result['transit'] = {str(h): [] for h in range(1, 13)}
        for pname, pid in PLANETS_SWE.items():
            try:
                pos, _ = swe.calc_ut(transit_jd, pid)
                lon_p = (pos[0] - transit_aya) % 360
                si = int(lon_p / 30)
                house = ((si - asc_idx) % 12) + 1
                result['transit'][str(house)].append(pname)
                if pname == 'Rahu':
                    klon = (lon_p + 180) % 360
                    ksi = int(klon / 30)
                    khouse = ((ksi - asc_idx) % 12) + 1
                    result['transit'][str(khouse)].append('Ketu')
            except Exception:
                pass

    # 判定
    flags = []
    lagna_count = len(result['natal']['lagna'])
    h7_count = len(result['natal']['house_7'])
    if 'Sun' in result['natal']['lagna'] or lagna_count >= 3:
        flags.append(f"Lagna聚集: {','.join(result['natal']['lagna'])}({lagna_count})")
    if 'Sun' in result['natal']['house_7'] or h7_count >= 3:
        flags.append(f"7H聚集: {','.join(result['natal']['house_7'])}({h7_count})")

    if result['transit']:
        slow = {'Saturn', 'Jupiter', 'Rahu', 'Ketu'}
        t_event = result['transit'].get(str(event_house), [])
        t_slow = [p for p in t_event if p in slow]
        if len(t_slow) >= 2:
            flags.append(f"Transit {event_house}宫慢行星聚集: {','.join(t_slow)}")

    result['flags'] = flags
    result['hit'] = len(flags) > 0
    result['summary'] = ' | '.join(flags) if flags else '无显著聚集'
    return result


# ============================================================================
# 8e. Vivah Saham + 婚姻计时管线（v3.9新增）
#
# Vivah Saham = norm(Venus - Saturn + Asc) — 度数级精确计算
# Transit 激活: Jupiter/Saturn PAC 到 Vivah Saham
# ============================================================================
def cmd_vivah_saham(args):
    """Vivah Saham 计算 + Transit 激活"""
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}

    natal = chart.get('planets', {})
    asc_deg = chart.get('ascendant', {}).get('lon', chart.get('ascendant', {}).get('degree', 0))
    venus_lon = natal.get('Venus', {}).get('degree', 0)
    saturn_lon = natal.get('Saturn', {}).get('degree', 0)

    # Vivah Saham = norm(Venus - Saturn + Asc)
    sahams_lon = (venus_lon - saturn_lon + asc_deg) % 360
    sahams_si = int(sahams_lon / 30)
    sahams_sign = SIGNS[sahams_si]
    sahams_deg = sahams_lon - sahams_si * 30

    result = {
        'vivah_saham': {
            'longitude': round(sahams_lon, 4),
            'sign': sahams_sign,
            'sign_cn': SIGNS_CN[sahams_sign],
            'degree_in_sign': round(sahams_deg, 4),
        },
        'formula': f'norm({venus_lon:.2f} Venus - {saturn_lon:.2f} Saturn + {asc_deg:.2f} Asc)',
        'transit_activation': None,
    }

    # Transit 激活
    if args.transit_date:
        t_year, t_month, t_day = map(int, args.transit_date.split('-'))
        transit_jd = swe.julday(t_year, t_month, t_day, 12.0 - args.tz)

        result['transit_activation'] = {'jupiter': [], 'saturn': [], 'double_activation': False}

        jup_lon = _calc_transit_lon(transit_jd, 'Jupiter')
        sat_lon = _calc_transit_lon(transit_jd, 'Saturn')

        if jup_lon is not None:
            jup_pac = _check_pac('Jupiter', jup_lon, sahams_lon, asc_idx)
            if jup_pac:
                result['transit_activation']['jupiter'] = jup_pac

        if sat_lon is not None:
            sat_pac = _check_pac('Saturn', sat_lon, sahams_lon, asc_idx)
            if sat_pac:
                result['transit_activation']['saturn'] = sat_pac

        if result['transit_activation']['jupiter'] and result['transit_activation']['saturn']:
            result['transit_activation']['double_activation'] = True

        # Venus transit 过 Saham 星座
        venus_t = _calc_transit_lon(transit_jd, 'Venus')
        if venus_t is not None:
            if SIGNS[int(venus_t / 30)] == sahams_sign:
                result['transit_activation']['venus_in_saham_sign'] = True

    return result


# ============================================================================
# 9. Shadbala 六重力量（v3.4新增）
# ============================================================================
def cmd_shadbala(args):
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from shadbala import build_shadbala_context, calc_shadbala
    except ImportError as e:
        return {"error": f"shadbala模块导入失败: {e}"}
    planets = chart.get("planets", {})
    asc_sign = chart.get("ascendant", {}).get("sign", "Aries")
    birth_hour = _birth_hour_decimal(args.hour, args.minute, _arg_second(args))
    sun_lon = planets.get("Sun", {}).get("degree", 0)
    moon_lon = planets.get("Moon", {}).get("degree", 0)
    context = build_shadbala_context(jd, args.lat, args.lon, _current_ayanamsa_name(args))
    return calc_shadbala(planets, asc_sign, birth_hour, sun_lon, moon_lon, context=context)


# ============================================================================
# 10. Ashtakavarga 八分法（v3.4新增）
# ============================================================================
def cmd_ashtakavarga(args):
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from ashtakavarga import calc_ashtakavarga
    except ImportError as e:
        return {"error": f"ashtakavarga模块导入失败: {e}"}
    planets = chart.get("planets", {})
    return calc_ashtakavarga(planets, asc_idx)


# ============================================================================
# 10c. Ashtakoot 合婚（v6.9.12新增）
# ============================================================================
def cmd_ashtakoot(args):
    """Ashtakoot 36点合婚 + Kuja Dosha"""
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from ashtakoot import calculate_ashtakoot
    except ImportError as e:
        return {"error": f"ashtakoot模块导入失败: {e}"}

    # 男方星盘
    m_chart, m_asc_idx, m_jd, m_aya = compute_chart_data(
        args.m_year, args.m_month, args.m_day, args.m_hour, args.m_minute,
        args.m_lat, args.m_lon, args.m_tz, getattr(args, 'node_mode', 'mean'))
    if m_chart is None:
        return {"error": "男方: swisseph未安装"}

    # 女方星盘
    f_chart, f_asc_idx, f_jd, f_aya = compute_chart_data(
        args.f_year, args.f_month, args.f_day, args.f_hour, args.f_minute,
        args.f_lat, args.f_lon, args.f_tz, getattr(args, 'node_mode', 'mean'))
    if f_chart is None:
        return {"error": "女方: swisseph未安装"}

    m_moon_lon = m_chart.get("planets", {}).get("Moon", {}).get("degree", 0)
    f_moon_lon = f_chart.get("planets", {}).get("Moon", {}).get("degree", 0)

    # 构建 lagna 数据供附加 Kuta 使用
    m_chart_full = {"lagna": m_chart.get("ascendant", {}), "planets": m_chart.get("planets", {})}
    f_chart_full = {"lagna": f_chart.get("ascendant", {}), "planets": f_chart.get("planets", {})}

    return calculate_ashtakoot(m_moon_lon, f_moon_lon, m_chart_full, f_chart_full)


# ============================================================================
# 10b. KP 系统（v6.9.10新增）
# ============================================================================
def cmd_kp(args):
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}

    asc_sign = chart.get("ascendant", {}).get("sign", "Aries")
    planets = chart.get("planets", {})

    # 构建KP需要的行星位置格式
    planet_positions = {}
    for pname, pdata in planets.items():
        if isinstance(pdata, dict) and 'sign' in pdata:
            planet_positions[pname] = {
                'sign': pdata['sign'],
                'degree': pdata.get('degree_in_sign', pdata.get('degree', 0) % 30),
                'house': pdata.get('house', 1),
            }

    return calc_kp_analysis(planet_positions, asc_sign)


# ============================================================================
# 11. Hermes 记忆系统（v3.4新增）
# ============================================================================
def cmd_memory(args):
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from hermes_memory_core import HermesMemoryCore
    except ImportError as e:
        return {"error": f"Hermes记忆模块导入失败: {e}", "hint": "确保hermes_memory_core.py在scripts/目录下"}
    db_file = os.path.join(SCRIPT_DIR, 'hermes_memory.db')
    mem = HermesMemoryCore(db_file)
    result = {"action": args.action}
    if args.action == "store":
        if not args.content:
            return {"error": "store操作需要 --content 参数"}
        tags = args.tags.split(',') if args.tags else []
        importance = args.importance if args.importance else 5
        metadata = {"tags": tags, "importance": importance}
        mem_id = mem.store_memory(args.content, metadata)
        result.update({"stored": True, "memory_id": mem_id, "content": args.content, "tags": tags})
    elif args.action == "search":
        if not args.query:
            return {"error": "search操作需要 --query 参数"}
        results = mem.search(args.query, limit=args.limit or 10)
        result.update({"query": args.query, "found": len(results), "results": results})
    elif args.action == "context":
        session_id = f"jyotish-cli-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        ctx = mem.get_context_for_session(session_id)
        result.update({"session_id": session_id, "context": ctx})
    elif args.action == "stats":
        # Hermes没有get_stats，用搜索空串获取总数
        try:
            all_mem = mem.search("", limit=1000)
            result["total_memories"] = len(all_mem)
        except:
            result["total_memories"] = "unknown"
        result["db_path"] = db_file
    else:
        result["error"] = f"未知action: {args.action}，支持: store/search/context/stats"
    return result


# ============================================================================
# 12. R1-R10 数学验证（v3.5新增）
# ============================================================================
def cmd_validate(args):
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from ashtakavarga import calc_ashtakavarga
        asht_result = calc_ashtakavarga(chart.get('planets', {}), asc_idx)
    except ImportError:
        asht_result = None
    try:
        from validate import validate_chart
        return validate_chart(chart, asht_result)
    except ImportError as e:
        return {"error": f"validate模块导入失败: {e}"}


# ============================================================================
# 13. P1-P12 行星审计管线（v3.5新增）
# ============================================================================
def _assess_conjunction_quality(lord, houses, planets):
    """评估仓库耦合的吉凶质量"""
    lord_info = planets.get(lord, {})
    lord_status = lord_info.get('status', '中性')
    # 凶宫组合
    dusthana = {6, 8, 12}
    trikona = {1, 5, 9}
    kendra = {1, 4, 7, 10}

    has_dusthana = any(h in dusthana for h in houses)
    has_trikona = any(h in trikona for h in houses)
    has_kendra = any(h in kendra for h in houses)

    if has_dusthana and has_trikona:
        return f"凶吉混合 — 挑战与成长并存"
    elif has_dusthana and has_kendra:
        return f"压力型 — 通过努力获取成就"
    elif has_trikona:
        return f"吉庆型 — 自然流畅的支持"
    elif has_dusthana:
        return f"消耗型 — 需要额外努力维持"
    else:
        return f"中性 — 标准互动"

def _conflict_arbitration(report):
    """
    冲突仲裁规则（CNWU16框架）：
    1. P1清理者+P7入旺 = "带毒高价值资产"，禁止说逢凶化吉
    2. P5凶宫+BAV高 = "乱世出英雄"
    3. P1吉+P2受损 = "空有雄心无着力点"
    """
    conflicts = []
    planets = report.get('planets', {})
    audit = report.get('audit', {})

    p1 = audit.get('P1_identity', {})
    p7 = audit.get('P7_dignity', {})
    p2 = audit.get('P2_health', {})

    asc_lord = p1.get('asc_lord', '')

    # 规则1: P1清理者+P7入旺 → 检查上升主是否掌管8/12宫（清理者角色）
    # 清理者定义：掌管8宫或12宫的行星
    SIGN_LORDS_MAP = {'Aries': 'Mars', 'Taurus': 'Venus', 'Gemini': 'Mercury', 'Cancer': 'Moon',
                      'Leo': 'Sun', 'Virgo': 'Mercury', 'Libra': 'Venus', 'Scorpio': 'Mars',
                      'Sagittarius': 'Jupiter', 'Capricorn': 'Saturn', 'Aquarius': 'Saturn', 'Pisces': 'Jupiter'}

    asc_sign = p1.get('asc_sign', '')
    asc_idx_local = SIGNS.index(asc_sign) if asc_sign in SIGNS else 0

    # 找8宫主和12宫主
    h8_sign = SIGNS[(asc_idx_local + 7) % 12]
    h12_sign = SIGNS[(asc_idx_local + 11) % 12]
    destroyer_lords = {SIGN_LORDS_MAP.get(h8_sign, ''), SIGN_LORDS_MAP.get(h12_sign, '')}

    for dl in destroyer_lords:
        if dl and dl in p7:
            dl_status = p7[dl].get('status', '')
            if 'Exalted' in dl_status or 'Own' in dl_status:
                conflicts.append({
                    'rule': 'Destroyer+Exalted',
                    'planets': [dl],
                    'verdict': '带毒高价值资产',
                    'instruction': f"{dl}既是清理者(掌8/12宫)又入旺/入庙，力量极强但方向凶险——禁止说逢凶化吉",
                })

    # 规则2: P5凶宫+BAV高 → 检查6/8/12宫的SAV是否 >28
    asht_data = report.get('ashtakavarga', {})
    house_scores = {}
    if asht_data:
        # 从ashtakavarga原始数据获取house_scores
        try:
            sys.path.insert(0, SCRIPT_DIR)
            from ashtakavarga import calc_ashtakavarga
            asht_result = calc_ashtakavarga(planets, asc_idx_local)
            house_scores = asht_result.get('house_scores', {})
        except:
            pass

    for h in [6, 8, 12]:
        hs = house_scores.get(f'house_{h}', {})
        sav_score = hs.get('score', 0)
        if sav_score > 28:
            conflicts.append({
                'rule': 'Dusthana+HighBAV',
                'house': h,
                'sav': sav_score,
                'verdict': '乱世出英雄',
                'instruction': f"{h}宫是凶宫但SAV={sav_score}（>28），在困境中反而能出成就",
            })

    # 规则3: P1吉+P2受损 → 上升主星状态好但太阳(健康指标)受损
    sun_info = p2.get('sun_status', '')
    lord_info = p7.get(asc_lord, {})
    lord_status = lord_info.get('status', '')
    if ('Exalted' in lord_status or 'Own' in lord_status) and ('Debilitated' in sun_info or 'Enemy' in sun_info):
        conflicts.append({
            'rule': 'GoodP1+DamagedP2',
            'planets': [asc_lord, 'Sun'],
            'verdict': '空有雄心无着力点',
            'instruction': f"上升主{asc_lord}强健但太阳受损，有野心但执行力/健康跟不上",
        })

    return conflicts


def cmd_audit(args):
    """P1-P12 行星审计：调用 chart→shadbala→ashtakavarga→yoga，输出统一审计报告"""
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}

    planets = chart.get('planets', {})
    asc_sign = chart.get('ascendant', {}).get('sign', 'Unknown')

    report = {
        'version': '3.5',
        'birth_info': chart.get('birth_info', {}),
        'ascendant': chart.get('ascendant', {}),
        'planets': planets,
        'audit': {},
    }

    # P1 Identity（本命身份）: 上升星座 + 上升主星
    asc_lord = chart.get('ascendant', {}).get('lord', 'Unknown')
    lord_info = planets.get(asc_lord, {})
    report['audit']['P1_identity'] = {
        'asc_sign': asc_sign,
        'asc_lord': asc_lord,
        'lord_sign': lord_info.get('sign', 'Unknown'),
        'lord_house': lord_info.get('house', 0),
        'lord_status': lord_info.get('status', '未知'),
    }

    # P2 Health（健康指标）: 6宫 + 8宫 + 12宫主星 + 太阳状态
    health_houses = [6, 8, 12]
    health_lords = set()
    health_info = {}
    for h in health_houses:
        sign_idx = (asc_idx + h - 1) % 12
        sign_name = SIGNS[sign_idx]
        lord = SIGN_LORDS.get(sign_name, 'Unknown')
        health_lords.add(lord)
        health_info[f'house_{h}'] = {'sign': sign_name, 'lord': lord}
    sun_info = planets.get('Sun', {})
    report['audit']['P2_health'] = {
        'houses': health_info,
        'sun_status': sun_info.get('status', '未知'),
        'sun_house': sun_info.get('house', 0),
    }

    # P3 Warehouse Coupling（仓库耦合）: 双宫掌管=货物捆绑
    # CNWU16逻辑：如果一颗行星同时掌管两个宫位，则两个宫位的事务被"捆绑"
    house_lord_map = {}
    for h in range(1, 13):
        sign_idx = (asc_idx + h - 1) % 12
        sname = SIGNS[sign_idx]
        lord = SIGN_LORDS.get(sname, 'Unknown')
        if lord not in house_lord_map:
            house_lord_map[lord] = []
        house_lord_map[lord].append(h)

    warehouse_coupling = {}
    for lord, houses in house_lord_map.items():
        if len(houses) > 1:
            warehouse_coupling[lord] = {
                'houses': houses,
                'meaning': f"{lord}同时掌管{houses[0]}宫和{houses[1]}宫，事务捆绑",
                'conjunction_quality': _assess_conjunction_quality(lord, houses, planets),
            }
    report['audit']['P3_warehouse_coupling'] = warehouse_coupling

    # P8 Age Status（年龄状态）: 青壮=主动, 老婴=辅助, 死=自动执行
    # 基于行星在星座中的度数区间判定生命周期
    age_status_map = {}
    for pname, pd in planets.items():
        deg_in_sign = pd.get('degree_in_sign', 0)
        if pname in ['Rahu', 'Ketu']:
            age_status_map[pname] = {'status': '永远逆行', 'phase': 'Rahu/Ketu无年龄状态'}
            continue
        if deg_in_sign < 10:
            phase = '婴幼(0-10°)'
            quality = '辅助型 — 能量尚未完全展开'
        elif deg_in_sign < 20:
            phase = '青壮(10-20°)'
            quality = '主动型 — 能量最活跃，主导性强'
        else:
            phase = '老年(20-30°)'
            quality = '自动执行型 — 已内化的能力，自动化运作'
        age_status_map[pname] = {
            'degree_in_sign': round(deg_in_sign, 2),
            'phase': phase,
            'quality': quality,
        }
    report['audit']['P8_age_status'] = age_status_map

    # P4 Resource SAV（资源SAV）& P6 Exit SAV（退出SAV）
    # 需要 Ashtakavarga 数据
    asht_data = None
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from ashtakavarga import calc_ashtakavarga
        asht_data = calc_ashtakavarga(planets, asc_idx)
        report['ashtakavarga'] = {
            'sav_total': asht_data.get('sav', {}).get('total', 0),
            'sav_valid': asht_data.get('sav', {}).get('valid', False),
            'strongest': asht_data.get('strongest_signs', []),
            'weakest': asht_data.get('weakest_signs', []),
        }
        house_scores = asht_data.get('house_scores', {})
        # P4: 财富宫(2,11) SAV
        p4_info = {}
        for h in [2, 11]:
            hs = house_scores.get(f'house_{h}', {})
            p4_info[f'house_{h}'] = hs
        report['audit']['P4_resource_sav'] = p4_info
        # P6: 退出宫(12) SAV + 8宫
        p6_info = {}
        for h in [8, 12]:
            hs = house_scores.get(f'house_{h}', {})
            p6_info[f'house_{h}'] = hs
        report['audit']['P6_exit_sav'] = p6_info
        # P5: 路况(1,5,9三宫) SAV
        p5_info = {}
        for h in [1, 5, 9]:
            hs = house_scores.get(f'house_{h}', {})
            p5_info[f'house_{h}'] = hs
        report['audit']['P5_road_condition'] = p5_info
    except Exception as e:
        report['audit']['ashtakavarga_error'] = str(e)

    # P7 Dignity（尊严状态）
    dignity_map = {}
    for pname, pd in planets.items():
        dignity_map[pname] = {
            'sign': pd.get('sign', ''),
            'status': pd.get('status', '中性'),
            'house': pd.get('house', 0),
            'retrograde': pd.get('retrograde', False),
        }
    report['audit']['P7_dignity'] = dignity_map

    # P9 Shadbala（六重力量）
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from shadbala import build_shadbala_context, calc_shadbala
        birth_hour = _birth_hour_decimal(args.hour, args.minute, _arg_second(args))
        sun_lon = planets.get('Sun', {}).get('degree', 0)
        moon_lon = planets.get('Moon', {}).get('degree', 0)
        context = build_shadbala_context(jd, args.lat, args.lon, _current_ayanamsa_name(args))
        shadbala = calc_shadbala(planets, asc_sign, birth_hour, sun_lon, moon_lon, context=context)
        report['audit']['P9_shadbala'] = {
            'summary': shadbala.get('summary', {}),
            'ishta_bala_ranking': shadbala.get('ishta_bala_ranking', []),
        }
    except Exception as e:
        report['audit']['P9_shadbala_error'] = str(e)

    # P10 Aspects（相位）简化版
    aspect_map = {}
    for pname, pd in planets.items():
        if pname in ['Rahu', 'Ketu']:
            continue
        house = pd.get('house', 0)
        # 标准 7/4 相位（从该行星宫位数起）
        aspects_from_house = {1: [7], 2: [7], 3: [5, 9, 7], 4: [7, 10],
                              5: [7], 6: [7], 7: [7], 8: [7],
                              9: [5, 7], 10: [7], 11: [7], 12: [7]}
        # 特殊相位
        special = {'Mars': [4, 7, 8], 'Jupiter': [5, 7, 9], 'Saturn': [3, 7, 10]}
        if pname in special:
            aspect_houses = special[pname]
        else:
            aspect_houses = [7]  # 标准对宫
        aspect_map[pname] = {
            'from_house': house,
            'aspect_houses': aspect_houses,
        }
    report['audit']['P10_aspects'] = aspect_map

    # P11 Nakshatra
    nak_map = {}
    for pname, pd in planets.items():
        nak_map[pname] = {
            'nakshatra': pd.get('nakshatra', ''),
            'pada': pd.get('nakshatra_pada', 0),
            'lord': pd.get('nakshatra_lord', ''),
        }
    report['audit']['P11_nakshatra'] = nak_map

    # P12 Yogas（格局识别）
    try:
        yoga_planets = {}
        for pname, pd in planets.items():
            if isinstance(pd, dict) and 'sign' in pd and 'house' in pd:
                yoga_planets[pname] = {
                    'sign': pd['sign'],
                    'house': pd['house'],
                    'degree': pd.get('degree_in_sign', pd.get('degree')),
                }
        yoga_result = cmd_yoga(type('Args', (), {
            'ascendant': asc_sign,
            'planets': ','.join([
                f"{k}:{v['sign']}:{v['house']}" + (f":{v['degree']}" if v.get('degree') is not None else "")
                for k, v in yoga_planets.items()
            ])
        })())
        report['audit']['P12_yogas'] = {
            'count': yoga_result.get('yogas_detected', 0),
            'yogas': yoga_result.get('yogas', []),
        }
    except Exception as e:
        report['audit']['P12_yogas_error'] = str(e)

    # 验证
    try:
        from validate import validate_chart
        validation = validate_chart(chart, asht_data)
        report['validation'] = validation
    except Exception as e:
        report['validation'] = {"error": str(e)}

    # 冲突仲裁（CNWU16框架3条规则）
    report['conflict_arbitration'] = _conflict_arbitration(report)

    return report


# ============================================================================
# 14. 报告生成（v3.6新增）
# ============================================================================
def cmd_report(args):
    """调用 report_builder.py 生成 HTML 报告"""
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from report_builder import main as report_main
    except ImportError as e:
        return {"error": f"report_builder模块导入失败: {e}"}

    # 构造 sys.argv 并调用 report_builder
    folder = args.folder
    if not os.path.isdir(folder):
        return {"error": f"目录不存在: {folder}"}

    report_argv = [
        'report_builder.py', folder,
        '--name', args.name,
        '--lagna', args.lagna,
        '--gender', args.gender,
        '--status', args.status,
        '--lang', args.lang,
    ]
    if args.output:
        report_argv.extend(['--output', args.output])

    old_argv = sys.argv
    sys.argv = report_argv
    try:
        report_main()
        output_path = args.output or os.path.join(folder, 'report.html')
        return {
            'status': 'ok',
            'output': output_path,
            'name': args.name,
            'lagna': args.lagna,
            'lang': args.lang,
        }
    except SystemExit:
        return {"error": "report_builder执行出错，请检查MD文件格式"}
    except Exception as e:
        return {"error": f"报告生成失败: {e}"}
    finally:
        sys.argv = old_argv


# ============================================================================
# 15. BPHS十六分盘完整计算（v3.7新增）
# ============================================================================
def cmd_varga_full(args):
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}

    # --- Custom D-N mode (v6.9.12) ---
    custom_n = getattr(args, 'custom', None)
    if custom_n:
        try:
            sys.path.insert(0, SCRIPT_DIR)
            from divisional_charts_extended import DivisionalChartsCalculator
            calc = DivisionalChartsCalculator()
        except ImportError as e:
            return {"error": f"divisional_charts_extended模块导入失败: {e}"}
        planets = chart.get('planets', {})
        planet_lons = {pn: pd.get('degree_raw', pd['degree']) for pn, pd in planets.items() if isinstance(pd, dict) and 'degree' in pd}
        asc_deg = chart.get('ascendant', {}).get('lon', chart.get('ascendant', {}).get('degree', 0))
        result = {'custom_div': custom_n}
        result['Ascendant'] = calc.calc_custom_varga(asc_deg, custom_n)
        for pn, lon in planet_lons.items():
            result[pn] = calc.calc_custom_varga(lon, custom_n)
        return result

    # --- Composite D-m×n mode (v6.9.12) ---
    composite = getattr(args, 'composite', None)
    if composite:
        try:
            sys.path.insert(0, SCRIPT_DIR)
            from divisional_charts_extended import DivisionalChartsCalculator
            calc = DivisionalChartsCalculator()
        except ImportError as e:
            return {"error": f"divisional_charts_extended模块导入失败: {e}"}
        parts = [int(x.strip()) for x in composite.split(',')]
        if len(parts) != 2:
            return {"error": "--composite 需要两个整数，逗号分隔（如 9,12 表示D9×D12）"}
        outer, inner = parts
        planets = chart.get('planets', {})
        planet_lons = {pn: pd.get('degree_raw', pd['degree']) for pn, pd in planets.items() if isinstance(pd, dict) and 'degree' in pd}
        asc_deg = chart.get('ascendant', {}).get('lon', chart.get('ascendant', {}).get('degree', 0))
        result = {'composite_div': f'D{outer}×D{inner}=D{outer*inner}', 'outer': outer, 'inner': inner}
        result['Ascendant'] = calc.calc_composite_varga(asc_deg, outer, inner)
        for pn, lon in planet_lons.items():
            result[pn] = calc.calc_composite_varga(lon, outer, inner)
        return result

    # --- Standard / variant mode ---
    variant = getattr(args, 'variant', None)
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from varga import calc_all_vargas
    except ImportError as e:
        return {"error": f"varga模块导入失败: {e}"}
    planets = chart.get('planets', {})
    planet_lons = {pn: pd.get('degree_raw', pd['degree']) for pn, pd in planets.items() if isinstance(pd, dict) and 'degree' in pd}
    asc_deg = chart.get('ascendant', {}).get('lon', chart.get('ascendant', {}).get('degree', 0))
    divisions = [int(d.strip().replace('D','')) for d in args.divisions.split(',')] if args.divisions else None

    # If variant requested for D2/D3, use DivisionalChartsCalculator
    if variant and divisions and len(divisions) == 1 and divisions[0] in (2, 3):
        try:
            sys.path.insert(0, SCRIPT_DIR)
            from divisional_charts_extended import DivisionalChartsCalculator
            calc = DivisionalChartsCalculator()
        except ImportError:
            variant = None  # fallback to standard
        if variant:
            result = {'variant': variant, 'div': divisions[0]}
            result['Ascendant'] = calc.calc_varga_with_variant(asc_deg, divisions[0], variant)
            for pn, lon in planet_lons.items():
                result[pn] = calc.calc_varga_with_variant(lon, divisions[0], variant)
            return result

    try:
        sys.path.insert(0, SCRIPT_DIR)
        from divisional_charts_extended import DivisionalChartsCalculator, VargaType
        extended_available = {varga.division: varga for varga in VargaType}
        if any(division not in {2, 3, 4, 7, 9, 10, 12, 16, 20, 24, 27, 30, 40, 45, 60} for division in (divisions or [])):
            calc = DivisionalChartsCalculator()
            selected = [extended_available[division] for division in divisions]
            result = {}
            for varga in selected:
                key = f'D{varga.division}_{varga.varga_name}'
                result[key] = calc._calculate_single_varga(varga, planet_lons, asc_deg)
            return result
    except KeyError as e:
        return {"error": f"不支持的D{e.args[0]}。请使用 --custom N 计算任意D-N分盘。"}
    except ImportError:
        pass

    return calc_all_vargas(planet_lons, asc_deg, divisions)


# ============================================================================
# 16. 度数精确相位系统（v3.7新增）
# ============================================================================
def cmd_aspects(args):
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from aspects import calc_all_aspects
    except ImportError as e:
        return {"error": f"aspects模块导入失败: {e}"}
    planets = chart.get('planets', {})
    planet_lons = {}
    for pn, pd in planets.items():
        if isinstance(pd, dict) and 'degree' in pd:
            planet_lons[pn] = pd['degree']
    asc_deg = chart.get('ascendant', {}).get('lon', chart.get('ascendant', {}).get('degree', 0))
    return calc_all_aspects(planet_lons, asc_deg)


# ============================================================================
# 17. Jaimini系统（v3.7新增）
# ============================================================================
def cmd_jaimini(args):
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from jaimini import (calc_chara_karaka_7, calc_chara_karaka_8, calc_chara_dasha,
                             calc_karakamsha, calc_chara_dasha_with_antardasha,
                             calc_arudha_padas, calc_graha_padas, calc_special_lagnas)
        from varga import calc_varga
    except ImportError as e:
        return {"error": f"jaimini模块导入失败: {e}"}
    planets = chart.get('planets', {})
    planet_lons = {}
    planet_degs = {}  # 星座内度数(0-30)，用于Jaimini Karaka计算
    for pn, pd in planets.items():
        if isinstance(pd, dict) and 'degree' in pd:
            planet_lons[pn] = pd['degree']
            planet_degs[pn] = pd.get('degree_in_sign', pd['degree'] % 30)
    asc_deg = chart.get('ascendant', {}).get('lon', chart.get('ascendant', {}).get('degree', 0))

    result = {}
    # Chara Karaka（必须传星座内度数0-30，不是完整经度0-360）
    mode = args.mode or 'all'
    if mode in ('all', 'karaka'):
        result['chara_karaka_7'] = calc_chara_karaka_7(planet_degs)
        result['chara_karaka_8'] = calc_chara_karaka_8(planet_degs)
    if mode in ('all', 'dasha'):
        use_antardasha = getattr(args, 'antardasha', False)
        if use_antardasha:
            result['chara_dasha'] = calc_chara_dasha_with_antardasha(asc_idx, planet_lons, args.year, args.month)
        else:
            result['chara_dasha'] = calc_chara_dasha(asc_idx, planet_lons, args.year, args.month)
    if mode in ('all', 'karakamsha'):
        # AK（灵魂星）的D9位置 — Karakamsha定义是AK在Navamsa中的星座
        # ⚠️ 2026-05-03修正：此前错误使用DK，现已修正为AK
        ck7 = calc_chara_karaka_7(planet_degs)
        ak_name = ck7['karaka_table']['Atmakaraka']['planet']
        ak_lon = planet_lons.get(ak_name, 0)
        ak_d9 = calc_varga(ak_lon, 9)
        result['karakamsha'] = calc_karakamsha(ak_d9.get('sign', 'Aries'), ak_d9.get('degree_in_sign', 0))
    if mode in ('all', 'arudha'):
        result['arudha_padas'] = calc_arudha_padas(asc_idx, planet_lons)
        result['graha_padas'] = calc_graha_padas(planet_lons)
    if mode in ('all', 'special'):
        result['special_lagnas'] = calc_special_lagnas(asc_idx, args.hour, args.minute + _arg_second(args) / 60.0)
    return result


# ============================================================================
# 18. 高级Nakshatra分析（v3.7 → v6.0.22 移至 cmd_nakshatra_adv.py）
# ============================================================================
def cmd_narayana_dasha(args):
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is not None:
        chart['ascendant_index'] = asc_idx
    return _cmd_narayana_dasha_impl(args, chart)


def cmd_nakshatra_adv(args):
    from cmd_nakshatra_adv import cmd_nakshatra_adv as _impl
    return _impl(args)


def cmd_nakshatra_dasha(args):
    from cmd_nakshatra_adv import cmd_nakshatra_dasha as _impl
    return _impl(args)


def cmd_nakshatra_full(args):
    from cmd_nakshatra_adv import cmd_nakshatra_full as _impl
    return _impl(args)


# ============================================================================
# 19. Argala门闩系统（v3.7新增）
# ============================================================================
def cmd_argala(args):
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from argala import calc_argala
    except ImportError as e:
        return {"error": f"argala模块导入失败: {e}"}
    planets = chart.get('planets', {})
    # 构建宫位到行星的映射 - argala需要sign_indices
    planet_sign_indices = {}
    for pn, pd in planets.items():
        if isinstance(pd, dict) and 'sign' in pd:
            si = SIGNS.index(pd['sign']) if pd['sign'] in SIGNS else 0
            planet_sign_indices[pn] = si
    return calc_argala(planet_sign_indices, asc_idx)


# ============================================================================
# 20. Tajika/Varshaphala年运盘（v3.7新增）
# ============================================================================
def cmd_tajika(args):
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from tajika import calc_muntha, calc_year_lord, calc_mudda_dasha, calc_tri_pataka
    except ImportError as e:
        return {"error": f"tajika模块导入失败: {e}"}
    planets = chart.get('planets', {})
    planet_lons = {}
    for pn, pd in planets.items():
        if isinstance(pd, dict) and 'degree' in pd:
            planet_lons[pn] = pd['degree']
    asc_deg = chart.get('ascendant', {}).get('lon', chart.get('ascendant', {}).get('degree', 0))
    asc_si = int(asc_deg / 30) % 12  # sign index
    age = args.age
    if age is None:
        return {"error": "请提供 --age 参数（当前年龄）"}

    result = {}
    mode = args.mode or 'all'
    if mode in ('all', 'muntha'):
        result['muntha'] = calc_muntha(asc_si, age)
    if mode in ('all', 'yearlord'):
        result['year_lord'] = calc_year_lord(asc_si, age)
    if mode in ('all', 'mudda'):
        # 需要先获取 varsha_lord
        yl = calc_year_lord(asc_si, age)
        varsha_lord = yl.get('year_lord', 'Jupiter')
        result['mudda_dasha'] = calc_mudda_dasha(asc_si, varsha_lord, args.month)
    if mode in ('all', 'tripataka'):
        yl = calc_year_lord(asc_si, age)
        varsha_lord = yl.get('year_lord', 'Jupiter')
        muntha_si = (asc_si + age) % 12
        result['tri_pataka'] = calc_tri_pataka(planet_lons, varsha_lord, muntha_si)
    return result


# ============================================================================
# 21. 合盘分析（v3.7新增）
# ============================================================================
def cmd_synastry(args):
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from synastry import calc_synastry
    except ImportError as e:
        return {"error": f"synastry模块导入失败: {e}"}
    # 构建两人数据
    p1 = {'moon_lon': args.moon1, 'gender': args.gender1 or 'M'}
    p2 = {'moon_lon': args.moon2, 'gender': args.gender2 or 'F'}
    if args.mars1 is not None: p1['mars_lon'] = args.mars1
    if args.mars2 is not None: p2['mars_lon'] = args.mars2
    if args.asc1 is not None: p1['asc_lon'] = args.asc1
    if args.asc2 is not None: p2['asc_lon'] = args.asc2
    return calc_synastry(p1, p2)


# ============================================================================
# 22. 全自动综合解盘 full-reading（v3.7.1新增）
# ============================================================================


# ============================================================================
# Transit 多参考点分析（v4.5.0 P1补齐）
# 基于 transit-multi-reference-guide.md 强制规范
# 四参考点：Lagna / Chandra Lagna / Arudha Lagna / Navamsa Lagna
# ============================================================================
def _calc_transit_multi_reference(planets, asc_idx, asc_deg, planet_lons, transit_planets=None, transit_date=None, node_mode='mean'):
    """
    ⭐ v4.5.0: Transit多参考点分析（强制规范）
    每次Transit分析必须同时从四个参考点评估：
    1. Lagna（上升点）— 实际生活事件
    2. Chandra Lagna（月亮星座）— 心理状态、职业变动
    3. Arudha Lagna（AL）— 公众形象
    4. Navamsa Lagna（D9上升）— 灵魂层面
    """
    data_layer = 'true_transit_positions' if transit_planets else 'natal_positions_fallback'
    analysis_planets = transit_planets if transit_planets else planets
    # 四个参考点的星座索引
    moon_lon = planet_lons.get('Moon', 0)
    chandra_idx = int(moon_lon / 30) % 12

    # Arudha Lagna（从special_lagnas模块逻辑简化：AL = (Ascendant度数+12宫主度数)%360 对应的星座）
    twelfth_sign_idx = (asc_idx + 11) % 12
    twelfth_lord = SIGN_LORDS.get(SIGNS[twelfth_sign_idx], '')
    twelfth_lord_lon = planet_lons.get(twelfth_lord, 0)
    al_raw = (asc_deg + twelfth_lord_lon) % 360
    # AL 特殊规则：如果结果落在原始宫或第7宫，取对宫
    al_idx = int(al_raw / 30) % 12
    if al_idx == asc_idx or al_idx == (asc_idx + 6) % 12:
        al_idx = (al_idx + 7) % 12  # 取第8个 = 对宫再移一位

    # Navamsa Lagna
    d9_asc_idx = _navamsa_idx(asc_deg)

    references = {
        'Lagna': {
            'name': 'Lagna',
            'cn': '上升点',
            'sign': SIGNS[asc_idx],
            'sign_cn': SIGNS_CN[SIGNS[asc_idx]],
            'sign_idx': asc_idx,
            'priority': 'P1',
            'scope': '实际生活事件、身体健康',
        },
        'Chandra_Lagna': {
            'name': 'Chandra Lagna',
            'cn': '月亮上升',
            'sign': SIGNS[chandra_idx],
            'sign_cn': SIGNS_CN[SIGNS[chandra_idx]],
            'sign_idx': chandra_idx,
            'priority': 'P1',
            'scope': '心理状态、职业变动、情感体验',
        },
        'Arudha_Lagna': {
            'name': 'Arudha Lagna',
            'cn': '形象上升',
            'sign': SIGNS[al_idx],
            'sign_cn': SIGNS_CN[SIGNS[al_idx]],
            'sign_idx': al_idx,
            'priority': 'P2',
            'scope': '公众形象、社会认知、他人如何看待你',
        },
        'Navamsa_Lagna': {
            'name': 'Navamsa Lagna',
            'cn': '灵性上升',
            'sign': SIGNS[d9_asc_idx],
            'sign_cn': SIGNS_CN[SIGNS[d9_asc_idx]],
            'sign_idx': d9_asc_idx,
            'priority': 'P3',
            'scope': '灵魂层面的实际影响、内在真实',
        },
    }

    # 对每个外行星（Jupiter/Saturn/Rahu/Ketu），计算从四个参考点看的宫位
    OUTER_PLANETS = ['Jupiter', 'Saturn', 'Rahu', 'Ketu']
    transit_analysis = {}
    for pn in OUTER_PLANETS:
        pd = analysis_planets.get(pn, {})
        if not isinstance(pd, dict) or 'sign' not in pd:
            continue
        p_sign_idx = SIGNS.index(pd['sign']) if pd['sign'] in SIGNS else 0
        transit_analysis[pn] = {
            'sign': pd['sign'],
            'sign_cn': SIGNS_CN.get(pd['sign'], ''),
            'degree_in_sign': pd.get('degree_in_sign', pd.get('degree', 0) % 30),
            'house_from_ref': {},
        }
        for ref_name, ref_info in references.items():
            ref_idx = ref_info['sign_idx']
            house = ((p_sign_idx - ref_idx) % 12) + 1
            house_meaning = _house_theme(house)
            transit_analysis[pn]['house_from_ref'][ref_name] = {
                'house': house,
                'meaning': house_meaning,
            }

    # 差异检测：同一行星在不同参考点的宫位含义是否矛盾
    divergences = []
    for pn, pa in transit_analysis.items():
        houses = {ref: info['house'] for ref, info in pa['house_from_ref'].items()}
        unique_houses = set(houses.values())
        if len(unique_houses) > 1:
            divergences.append({
                'planet': pn,
                'houses': houses,
                'divergence': f'{pn}在四个参考点分别落在不同宫位，需综合判断',
            })

    # Sade Sati / Ashtama Shani 检测（基于Chandra Lagna）
    special_checks = {}
    saturn_sign_idx = SIGNS.index(analysis_planets.get('Saturn', {}).get('sign', 'Aries')) if isinstance(analysis_planets.get('Saturn'), dict) and analysis_planets.get('Saturn', {}).get('sign') in SIGNS else 0
    # Sade Sati: Saturn 在月亮星座或前后1宫
    sade_sati_phase = None
    if saturn_sign_idx == chandra_idx:
        sade_sati_phase = 'peak'
    elif saturn_sign_idx == (chandra_idx - 1) % 12:
        sade_sati_phase = 'rising'
    elif saturn_sign_idx == (chandra_idx + 1) % 12:
        sade_sati_phase = 'setting'
    if sade_sati_phase:
        special_checks['sade_sati'] = {
            'active': True,
            'phase': sade_sati_phase,
            'note': f'土星过境月亮{SIGNS_CN[SIGNS[chandra_idx]]}附近，Sade Sati {sade_sati_phase}期',
        }
    # Ashtama Shani: Saturn在月亮第8宫
    saturn_from_chandra = ((saturn_sign_idx - chandra_idx) % 12) + 1
    if saturn_from_chandra == 8:
        special_checks['ashtama_shani'] = {
            'active': True,
            'note': '土星过境月亮第8宫（Ashtama Shani），压力期',
        }

    return {
        'references': references,
        'target_date': transit_date,
        'node_mode': node_mode,
        'data_layer': data_layer,
        'transit_analysis': transit_analysis,
        'divergences': divergences,
        'divergence_count': len(divergences),
        'special_checks': special_checks,
        'protocol': 'v6.0.10 Transit多参考点强制规范：AI必须用真实过境行星位置，并同时呈现Lagna和Chandra Lagna两个视角。任何矛盾信号必须记录并解释。',
    }


# ============================================================================
# Dasa Convergence 多系统交叉验证（v6.1.6）
# 基于 dasa-convergence-methodology.md
# 系统：Vimshottari + Chara Dasha + Yogini + Ashtottari + Kalachakra
# ============================================================================
# Yogini Dasha 常量
YOGINI_ORDER = ['Mangala', 'Pingala', 'Dhanya', 'Bhramari', 'Bhadrika', 'Ulka', 'Siddha', 'Sankata']
YOGINI_YEARS = {'Mangala': 1, 'Pingala': 2, 'Dhanya': 3, 'Bhramari': 4, 'Bhadrika': 5, 'Ulka': 6, 'Siddha': 7, 'Sankata': 8}
# Yogini 从月亮 Nakshatra 的第3个 Nakshatra（Dhanishta）开始计数
YOGINI_NAK_START = 23  # Dhanishta 在 NAKSHATRA_LIST 中的索引


def _calc_yogini_dasha(moon_lon, birthdate_str):
    """
    计算 Yogini Dasha 时间线
    Yogini 基于 8 位女神循环，总周期 36 年
    起始点由月亮所在 Nakshatra 决定
    """
    nak_idx = int(moon_lon / (360 / 27)) % 27
    # Yogini 起始索引 = (nak_idx - YOGINI_NAK_START) % 8
    yog_start = (nak_idx - YOGINI_NAK_START) % 8
    # 余数 = 在当前 Yogini 周期中的已过比例
    nak_in_yog = nak_idx % 8  # 在8分组的第几个
    pada = int((moon_lon % (360/27)) / (360/108)) + 1
    # 余数比例
    balance_frac = (nak_in_yog * 4 + pada - 1) / 32  # 8 Nakshatra × 4 Pada = 32 份
    balance_frac = min(balance_frac, 1.0)

    birth_date = datetime.strptime(birthdate_str, '%Y-%m-%d')
    maha_periods = []
    total_years = 0
    for i in range(8):
        idx = (yog_start + i) % 8
        name = YOGINI_ORDER[idx]
        years = YOGINI_YEARS[name]
        if i == 0:
            elapsed_years = years * balance_frac
            actual_years = years - elapsed_years
            start_offset = total_years
            maha_periods.append({
                'yogini': name,
                'full_years': years,
                'balance_years': round(actual_years, 3),
                'start_offset_years': round(start_offset, 3),
                'start_date': (birth_date + timedelta(days=round(start_offset * 365.25))).strftime('%Y-%m-%d'),
                'end_date': (birth_date + timedelta(days=round((start_offset + actual_years) * 365.25))).strftime('%Y-%m-%d'),
                'is_current_start': True,
            })
            total_years += actual_years
        else:
            start_offset = total_years
            maha_periods.append({
                'yogini': name,
                'full_years': years,
                'start_offset_years': round(start_offset, 3),
                'start_date': (birth_date + timedelta(days=round(start_offset * 365.25))).strftime('%Y-%m-%d'),
                'end_date': (birth_date + timedelta(days=round((start_offset + years) * 365.25))).strftime('%Y-%m-%d'),
            })
            total_years += years

    # 计算当前 Yogini
    today = datetime.now()
    age_days = (today - birth_date).days
    age_years = age_days / 365.25
    cycle_years = 36  # Yogini 总周期
    current_in_cycle = age_years % cycle_years
    current_yogini = None
    cumulative = 0
    for yp in maha_periods:
        dur = yp.get('balance_years', yp['full_years'])
        if cumulative <= current_in_cycle < cumulative + dur:
            current_yogini = yp
            break
        cumulative += dur

    return {
        'moon_nakshatra_idx': nak_idx,
        'yogini_start_index': yog_start,
        'total_cycle_years': 36,
        'maha_periods': maha_periods,
        'current_yogini': current_yogini,
    }


def _calc_dasa_convergence(dasha_result, chara_dasha_result, yogini_result, planet_lons, asc_idx, ashtottari_result=None, kalachakra_result=None):
    """
    ⭐ v6.1.6: Dasa Convergence 多系统交叉验证
    Vimshottari + Chara Dasha + Yogini + Ashtottari + Kalachakra 同时激活同一生活领域时，概率大幅提升。
    Chara Dasha 计算层为 covered；事件预测仍需多系统交叉确认。
    """
    # 提取各系统当前周期
    convergence_data = {'systems': {}}

    # 系统1: Vimshottari
    if isinstance(dasha_result, dict):
        current_d = dasha_result.get('current_dasha', {})
        if isinstance(current_d, dict):
            maha = current_d.get('mahadasha', current_d.get('maha'))
            antar = current_d.get('antardasha', current_d.get('antar'))
            convergence_data['systems']['vimshottari'] = {
                'maha': maha,
                'antar': antar,
                'pratyantar': current_d.get('pratyantar'),
                'basis': 'Nakshatra (Moon)',
            }

    # 系统2: Chara Dasha
    if isinstance(chara_dasha_result, dict):
        cd_maha = chara_dasha_result.get('current_maha', chara_dasha_result.get('current'))
        cd_antar = chara_dasha_result.get('current_antar')
        if isinstance(cd_maha, dict):
            cd_sign = cd_maha.get('sign', cd_maha.get('rashi'))
        elif isinstance(cd_maha, str):
            cd_sign = cd_maha
        else:
            cd_sign = None
        convergence_data['systems']['chara_dasha'] = {
            'maha_sign': cd_sign,
            'antar_sign': cd_antar.get('sign', cd_antar) if isinstance(cd_antar, dict) else cd_antar,
            'basis': 'Rashi (Sign-based)',
        }

    # 系统3: Yogini
    if isinstance(yogini_result, dict):
        cur_yog = yogini_result.get('current_yogini') or yogini_result.get('current') or {}
        convergence_data['systems']['yogini'] = {
            'yogini': cur_yog.get('yogini') if isinstance(cur_yog, dict) else None,
            'planet': cur_yog.get('planet') if isinstance(cur_yog, dict) else None,
            'years': cur_yog.get('full_years', cur_yog.get('years')) if isinstance(cur_yog, dict) else None,
            'basis': 'Nakshatra/Lagna 36-year cycle',
        }

    # 系统4: Ashtottari Dasha（条件性）
    if isinstance(ashtottari_result, dict):
        cur_ash = ashtottari_result.get('current') or {}
        convergence_data['systems']['ashtottari'] = {
            'applicable': ashtottari_result.get('applicable', True),
            'planet': cur_ash.get('planet') if isinstance(cur_ash, dict) else None,
            'years': cur_ash.get('years') if isinstance(cur_ash, dict) else None,
            'basis': 'Conditional Nakshatra/Paksha 108-year cycle',
        }

    # 系统5: Kalachakra Dasha
    if isinstance(kalachakra_result, dict):
        cur_kal = kalachakra_result.get('current') or {}
        convergence_data['systems']['kalachakra'] = {
            'mode': kalachakra_result.get('mode'),
            'lord': cur_kal.get('lord') if isinstance(cur_kal, dict) else None,
            'rashi': cur_kal.get('rashi') if isinstance(cur_kal, dict) else None,
            'years': cur_kal.get('years') if isinstance(cur_kal, dict) else None,
            'basis': 'Moon Nakshatra Pada / Rashi-year cycle',
        }

    # 宫位主题映射
    house_themes_map = {
        1: 'self_health', 2: 'wealth_family', 3: 'communication_skill', 4: 'home_mother',
        5: 'creativity_children', 6: 'health_service', 7: 'marriage_partnership',
        8: 'transformation', 9: 'fortune_dharma', 10: 'career_status',
        11: 'gains_wishes', 12: 'loss_spirituality',
    }

    # 逐领域检测三系统激活
    domain_activations = {}
    for house, domain in house_themes_map.items():
        activations = []

        # Vimshottari: 检查大运/小运行星是否关联该宫
        vims = convergence_data['systems'].get('vimshottari', {})
        if vims:
            for level in ['maha', 'antar']:
                planet = vims.get(level)
                if planet and isinstance(planet, str):
                    # 该行星是否掌管此宫？
                    target_sign_idx = (asc_idx + house - 1) % 12
                    target_sign = SIGNS[target_sign_idx]
                    target_lord = SIGN_LORDS.get(target_sign, '')
                    if planet == target_lord:
                        activations.append({
                            'system': 'Vimshottari',
                            'level': level,
                            'planet': planet,
                            'reason': f'{planet}是{house}宫({target_sign})的宫主星',
                        })
                    # 该行星是否落在此宫？
                    p_sign_idx = int(planet_lons.get(planet, 0) / 30) % 12
                    p_house = ((p_sign_idx - asc_idx) % 12) + 1
                    if p_house == house:
                        activations.append({
                            'system': 'Vimshottari',
                            'level': level,
                            'planet': planet,
                            'reason': f'{planet}落在{house}宫',
                        })

        # Chara Dasha: 检查当前星座是否关联该宫
        cd = convergence_data['systems'].get('chara_dasha', {})
        if cd and cd.get('maha_sign'):
            cd_sign = cd['maha_sign']
            if cd_sign in SIGNS:
                cd_sign_idx = SIGNS.index(cd_sign)
                cd_house_from_asc = ((cd_sign_idx - asc_idx) % 12) + 1
                if cd_house_from_asc == house:
                    activations.append({
                        'system': 'Chara Dasha',
                        'level': 'maha',
                        'sign': cd_sign,
                        'reason': f'Chara大运星座{cd_sign}是{house}宫',
                    })

        # Yogini / Ashtottari: 当前行星是否掌管或落入该宫
        for system_key, system_label, planet_key in [
            ('yogini', 'Yogini', 'planet'),
            ('ashtottari', 'Ashtottari', 'planet'),
        ]:
            sys_data = convergence_data['systems'].get(system_key, {})
            planet = sys_data.get(planet_key)
            if not planet or not isinstance(planet, str):
                continue
            target_sign_idx = (asc_idx + house - 1) % 12
            target_sign = SIGNS[target_sign_idx]
            target_lord = SIGN_LORDS.get(target_sign, '')
            if planet == target_lord:
                activations.append({
                    'system': system_label,
                    'level': 'maha',
                    'planet': planet,
                    'reason': f'{system_label}当前主星{planet}是{house}宫({target_sign})的宫主星',
                })
            if planet in planet_lons:
                p_sign_idx = int(planet_lons.get(planet, 0) / 30) % 12
                p_house = ((p_sign_idx - asc_idx) % 12) + 1
                if p_house == house:
                    activations.append({
                        'system': system_label,
                        'level': 'maha',
                        'planet': planet,
                        'reason': f'{system_label}当前主星{planet}落在{house}宫',
                    })

        # Kalachakra: 当前 Rashi 是否关联该宫，当前 lord 是否掌管或落入该宫
        kal = convergence_data['systems'].get('kalachakra', {})
        if kal:
            kal_rashi = kal.get('rashi')
            if kal_rashi in SIGNS:
                kal_sign_idx = SIGNS.index(kal_rashi)
                kal_house_from_asc = ((kal_sign_idx - asc_idx) % 12) + 1
                if kal_house_from_asc == house:
                    activations.append({
                        'system': 'Kalachakra',
                        'level': 'maha_rashi',
                        'sign': kal_rashi,
                        'reason': f'Kalachakra当前推运星座{kal_rashi}是{house}宫',
                    })
            kal_lord = kal.get('lord')
            if kal_lord and isinstance(kal_lord, str):
                target_sign_idx = (asc_idx + house - 1) % 12
                target_sign = SIGNS[target_sign_idx]
                target_lord = SIGN_LORDS.get(target_sign, '')
                if kal_lord == target_lord:
                    activations.append({
                        'system': 'Kalachakra',
                        'level': 'maha_lord',
                        'planet': kal_lord,
                        'reason': f'Kalachakra当前主星{kal_lord}是{house}宫({target_sign})的宫主星',
                    })
                if kal_lord in planet_lons:
                    p_sign_idx = int(planet_lons.get(kal_lord, 0) / 30) % 12
                    p_house = ((p_sign_idx - asc_idx) % 12) + 1
                    if p_house == house:
                        activations.append({
                            'system': 'Kalachakra',
                            'level': 'maha_lord',
                            'planet': kal_lord,
                            'reason': f'Kalachakra当前主星{kal_lord}落在{house}宫',
                        })

        if activations:
            domain_activations[domain] = {
                'house': house,
                'activations': activations,
                'system_count': len(set(a['system'] for a in activations)),
            }

    # 收敛等级评估
    for domain, info in domain_activations.items():
        sc = info['system_count']
        if sc >= 4:
            info['convergence_level'] = 'L5'
            info['probability'] = '85-92%'
            info['interpretation'] = '四个及以上推运系统同时激活，顶级收敛信号'
        elif sc >= 3:
            info['convergence_level'] = 'L4'
            info['probability'] = '75-85%'
            info['interpretation'] = '三系统同时激活，极强信号'
        elif sc >= 2:
            info['convergence_level'] = 'L3'
            info['probability'] = '50-65%'
            info['interpretation'] = '双系统激活，强信号'
        else:
            info['convergence_level'] = 'L1'
            info['probability'] = '+15-20%'
            info['interpretation'] = '单系统激活，需Transit确认'

    # 收敛窗口（最高优先级的领域）
    top_domains = sorted(domain_activations.items(), key=lambda x: x[1]['system_count'], reverse=True)[:5]

    return {
        'systems_summary': convergence_data['systems'],
        'domain_activations': domain_activations,
        'top_convergent_domains': [(d, info['convergence_level']) for d, info in top_domains],
        'protocol': 'v6.1.6 Dasa Convergence 多系统交叉验证。收敛等级: L1(单系统)→L3(双系统)→L4(三系统)→L5(四个及以上系统)。Chara Dasha 计算层为 covered；所有预测仍必须由 Vimshottari/Transit/Varga 等独立层确认。',
    }


def _calc_actionable_context(planets, asc_idx):
    """⭐ v4.1.0: 计算Transit Actionable Output所需的上下文数据
    输出：宫位激活映射 + 关键行星宫位关系 → 供AI生成Actionable Output时直接引用
    """
    # 宫位主星映射（哪个行星掌管哪个宫）
    house_lord_map = {}
    for h in range(1, 13):
        sign_idx = (asc_idx + h - 1) % 12
        sname = SIGNS[sign_idx]
        lord = SIGN_LORDS.get(sname, 'Unknown')
        house_lord_map[h] = {'sign': sname, 'lord': lord}

    # 行星落宫映射（哪个行星落在哪个宫）
    planet_house_map = {}
    for pn, pd in planets.items():
        if isinstance(pd, dict):
            planet_house_map[pn] = {
                'sign': pd.get('sign', 'Unknown'),
                'house': pd.get('house', 0),
                'degree_in_sign': pd.get('degree_in_sign', 0),
            }

    # 双宫掌管检测（仓库耦合）
    lord_to_houses = {}
    for h, info in house_lord_map.items():
        lord = info['lord']
        if lord not in lord_to_houses:
            lord_to_houses[lord] = []
        lord_to_houses[lord].append(h)
    warehouse_coupling = {l: hs for l, hs in lord_to_houses.items() if len(hs) > 1}

    # 关键宫位激活条件（Transit激活该宫需要哪些行星过境相关星座）
    KEY_HOUSES = {
        2: '财富/家庭/语言',
        3: '沟通/技能/短途/内容创作',
        5: '创造力/子女/投机/恋爱',
        7: '婚姻/合作/公开对手',
        9: '长途旅行/高等教育/宗教/出版',
        10: '事业/社会地位/权威',
        11: '收入/愿望/社交网络/贵人',
        12: '海外/灵性/损失/解脱',
    }

    activation_map = {}
    for h, meaning in KEY_HOUSES.items():
        sign_idx = (asc_idx + h - 1) % 12
        sname = SIGNS[sign_idx]
        lord = SIGN_LORDS.get(sname, 'Unknown')
        lord_house = planet_house_map.get(lord, {}).get('house', 0)
        activation_map[h] = {
            'house_meaning': meaning,
            'sign': sname,
            'lord': lord,
            'lord_house': lord_house,
            'transit_triggers': f'{lord}过境{h}宫({sname})或{lord}本身过境相关宫位',
            'double_transit_hint': f'需要Saturn和Jupiter同时激活{h}宫或{h}宫主所在宫',
        }

    # 内容创作相关信号（3宫/5宫/9宫/10宫交叉）
    content_signals = {}
    for h in [3, 5, 9, 10]:
        if h in activation_map:
            content_signals[f'house_{h}'] = activation_map[h]

    # 贵人相关信号（7宫/9宫/11宫）
    mentor_signals = {}
    for h in [7, 9, 11]:
        if h in activation_map:
            mentor_signals[f'house_{h}'] = activation_map[h]

    return {
        'house_lord_map': house_lord_map,
        'planet_house_map': planet_house_map,
        'warehouse_coupling': warehouse_coupling,
        'key_house_activations': activation_map,
        'content_creation_context': content_signals,
        'mentor_discovery_context': mentor_signals,
        'actionable_hint': 'AI应基于此上下文生成Transit Actionable Output：每条Transit预测必须包含时间段+行动类型+置信度。详见SKILL.md Transit Actionable Output规范。',
    }

def cmd_full_reading(args):
    """
    用户只需提供出生信息，引擎自动串起全链路分析：
    chart → dasha → yoga → varga-full → aspects → jaimini → nakshatra-adv
    → argala → tajika → shadbala → ashtakavarga → validate → audit
    → 综合报告输出
    """
    import time
    t0 = time.perf_counter()
    stage_timings = []
    profile_stages = _full_reading_profiler_enabled(args)

    def _build_whole_sign_houses(asc_index, planets_data):
        """Build a compatibility house map for add-on modules.

        compute_chart_data() exposes Placidus/equal-style cusp keys (house_1...),
        while several v6.0.14-16 add-on modules expect 1..12 keys plus Hn_Lord.
        This adapter keeps those modules wired without changing their public API.
        """
        house_map = {}
        for house_num in range(1, 13):
            sign_idx = (asc_index + house_num - 1) % 12
            sign_name = SIGNS[sign_idx]
            house_map[house_num] = {
                'sign': sign_name,
                'lord': SIGN_LORDS.get(sign_name, ''),
                'planets': [],
                'strength': 'Neutral',
            }
            house_map[str(house_num)] = house_map[house_num]
            house_map[f'H{house_num}_Lord'] = house_map[house_num]['lord']
        for planet_name, planet_data in planets_data.items():
            if isinstance(planet_data, dict):
                house_num = planet_data.get('house')
                if isinstance(house_num, int) and house_num in house_map:
                    house_map[house_num]['planets'].append(planet_name)
        return house_map

    def _varga_planet_lons(varga_chart):
        """Convert calc_all_vargas() planet sign/degree data to longitude dict."""
        lons = {}
        if not isinstance(varga_chart, dict):
            return lons
        for planet_name, planet_data in varga_chart.items():
            if planet_name.startswith('_') or planet_name == 'Ascendant':
                continue
            if isinstance(planet_data, dict) and 'sign_idx' in planet_data:
                lons[planet_name] = planet_data['sign_idx'] * 30 + planet_data.get('degree_in_sign', 0)
        return lons

    report = {
        'version': '4.4.0-full-reading',
        'birth_info': {
            'date': f"{args.year}-{args.month:02d}-{args.day:02d}",
            'time': _birth_time_string(args.hour, args.minute, _arg_second(args)),
            'hour': int(args.hour),
            'minute': int(args.minute),
            'second': _arg_second(args),
            'lat': args.lat, 'lon': args.lon,
            'tz': f"UTC{'+' if args.tz >= 0 else ''}{args.tz}",
        },
        'modules': {},
        'errors': [],
        'warnings': [],
    }

    # ── Step 1: 核心星盘 ──
    stage_started = time.perf_counter()
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装，无法计算星盘"}

    chart_birth = chart.get('birth_info', {}) if isinstance(chart, dict) else {}
    report['birth_info']['ayanamsa'] = chart_birth.get('ayanamsa')
    report['birth_info']['ayanamsa_name'] = chart_birth.get('ayanamsa_name', _current_ayanamsa_name(args))
    report['birth_info']['ayanamsa_display'] = chart_birth.get(
        'ayanamsa_display',
        _ayanamsa_display_name(report['birth_info']['ayanamsa_name']),
    )
    report['birth_info']['node_mode'] = chart_birth.get('node_mode', getattr(args, 'node_mode', 'mean'))

    report['chart'] = chart
    report['modules']['chart'] = chart
    planets = chart.get('planets', {})
    asc_deg = chart.get('ascendant', {}).get('lon', chart.get('ascendant', {}).get('degree', 0))
    asc_sign = chart.get('ascendant', {}).get('sign', 'Unknown')
    planet_lons = {pn: pd.get('degree_raw', pd['degree']) for pn, pd in planets.items() if isinstance(pd, dict) and 'degree' in pd}
    planet_degs = {pn: pd.get('degree_in_sign_raw', pd.get('degree_in_sign', pd['degree'] % 30)) for pn, pd in planets.items() if isinstance(pd, dict) and 'degree' in pd}
    houses = _build_whole_sign_houses(asc_idx, planets)
    report['modules']['house_map'] = houses
    planet_sign_indices = {}
    for pn, pd in planets.items():
        if isinstance(pd, dict) and 'sign' in pd:
            planet_sign_indices[pn] = SIGNS.index(pd['sign']) if pd['sign'] in SIGNS else 0
    _record_stage_timing(
        stage_timings,
        'core_chart_and_setup',
        stage_started,
        enabled=profile_stages,
        details={'modules': ['chart', 'house_map']},
    )

    # ── Step 1.5: Special Lagnas 特殊上升点 (v4.4.0) ──
    stage_started = time.perf_counter()
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from special_lagnas import SpecialLagnasCalculator
        sl_calc = SpecialLagnasCalculator()
        birth_dt = _birth_datetime_from_args(args)
        # 简化处理：sunrise 近似为 6:00 当地时间
        sunrise_dt = datetime(args.year, args.month, args.day, 6, 0)
        sl_result = sl_calc.calculate_all_lagnas(
            asc_degree=asc_deg,
            sun_degree=planet_lons.get('Sun', 0),
            moon_degree=planet_lons.get('Moon', 0),
            birth_time=birth_dt,
            sunrise_time=sunrise_dt
        )
        # 补充 Arudha Lagna、A10/Karma Pada 和 Upapada Lagna
        try:
            first_house_sign_idx = asc_idx
            first_lord = SIGN_LORDS.get(SIGNS[first_house_sign_idx], '')
            first_lord_deg = planet_lons.get(first_lord, 0)
            sl_result['Arudha_Lagna'] = sl_calc.calculate_arudha_lagna(asc_deg, first_lord_deg)
        except Exception as e:
            sl_result['Arudha_Lagna'] = {"error": str(e)}
        try:
            tenth_house_sign_idx = (asc_idx + 9) % 12
            tenth_lord = SIGN_LORDS.get(SIGNS[tenth_house_sign_idx], '')
            tenth_lord_deg = planet_lons.get(tenth_lord, 0)
            sl_result['A10_Karma_Pada'] = sl_calc.calculate_a10(asc_deg, tenth_lord_deg)
        except Exception as e:
            sl_result['A10_Karma_Pada'] = {"error": str(e)}
        try:
            twelfth_house_sign_idx = (asc_idx + 11) % 12
            twelfth_lord = SIGN_LORDS.get(SIGNS[twelfth_house_sign_idx], '')
            twelfth_lord_deg = planet_lons.get(twelfth_lord, 0)
            sl_result['Upapada_Lagna'] = sl_calc.calculate_upapada_lagna(asc_deg, twelfth_lord_deg)
        except Exception as e:
            sl_result['Upapada_Lagna'] = {"error": str(e)}
        report['modules']['special_lagnas'] = sl_result
    except Exception as e:
        report['errors'].append(f"special-lagnas: {e}")

    # ── Step 2: Vimshottari Dasha ──
    try:
        moon_data = planets.get('Moon', {})
        moon_lon = moon_data.get('degree_raw', moon_data.get('degree', 0))
        nak_idx = int(moon_lon / (360 / 27)) % 27
        nak_name = NAKSHATRA_LIST[nak_idx][0]
        nak_lord = NAKSHATRA_LIST[nak_idx][1]
        pada = int((moon_lon % (360/27)) / (360/108)) + 1

        birthdate = f"{args.year}-{args.month:02d}-{args.day:02d}"
        today_str = getattr(args, 'transit_date', None) or getattr(args, 'today', None) or datetime.now().strftime('%Y-%m-%d')
        dasha_result = cmd_dasha(type('Args', (), {
            'nakshatra': nak_name, 'pada': pada,
            'moon_lon': moon_lon,
            'birthdate': birthdate,
            'year': args.year,
            'month': args.month,
            'day': args.day,
            'hour': args.hour,
            'minute': args.minute,
            'second': _arg_second(args),
            'lat': args.lat,
            'lon': args.lon,
            'tz': args.tz,
            'node_mode': getattr(args, 'node_mode', 'mean'),
            'today': today_str
        })())
        report['modules']['dasha'] = dasha_result
        report['modules']['dasha_sandhi'] = _calc_dasha_sandhi(dasha_result, today_str)
    except Exception as e:
        report['errors'].append(f"dasha: {e}")

    # ── Step 3: Yoga格局 ──
    try:
        yoga_planets = {}
        for pn, pd in planets.items():
            if isinstance(pd, dict) and 'sign' in pd and 'house' in pd:
                yoga_planets[pn] = {'sign': pd['sign'], 'house': pd['house']}
        yoga_result = cmd_yoga(type('Args', (), {
            'ascendant': asc_sign,
            'planets': ','.join([f"{k}:{v['sign']}:{v['house']}" for k, v in yoga_planets.items()])
        })())
        report['modules']['yoga'] = yoga_result
    except Exception as e:
        report['errors'].append(f"yoga: {e}")

    # ── Step 4: BPHS十六分盘 ──
    try:
        sys.path.insert(0, SCRIPT_DIR)
        from varga import calc_all_vargas
        varga_result = calc_all_vargas(planet_lons, asc_deg, None)  # None = 全部分盘
        # 补充 D1_Rashi 到 varga_full（使用 chart 中的行星位置）
        d1_data = {}
        for pn, pd in planets.items():
            if isinstance(pd, dict) and 'sign' in pd:
                d1_data[pn] = {
                    "sign": pd["sign"],
                    "degree": pd.get("degree", 0),
                    "degree_in_sign": pd.get("degree_in_sign", pd.get("degree", 0) % 30),
                    "house": pd.get("house"),
                    "nakshatra": pd.get("nakshatra"),
                    "nakshatra_pada": pd.get("nakshatra_pada"),
                }
        if d1_data:
            varga_result["D1_Rashi"] = d1_data
        if "D11_Rudramsa" not in varga_result:
            try:
                from divisional_charts_extended import DivisionalChartsCalculator, VargaType
                dc_calc_for_d11 = DivisionalChartsCalculator()
                varga_result["D11_Rudramsa"] = dc_calc_for_d11._calculate_single_varga(
                    VargaType.D11,
                    planet_lons,
                    asc_deg,
                )
            except Exception as d11_error:
                varga_result["D11_Rudramsa"] = {"error": str(d11_error)}
        report['modules']['varga_full'] = varga_result

        # v6.1.7: Re-run Yoga with D9/D60 context after varga-full is available.
        # The earlier Step 3 remains a D1-only fallback for backward compatibility.
        try:
            yoga_context = _build_yoga_context_from_vargas(varga_result, planet_lons)
            yoga_planets = {}
            for pn, pd in planets.items():
                if isinstance(pd, dict) and 'sign' in pd and 'house' in pd:
                    yoga_planets[pn] = {
                        'sign': pd['sign'],
                        'house': pd['house'],
                        'degree': pd.get('degree_in_sign', pd.get('degree')),
                    }
            yoga_result = cmd_yoga(type('Args', (), {
                'ascendant': asc_sign,
                'planets': ','.join([
                    f"{k}:{v['sign']}:{v['house']}" + (f":{v['degree']}" if v.get('degree') is not None else "")
                    for k, v in yoga_planets.items()
                ]),
                'context_json': json.dumps(yoga_context, ensure_ascii=False),
            })())
            yoga_result['context_layers'] = sorted(k for k, v in yoga_context.items() if v)
            report['modules']['yoga'] = yoga_result
        except Exception as yoga_ctx_e:
            report['errors'].append(f"yoga-context-injection: {yoga_ctx_e}")

        report['modules']['vargottama'] = _calc_vargottama(planets, varga_result)
        report['modules']['pushkara'] = _calc_pushkara_flags(planets)
        report['modules']['sensitive_points'] = _calc_sensitive_points(planets)
    except Exception as e:
        report['errors'].append(f"varga-full: {e}")

    # ── Step 4.5: Vimsopaka Bala 分盘力量 (v4.4.0) ──
    try:
        from vimsopaka_calculator import VimsopakaBalaCalculator, VargaType as VimsVargaType, DignityLevel
        vims_calc = VimsopakaBalaCalculator(mode="shodasavarga")
        # 将 varga_result 转换为 Vimsopaka 所需的 planet_vargas 格式
        # varga_result 结构: {varga_name: {planet: {sign, degree, ...}}}
        # 需要转为: {planet: {VargaType: DignityLevel}}
        dignity_map = {
            'EXALTED': DignityLevel.EXALTED, 'MOOLATRIKONA': DignityLevel.MOOLATRIKONA,
            'OWN_SIGN': DignityLevel.OWN_SIGN, 'GREAT_FRIEND': DignityLevel.GREAT_FRIEND,
            'FRIEND': DignityLevel.FRIEND, 'NEUTRAL': DignityLevel.NEUTRAL,
            'ENEMY': DignityLevel.ENEMY, 'GREAT_ENEMY': DignityLevel.GREAT_ENEMY,
            'DEBILITATED': DignityLevel.DEBILITATED, 'NEECHA_BHANGA': DignityLevel.NEECHA_BHANGA,
        }
        # 建立 VargaType → varga_result key 的映射（修复：每个分盘独立计算尊贵）
        _vt_div = {VimsVargaType.D1:1, VimsVargaType.D2:2, VimsVargaType.D3:3,
                   VimsVargaType.D4:4, VimsVargaType.D7:7, VimsVargaType.D9:9,
                   VimsVargaType.D10:10, VimsVargaType.D12:12, VimsVargaType.D16:16,
                   VimsVargaType.D20:20, VimsVargaType.D24:24, VimsVargaType.D27:27,
                   VimsVargaType.D30:30, VimsVargaType.D40:40, VimsVargaType.D45:45,
                   VimsVargaType.D60:60}
        _div_meta = {2:'Hora',3:'Drekkana',4:'Turyamsa',7:'Saptamsa',9:'Navamsa',
                     10:'Dasamsa',12:'Dwadashamsa',16:'Shodasamsa',20:'Vimsamsa',
                     24:'Siddhamsa',27:'Bhamsa',30:'Trimsamsa',40:'Khavedamsa',
                     45:'Akshavedamsa',60:'Shashtiamsa'}
        planet_vargas_input = {}
        for pn in planet_lons:
            planet_vargas_input[pn] = {}
            for vt in VimsVargaType:
                div = _vt_div.get(vt)
                if div and varga_result:
                    # 构造对应的 key，如 D9_Navamsa
                    vkey = f"D{div}_{_div_meta.get(div, f'D{div}')}"
                    vdata = varga_result.get(vkey, {})
                    # 使用 _get_dignity_level 计算完整5-fold尊贵（含Friend/Enemy）
                    # 不使用 _dignity 字典（只有 Exalted/Debilitated/Own Sign）
                    pinfo = vdata.get(pn, {})
                    if isinstance(pinfo, dict) and 'sign' in pinfo:
                        dignity_context = planets if div == 1 else _build_dignity_context(vdata)
                        dl_key = _get_dignity_level(pn, pinfo['sign'],
                                      pinfo.get('degree_in_sign', pinfo.get('degree', 0) % 30),
                                      dignity_context)
                        planet_vargas_input[pn][vt] = dignity_map.get(dl_key, DignityLevel.NEUTRAL)
                    elif div == 1:
                        # D1 直接用本命盘数据
                        p_sign = SIGNS[int(planet_lons.get(pn, 0) / 30) % 12]
                        d_in_s = planet_lons.get(pn, 0) % 30
                        dl_key = _get_dignity_level(pn, p_sign, d_in_s, planets)
                        planet_vargas_input[pn][vt] = dignity_map.get(dl_key, DignityLevel.NEUTRAL)
                    else:
                        planet_vargas_input[pn][vt] = DignityLevel.NEUTRAL
                elif div == 1 and not varga_result:
                    # fallback: D1 从 planet_lons 计算
                    p_sign = SIGNS[int(planet_lons.get(pn, 0) / 30) % 12]
                    d_in_s = planet_lons.get(pn, 0) % 30
                    dl_key = _get_dignity_level(pn, p_sign, d_in_s, planets)
                    planet_vargas_input[pn][vt] = dignity_map.get(dl_key, DignityLevel.NEUTRAL)
                else:
                    planet_vargas_input[pn][vt] = DignityLevel.NEUTRAL
        vimsopaka_result = vims_calc.calculate_vimsopaka_bala(planet_vargas_input)
        # 添加顶层汇总
        if isinstance(vimsopaka_result, dict):
            total_scores = []
            for pn, pdata in vimsopaka_result.items():
                if isinstance(pdata, dict) and 'total_score' in pdata:
                    total_scores.append(pdata['total_score'])
            if total_scores:
                avg_score = round(sum(total_scores) / len(total_scores), 2)
                vimsopaka_result['total_score'] = avg_score
                vimsopaka_result['total_score_max'] = 20.0
                vimsopaka_result['status'] = '优秀' if avg_score >= 15 else '良好' if avg_score >= 10 else '一般' if avg_score >= 7 else '偏弱'
        report['modules']['vimsopaka'] = vimsopaka_result
    except Exception as e:
        report['errors'].append(f"vimsopaka: {e}")

    # ── Step 4.6: Divisional Charts Extended 扩展分盘 (v4.4.0) ──
    try:
        from divisional_charts_extended import DivisionalChartsCalculator
        dc_calc = DivisionalChartsCalculator()
        # 只计算 D5/D6/D8/D11（扩展分盘，与 Step 4 的标准分盘互补）
        ext_vargas = dc_calc.calculate_all_vargas(planet_lons, asc_deg)
        # 过滤只保留 Step 4 没有的分盘
        ext_filtered = {k: v for k, v in ext_vargas.items()
                       if v.get('division') in [5, 6, 8, 11]}
        report['modules']['varga_extended'] = ext_filtered
    except Exception as e:
        report['errors'].append(f"varga-extended: {e}")


    # ── Step 4.7: Dispositor Chains + Inter-chart Linkage (v6.0.12) ──
    try:
        # 准备分盘数据：从 varga_full 提取 D1/D9/D10/D12
        vf = report['modules'].get('varga_full', {})
        d1_for_dc = vf.get('D1_Rashi', {})
        d9_for_ic = vf.get('D9_Navamsa', {}) if isinstance(vf.get('D9_Navamsa'), dict) else {}
        d10_for_ic = vf.get('D10_Dasamsa', {}) if isinstance(vf.get('D10_Dasamsa'), dict) else {}
        d12_for_ic = vf.get('D12_Dwadashamsa', {}) if isinstance(vf.get('D12_Dwadashamsa'), dict) else None

        # Dispositor Chains：基于 D1 行星数据
        dc_result = calc_all_dispositor_chains(planets)
        report['modules']['dispositor_chains'] = dc_result

        # Inter-chart Linkage：需要各分盘的 asc_idx
        # D1 asc_idx 已知；D9/D10/D12 的 asc_idx 需要从各自分盘数据提取
        d9_asc_idx = None
        d10_asc_idx = None
        d12_asc_idx = None
        if isinstance(d9_for_ic, dict):
            d9_asc = d9_for_ic.get('Ascendant', {})
            if isinstance(d9_asc, dict) and 'sign' in d9_asc:
                d9_asc_idx = SIGNS.index(d9_asc['sign']) if d9_asc['sign'] in SIGNS else None
        if isinstance(d10_for_ic, dict):
            d10_asc = d10_for_ic.get('Ascendant', {})
            if isinstance(d10_asc, dict) and 'sign' in d10_asc:
                d10_asc_idx = SIGNS.index(d10_asc['sign']) if d10_asc['sign'] in SIGNS else None
        if d12_for_ic and isinstance(d12_for_ic, dict):
            d12_asc = d12_for_ic.get('Ascendant', {})
            if isinstance(d12_asc, dict) and 'sign' in d12_asc:
                d12_asc_idx = SIGNS.index(d12_asc['sign']) if d12_asc['sign'] in SIGNS else None

        ic_result = calc_all_inter_chart_linkages(
            d1_for_dc, d9_for_ic, d10_for_ic, d12_for_ic,
            asc_idx, d9_asc_idx, d10_asc_idx
        )
        report['modules']['inter_chart_linkage'] = ic_result

        # 补充：每个行星的"最终定位星"（Dispositor Chain 的最后一个非循环元素）
        final_dispositors = {}
        for pname, chain in dc_result.items():
            if chain:
                # 找到最后一个不重复的元素
                seen = set()
                last_valid = None
                for item in chain:
                    if item['dispositor'] in seen:
                        break
                    seen.add(item['dispositor'])
                    last_valid = item
                if last_valid:
                    final_dispositors[pname] = last_valid['dispositor']
                else:
                    final_dispositors[pname] = chain[-1]['dispositor'] if chain else None
            else:
                final_dispositors[pname] = None
        report['modules']['final_dispositors'] = final_dispositors

    except Exception as e:
        report['errors'].append(f"dispositor-chain+inter-chart: {e}")

    # ── Step 4.8: Tajika Yogas + Sahams (v6.0.13) ──
    try:
        from tajika import calc_tajika_yogas, calc_all_sahams

        # Seven-planet Tajika candidates require actual instantaneous speed.
        tajika_planets = {
            name: {"longitude": item.get("degree_raw", item.get("lon")), "speed": item.get("speed")}
            for name, item in planets.items()
            if isinstance(item, dict) and name in {"Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"}
        }
        tc_yogas = calc_tajika_yogas(tajika_planets)
        report['modules']['tajika_yogas'] = tc_yogas

        # Sahams（特殊点）—— 需要出生时间
        birth_dt = _birth_datetime_from_args(args)
        if birth_dt and planet_lons:
            sahams_result = calc_all_sahams(
                planet_lons,
                asc_deg,
                birth_dt,
                lat=getattr(args, 'lat', None),
                lon=getattr(args, 'lon', None),
                tz=getattr(args, 'tz', None),
            )
            report['modules']['sahams'] = sahams_result
        else:
            report['modules']['sahams'] = {'warning': 'birth_datetime or planet_lons missing, skip saham calc'}

    except Exception as e:
        report['errors'].append(f"tajika-yogas+sahams: {e}")

    # ── Step 4.9: Yogas + Doshas + Special Lagnas (v6.0.14) ──
    try:
        from yogas_doshas import calc_all_yogas_doshas

        # 准备参数
        asc_sign = SIGNS[asc_idx] if 'asc_idx' in dir() else SIGNS[0]
        asc_lord = SIGN_LORDS.get(asc_sign, '')
        moon_data = planets.get('Moon', {})
        moon_sign = moon_data.get('sign', '') if isinstance(moon_data, dict) else ''
        moon_house = moon_data.get('house', 0) if isinstance(moon_data, dict) else 0
        mars_data = planets.get('Mars', {})
        mars_house = mars_data.get('house', 0) if isinstance(mars_data, dict) else 0
        sun_data = planets.get('Sun', {})
        sun_house = sun_data.get('house', 0) if isinstance(sun_data, dict) else 0
        # 12宫主星
        h12_lord = SIGN_LORDS.get(SIGNS[(asc_idx + 11) % 12], '')

        yd_result = calc_all_yogas_doshas(
            planets, houses,
            asc_sign, asc_lord,
            moon_sign, moon_house,
            mars_house, sun_house,
            h12_lord
        )
        report['modules']['yogas_doshas'] = yd_result

    except Exception as e:
        report['errors'].append(f"yogas-doshas: {e}")

    # ── Step 4.10: Tithi Lord + Pancha Pakshi + Rashi Tulya Navamsa (v6.0.15) ──
    try:
        # Tithi Lord（出生 Tithi + Lord 分析）
        from tithi_lord import calc_tithi_lord_full
        sun_deg = planet_lons.get('Sun', 0)
        moon_deg = planet_lons.get('Moon', 0)
        tithi_result = calc_tithi_lord_full(sun_deg, moon_deg, planets, houses)
        report['modules']['tithi_lord'] = tithi_result
    except Exception as e:
        report['errors'].append(f"tithi-lord: {e}")

    try:
        # Pancha Pakshi（五鸟系统，需要出生 Nakshatra）
        # v6.1.6: 对齐 pancha_pakshi.py 现有公共接口 get_pancha_pakshi_schedule()
        moon_deg = planet_lons.get('Moon', 0)
        nak_num = int(moon_deg / (360.0 / 27)) + 1
        if nak_num > 27:
            nak_num = 27
        nak_name = NAKSHATRA_LIST[nak_num - 1][0]
        tithi_number = int(((moon_deg - planet_lons.get('Sun', 0)) % 360) / 12) + 1
        paksha = 'shukla' if 1 <= tithi_number <= 15 else 'krishna'
        from pancha_pakshi import get_pancha_pakshi_schedule
        pk_result = get_pancha_pakshi_schedule(
            birth_nakshatra=nak_name,
            paksha=paksha,
            date=f"{args.year}-{args.month:02d}-{args.day:02d}",
        )
        pk_result['input_context'] = {
            'moon_nakshatra_index': nak_num - 1,
            'moon_nakshatra': nak_name,
            'tithi_number': tithi_number,
            'paksha': paksha,
        }
        report['modules']['pancha_pakshi'] = pk_result
    except Exception as e:
        report['errors'].append(f"pancha-pakshi: {e}")

    try:
        # Rashi Tulya Navamsa（D1 与 D9 同宫对比分析）
        # v6.1.6: 对齐 rashi_tulya_navamsa.py 现有公共接口 analyze_rtn(chart_data)
        from rashi_tulya_navamsa import analyze_rtn
        varga_full = report['modules'].get('varga_full', {})
        d9_data = varga_full.get('D9_Navamsa', {})
        if d9_data:
            d9_planets = d9_data.get('planets') if isinstance(d9_data, dict) else None
            if not d9_planets and isinstance(d9_data, dict):
                d9_planets = {
                    pn: pd for pn, pd in d9_data.items()
                    if isinstance(pd, dict) and pn not in ('_meta', 'Ascendant') and 'sign' in pd
                }
            if d9_planets:
                rt_chart = {
                    'ascendant': chart.get('ascendant', {}),
                    'planets': planets,
                    'context': {'navamsa_planets': d9_planets},
                }
                rt_result = analyze_rtn(rt_chart)
                report['modules']['rashi_tulya_navamsa'] = {
                    'analysis': rt_result,
                    'summary': {
                        'strength_score': rt_result.get('strength_score'),
                        'weakness_score': rt_result.get('weakness_score'),
                        'exalted_cancelled_count': len(rt_result.get('exalted_cancelled', [])),
                        'debilitated_cancelled_count': len(rt_result.get('debilitated_cancelled', [])),
                    },
                }
            else:
                report['modules']['rashi_tulya_navamsa'] = {'note': 'D9 planet data incomplete, skip Rashi Tulya Navamsa'}
        else:
            report['modules']['rashi_tulya_navamsa'] = {'note': 'D9 data incomplete, skip Rashi Tulya Navamsa'}
    except Exception as e:
        report['errors'].append(f"rashi-tulya-navamsa: {e}")

    # ── Step 4.11: Marriage Counting + Muntha + D30 + Prashna (v6.0.16) ──
    try:
        # Marriage Counting Method (Bhrigu)
        from marriage_counting import marriage_counting_full_analysis
        d1_house7_lord = houses.get('7', {}).get('lord', '') if isinstance(houses.get('7'), dict) else ''
        if d1_house7_lord and 'varga_full' in report['modules']:
            d9_data = report['modules']['varga_full'].get('D9_Navamsa', {})
            d9_planet_lons = _varga_planet_lons(d9_data)
            if d9_planet_lons:
                mc_result = marriage_counting_full_analysis(
                    d1_house7_lord, planet_lons, d9_planet_lons,
                    houses, None
                )
                report['modules']['marriage_counting'] = mc_result
    except Exception as e:
        report['errors'].append(f"marriage-counting: {e}")

    try:
        # Bhrigu Pada Dasha（通用近似版，精确公式因流派而异）
        from bhrigu_pada_dasha import bhrigu_pada_dasha_full_report
        moon_lon = planet_lons.get('Moon', 0)
        birth_jd = report.get('metadata', {}).get('birth_jd', 0) or 0
        if moon_lon and birth_jd:
            bpd_result = bhrigu_pada_dasha_full_report(
                moon_lon, birth_jd,
                d9_7lord_sign=None  # 将在 D9 数据可用时补充
            )
            report['modules']['bhrigu_pada_dasha'] = bpd_result
    except Exception as e:
        report['errors'].append(f"bhrigu-pada-dasha: {e}")

    try:
        # Muntha (Tajika Varshaphala) — 需要 Varshaphala 盘数据
        # Varshaphala 盘需另外排盘（太阳返照时刻），full-reading 中暂不可用
        # 如需 Varshaphala 分析，请使用 cmd_prashna（独立命令支持 Varshaphala 排盘）
        report['modules']['muntha'] = {
            'note': 'Muntha 需要 Varshaphala（太阳返照）盘数据。请使用 cmd_prashna 独立命令获取 Varshaphala 分析。',
            'varshaphala_available': False
        }
    except Exception as e:
        report['errors'].append(f"muntha: {e}")

    try:
        # D30 Trimshamsa analysis
        from trimshamsa_d30 import d30_full_report
        d30_result = d30_full_report(planet_lons)
        report['modules']['trimshamsa_d30'] = d30_result
    except Exception as e:
        report['errors'].append(f"trimshamsa-d30: {e}")

    try:
        # Prashna（问事占星）—— full-reading 中暂不接入
        # 原因：Prashna 需要问卜时刻（用户提问时间）排盘，full-reading 只有出生数据
        # 如需 Prashna 分析：使用 cmd_prashna 独立命令
        # 该命令接受问卜时间 + 地点，排 Prashna 盘并做分析
        report['modules']['prashna'] = {
            'note': 'Prashna 需要问卜时间排盘，请使用 cmd_prashna 独立命令。',
            'cmd': 'cmd_prashna',
            'available': True
        }
    except Exception as e:
        report['errors'].append(f"prashna: {e}")

        # ── Step 4.12: Solar Return (Varshaphala) + Muntha proper (v6.0.18) ──
    try:
        # Solar Return（太阳返照盘）计算
        if hasattr(args, 'target_year') and args.target_year:
            from solar_return import solar_return_full_report
            sr_result = solar_return_full_report(
                args.year, args.month, args.day,
                args.hour, args.minute,
                args.lat, args.lon, args.tz,
                args.target_year,
                ayanamsa_name=_current_ayanamsa_name(args),
            )
            report['modules']['solar_return'] = sr_result
            # 更新 muntha 为正确值（来自太阳返照盘）
            if 'muntha' in sr_result:
                report['modules']['muntha'] = {
                    'source': 'solar_return_proper',
                    'muntha_sign': sr_result.get('muntha', {}).get('muntha_sign', '?'),
                    'muntha_lord': sr_result.get('muntha', {}).get('muntha_lord', '?'),
                    'note': '来自太阳返照盘的正确 Muntha 计算',
                }
        else:
            report['modules']['solar_return'] = {
                'note': '未提供 --target-year，跳过太阳返照盘计算',
                'skipped': True,
                'hint': '使用 --target-year <年份> 重新运行以获取 Varshaphala 分析'
            }
    except Exception as e:
        report['errors'].append(f"solar-return: {e}")

    # ── Step 4.13: Narayana Dasha（Rishi Dasha，v6.0.20）──
    try:
        from narayana_dasha import narayana_dasha_full_report
        # 计算当前年龄（从出生到 today）
        birth_dt = _birth_datetime_from_args(args)
        today_dt = datetime.strptime(args.today, '%Y-%m-%d') if hasattr(args, 'today') and args.today else datetime.now()
        current_age = (today_dt - birth_dt).days / 365.25
        narayana_result = narayana_dasha_full_report(
            lagna_sign_idx=asc_idx,
            planet_lons=planet_lons,
            current_age=current_age,
            birth_year=args.year,
        )
        report['modules']['narayana_dasha'] = narayana_result
    except Exception as e:
        report['errors'].append(f"narayana-dasha: {e}")
    _record_stage_timing(
        stage_timings,
        'dasha_and_core_varga_stack',
        stage_started,
        enabled=profile_stages,
        status='error' if any(err.startswith(('special-lagnas:', 'dasha:', 'yoga:', 'varga-full:', 'vimsopaka:', 'varga-extended:', 'dispositor-chain+inter-chart:', 'tajika-yogas+sahams:', 'yogas-doshas:', 'tithi-lord:', 'pancha-pakshi:', 'rashi-tulya-navamsa:', 'marriage-counting:', 'bhrigu-pada-dasha:', 'muntha:', 'trimshamsa-d30:', 'prashna:', 'solar-return:', 'narayana-dasha:')) for err in report['errors']) else 'ok',
        details={'through_step': '4.13'},
    )

    # ── Step 5: 精确相位 ──
    stage_started = time.perf_counter()
    try:
        from aspects import calc_all_aspects
        aspects_result = calc_all_aspects(planet_lons, asc_deg)
        report['modules']['aspects'] = aspects_result
    except Exception as e:
        report['errors'].append(f"aspects: {e}")

    # ── Step 6: Jaimini系统 ──
    try:
        from jaimini import (calc_chara_karaka_7, calc_chara_karaka_8, calc_chara_dasha,
                             calc_karakamsha, calc_chara_dasha_with_antardasha,
                             calc_arudha_padas, calc_graha_padas, calc_special_lagnas)
        from varga import calc_varga

        jaimini_result = {}
        jaimini_result['chara_karaka_7'] = calc_chara_karaka_7(planet_degs)
        jaimini_result['chara_karaka_8'] = calc_chara_karaka_8(planet_degs)

        # Step 6+: Karaka JH Compatible Mode (v4.4.0)
        try:
            from karaka_calculator import KarakaCalculator, KarakaMode
            kc_jh = KarakaCalculator(mode=KarakaMode.JH_COMPATIBLE)
            jaimini_result['chara_karaka_jh'] = kc_jh.calculate_karaka(planet_lons)
        except Exception as e:
            jaimini_result['chara_karaka_jh'] = {"error": str(e)}

        # 使用带 Antardasha 子周期的 Chara Dasha（v4.3.0；v6.1.12 KN Rao benchmark 通过）
        jaimini_result['chara_dasha'] = calc_chara_dasha_with_antardasha(asc_idx, planet_lons, args.year, args.month)
        jaimini_result['has_antardasha'] = True
        jaimini_result['chara_dasha_capability'] = {
            'status': 'covered',
            'reason': 'KN Rao benchmark overall match 95.83%; Aquarius/Scorpio co-lord strength arbitration remains a documented edge case.',
            'usage_rule': 'Use Chara Karaka/Karakamsha normally; use Chara Dasha timing with Vimshottari/Transit/Varga corroboration.'
        }

        # Karakamsha（用AK灵魂星，非DK配偶星）
        # ⚠️ 2026-05-03修正：此前错误使用DK，现已修正为AK
        ck7 = jaimini_result['chara_karaka_7']
        ak_name = ck7['karaka_table']['Atmakaraka']['planet']
        ak_lon = planet_lons.get(ak_name, 0)
        ak_d9 = calc_varga(ak_lon, 9)
        jaimini_result['karakamsha'] = calc_karakamsha(
            ak_d9.get('sign', 'Aries'), ak_d9.get('degree_in_sign', 0))
        jaimini_result['arudha_padas'] = calc_arudha_padas(asc_idx, planet_lons)
        jaimini_result['graha_padas'] = calc_graha_padas(planet_lons)
        jaimini_result['special_lagnas'] = calc_special_lagnas(asc_idx, args.hour, args.minute + _arg_second(args) / 60.0)

        # Darakaraka 深度解读（v6.1.10）
        # Registry 已将 modules.jaimini.darakaraka 标为 covered；这里把独立 DK
        # reader 接入 full-reading，使婚姻主题报告可消费真实 DK 画像、D9 状态、
        # 合相影响和质量评分，而不是只停留在 chara_karaka 表格层。
        try:
            from darakaraka_reader import analyze_darakaraka
            d9_planets_for_dk = {}
            varga_data = report['modules'].get('varga_full', {})
            d9_data = varga_data.get('D9_Navamsa', {}) if isinstance(varga_data, dict) else {}
            d9_asc = d9_data.get('Ascendant', {}) if isinstance(d9_data, dict) else {}
            d9_asc_idx = SIGNS.index(d9_asc.get('sign', 'Aries')) if isinstance(d9_asc, dict) and d9_asc.get('sign') in SIGNS else 0
            d9_context = _build_dignity_context(d9_data)
            if isinstance(d9_data, dict):
                for d9_pn, d9_pd in d9_data.items():
                    if d9_pn == '_meta' or d9_pn == 'Ascendant' or not isinstance(d9_pd, dict) or 'sign' not in d9_pd:
                        continue
                    d9_sign = d9_pd.get('sign')
                    d9_deg = d9_pd.get('degree_in_sign', d9_pd.get('degree', 0) % 30)
                    d9_sign_idx = SIGNS.index(d9_sign) if d9_sign in SIGNS else 0
                    d9_planets_for_dk[d9_pn] = {
                        'sign': d9_sign,
                        'house': ((d9_sign_idx - d9_asc_idx) % 12) + 1,
                        'degree_in_sign': d9_deg,
                        'dignity': _get_dignity_level(d9_pn, d9_sign, d9_deg, d9_context),
                    }
            jaimini_result['darakaraka'] = analyze_darakaraka({
                'ascendant': chart.get('ascendant', {}),
                'planets': planets,
                'context': {'navamsa_planets': d9_planets_for_dk},
            }, use_8_karaka=True)
        except Exception as dk_e:
            jaimini_result['darakaraka'] = {'error': str(dk_e)}

        report['modules']['jaimini'] = jaimini_result
    except Exception as e:
        report['errors'].append(f"jaimini: {e}")

    # ── Step 7: 高级Nakshatra（v6.0.22 升级：含 Chandra Bala + 综合报告）──
    try:
        from nakshatra_advanced import nakshatra_full_report as nakshatra_report
        nak_full = nakshatra_report(chart)
        report['modules']['nakshatra_advanced'] = nak_full
    except Exception as e:
        report['errors'].append(f"nakshatra-adv: {e}")

    # ── Step 7.5: Nakshatra Dasha 星宿大运（v6.0.22 新增）──
    try:
        from nakshatra_dasha import nakshatra_dasha_full_report

        birth_date_str = f"{args.year}-{args.month:02d}-{args.day:02d}"
        # 年龄
        nak_age = args.age
        if nak_age is None:
            try:
                birth_date = datetime(args.year, args.month, args.day)
                nak_age = (datetime.now() - birth_date).days / 365.25
            except:
                nak_age = None

        if nak_age is not None:
            # 获取过境星宿数据
            transit_lons_for_nak = None
            try:
                transit_ref = getattr(args, 'transit_date', None) or datetime.now().strftime('%Y-%m-%d')
                ty, tm, td = map(int, transit_ref.split('-'))
                transit_jd_nak = swe.julday(ty, tm, td, 12.0 - args.tz)
                transit_pl_nak, _ = _calc_sidereal_planets_for_jd(
                    transit_jd_nak, node_mode=getattr(args, 'node_mode', 'mean'), include_ketu=True)
                transit_lons_for_nak = {}
                for pn, pd in transit_pl_nak.items():
                    if isinstance(pd, dict) and 'degree' in pd:
                        transit_lons_for_nak[pn] = pd['degree']
            except:
                pass

            nak_dasha = nakshatra_dasha_full_report(
                chart, birth_date_str, nak_age, transit_lons_for_nak)
            report['modules']['nakshatra_dasha'] = nak_dasha
    except Exception as e:
        report['errors'].append(f"nakshatra-dasha: {e}")

    # ── Step 8: Argala门闩 ──
    try:
        from argala import calc_argala
        report['modules']['argala'] = calc_argala(planet_sign_indices, asc_idx)
    except Exception as e:
        report['errors'].append(f"argala: {e}")

    # ── Step 9: Tajika年运盘（需要年龄） ──
    age = args.age
    if age is None:
        # 自动计算年龄
        try:
            birth_date = datetime(args.year, args.month, args.day)
            age = (datetime.now() - birth_date).days // 365
            report['warnings'].append(f"未提供年龄，自动计算为 {age} 岁")
        except:
            age = None

    if age is not None:
        try:
            from tajika import calc_muntha, calc_year_lord, calc_mudda_dasha, calc_tri_pataka
            asc_si = int(asc_deg / 30) % 12
            tajika_result = {}
            tajika_result['muntha'] = calc_muntha(asc_si, age)
            yl = calc_year_lord(asc_si, age)
            tajika_result['year_lord'] = yl
            varsha_lord = yl.get('year_lord', 'Jupiter')
            tajika_result['mudda_dasha'] = calc_mudda_dasha(asc_si, varsha_lord, args.month)
            muntha_si = (asc_si + age) % 12
            tajika_result['tri_pataka'] = calc_tri_pataka(planet_lons, varsha_lord, muntha_si)
            report['modules']['tajika'] = tajika_result
        except Exception as e:
            report['errors'].append(f"tajika: {e}")

    # ── Step 10: Shadbala六重力量 ──
    try:
        from shadbala import calc_shadbala
        birth_hour = _birth_hour_decimal(args.hour, args.minute, _arg_second(args))
        sun_lon = planet_lons.get('Sun', 0)
        moon_lon = planet_lons.get('Moon', 0)
        shadbala_result = calc_shadbala(planets, asc_sign, birth_hour, sun_lon, moon_lon, context=context)
        # 添加顶层汇总
        if isinstance(shadbala_result, dict):
            sb_planets = shadbala_result.get('planets', {})
            total_rupas = 0
            min_req_total = 0
            strong_count = 0
            for pn, pdata in sb_planets.items():
                if isinstance(pdata, dict):
                    total_rupas += pdata.get('total_rupas', 0)
                    min_req_total += pdata.get('min_required', 0)
                    if pdata.get('total_rupas', 0) >= pdata.get('min_required', 0):
                        strong_count += 1
            shadbala_result['total_shadbala'] = round(total_rupas, 2)
            shadbala_result['total_min_required'] = round(min_req_total, 2)
            shadbala_result['strong_planets'] = strong_count
            shadbala_result['weak_planets'] = len(sb_planets) - strong_count
            shadbala_result['status'] = '优秀' if strong_count >= 5 else '良好' if strong_count >= 3 else '一般'
        report['modules']['shadbala'] = shadbala_result
    except Exception as e:
        report['errors'].append(f"shadbala: {e}")

    # ── Step 10.1: Remedies 补救建议 ──
    try:
        from remedies import recommend_remedies
        shadbala_for_remedies = {}
        for pn, pdata in (report['modules'].get('shadbala') or {}).get('planets', {}).items():
            if isinstance(pdata, dict):
                shadbala_for_remedies[pn] = {
                    'total_rupas': pdata.get('total_rupas', pdata.get('rupas', 1.0)),
                    'strength_level': pdata.get('strength_level', pdata.get('level', '')),
                }
        yd = report['modules'].get('yogas_doshas') or {}
        doshas = []
        dosha_sources = [
            ('mangal_dosha', 'Mangal Dosha'),
            ('kaal_sarp_dosha', 'Kaal Sarp Dosha'),
            ('pitra_dosha', 'Pitra Dosha'),
        ]
        for key, label in dosha_sources:
            item = yd.get(key) if isinstance(yd, dict) else None
            if isinstance(item, dict) and item.get('has_dosha'):
                doshas.append(label)
        dasha = report['modules'].get('dasha') or {}
        current_dasha = dasha.get('current_dasha') if isinstance(dasha, dict) else {}
        active_dasha_lord = current_dasha.get('lord') if isinstance(current_dasha, dict) else None
        report['modules']['remedies'] = recommend_remedies(
            shadbala_for_remedies,
            active_dasha_lord=active_dasha_lord,
            doshas=doshas,
        )
    except Exception as e:
        report['errors'].append(f"remedies: {e}")

    # ── Step 10.5: Avasthas 行星状态 (v4.4.0) ──
    try:
        from avastha_calculator import AvasthaCalculator
        avast_calc = AvasthaCalculator()
        avast_result = {}
        for pn, pd in planets.items():
            if isinstance(pd, dict) and 'sign' in pd and 'degree' in pd:
                sign = pd['sign']
                deg_in_sign = pd.get('degree_in_sign', pd['degree'] % 30)
                house = pd.get('house', 0)
                # 收集同宫行星作为 conjunctions
                conjunctions = [p2 for p2, pd2 in planets.items()
                               if isinstance(pd2, dict) and pd2.get('house') == house and p2 != pn]
                avast_result[pn] = avast_calc.calculate_all_avasthas(
                    planet=pn, sign=sign, degree=deg_in_sign,
                    house=house, conjunctions=conjunctions)
        report['modules']['avasthas'] = avast_result
    except Exception as e:
        report['errors'].append(f"avasthas: {e}")

    # ── Step 11: Ashtakavarga八分法 ──
    asht_data = None
    try:
        from ashtakavarga import calc_ashtakavarga
        asht_data = calc_ashtakavarga(planets, asc_idx)
        report['modules']['ashtakavarga'] = asht_data
    except Exception as e:
        report['errors'].append(f"ashtakavarga: {e}")

    # ── Step 12: R1-R10数学验证 ──
    try:
        from validate import validate_chart
        report['modules']['validation'] = validate_chart(chart, asht_data)
    except Exception as e:
        report['errors'].append(f"validate: {e}")

    # ── Step 13: P1-P12行星审计 ──
    try:
        audit_result = cmd_audit(args)
        report['modules']['audit'] = audit_result
    except Exception as e:
        report['errors'].append(f"audit: {e}")

    # ── Step 14: ⭐ Transit Actionable Context (v4.1.0) ──
    try:
        actionable_ctx = _calc_actionable_context(planets, asc_idx)
        report['modules']['actionable_context'] = actionable_ctx
    except Exception as e:
        report['errors'].append(f"actionable-context: {e}")

    # ── Step 15: Planetary Congregation 行星聚集 (v4.3.0) ──
    try:
        congregation = _calc_planetary_congregation(planets, asc_idx)
        report['modules']['congregation'] = congregation
    except Exception as e:
        report['errors'].append(f"congregation: {e}")

    # ── Step 16: Vivah Saham 婚姻敏感点 (v4.3.0) ──
    try:
        sahams = _calc_vivah_saham(planets, asc_deg)
        # 包装为标准结构，与 standalone vivah-saham 子命令一致
        if 'error' not in sahams:
            report['modules']['vivah_saham'] = {
                'vivah_saham': {
                    'longitude': sahams['saham_lon'],
                    'sign': sahams['saham_sign'],
                    'degree_in_sign': sahams['saham_deg_in_sign'],
                    'house': sahams['saham_house'],
                },
                **sahams
            }
        else:
            report['modules']['vivah_saham'] = sahams
    except Exception as e:
        report['errors'].append(f"vivah-saham: {e}")

    # ── Step 17: Transit 多参考点分析 (v6.0.10 true transit) ──
    try:
        transit_reference_date = getattr(args, 'transit_date', None) or getattr(args, 'today', None) or datetime.now().strftime('%Y-%m-%d')
        ty, tm, td = map(int, transit_reference_date.split('-'))
        transit_jd = swe.julday(ty, tm, td, 12.0 - args.tz)
        transit_planets, transit_ayanamsa = _calc_sidereal_planets_for_jd(transit_jd, node_mode=getattr(args, 'node_mode', 'mean'), include_ketu=True)
        report['modules']['transit_positions'] = {
            'method': 'Swiss Ephemeris true transit positions',
            'target_date': transit_reference_date,
            'ayanamsa': round(transit_ayanamsa, 4) if transit_ayanamsa is not None else None,
            'node_mode': getattr(args, 'node_mode', 'mean'),
            'data_layer': 'true_transit_positions',
            'planets': transit_planets,
        }
        transit_multi = _calc_transit_multi_reference(planets, asc_idx, asc_deg, planet_lons, transit_planets=transit_planets, transit_date=transit_reference_date, node_mode=getattr(args, 'node_mode', 'mean'))
        report['modules']['transit_multi_reference'] = transit_multi
    except Exception as e:
        report['errors'].append(f"transit-multi-ref: {e}")

    # ── Step 18: Dasa Convergence 多系统交叉验证 (v6.1.6) ──
    try:
        dasha_data = report['modules'].get('dasha', {})
        jaimini_data = report['modules'].get('jaimini', {})
        chara_dasha_data = jaimini_data.get('chara_dasha', {}) if isinstance(jaimini_data, dict) else {}
        moon_lon = planet_lons.get('Moon', 0)
        moon_nakshatra_index = int(moon_lon / (360 / 27)) % 27
        moon_pada = int((moon_lon % (360 / 27)) / (360 / 108)) + 1
        tithi_number = int(((moon_lon - planet_lons.get('Sun', 0)) % 360) / 12) + 1
        birth_info_for_alt_dasha = {
            'birth_datetime': _birth_datetime_from_args(args),
            'moon_nakshatra_index': moon_nakshatra_index,
            'moon_pada': moon_pada,
            'is_shukla_paksha': 1 <= tithi_number <= 15,
            'lagna_rashi_index': asc_idx,
        }

        try:
            from yogini_dasha import calculate_yogini_dasha
            yogini_data = calculate_yogini_dasha(birth_info_for_alt_dasha)
            report['modules']['yogini_dasha'] = yogini_data
        except Exception as alt_e:
            yogini_data = {'error': str(alt_e)}
            report['modules']['yogini_dasha'] = yogini_data

        try:
            from ashtottari_dasha import calculate_ashtottari_dasha
            ashtottari_data = calculate_ashtottari_dasha(birth_info_for_alt_dasha)
            report['modules']['ashtottari_dasha'] = ashtottari_data
        except Exception as alt_e:
            ashtottari_data = {'error': str(alt_e)}
            report['modules']['ashtottari_dasha'] = ashtottari_data

        try:
            from kalachakra_dasha import calculate_kalachakra_dasha
            kalachakra_data = calculate_kalachakra_dasha(birth_info_for_alt_dasha)
            report['modules']['kalachakra_dasha'] = kalachakra_data
        except Exception as alt_e:
            kalachakra_data = {'error': str(alt_e)}
            report['modules']['kalachakra_dasha'] = kalachakra_data

        convergence = _calc_dasa_convergence(
            dasha_data,
            chara_dasha_data,
            yogini_data,
            planet_lons,
            asc_idx,
            ashtottari_result=ashtottari_data,
            kalachakra_result=kalachakra_data,
        )
        report['modules']['dasa_convergence'] = convergence
    except Exception as e:
        report['errors'].append(f"dasa-convergence: {e}")

    # ── Step 19: D9 Navamsa 逐行星尊严展开 (v4.5.0 P1) ──
    try:
        varga_data = report['modules'].get('varga_full', {})
        d9_data = varga_data.get('D9_Navamsa', {}) if isinstance(varga_data, dict) else {}
        if d9_data:
            d9_expanded = {}
            d9_context = _build_dignity_context(d9_data)
            for pn, pd in d9_data.items():
                if pn == '_meta' or not isinstance(pd, dict) or 'sign' not in pd:
                    continue
                d9_sign = pd['sign']
                d9_deg = pd.get('degree_in_sign', pd.get('degree', 0) % 30)
                dignity = _get_dignity_level(pn, d9_sign, d9_deg, d9_context)
                # D9 宫位（从D9 Asc计算）
                d9_asc_data = d9_data.get('Ascendant', {})
                d9_asc_sign_idx = SIGNS.index(d9_asc_data.get('sign', 'Aries')) if isinstance(d9_asc_data, dict) and d9_asc_data.get('sign') in SIGNS else 0
                p_sign_idx = SIGNS.index(d9_sign) if d9_sign in SIGNS else 0
                d9_house = ((p_sign_idx - d9_asc_sign_idx) % 12) + 1
                # 关系状态
                d9_sign_lord = SIGN_LORDS.get(d9_sign, '')
                is_own = (d9_sign_lord == pn)
                is_exalted = (EXALTATION.get(pn) == d9_sign)
                is_debilitated = (DEBILITATION.get(pn) == d9_sign)
                is_moola = False
                if pn in MOOLATRIKONA:
                    mt_sign, mt_start, mt_end = MOOLATRIKONA[pn]
                    if mt_sign == d9_sign and mt_start <= d9_deg < mt_end:
                        is_moola = True
                d9_expanded[pn] = {
                    'sign': d9_sign,
                    'sign_cn': SIGNS_CN.get(d9_sign, ''),
                    'house_in_d9': d9_house,
                    'dignity': dignity,
                    'is_own_sign': is_own,
                    'is_exalted': is_exalted,
                    'is_debilitated': is_debilitated,
                    'is_moolatrikona': is_moola,
                    'pada': pd.get('pada'),
                    'lord': d9_sign_lord,
                    'degree_in_sign': round(d9_deg, 4),
                }
            report['modules']['d9_navamsa_expanded'] = d9_expanded
    except Exception as e:
        report['errors'].append(f"d9-expanded: {e}")
    _record_stage_timing(
        stage_timings,
        'advanced_interpretation_and_timing_layers',
        stage_started,
        enabled=profile_stages,
        status='error' if any(err.startswith(('aspects:', 'jaimini:', 'nakshatra-adv:', 'nakshatra-dasha:', 'argala:', 'tajika:', 'shadbala:', 'remedies:', 'avasthas:', 'ashtakavarga:', 'validate:', 'audit:', 'actionable-context:', 'congregation:', 'vivah-saham:', 'transit-multi-ref:', 'dasa-convergence:', 'd9-expanded:')) for err in report['errors']) else 'ok',
        details={'through_step': '19'},
    )

    # ── 汇总 ──
    stage_started = time.perf_counter()
    # ── 生成动态引导 (Dynamic Hooks) ──
    try:
        report['dynamic_hooks'] = generate_life_stage_hooks(
            planets=report['modules'].get('chart', {}).get('planets', {}),
            asc_sign=report['modules'].get('chart', {}).get('ascendant', {}).get('sign', ''),
            asc_idx=report['modules'].get('chart', {}).get('ascendant', {}).get('sign_idx', 0),
            current_dasha=report['modules'].get('dasha', {}).get('current_dasha', {}),
            narayana_dasha=report['modules'].get('narayana_dasha', {})
        )
    except Exception as e:
        report['dynamic_hooks'] = []
        report['errors'].append(f"hook_engine: {e}")
    _record_stage_timing(
        stage_timings,
        'dynamic_hooks',
        stage_started,
        enabled=profile_stages,
        status='error' if any(err.startswith('hook_engine:') for err in report['errors']) else 'ok',
    )

    report['summary'] = {}

    stage_started = time.perf_counter()
    try:
        _attach_vedastro_official_full_snapshot(report, args)
    except Exception as e:
        report['warnings'].append(f"vedastro-official-full-snapshot: {e}")
    _record_stage_timing(
        stage_timings,
        'vedastro_official_snapshot',
        stage_started,
        enabled=profile_stages,
        status='warning' if any(warn.startswith('vedastro-official-full-snapshot:') for warn in report['warnings']) else 'ok',
    )

    stage_started = time.perf_counter()
    try:
        _attach_vedastro_main_entry_overview(report, args)
    except Exception as e:
        report['warnings'].append(f"vedastro-main-entry-overview: {e}")
    _record_stage_timing(
        stage_timings,
        'vedastro_main_entry_overview',
        stage_started,
        enabled=profile_stages,
        status='warning' if any(warn.startswith('vedastro-main-entry-overview:') for warn in report['warnings']) else 'ok',
    )

    stage_started = time.perf_counter()
    try:
        strict_evidence_collector = _load_strict_evidence_collector()
        for route in ('relationship', 'career', 'finance'):
            module_name = STRICT_WORKFLOW_MODULE_MAP[route]
            report['modules'][module_name] = strict_evidence_collector(route, report)
        report['modules']['career_strict_evidence']['user_narrative'] = _build_career_narrative_payload(
            report['modules']['career_strict_evidence']
        )
        report['modules']['relationship_strict_evidence']['user_narrative'] = _build_relationship_narrative_payload(
            report['modules']['relationship_strict_evidence']
        )
        report['modules']['finance_strict_evidence']['user_narrative'] = _build_finance_narrative_payload(
            report['modules']['finance_strict_evidence']
        )
    except Exception as e:
        report['errors'].append(f"strict-evidence-collector: {e}")
    _record_stage_timing(
        stage_timings,
        'strict_contracts',
        stage_started,
        enabled=profile_stages,
        status='error' if any(err.startswith('strict-evidence-collector:') for err in report['errors']) else 'ok',
    )

    stage_started = time.perf_counter()
    try:
        report['modules']['guided_topics'] = build_guided_topics(report)
    except Exception as e:
        report['warnings'].append(f"guided-topics: {e}")
        report['modules']['guided_topics'] = []
    _record_stage_timing(
        stage_timings,
        'guided_topics',
        stage_started,
        enabled=profile_stages,
        status='warning' if any(warn.startswith('guided-topics:') for warn in report['warnings']) else 'ok',
    )

    stage_started = time.perf_counter()
    report['ai_prompt_pack'] = _build_ai_prompt_pack(report)
    _record_stage_timing(
        stage_timings,
        'ai_prompt_pack',
        stage_started,
        enabled=profile_stages,
    )

    elapsed = round(time.perf_counter() - t0, 4)
    module_count = len(report['modules'])
    error_count = len(report['errors'])
    slowest_stages = sorted(stage_timings, key=lambda item: item.get('elapsed_seconds', 0), reverse=True)[:5]
    unified_stage_contract = _build_unified_stage_contract(stage_timings)
    report['summary'] = {
        'elapsed_seconds': elapsed,
        'modules_computed': module_count,
        'errors': error_count,
        'status': 'complete' if error_count == 0 else f'{error_count} errors',
        'stage_timing_enabled': True,
        'stage_timings': stage_timings,
        'slowest_stages': slowest_stages,
        'guided_topics': report['modules'].get('guided_topics', []),
        **unified_stage_contract,
        'next_step': '⭐ v6.1.6: full-reading 已输出 transit_multi_reference(四参考点) + dasa_convergence(五系统交叉) + yogini_dasha + ashtottari_dasha + kalachakra_dasha + d9_navamsa_expanded。AI必须使用四参考点分析Transit，Dasa预测必须标注多系统收敛等级。',
    }

    return report


# ============================================================================
# 23. Prashna 问事占星 (v3.9新增)
# ============================================================================
def cmd_prashna(args):
    """Prashna 问事占星：基于提问时刻的即时星盘分析"""
    try:
        from prashna_context import PrashnaContextError, build_prashna_context
    except ImportError:
        from scripts.prashna_context import PrashnaContextError, build_prashna_context
    try:
        context = build_prashna_context({
            "question_text": args.question_text,
            "question_timestamp": args.datetime,
            "lat": args.lat,
            "lon": args.lon,
            "timezone": args.timezone,
            "ayanamsa": args.ayanamsa,
            "node_mode": args.node_mode,
            "location_convention": args.location_convention,
        })
    except PrashnaContextError as exc:
        return {"scope": "prashna_context", "status": "blocked", "reason": str(exc)}
    if args.mode != "chart":
        return {
            "scope": "prashna",
            "status": "blocked",
            "reason": f"{args.mode} is blocked pending validated Prashna kernel implementation",
            "prashna_context": context,
        }
    return context


# ============================================================================
# Sudarshana Chakra (v6.9.14新增)
# ============================================================================
def cmd_sudarshana(args):
    """Sudarshana Chakra 三参考点盘分析"""
    chart, asc_idx, jd, ayanamsa = _compute_chart_from_args(args)
    if chart is None:
        return {"error": "swisseph未安装"}

    # 构造 planet_lons 和 asc_lon
    planet_lons = {}
    for pname, pdata in chart.get('planets', {}).items():
        if isinstance(pdata, dict) and 'degree_raw' in pdata:
            planet_lons[pname] = pdata['degree_raw']

    asc_data = chart.get('ascendant', {})
    asc_lon = asc_data.get('degree_raw', asc_data.get('degree', 0))
    if asc_lon == 0:
        asc_lon = asc_idx * 30.0

    house = getattr(args, 'house', None)
    if getattr(args, 'text', False):
        report = generate_sudarshana_report(planet_lons, asc_lon)
        print(report)
        return {"format": "text", "report_printed": True}

    return calc_sudarshana_chakra(planet_lons, asc_lon, house=house)


# ============================================================================
# CLI入口
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description='印度占星统一引擎 v6.9.14', formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', help='子命令')

    # 1. chart
    p = sub.add_parser('chart', help='计算完整星盘')
    _add_chart_args(p)
    p.add_argument('--validate', action='store_true', help='附加R1-R10数学验证')
    p.add_argument('--table', action='store_true', help='以 ASCII 表格输出核心排盘结果')

    # 2. dasha
    p = sub.add_parser('dasha', help='计算Dasha大运')
    # Birth datetime args: required only when nakshatra/moon-lon not provided
    p.add_argument('--year', type=int, required=False)
    p.add_argument('--month', type=int, required=False)
    p.add_argument('--day', type=int, required=False)
    p.add_argument('--hour', type=int, required=False)
    p.add_argument('--minute', type=int, required=False)
    p.add_argument('--second', type=_second_arg, default=0)
    p.add_argument('--lat', type=float, required=False)
    p.add_argument('--lon', type=float, required=False)
    p.add_argument('--tz', type=float, default=None)
    p.add_argument('--node-mode', default='mean', choices=['mean', 'true'])
    p.add_argument('--ayanamsa', default='lahiri', choices=list(AYANAMSA_MODES.keys()),
                   help='恒星黄道系统（默认lahiri）。可选: raman, kp, fagan_bradley, djwhal_khul, sassanian, true_citra')
    p.add_argument('--nakshatra', default=None); p.add_argument('--pada', type=int, default=None)
    p.add_argument('--moon-lon', type=float, default=None); p.add_argument('--birthdate', default=None)
    p.add_argument('--today', default=None)
    p.add_argument('--years', type=int, default=10)
    p.add_argument('--table', action='store_true', help='以 ASCII 表格输出大运主时间线')

    # 3. yoga
    p = sub.add_parser('yoga', help='Yoga格局识别')
    _add_chart_args(p)
    p.add_argument('--ascendant', default=None)
    p.add_argument('--planets', default=None, help="格式: 'Sun:Aries:9[:10.5],Moon:Aquarius:7[:15.2],...'；若提供则优先使用并忽略出生信息")
    p.add_argument('--context-json', default=None, help='可选：传入包含 d9/d60/panchanga 的 YogaContext JSON')
    for action in p._actions:
        if action.dest in ['year', 'month', 'day', 'hour', 'minute', 'lat', 'lon']:
            action.required = False

    # 4. predict
    p = sub.add_parser('predict', help='三层验证法事件预测')
    p.add_argument('--chart', default=None, help='星盘JSON字符串')
    p.add_argument('--event-type', default='all', choices=['all', 'marriage', 'career', 'wealth', 'health'])
    p.add_argument('--past-verify', action='store_true', help='验前事模式：推断2-4个高信号历史时段')
    p.add_argument('--year', type=int, default=None, help='出生年（验前事模式需要）')
    p.add_argument('--month', type=int, default=None, help='出生月')
    p.add_argument('--day', type=int, default=None, help='出生日')
    p.add_argument('--hour', type=int, default=None, help='出生时')
    p.add_argument('--minute', type=int, default=None, help='出生分')
    p.add_argument('--second', type=_second_arg, default=0, help='出生秒')
    p.add_argument('--lat', type=float, default=None, help='纬度')
    p.add_argument('--lon', type=float, default=None, help='经度')
    p.add_argument('--tz', type=float, default=None, help='时区')

    # 5. varga
    p = sub.add_parser('varga', help='分盘计算')
    _add_chart_args(p)
    p.add_argument('--d9', action='store_true'); p.add_argument('--d10', action='store_true')
    p.add_argument('--all', action='store_true')

    # 6. celebrity
    p = sub.add_parser('celebrity', help='名人案例查询')
    p.add_argument('--name', default=None); p.add_argument('--limit', type=int, default=20)

    # 7. db-stats
    sub.add_parser('db-stats', help='验证数据库统计')

    # 8. transit
    p = sub.add_parser('transit', help='行星过境查询（Swiss Ephemeris实时计算）')
    p.add_argument('--year', type=int, required=True); p.add_argument('--month', type=int, required=True)
    p.add_argument('--day', type=int, default=15, help='指定日期（默认15日取月中代表）')
    p.add_argument('--planet', default=None, help='目标行星，逗号分隔（默认全部，如：Jupiter,Saturn）')
    p.add_argument('--tz', type=float, default=None, help='时区')
    p.add_argument('--node-mode', default='mean', choices=['mean', 'true'], help='Rahu/Ketu节点口径：mean=Mean Node（默认），true=True Node')

    # 9. shadbala (v3.4新增)
    p = sub.add_parser('shadbala', help='Shadbala六重力量计算（covered；外部绝对值校准前保留置信度上限）')
    _add_chart_args(p)
    p.add_argument('--table', action='store_true', help='以 ASCII 表格输出七曜力量汇总')

    # 10. ashtakavarga (v3.4新增)
    p = sub.add_parser('ashtakavarga', help='Ashtakavarga八分法计算')
    _add_chart_args(p)
    p.add_argument('--table', action='store_true', help='以 ASCII 表格输出 SAV 总表与 BAV 校验')

    # 10b. kp (v6.9.10新增)
    p = sub.add_parser('kp', help='KP Krishnamurti Paddhati 完整分析（Sublord+SubSub+ABCD Significator）')
    _add_chart_args(p)

    # 10c. ashtakoot (v6.9.12新增)
    p = sub.add_parser('ashtakoot', help='Ashtakoot 36点合婚 + Kuja Dosha 火星凶相分析')
    # 男方参数
    for prefix in ['m_', 'f_']:
        label = '男方' if prefix == 'm_' else '女方'
        p.add_argument(f'--{prefix}year', type=int, required=True, help=f'{label}出生年')
        p.add_argument(f'--{prefix}month', type=int, required=True, help=f'{label}出生月')
        p.add_argument(f'--{prefix}day', type=int, required=True, help=f'{label}出生日')
        p.add_argument(f'--{prefix}hour', type=int, required=True, help=f'{label}出生时')
        p.add_argument(f'--{prefix}minute', type=int, required=True, help=f'{label}出生分')
        p.add_argument(f'--{prefix}lat', type=float, required=True, help=f'{label}出生纬度')
        p.add_argument(f'--{prefix}lon', type=float, required=True, help=f'{label}出生经度')
        p.add_argument(f'--{prefix}tz', type=float, default=0, help=f'{label}时区')
    p.add_argument('--node-mode', default='mean', choices=['mean', 'true'])
    p.add_argument('--table', action='store_true', help='以 ASCII 表格输出 8 Kuta 分数和总分')

    # 11. memory (v3.4新增)
    p = sub.add_parser('memory', help='Hermes记忆系统')
    p.add_argument('--action', default='stats', choices=['store', 'search', 'context', 'stats'])
    p.add_argument('--content', default=None, help='存储内容（store操作必填）')
    p.add_argument('--query', default=None, help='搜索查询（search操作必填）')
    p.add_argument('--tags', default=None, help='标签，逗号分隔')
    p.add_argument('--importance', type=int, default=5, help='重要性 1-10')
    p.add_argument('--limit', type=int, default=10, help='搜索结果数量')

    # 12. validate (v3.5新增)
    p = sub.add_parser('validate', help='R1-R10数学验证')
    _add_chart_args(p)

    # 13. audit (v3.5新增)
    p = sub.add_parser('audit', help='P1-P12行星审计管线')
    _add_chart_args(p)

    # 14. report (v3.6新增)
    p = sub.add_parser('report', help='MD→HTML报告生成（羊皮纸主题）')
    p.add_argument('folder', help='包含MD文件的目录路径')
    p.add_argument('--name', default='Client', help='客户姓名')
    p.add_argument('--lagna', default='—', help='上升星座')
    p.add_argument('--gender', default='—', help='性别')
    p.add_argument('--status', default='—', help='当前状态')
    p.add_argument('--lang', default='cn', choices=['cn', 'en'], help='语言 (默认cn)')
    p.add_argument('--output', default=None, help='输出HTML路径')

    # 15. varga-full (v3.7新增 → v6.9.12 扩展变体/复合/自定义D-N)
    p = sub.add_parser('varga-full', help='BPHS十六分盘+变体+复合+自定义D-N(2-300)')
    _add_chart_args(p)
    p.add_argument('--divisions', default=None, help='指定分盘，逗号分隔(如 D2,D9,D60)，空=全部')
    p.add_argument('--variant', default=None,
                   help='D2/D3变体名称。D2: parashara/pariveshta/parivritta/parivritta_trayodamsa/surya_chandra/ahoratra; D3: parashara/parivritta_trayodamsa/somaja/khara')
    p.add_argument('--custom', type=int, default=None,
                   help='自定义D-N分盘，N=2-300（如 --custom 150）')
    p.add_argument('--composite', default=None,
                   help='复合分盘D-m×n，逗号分隔两个整数（如 --composite 9,12 = D108）')

    # 16. aspects (v3.7新增)
    p = sub.add_parser('aspects', help='度数精确相位系统')
    _add_chart_args(p)

    # 17. jaimini (v3.7新增)
    p = sub.add_parser('jaimini', help='Jaimini系统（Chara Karaka/Dasha/Karakamsha/Arudha/Special Lagnas）')
    _add_chart_args(p)
    p.add_argument('--mode', default='all', choices=['all','karaka','dasha','karakamsha','arudha','special'], help='分析模式')
    p.add_argument('--antardasha', action='store_true', help='Chara Dasha含Antardasha子周期（covered；仍需多系统确认）')

    # 18. nakshatra-adv (v3.7新增 → v6.0.22 升级)
    p = sub.add_parser('nakshatra-adv', help='高级Nakshatra分析（Tara/Chandra/Sub-Lord/综合）')
    _add_chart_args(p)
    p.add_argument('--mode', default='all',
                   choices=['all','detail','tara','chandra','combined','sublord','full'],
                   help='分析模式')

    # 18.5 nakshatra-dasha (v6.0.22新增)
    p = sub.add_parser('nakshatra-dasha', help='星宿大运推演（Ashtottari / Vimshottari Nakshatra-level / Transit Overlay）')
    _add_chart_args(p)
    p.add_argument('--age', type=float, default=None, help='当前年龄（自动计算如果不提供）')
    p.add_argument('--mode', default='all',
                   choices=['all','ashtottari','vimshottari','overlay'],
                   help='分析模式')
    p.add_argument('--transit-date', default=None, help='过境日期 YYYY-MM-DD（overlay/all模式，默认今天）')

    # 18.6 nakshatra-full (v6.0.22新增)
    p = sub.add_parser('nakshatra-full', help='综合星宿完整报告（本命 + 大运 + 过境）')
    _add_chart_args(p)
    p.add_argument('--age', type=float, default=None, help='当前年龄')
    p.add_argument('--transit-date', default=None, help='过境日期 YYYY-MM-DD（默认今天）')

    # 19. argala (v3.7新增)
    p = sub.add_parser('argala', help='Argala门闩系统')
    _add_chart_args(p)

    # 20. tajika (v3.7新增)
    p = sub.add_parser('tajika', help='Tajika/Varshaphala年运盘')
    _add_chart_args(p)
    p.add_argument('--age', type=int, required=True, help='当前年龄')
    p.add_argument('--mode', default='all', choices=['all','muntha','yearlord','mudda','tripataka'], help='分析模式')

    # 21.5 solar-return (v6.0.18新增)
    p = sub.add_parser('solar-return', help='太阳返照盘 Varshaphala 年运分析')
    _add_chart_args(p)
    p.add_argument('--target-year', type=int, required=True, help='目标年份（计算该年太阳返照）')

    # 21.6 narayana-dasha (v6.0.20新增)
    p = sub.add_parser('narayana-dasha', help='Narayana Dasha（Rishi Dasha）星座大运分析')
    _add_chart_args(p)
    p.add_argument('--age', type=float, default=None, help='当前年龄（用于定位大运位置）')

    # 21.7 muhurta (v6.0.21新增)
    p = sub.add_parser('muhurta', help='Muhurta 择时分析（Panchanga 五要素）')
    p.add_argument('--date', default=None, help='查询日期 YYYY-MM-DD（默认今天）')
    p.add_argument('--activity', default=None,
                   choices=['marriage', 'business', 'travel', 'medical', 'education'],
                   help='指定活动类型（默认检查所有）')
    p.add_argument('--scan-days', type=int, default=1, help='扫描天数（默认1天，最多30天）')
    p.add_argument('--hour-from-sunrise', type=float, default=6.0,
                   help='从日出起算的小时数（默认6h约正午）')

    # 21. synastry (v3.7新增)
    p = sub.add_parser('synastry', help='合盘分析（Ashta Koota 36分制）')
    p.add_argument('--moon1', type=float, required=True, help='Person1月亮黄经')
    p.add_argument('--moon2', type=float, required=True, help='Person2月亮黄经')
    p.add_argument('--mars1', type=float, default=None, help='Person1火星黄经')
    p.add_argument('--mars2', type=float, default=None, help='Person2火星黄经')
    p.add_argument('--asc1', type=float, default=None, help='Person1上升黄经')
    p.add_argument('--asc2', type=float, default=None, help='Person2上升黄经')
    p.add_argument('--gender1', default='M', help='Person1性别')
    p.add_argument('--gender2', default='F', help='Person2性别')

    # 22. full-reading (v3.7.1新增)
    p = sub.add_parser('full-reading', help='全自动综合解盘（出生信息→全链路→完整报告）')
    _add_chart_args(p)
    p.add_argument('--age', type=int, default=None, help='当前年龄（不提供则自动计算）')
    p.add_argument('--today', default=None, help='Dasha/Sandhi参考日期 YYYY-MM-DD（默认今天）')
    p.add_argument('--transit-date', default=None, help='Transit真实过境参考日期 YYYY-MM-DD（默认跟随--today或今天）')
    p.add_argument('--target-year', type=int, default=None, help='太阳返照盘目标年份（默认不计算 Varshaphala）')
    p.add_argument('--profile-stages', action='store_true', help='输出 full-reading 粗粒度阶段耗时，并在 summary 中附带 stage timings')

    # 23. prashna (v3.9新增)
    p = sub.add_parser('prashna', help='Prashna问事占星（提问时刻星盘+Arudha+Sphuta+Sahams）')
    p.add_argument('--datetime', required=True, help='提问时间 ISO-8601，例如 2026-07-12T12:00:00+08:00')
    p.add_argument('--question-text', required=True, help='用户原始问事文本')
    p.add_argument('--lat', type=float, required=True, help='纬度')
    p.add_argument('--lon', type=float, required=True, help='经度')
    p.add_argument('--timezone', required=True, help='UTC offset，例如 8 或 +08:00')
    p.add_argument('--ayanamsa', default='lahiri')
    p.add_argument('--node-mode', default='mean', choices=['mean', 'true'])
    p.add_argument('--location-convention', default='wgs84', choices=['wgs84'])
    p.add_argument('--mode', default='chart', choices=['chart','arudha','sphutas','sahams','lost-item','life','kunda'], help='分析模式')

    # 24. double-transit-pac (v3.9新增)
    p = sub.add_parser('double-transit-pac', help='Double Transit PAC + D9层（KN Rao完整实现）')
    _add_chart_args(p)
    p.add_argument('--date', required=True, help='过境日期 YYYY-MM-DD')
    p.add_argument('--house', type=int, default=7, help='目标宫位（默认7=婚姻）')

    # 25. transit-ll7l (v3.9新增)
    p = sub.add_parser('transit-ll7l', help='Transit LL/7L连接+互换检测')
    _add_chart_args(p)
    p.add_argument('--date', required=True, help='过境日期 YYYY-MM-DD')

    # 26. planetary-congregation (v3.9新增)
    p = sub.add_parser('planetary-congregation', help='行星聚集检测（Lagna/7H+Transit）')
    _add_chart_args(p)
    p.add_argument('--house', type=int, default=7, help='目标宫位')
    p.add_argument('--transit-date', default=None, help='过境日期 YYYY-MM-DD（可选）')

    # 27. vivah-saham (v3.9新增)
    p = sub.add_parser('vivah-saham', help='Vivah Saham计算+Transit激活')
    _add_chart_args(p)
    p.add_argument('--transit-date', default=None, help='过境日期 YYYY-MM-DD（可选）')

    # 29. bhava-chalit (v6.9.13新增)
    p = sub.add_parser('bhava-chalit', help='Bhava Chalit 不等宫边界调整（Rashi vs Bhava 宫位对比）')
    _add_chart_args(p)
    p.add_argument('--house-system', default='sripati',
                   choices=['equal', 'placidus', 'porphyry', 'sripati', 'whole_sign', 'koch'],
                   help='宫位制（默认sripati）')
    p.add_argument('--mode', default='compare', choices=['compare', 'chart', 'boundaries'],
                   help='输出模式: compare=Rashi与Bhava对比, chart=Bhava宫位表, boundaries=宫位边界详情')

    # 30. sudarshana (v6.9.14新增)
    p = sub.add_parser('sudarshana', help='Sudarshana Chakra 三参考点盘分析（上升/月亮/太阳）')
    _add_chart_args(p)
    p.add_argument('--house', type=int, default=None, help='指定宫位(1-12)详细分析')
    p.add_argument('--text', action='store_true', help='输出文本报告（默认JSON）')

    # 28. audit-capabilities (v6.0.3新增)
    p = sub.add_parser('audit-capabilities', help='校验 technique registry 并输出能力覆盖审计')
    p.add_argument('--registry', default=None, help='technique_registry.json 路径（默认 references/technique_registry.json）')
    p.add_argument('--mode', default='validate', choices=['validate', 'table'], help='validate=校验注册表；table=输出路由审计表')
    p.add_argument('--route', default=None, help='table模式下的 route id，如 career_timing_strict')


    args = parser.parse_args()

    if hasattr(args, 'tz') and args.tz is None:
        from timezone_utils import infer_timezone
        from datetime import datetime
        try:
            if hasattr(args, 'year'):
                dt = datetime(args.year, args.month, args.day, args.hour, args.minute)
            else:
                dt = datetime.utcnow()
        except Exception:
            dt = datetime.utcnow()
        args.tz = infer_timezone(getattr(args, 'lat', 0), getattr(args, 'lon', 0), dt)
        if args.tz is None:
            args.tz = 8.0

    if not args.command:
        parser.print_help(); sys.exit(1)

    # 应用 Ayanamsa 设置（v6.9.9 新增多系统支持）
    ayanamsa_name = getattr(args, 'ayanamsa', 'lahiri')
    if ayanamsa_name and ayanamsa_name != 'lahiri':
        applied = _apply_ayanamsa(ayanamsa_name)
        if not applied:
            print(f"Warning: Ayanamsa '{ayanamsa_name}' not recognized, using default Lahiri", file=sys.stderr)
        else:
            print(f"  [Ayanamsa] {ayanamsa_name}", file=sys.stderr)

    cmds = {            'chart': cmd_chart, 'dasha': cmd_dasha, 'yoga': cmd_yoga, 'predict': cmd_predict,
            'varga': cmd_varga, 'celebrity': cmd_celebrity, 'db-stats': cmd_db_stats, 'transit': cmd_transit,
            'shadbala': cmd_shadbala, 'ashtakavarga': cmd_ashtakavarga, 'kp': cmd_kp,
            'ashtakoot': cmd_ashtakoot, 'memory': cmd_memory,
            'validate': cmd_validate, 'audit': cmd_audit, 'report': cmd_report,
            'varga-full': cmd_varga_full, 'aspects': cmd_aspects, 'jaimini': cmd_jaimini,
            'nakshatra-adv': cmd_nakshatra_adv, 'nakshatra-dasha': cmd_nakshatra_dasha,
            'nakshatra-full': cmd_nakshatra_full, 'argala': cmd_argala, 'tajika': cmd_tajika,
            'synastry': cmd_synastry, 'solar-return': cmd_solar_return,
            'narayana-dasha': cmd_narayana_dasha, 'muhurta': cmd_muhurta,
            'full-reading': cmd_full_reading, 'prashna': cmd_prashna,
            'double-transit-pac': cmd_double_transit_pac,
            'transit-ll7l': cmd_transit_ll7l, 'planetary-congregation': cmd_planetary_congregation,
            'vivah-saham': cmd_vivah_saham,
            'bhava-chalit': cmd_bhava_chalit,
            'sudarshana': cmd_sudarshana}
    if args.command == 'audit-capabilities':
        from audit_capabilities import build_audit_table, load_registry, validate_registry
        registry = load_registry(args.registry) if args.registry else load_registry()
        result = validate_registry(registry) if args.mode == 'validate' else build_audit_table(registry, args.route)
        output_json(result)
        sys.exit(0 if result.get('valid', True) else 1)
    result = cmds[args.command](args)
    if getattr(args, 'table', False):
        output_table(args.command, result)
    else:
        output_json(result)


if __name__ == '__main__':
    main()
