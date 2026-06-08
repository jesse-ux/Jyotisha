# NOTE: This script was sanitized for the public repository in v6.1.9.
# It assumes it is run from the repository root unless JYOTISH_BENCHMARK_ROOT
# or JYOTISH_SKILL_SCRIPT is provided. Raw output directories are generated locally
# and are intentionally not committed.
#!/usr/bin/env python3
"""Chara Dasha benchmark.

Compares the local Jyotish skill's simplified Chara Dasha implementation with
PyJHora's KN Rao Chara Dasha over fictional/public smoke samples. This script is
intended to identify whether the local module is production-grade or only a
placeholder workflow component.
"""
import csv
import json
import sys
from pathlib import Path

import swisseph as swe

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/benchmark_samples.json'
OUT = ROOT / 'outputs'
CANON = OUT / 'canonical'
REPORT = OUT / 'jyotish_benchmark_round7_chara_dasha_compare.md'
MATRIX = OUT / 'chara_dasha_comparison_matrix.csv'
SKILL_SCRIPTS = Path(__file__).resolve().parents[2] / 'scripts'
PYJHORA_SITE = Path(__import__('os').environ.get('PYJHORA_SITE', ''))
PYJHORA_COMPAT = ROOT / 'scripts/pyjhora_compat'

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']


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


def canon(sample_id):
    return json.loads((CANON / f'{sample_id}.canonical.json').read_text())


def local_chara(sample, c):
    if str(SKILL_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SKILL_SCRIPTS))
    from jaimini import calc_chara_dasha
    asc_idx = SIGNS.index(c['ascendant']['sign'])
    planet_lons = {}
    for pname, pdata in c['planets'].items():
        if pname not in ('Sun','Moon','Mars','Mercury','Jupiter','Venus','Saturn','Rahu','Ketu'):
            continue
        sign_idx = SIGNS.index(pdata['sign'])
        deg = pdata.get('degree_in_sign_raw', pdata.get('degree_in_sign', pdata.get('degree', 0)))
        planet_lons[pname] = sign_idx * 30.0 + float(deg)
    b = sample['birth']
    d = calc_chara_dasha(asc_idx, planet_lons, b['year'], b['month'])
    return [{'order': x['order'], 'sign': x['sign'], 'duration_years': float(x['duration_years'])} for x in d['dasha_sequence']]


def pyjhora_chara(sample):
    if str(PYJHORA_COMPAT) not in sys.path:
        sys.path.insert(0, str(PYJHORA_COMPAT))
    if str(PYJHORA_SITE) not in sys.path:
        sys.path.insert(0, str(PYJHORA_SITE))
    patch_swisseph_for_pyjhora()
    from jhora import const
    from jhora.panchanga import drik
    from jhora.horoscope.dhasa.raasi import chara
    const._DEFAULT_AYANAMSA_MODE = 'LAHIRI'
    drik.set_ayanamsa_mode('LAHIRI')
    b = sample['birth']
    dob = (b['year'], b['month'], b['day'])
    tob = (b['hour'], b['minute'], 0)
    place = drik.Place(sample['label'], b['lat'], b['lon'], b['tz'])
    rows = chara.get_dhasa_antardhasa(
        dob,
        tob,
        place,
        chara_method=const.CHARA_TYPE.KN_RAO,
        dhasa_level_index=const.MAHA_DHASA_DEPTH.MAHA_DHASA_ONLY,
        round_duration=False,
        dhasa_duration_type=const.DHASA_YEAR_DURATION.MEAN_SIDEREAL_YEAR,
    )
    out = []
    for order, row in enumerate(rows[:12], 1):
        lord_tuple, _start, duration = row
        sign_idx = lord_tuple[0]
        out.append({'order': order, 'sign': SIGNS[sign_idx], 'duration_years': float(duration)})
    return out


def add(rows, sample_id, field, local, target):
    rows.append({
        'sample_id': sample_id,
        'field': field,
        'local_skill': local,
        'pyjhora_kn_rao': target,
        'status': 'match' if local == target else 'mismatch',
    })


def summarize(rows, prefix=None):
    subset = [r for r in rows if prefix is None or r['field'].startswith(prefix)]
    total = len(subset)
    match = sum(1 for r in subset if r['status'] == 'match')
    return total, match, total - match, match / total if total else 0.0


