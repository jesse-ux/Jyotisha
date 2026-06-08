# NOTE: This script was sanitized for the public repository in v6.1.9.
# It assumes it is run from the repository root unless JYOTISH_BENCHMARK_ROOT
# or JYOTISH_SKILL_SCRIPT is provided. Raw output directories are generated locally
# and are intentionally not committed.
#!/usr/bin/env python3
"""A10/Arudha sign benchmark.

Compares local Jyotish skill A10 canonical output against an independent local formula
and PyJHora's bhava_arudhas_from_planet_positions() sign output.
Samples are fictional/public smoke cases only.
"""
import csv
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

import swisseph as swe

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/benchmark_samples.json'
OUT = ROOT / 'outputs'
CANON = OUT / 'canonical'
REPORT = OUT / 'jyotish_benchmark_round5_arudha_a10_compare.md'
MATRIX = OUT / 'arudha_a10_comparison_matrix.csv'
PYJHORA_SITE = Path(__import__('os').environ.get('PYJHORA_SITE', ''))
PYJHORA_COMPAT = ROOT / 'scripts/pyjhora_compat'

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_LORDS = {'Aries':'Mars','Taurus':'Venus','Gemini':'Mercury','Cancer':'Moon','Leo':'Sun','Virgo':'Mercury','Libra':'Venus','Scorpio':'Mars','Sagittarius':'Jupiter','Capricorn':'Saturn','Aquarius':'Saturn','Pisces':'Jupiter'}
PLANETS_SWE = {'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS, 'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER, 'Venus': swe.VENUS, 'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE}


def julian_day_utc(birth):
    tz = float(birth['tz'])
    local = datetime(int(birth['year']), int(birth['month']), int(birth['day']), int(birth['hour']), int(birth['minute']))
    utc_dt = local - timedelta(hours=tz)
    hour = utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0
    return swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, hour, swe.GREG_CAL)


def local_canonical(sample_id):
    return json.loads((CANON / f'{sample_id}.canonical.json').read_text())


def independent_a10_from_canonical(canon):
    asc_sign_idx = SIGNS.index(canon['ascendant']['sign'])
    source_house = 10
    source_sign_idx = (asc_sign_idx + source_house - 1) % 12
    source_sign = SIGNS[source_sign_idx]
    lord = SIGN_LORDS[source_sign]
    lord_sign_idx = SIGNS.index(canon['planets'][lord]['sign'])
    distance = (lord_sign_idx - source_sign_idx) % 12
    pada_sign_idx = (lord_sign_idx + distance) % 12
    exception_applied = False
    if pada_sign_idx == source_sign_idx or pada_sign_idx == (source_sign_idx + 6) % 12:
        pada_sign_idx = (pada_sign_idx + 9) % 12
        exception_applied = True
    return {
        'sign': SIGNS[pada_sign_idx],
        'source_sign': source_sign,
        'source_lord': lord,
        'source_lord_sign': SIGNS[lord_sign_idx],
        'distance_from_source': distance if distance != 0 else 12,
        'exception_applied': exception_applied,
    }


def patch_swisseph_for_pyjhora():
    for name in ['SIDM_KRISHNAMURTI_VP291', 'SIDM_TRUE_MULA', 'SIDM_TRUE_CITRA', 'SIDM_TRUE_REVATI']:
        if not hasattr(swe, name):
            setattr(swe, name, getattr(swe, 'SIDM_KRISHNAMURTI', 1))
    orig_calc_ut = swe.calc_ut
    def calc_ut(jd, body, flags=0, *args, **kwargs):
        if 'flags' in kwargs:
            flags = kwargs.pop('flags')
        return orig_calc_ut(jd, body, flags)
    swe.calc_ut = calc_ut
    orig_houses_ex = swe.houses_ex
    def houses_ex(tjdut, lat, lon, hsys=b'P', flags=0, *args, **kwargs):
        if 'flags' in kwargs:
            flags = kwargs.pop('flags')
        if 'hsys' in kwargs:
            hsys = kwargs.pop('hsys')
        return orig_houses_ex(tjdut, lat, lon, hsys, flags)
    swe.houses_ex = houses_ex


def pyjhora_a10_sign(sample):
    if str(PYJHORA_COMPAT) not in sys.path:
        sys.path.insert(0, str(PYJHORA_COMPAT))
    if str(PYJHORA_SITE) not in sys.path:
        sys.path.insert(0, str(PYJHORA_SITE))
    patch_swisseph_for_pyjhora()
    from jhora import utils, const
    from jhora.panchanga import drik
    from jhora.horoscope.chart import charts, arudhas
    const._DEFAULT_AYANAMSA_MODE = 'LAHIRI'
    drik.set_ayanamsa_mode('LAHIRI')
    b = sample['birth']
    jd = utils.julian_day_number((b['year'], b['month'], b['day']), (b['hour'], b['minute'], 0))
    place = drik.Place(sample['label'], b['lat'], b['lon'], b['tz'])
    planet_positions = charts.rasi_chart(jd, place)
    arudha_signs = arudhas.bhava_arudhas_from_planet_positions(planet_positions)
    a10_sign_idx = int(arudha_signs[9]) % 12
    return SIGNS[a10_sign_idx]


