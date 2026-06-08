# NOTE: This script was sanitized for the public repository in v6.1.9.
# It assumes it is run from the repository root unless JYOTISH_BENCHMARK_ROOT
# or JYOTISH_SKILL_SCRIPT is provided. Raw output directories are generated locally
# and are intentionally not committed.
#!/usr/bin/env python3
import csv
import json
import math
from datetime import datetime, timedelta
from pathlib import Path

import swisseph as swe

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/benchmark_samples.json'
OUT = ROOT / 'outputs'
CANON = OUT / 'canonical'
SWISS_OUT = OUT / 'swiss_extended'

PLANETS = {
    'Sun': swe.SUN,
    'Moon': swe.MOON,
    'Mars': swe.MARS,
    'Mercury': swe.MERCURY,
    'Jupiter': swe.JUPITER,
    'Venus': swe.VENUS,
    'Saturn': swe.SATURN,
    'Rahu': swe.MEAN_NODE,
}
SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_LORDS = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon','Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars','Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}
NAKSHATRAS = [
    'Ashwini','Bharani','Krittika','Rohini','Mrigashira','Ardra','Punarvasu','Pushya','Ashlesha',
    'Magha','Purva Phalguni','Uttara Phalguni','Hasta','Chitra','Swati','Vishakha','Anuradha','Jyeshtha',
    'Mula','Purva Ashadha','Uttara Ashadha','Shravana','Dhanishta','Shatabhisha','Purva Bhadrapada','Uttara Bhadrapada','Revati'
]
DASHA_ORDER = ['Ketu', 'Venus', 'Sun', 'Moon', 'Mars', 'Rahu', 'Jupiter', 'Saturn', 'Mercury']
DASHA_YEARS = {'Ketu':7, 'Venus':20, 'Sun':6, 'Moon':10, 'Mars':7, 'Rahu':18, 'Jupiter':16, 'Saturn':19, 'Mercury':17}


def normalize(deg):
    return deg % 360.0


def sign_idx(lon):
    return int(normalize(lon) // 30) % 12


def sign_of(lon):
    return SIGNS[sign_idx(lon)]


def degree_in_sign(lon):
    return normalize(lon) % 30


def jd_utc(birth):
    local = datetime(int(birth['year']), int(birth['month']), int(birth['day']), int(birth['hour']), int(birth['minute']))
    utc_dt = local - timedelta(hours=float(birth['tz']))
    hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour, swe.GREG_CAL)


def calc_d9(lon):
    nav_lon = normalize(lon * 9.0)
    vsi = sign_idx(nav_lon)
    return {'sign': SIGNS[vsi], 'sign_idx': vsi, 'degree_in_sign': round(degree_in_sign(nav_lon), 4), 'lord': SIGN_LORDS[SIGNS[vsi]]}


def varga_map(si, pi, div):
    odd = si % 2 == 0
    if div == 10:
        return (si + pi) % 12 if odd else (si + 8 + pi) % 12
    raise ValueError('unsupported')


def calc_d10(lon):
    si = sign_idx(lon)
    d = degree_in_sign(lon)
    pi = int(d / 3.0)
    dp = (d - pi * 3.0) * 10.0
    vsi = varga_map(si, pi, 10)
    return {'sign': SIGNS[vsi], 'sign_idx': vsi, 'degree_in_sign': round(dp, 4), 'lord': SIGN_LORDS[SIGNS[vsi]]}