def write_report(rows, per_sample):
    lines = []
    lines.append('# Jyotish benchmark 第七轮：Chara Dasha / Jaimini 时间线对标')
    lines.append('')
    lines.append('生成时间：2026-06-03')
    lines.append('')
    lines.append('## 1. 本轮目的')
    lines.append('')
    lines.append('- 验证当前 skill `scripts/jaimini.py` 的 Chara Dasha 是否可作为正式计算模块使用。')
    lines.append('- 对标对象：PyJHora `raasi/chara.py` 的 KN Rao method（PyJHora 默认 `CHARA_TYPE_DEFAULT = KN_RAO`）。')
    lines.append('- 样本仍为10个公开/虚构 smoke case，不包含用户个人资料。')
    lines.append('')
    lines.append('## 2. 总体结果')
    lines.append('')
    lines.append('| Field group | Total | Match | Mismatch | Match rate |')
    lines.append('|---|---:|---:|---:|---:|')
    for label, prefix in [('sequence_sign', 'md.sign'), ('duration_years', 'md.duration'), ('all', None)]:
        total, match, mismatch, rate = summarize(rows, prefix)
        lines.append(f'| {label} | {total} | {match} | {mismatch} | {rate:.2%} |')
    lines.append('')
    lines.append('## 3. 逐样本摘要')
    lines.append('')
    lines.append('| Sample | Sign match | Duration match | Local first 3 | PyJHora first 3 |')
    lines.append('|---|---:|---:|---|---|')
    for item in per_sample:
        lines.append(f"| {item['sample_id']} | {item['sign_match']}/12 | {item['duration_match']}/12 | {item['local_first3']} | {item['pyjhora_first3']} |")
    lines.append('')
    lines.append('## 4. 仲裁结论')
    lines.append('')
    sign_total, sign_match, _, sign_rate = summarize(rows, 'md.sign')
    dur_total, dur_match, _, dur_rate = summarize(rows, 'md.duration')
    if sign_rate < 0.9 or dur_rate < 0.9:
        lines.append('- 当前 skill 的 Chara Dasha 与 PyJHora KN Rao method 存在明显差异。')
        lines.append('- 根因从源码可见：当前 `calc_chara_dasha()` 仍是简化实现（上升顺/逆 + `12 - sign planet count`），并非 KN Rao / PVN Rao / Iranganti 的完整传统算法。')
        lines.append('- 决策：Chara Dasha 不应标记为 `covered` 的强计算模块；在可信度矩阵中应降级为 `partial-code`，除非后续直接实装 KN Rao/PVN Rao method 并回归通过。')
        lines.append('- 加速策略：可把 PyJHora KN Rao method 作为外部 oracle，重写本地 Chara Dasha；或者在 skill 中明确声明 Jaimini Chara Dasha 暂不可用于高置信度应期。')
    else:
        lines.append('- 当前 skill Chara Dasha 与 PyJHora KN Rao method 基本一致，可暂定通过。')
    return '\n'.join(lines)


def main():
    samples = json.loads(DATA.read_text())
    rows = []
    per_sample = []
    for sample in samples:
        sid = sample['id']
        c = canon(sid)
        local = local_chara(sample, c)
        pyj = pyjhora_chara(sample)
        sign_match = 0
        duration_match = 0
        for i in range(12):
            add(rows, sid, f'md.sign.{i+1}', local[i]['sign'], pyj[i]['sign'])
            sign_match += 1 if rows[-1]['status'] == 'match' else 0
            # durations are integers in both systems for maha periods; compare rounded to 4 places.
            lv = round(local[i]['duration_years'], 4)
            pv = round(pyj[i]['duration_years'], 4)
            add(rows, sid, f'md.duration.{i+1}', lv, pv)
            duration_match += 1 if rows[-1]['status'] == 'match' else 0
        per_sample.append({
            'sample_id': sid,
            'sign_match': sign_match,
            'duration_match': duration_match,
            'local_first3': ', '.join(f"{x['sign']}({x['duration_years']:.0f})" for x in local[:3]),
            'pyjhora_first3': ', '.join(f"{x['sign']}({x['duration_years']:.0f})" for x in pyj[:3]),
        })
    with MATRIX.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    REPORT.write_text(write_report(rows, per_sample))
    print(json.dumps({'report': str(REPORT), 'matrix': str(MATRIX), 'rows': len(rows)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
