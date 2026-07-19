#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
吠陀占星分盘计算模块 v1.0
BPHS Shodasavarga（十六分盘体系）
支持: D2/D3/D4/D5/D6/D7/D8/D9/D10/D11/D12/D16/D20/D24/D27/D30/D40/D45/D60/D81/D108/D144
每个分盘输出精确度数，支持进一步分析。
"""
from typing import Dict, List, Optional

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGNS_CN = {s: f"{cn}" for s, cn in zip(SIGNS,
    ['白羊座','金牛座','双子座','巨蟹座','狮子座','处女座',
     '天秤座','天蝎座','射手座','摩羯座','水瓶座','双鱼座'])}
SIGN_LORDS = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon',
    'Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars',
    'Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}
EXALT_SIGN = {'Sun':0,'Moon':1,'Mars':9,'Mercury':5,'Jupiter':3,'Venus':11,'Saturn':6}
DEBIL_SIGN = {'Sun':6,'Moon':7,'Mars':3,'Mercury':11,'Jupiter':9,'Venus':5,'Saturn':0}
OWN_SIGNS = {'Sun':[4],'Moon':[3],'Mars':[0,7],'Mercury':[2,5],
    'Jupiter':[8,11],'Venus':[1,6],'Saturn':[9,10]}
VARGA_META = {
    2:{'name':'Hora','cn':'财富','area':'财富资源'},3:{'name':'Drekkana','cn':'兄弟','area':'兄弟姐妹'},
    4:{'name':'Turyamsa','cn':'财产','area':'财产住所'},5:{'name':'Panchamsa','cn':'名声','area':'名声权力'},
    6:{'name':'Shashthamsa','cn':'健康','area':'健康敌人'},7:{'name':'Saptamsa','cn':'子女','area':'子女后代'},
    8:{'name':'Ashtamsa','cn':'突发','area':'突发转化'},
    9:{'name':'Navamsa','cn':'婚姻','area':'婚姻伴侣灵魂'},10:{'name':'Dasamsa','cn':'事业','area':'事业公众形象'},
    11:{'name':'Rudramsa','cn':'收益转化','area':'收益朋友愿望'},12:{'name':'Dwadashamsa','cn':'父母','area':'父母祖先'},16:{'name':'Shodasamsa','cn':'享受','area':'车辆物质'},
    20:{'name':'Vimsamsa','cn':'修行','area':'精神修行'},24:{'name':'Siddhamsa','cn':'学识','area':'教育学识'},
    27:{'name':'Bhamsa','cn':'力量','area':'力量弱点'},30:{'name':'Trimsamsa','cn':'苦难','area':'灾难苦难'},
    40:{'name':'Khavedamsa','cn':'运势','area':'吉凶运势'},45:{'name':'Akshavedamsa','cn':'格局','area':'整体格局'},
    60:{'name':'Shashtyamsa','cn':'业力','area':'前世业力同盘区分'},
    81:{'name':'Navamsa-Navamsa','cn':'D9之D9','area':'配偶灵性精微层'},
    108:{'name':'Dwadasamsa-Navamsa','cn':'D12之D9','area':'祖先父母精微层'},
    144:{'name':'Dwadasamsa-Dwadasamsa','cn':'D12之D12','area':'父母祖先精微层'}}

def _si(lon): return int(lon/30)%12
def _sn(i): return SIGNS[i%12]
def _odd(si): return si%2==0  # Aries(0)=odd
def _modality(si):
    if si % 3 == 0:
        return 'movable'
    if si % 3 == 1:
        return 'fixed'
    return 'dual'

def _element(si):
    return si % 4

def _d30_map(si, pi):
    if _odd(si):
        if pi<5: return 0
        if pi<10: return 10
        if pi<18: return 8
        if pi<25: return 2
        return 6
    else:
        if pi<5: return 1
        if pi<12: return 5
        if pi<20: return 9
        if pi<25: return 7
        return 11

def varga_map(si, pi, div):
    """BPHS分盘映射：星座索引si的第pi份→目标星座索引"""
    o = _odd(si)
    if div==2: return (4 if o else 3) if pi==0 else (3 if o else 4)
    if div==3: return (si+pi*4)%12  # Drekkana: same → +4 → +8, no odd/even distinction
    if div==4: return (si+pi*3)%12
    if div==5: return (si+pi)%12 if o else (si+8+pi)%12
    if div==6: return (si+pi)%12 if o else (si+6+pi)%12
    if div==7: return (si+pi)%12 if o else (si+6+pi)%12
    if div==8: return (si+pi)%12 if o else (si+8+pi)%12
    if div==9:
        # BPHS Navamsa: movable=same, fixed=9th from sign (+8), dual=5th from sign (+4)
        if si%3==0: start=si
        elif si%3==1: start=(si+8)%12
        else: start=(si+4)%12
        return (start+pi)%12
    if div==10: return (si+pi)%12 if o else (si+8+pi)%12  # D10: even signs count from 9th inclusively => +8 offset
    if div==11: return (si+pi)%12 if o else (si+8+pi)%12  # D11 Rudramsa: mirror extended calculator
    if div==12: return (si+pi)%12
    if div==16: return ((0 if o else 4)+pi)%12  # D16: movable=+0, fixed=+4; dual needs separate (2026-05-03 fix: was +1)
    if div==20: return ((0 if o else 8)+pi)%12
    if div==24: return ((4 if o else 3)+pi)%12
    if div==27: return ((0 if o else 6)+pi)%12
    if div==30: return _d30_map(si,pi)
    if div==40: return ((0 if o else 6)+pi)%12
    if div==45: return ((0 if o else 6)+pi)%12
    if div==60: return (si+pi)%12 if o else (si+1+pi)%12
    if div==81:
        outer_part = pi // 9
        inner_part = pi % 9
        outer_sign = varga_map(si, outer_part, 9)
        return varga_map(outer_sign, inner_part, 9)
    if div==108:
        outer_part = pi // 12
        inner_part = pi % 12
        outer_sign = varga_map(si, outer_part, 9)
        return varga_map(outer_sign, inner_part, 12)
    if div==144:
        outer_part = pi // 12
        inner_part = pi % 12
        return (si + outer_part + inner_part) % 12
    raise ValueError(f"不支持的D{div}")


def _d30_map_vedastro(si, pi):
    if _odd(si):
        if pi < 5: return 7
        if pi < 10: return 10
        if pi < 18: return 8
        if pi < 25: return 2
        return 6
    else:
        if pi < 5: return 1
        if pi < 12: return 2
        if pi < 20: return 8
        if pi < 25: return 9
        return 7


def varga_map_vedastro(si, pi, div):
    """VedAstro-compatible varga sign mapping.

    This mode is calibrated against VedAstro official AllPlanetData /
    AllHouseData outputs. It intentionally lives beside the historical local
    mapping so older research workflows can still audit classical variants.
    """
    if div == 2:
        return (si + pi * 4) % 12
    if div == 4:
        return (si + pi * 3) % 12
    if div == 7:
        return (si + pi) % 12
    if div == 16:
        start = {'movable': 0, 'fixed': 4, 'dual': 8}[_modality(si)]
        return (start + pi) % 12
    if div == 20:
        start = {'movable': 0, 'fixed': 8, 'dual': 4}[_modality(si)]
        return (start + pi) % 12
    if div == 27:
        start = {0: 0, 1: 3, 2: 6, 3: 9}[_element(si)]
        return (start + pi) % 12
    if div == 30:
        return _d30_map_vedastro(si, pi)
    if div == 45:
        start = {'movable': 0, 'fixed': 4, 'dual': 8}[_modality(si)]
        return (start + pi) % 12
    if div == 60:
        return (si + pi) % 12
    return varga_map(si, pi, div)

def calc_varga(lon, div, mode='classical_local'):
    """计算行星在指定分盘的位置（星座+精确度数+尊贵状态）"""
    si=_si(lon); d=lon-si*30
    if mode == 'vedastro' and div == 2:
        ps = 10.0
        pi = int(d / ps)
        dp = (d - pi * ps) * 3
        dp_display = round(dp, 4)
        if dp_display >= 30:
            dp_display = 0.0
        vsi = varga_map_vedastro(si, pi, div)
        r={'sign':_sn(vsi),'sign_idx':vsi,'degree_in_sign':dp_display,
           'part_index':pi,'lord':SIGN_LORDS.get(_sn(vsi),'')}
        return r
    ps=30.0/div; pi=int(d/ps)
    # For all vargas, degree within divisional sign is scaled to 0-30 degrees.
    dp=(d-pi*ps)*div
    # Keep the displayed divisional degree inside [0, 30). Values such as
    # 29.9999997 can round to 30.0000 at sign boundaries, which breaks
    # downstream range invariants while the underlying sign mapping is valid.
    dp_display = round(dp, 4)
    if dp_display >= 30:
        dp_display = 0.0
    vsi=varga_map_vedastro(si,pi,div) if mode == 'vedastro' else varga_map(si,pi,div)
    r={'sign':_sn(vsi),'sign_idx':vsi,'degree_in_sign':dp_display,
       'part_index':pi,'lord':SIGN_LORDS.get(_sn(vsi),'')}
    if div==9: r['pada']=pi+1
    return r


def calc_64th_navamsa(moon_lon: float) -> Dict:
    """Compute the 64th Navamsa from the Moon's Navamsa position.

    Traditional counting is inclusive, so the 64th point is +63 signs from the
    Moon's Navamsa anchor.
    """
    base = calc_varga(moon_lon, 9)
    sign_idx = (base['sign_idx'] + 63) % 12
    return {
        'base_navamsa_sign_idx': base['sign_idx'],
        'base_navamsa_sign': base['sign'],
        'offset_from_moon_navamsa': 64,
        'sign_idx': sign_idx,
        'sign': _sn(sign_idx),
        'lord': SIGN_LORDS.get(_sn(sign_idx), ''),
    }


def calc_22nd_drekkana(lagna_lon: float) -> Dict:
    """Compute the 22nd Drekkana from the Lagna's Drekkana position.

    Traditional counting is inclusive, so the 22nd point is +21 signs from the
    Lagna Drekkana anchor.
    """
    base = calc_varga(lagna_lon, 3)
    sign_idx = (base['sign_idx'] + 21) % 12
    return {
        'base_drekkana_sign_idx': base['sign_idx'],
        'base_drekkana_sign': base['sign'],
        'offset_from_lagna_drekkana': 22,
        'sign_idx': sign_idx,
        'sign': _sn(sign_idx),
        'lord': SIGN_LORDS.get(_sn(sign_idx), ''),
    }


def calc_bhrigu_bindu(moon_lon: float, rahu_lon: float) -> Dict:
    """Compute Bhrigu Bindu as the midpoint on the Rahu->Moon forward arc."""
    moon = moon_lon % 360
    rahu = rahu_lon % 360
    arc = (moon - rahu) % 360
    longitude = (rahu + arc / 2.0) % 360
    sign_idx = _si(longitude)
    degree_in_sign = round(longitude - sign_idx * 30, 4)
    return {
        'longitude': round(longitude, 4),
        'sign_idx': sign_idx,
        'sign': _sn(sign_idx),
        'degree_in_sign': degree_in_sign,
        'arc_mode': 'forward_rahu_to_moon',
        'lord': SIGN_LORDS.get(_sn(sign_idx), ''),
    }


SARPA_DREKKANA_SIGNS = {'Cancer': 2, 'Scorpio': 1, 'Pisces': 3}


def calc_sarpa_drekkana(lon: float) -> Dict:
    """Classify Sarpa Drekkana using the classical water-sign sensitive drekkanas."""
    base = calc_varga(lon, 3)
    sign = _sn(_si(lon))
    degree_in_sign = round((lon % 30), 4)
    drekkana_number = int(degree_in_sign / 10) + 1
    expected = SARPA_DREKKANA_SIGNS.get(sign)
    return {
        'longitude': round(lon % 360, 4),
        'sign': sign,
        'sign_idx': _si(lon),
        'degree_in_sign': degree_in_sign,
        'drekkana_number': drekkana_number,
        'd3_sign': base['sign'],
        'd3_sign_idx': base['sign_idx'],
        'is_sarpa_drekkana': bool(expected == drekkana_number),
        'definition': 'Cancer-2, Scorpio-1, Pisces-3',
    }

def dignity(planet, sign_idx):
    if planet in EXALT_SIGN and sign_idx==EXALT_SIGN[planet]: return 'Exalted'
    if planet in DEBIL_SIGN and sign_idx==DEBIL_SIGN[planet]: return 'Debilitated'
    if planet in OWN_SIGNS and sign_idx in OWN_SIGNS[planet]: return 'Own Sign'
    return 'Neutral'

def calc_all_vargas(planet_lons, asc_lon, divisions=None, mode='classical_local'):
    """批量计算所有指定分盘"""
    if divisions is None:
        divisions=[2,3,4,5,6,7,8,9,10,11,12,16,20,24,27,30,40,45,60,81,108,144]
    results={}
    for div in divisions:
        m=VARGA_META.get(div,{})
        key=f"D{div}_{m.get('name',f'D{div}')}"
        vd={'_meta':{'div':div,'name':m.get('name',''),'cn':m.get('cn',''),
                      'area':m.get('area',''),'part_size':30.0/div}}
        vd['Ascendant']=calc_varga(asc_lon,div,mode=mode)
        for pn,lon in planet_lons.items():
            vd[pn]=calc_varga(lon,div,mode=mode)
        # 尊贵状态
        vd['_dignity']={pn:dignity(pn,pd['sign_idx'])
            for pn,pd in vd.items() if pn not in ('Ascendant','_meta') and isinstance(pd,dict) and 'sign_idx' in pd}
        # D9专项
        if div==9:
            ai=vd['Ascendant']['sign_idx']
            s7=(ai+6)%12
            p7=[pn for pn,pd in vd.items() if isinstance(pd,dict) and pd.get('sign_idx')==s7]
            vd['_d9_analysis']={
                'navamsa_7th_sign':_sn(s7),'navamsa_7th_lord':SIGN_LORDS.get(_sn(s7),''),
                'planets_in_d9_7th':p7,
                'venus_d9':f"{vd.get('Venus',{}).get('sign','?')} {vd.get('Venus',{}).get('degree_in_sign',0):.2f}°",
                'jupiter_d9':f"{vd.get('Jupiter',{}).get('sign','?')} {vd.get('Jupiter',{}).get('degree_in_sign',0):.2f}°",
                'venus_dignity':dignity('Venus',vd.get('Venus',{}).get('sign_idx',-1)),
                'jupiter_dignity':dignity('Jupiter',vd.get('Jupiter',{}).get('sign_idx',-1)),
            }
        # D60专项
        if div==60:
            ai=vd['Ascendant']['sign_idx']
            ben,mal=[],[]
            for pn,pd in vd.items():
                if not isinstance(pd,dict) or 'sign_idx' not in pd: continue
                h=((pd['sign_idx']-ai)%12)+1
                if h in (1,4,7,10):
                    if pn in ('Jupiter','Venus','Moon'): ben.append(f"{pn}({h}宫)")
                    elif pn in ('Saturn','Mars','Sun','Rahu','Ketu'): mal.append(f"{pn}({h}宫)")
            vd['_d60_analysis']={'benefics_in_kendras':ben,'malefics_in_kendras':mal,
                'karma_hint':'前世善业较重' if len(ben)>len(mal) else '前世有业力课题' if len(mal)>len(ben) else '善恶交织'}
        results[key]=vd
    return results