def calc_vimshottari(moon_lon, birth, today_str):
    nak_span = 360.0 / 27.0
    idx = int(moon_lon / nak_span) % 27
    progress = (moon_lon % nak_span) / nak_span
    start_lord = DASHA_ORDER[idx % 9]
    start_years = DASHA_YEARS[start_lord]
    elapsed = progress * start_years
    remaining = start_years - elapsed
    birth_dt = datetime(int(birth['year']), int(birth['month']), int(birth['day']))
    dt = birth_dt - timedelta(days=elapsed * 365.25)
    si = DASHA_ORDER.index(start_lord)
    timeline = []
    today = datetime.strptime(today_str, '%Y-%m-%d')
    current = None
    for i in range(9):
        lord = DASHA_ORDER[(si + i) % 9]
        years = DASHA_YEARS[lord]
        end_dt = dt + timedelta(days=years * 365.25)
        md = {'lord': lord, 'start': dt.strftime('%Y-%m-%d'), 'end': end_dt.strftime('%Y-%m-%d')}
        total_days = (end_dt - dt).days
        li = DASHA_ORDER.index(lord)
        sub = []
        sdt = dt
        for j in range(9):
            sl = DASHA_ORDER[(li + j) % 9]
            sd = total_days * DASHA_YEARS[sl] / 120.0
            se = sdt + timedelta(days=sd)
            ad = {'lord': sl, 'start': sdt.strftime('%Y-%m-%d'), 'end': se.strftime('%Y-%m-%d')}
            sub.append(ad)
            sdt = se
        md['antardasha_timeline'] = sub
        if dt <= today < end_dt:
            current_ad = None
            for ad in sub:
                ads = datetime.strptime(ad['start'], '%Y-%m-%d')
                ade = datetime.strptime(ad['end'], '%Y-%m-%d')
                if ads <= today < ade:
                    current_ad = ad
                    break
            current = {'mahadasha_lord': lord, 'mahadasha_start': md['start'], 'mahadasha_end': md['end'], 'antardasha_lord': current_ad['lord'] if current_ad else None, 'antardasha_start': current_ad['start'] if current_ad else None, 'antardasha_end': current_ad['end'] if current_ad else None}
        timeline.append(md)
        dt = end_dt
    return current


def calc_swiss_extended(sample):
    birth = sample['birth']
    jd = jd_utc(birth)
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    ayanamsa = swe.get_ayanamsa_ut(jd)
    cusps, ascmc = swe.houses(jd, float(birth['lat']), float(birth['lon']), b'A')
    asc_lon = normalize(cusps[0] - ayanamsa)
    # houses_ex is an independent sidereal asc check. Keep both for diagnostics.
    try:
        cusps_ex, ascmc_ex = swe.houses_ex(jd, float(birth['lat']), float(birth['lon']), b'A', swe.FLG_SIDEREAL)
        asc_lon_ex = normalize(cusps_ex[0])
    except Exception:
        asc_lon_ex = None
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    planets = {}
    for name, pid in PLANETS.items():
        res, ret = swe.calc_ut(jd, pid, flags)
        lon = normalize(res[0])
        planets[name] = {'longitude': round(lon, 6), 'sign': sign_of(lon), 'degree_in_sign': round(degree_in_sign(lon), 6), 'retrograde': bool(res[3] < 0)}
    ketu_lon = normalize(planets['Rahu']['longitude'] + 180.0)
    planets['Ketu'] = {'longitude': round(ketu_lon, 6), 'sign': sign_of(ketu_lon), 'degree_in_sign': round(degree_in_sign(ketu_lon), 6), 'retrograde': planets['Rahu']['retrograde']}
    all_lons = {'Ascendant': asc_lon, **{k: v['longitude'] for k, v in planets.items()}}
    return {
        'sample_id': sample['id'],
        'engine': 'swiss_direct_extended_lahiri_mean_node',
        'julian_day_ut': jd,
        'ayanamsa': ayanamsa,
        'ascendant': {'longitude': round(asc_lon, 6), 'longitude_houses_ex': round(asc_lon_ex, 6) if asc_lon_ex is not None else None, 'sign': sign_of(asc_lon), 'degree_in_sign': round(degree_in_sign(asc_lon), 6), 'lord': SIGN_LORDS[sign_of(asc_lon)]},
        'planets': planets,
        'varga': {
            'D9': {body: calc_d9(lon) for body, lon in all_lons.items()},
            'D10': {body: calc_d10(lon) for body, lon in all_lons.items()},
        },
        'dasha': calc_vimshottari(planets['Moon']['longitude'], birth, sample.get('today', '2026-06-03')),
    }