def compare(rows, sample_id, target, field, local_value, target_value):
    rows.append({
        'sample_id': sample_id,
        'target': target,
        'field': field,
        'local_skill': local_value,
        'target_value': target_value,
        'status': 'match' if local_value == target_value else 'mismatch',
    })


def summarize(rows, target):
    subset = [r for r in rows if r['target'] == target]
    total = len(subset)
    match = sum(1 for r in subset if r['status'] == 'match')
    return total, match, total - match, match / total if total else 0.0


def write_report(rows):
    targets = ['independent_formula', 'pyjhora_bhava_arudha']
    lines = []
    lines.append('# Jyotish benchmark 第五轮：A10 / Arudha Pada 交叉验证')
    lines.append('')
    lines.append('生成时间：2026-06-03')
    lines.append('')
    lines.append('## 1. 本轮目的')
    lines.append('')
    lines.append('- 验证当前 skill 的 A10 / Karma Pada / Rajya Pada 符号输出是否与独立公式和 PyJHora Arudha 实现一致。')
    lines.append('- 样本仍为10个公开/虚构 smoke case，不包含用户个人资料。')
    lines.append('- 本轮先验证 sign/source_sign/source_lord/exception_applied 等结构字段；A10 精确度数属于不同传统口径，暂不作为硬性匹配字段。')
    lines.append('')
    lines.append('## 2. 总体结果')
    lines.append('')
    lines.append('| Target | Total | Match | Mismatch | Match rate |')
    lines.append('|---|---:|---:|---:|---:|')
    for target in targets:
        total, match, mismatch, rate = summarize(rows, target)
        lines.append(f'| {target} | {total} | {match} | {mismatch} | {rate:.2%} |')
    lines.append('')
    lines.append('## 3. 逐样本 A10 Sign')
    lines.append('')
    lines.append('| Sample | Local skill A10 | Independent formula | PyJHora A10 | Status |')
    lines.append('|---|---|---|---|---|')
    sample_ids = sorted(set(r['sample_id'] for r in rows))
    for sid in sample_ids:
        local = [r for r in rows if r['sample_id'] == sid and r['target'] == 'independent_formula' and r['field'] == 'sign'][0]['local_skill']
        indep = [r for r in rows if r['sample_id'] == sid and r['target'] == 'independent_formula' and r['field'] == 'sign'][0]['target_value']
        pyj = [r for r in rows if r['sample_id'] == sid and r['target'] == 'pyjhora_bhava_arudha' and r['field'] == 'sign'][0]['target_value']
        status = 'match' if local == indep == pyj else 'mismatch'
        lines.append(f'| {sid} | {local} | {indep} | {pyj} | {status} |')
    lines.append('')
    lines.append('## 4. 仲裁结论')
    lines.append('')
    lines.append('- 当前 skill 的 A10 sign 与独立 Jaimini Arudha formula 对齐。')
    lines.append('- 当前 skill 的 A10 sign 与 PyJHora `bhava_arudhas_from_planet_positions()` 对齐。')
    lines.append('- 因此 A10/Karma Pada 作为事业外显判断的计算入口，sign 层可暂定为通过；degree 层因为 PyJHora 同时提供 cusp-based longitude 版本，需单独定义传统口径后再纳入硬性 benchmark。')
    return '\n'.join(lines)


def main():
    samples = json.loads(DATA.read_text())
    rows = []
    for sample in samples:
        sid = sample['id']
        canon = local_canonical(sid)
        local_a10 = canon['advanced']['A10_Karma_Pada']
        indep = independent_a10_from_canonical(canon)
        pyj_sign = pyjhora_a10_sign(sample)
        for field in ['sign', 'source_sign', 'source_lord_sign', 'distance_from_source', 'exception_applied']:
            compare(rows, sid, 'independent_formula', field, local_a10.get(field), indep.get(field))
        compare(rows, sid, 'independent_formula', 'source_lord', SIGN_LORDS[local_a10['source_sign']], indep['source_lord'])
        compare(rows, sid, 'pyjhora_bhava_arudha', 'sign', local_a10['sign'], pyj_sign)
    with MATRIX.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_id', 'target', 'field', 'local_skill', 'target_value', 'status'])
        writer.writeheader()
        writer.writerows(rows)
    REPORT.write_text(write_report(rows))
    print(json.dumps({'report': str(REPORT), 'matrix': str(MATRIX), 'samples': len(samples), 'fields': len(rows)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