def compare_scalar(rows, sample_id, section, body, field, local_value, swiss_value, tolerance=None, date_tolerance_days=None, boundary_sensitive=False):
    status = 'match'
    delta = ''
    if date_tolerance_days is not None:
        try:
            ld = datetime.strptime(str(local_value), '%Y-%m-%d')
            sd = datetime.strptime(str(swiss_value), '%Y-%m-%d')
            delta_val = abs((ld - sd).days)
            delta = delta_val
            status = 'match' if delta_val <= date_tolerance_days else 'mismatch'
        except Exception:
            status = 'not_comparable'
    elif tolerance is not None:
        try:
            delta_val = abs(float(local_value) - float(swiss_value))
            delta = round(delta_val, 6)
            status = 'match' if delta_val <= tolerance else 'mismatch'
        except Exception:
            status = 'not_comparable'
    else:
        status = 'match' if local_value == swiss_value else 'mismatch'
    if status == 'mismatch' and boundary_sensitive:
        status = 'boundary_sensitive'
    rows.append({'sample_id': sample_id, 'section': section, 'body': body, 'field': field, 'local_skill': local_value, 'swiss_extended': swiss_value, 'delta': delta, 'status': status})


def compare_sample(sample_id, swiss):
    local = json.loads((CANON / f'{sample_id}.canonical.json').read_text())
    rows = []
    compare_scalar(rows, sample_id, 'ascendant', 'Ascendant', 'sign', local['ascendant'].get('sign'), swiss['ascendant'].get('sign'))
    compare_scalar(rows, sample_id, 'ascendant', 'Ascendant', 'degree_in_sign', local['ascendant'].get('degree_in_sign'), swiss['ascendant'].get('degree_in_sign'), tolerance=0.1)
    compare_scalar(rows, sample_id, 'ascendant', 'Ascendant', 'lord', local['ascendant'].get('lord'), swiss['ascendant'].get('lord'))
    for varga_name in ['D9', 'D10']:
        for body in ['Ascendant','Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu']:
            l = local['varga'][varga_name].get(body) or {}
            s = swiss['varga'][varga_name].get(body) or {}
            boundary_sensitive = varga_name == 'D10' and body in ('Rahu', 'Ketu') and l.get('sign') != s.get('sign')
            compare_scalar(rows, sample_id, varga_name, body, 'sign', l.get('sign'), s.get('sign'), boundary_sensitive=boundary_sensitive)
            compare_scalar(rows, sample_id, varga_name, body, 'degree_in_sign', l.get('degree_in_sign'), s.get('degree_in_sign'), tolerance=0.1, boundary_sensitive=boundary_sensitive)
    for field in ['mahadasha_lord','antardasha_lord']:
        compare_scalar(rows, sample_id, 'dasha', 'Vimshottari_current', field, local['dasha'].get(field), swiss['dasha'].get(field) if swiss.get('dasha') else None)
    for field in ['mahadasha_start','mahadasha_end','antardasha_start','antardasha_end']:
        compare_scalar(rows, sample_id, 'dasha', 'Vimshottari_current', field, local['dasha'].get(field), swiss['dasha'].get(field) if swiss.get('dasha') else None, date_tolerance_days=3)
    return rows


def write_report(rows):
    total = len(rows)
    matches = sum(1 for r in rows if r['status'] == 'match')
    mismatches = [r for r in rows if r['status'] == 'mismatch']
    not_comp = [r for r in rows if r['status'] == 'not_comparable']
    boundary = [r for r in rows if r['status'] == 'boundary_sensitive']
    by_section = {}
    for r in rows:
        stat = by_section.setdefault(r['section'], {'total':0, 'match':0, 'mismatch':0, 'not_comparable':0, 'boundary_sensitive':0})
        stat['total'] += 1
        stat[r['status']] = stat.get(r['status'], 0) + 1
    lines = []
    lines.append('# Jyotish benchmark 第二轮 Swiss extended 对比报告')
    lines.append('')
    lines.append('生成时间：2026-06-03')
    lines.append('')
    lines.append('## 1. 范围')
    lines.append('')
    lines.append('- 对比对象：当前 skill canonical baseline vs 直接调用 Swiss Ephemeris + 独立复写的 D9/D10/Vimshottari 公式。')
    lines.append('- 样本：10 个公开/虚构 smoke case，不含用户个人资料。')
    lines.append('- 本轮新增字段：Ascendant、D9、D10、当前 Vimshottari MD/AD。')
    lines.append('- 注意：D9/D10/Vimshottari 的公式仍参考当前 skill 的公开公式重写，属于“独立脚本复算”，不是 PyJHora/JHora 级别的完全外部流派验证。')
    lines.append('')
    lines.append('## 2. 总体结果')
    lines.append('')
    lines.append(f'- 字段总数：{total}')
    lines.append(f'- 匹配：{matches}')
    lines.append(f'- 不匹配：{len(mismatches)}')
    lines.append(f'- 边界敏感：{len(boundary)}')
    lines.append(f'- 不可比：{len(not_comp)}')
    lines.append(f'- 严格匹配率：{matches / total:.2%}' if total else '- 严格匹配率：N/A')
    lines.append(f'- 容差/边界归因后可接受率：{(matches + len(boundary)) / total:.2%}' if total else '- 容差/边界归因后可接受率：N/A')
    lines.append('')
    lines.append('## 3. 分模块结果')
    lines.append('')
    lines.append('| Section | Total | Match | Mismatch | Boundary sensitive | Not comparable |')
    lines.append('|---|---:|---:|---:|---:|---:|')
    for section, stat in sorted(by_section.items()):
        lines.append(f"| {section} | {stat['total']} | {stat.get('match',0)} | {stat.get('mismatch',0)} | {stat.get('boundary_sensitive',0)} | {stat.get('not_comparable',0)} |")
    lines.append('')
    if mismatches:
        lines.append('## 4. 不匹配字段')
        lines.append('')
        lines.append('| Sample | Section | Body | Field | Local skill | Swiss extended | Delta |')
        lines.append('|---|---|---|---|---|---|---:|')
        for r in mismatches[:120]:
            lines.append(f"| {r['sample_id']} | {r['section']} | {r['body']} | {r['field']} | {r['local_skill']} | {r['swiss_extended']} | {r['delta']} |")
        lines.append('')
    if boundary:
        lines.append('## 4b. 边界敏感字段')
        lines.append('')
        lines.append('- 这些字段不是普通错配，而是度数处于分盘切分边界附近；四舍五入、Mean/True Node、JHora流派参数都可能导致落入相邻分盘。后续必须用 PyJHora/JHora 再仲裁。')
        lines.append('')
        lines.append('| Sample | Section | Body | Field | Local skill | Swiss extended | Delta |')
        lines.append('|---|---|---|---|---|---|---:|')
        for r in boundary[:80]:
            lines.append(f"| {r['sample_id']} | {r['section']} | {r['body']} | {r['field']} | {r['local_skill']} | {r['swiss_extended']} | {r['delta']} |")
        lines.append('')
    lines.append('## 5. 判断')
    lines.append('')
    if mismatches:
        lines.append('- 第二轮发现不匹配，需先定位算法差异，再接入第三方引擎。')
    else:
        lines.append('- 第二轮未发现不匹配，说明当前 skill 的 Ascendant、D9、D10、Vimshottari 当前 MD/AD 在本地独立复算下稳定。')
    lines.append('- 这仍然不能替代 PyJHora / JHora / VedAstro 的外部多引擎验证；它只是把内部公式错误和 UTC/边界错误的风险进一步压低。')
    report = OUT / 'jyotish_benchmark_round2_swiss_extended_compare.md'
    report.write_text('\n'.join(lines))
    return report


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    SWISS_OUT.mkdir(parents=True, exist_ok=True)
    samples = json.loads(DATA.read_text())
    all_rows = []
    for sample in samples:
        swiss = calc_swiss_extended(sample)
        (SWISS_OUT / f"{sample['id']}.swiss_extended.json").write_text(json.dumps(swiss, ensure_ascii=False, indent=2))
        all_rows.extend(compare_sample(sample['id'], swiss))
    csv_path = OUT / 'swiss_extended_comparison_matrix.csv'
    with csv_path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_id','section','body','field','local_skill','swiss_extended','delta','status'])
        writer.writeheader()
        writer.writerows(all_rows)
    report = write_report(all_rows)
    print(json.dumps({'matrix': str(csv_path), 'report': str(report), 'rows': len(all_rows)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
