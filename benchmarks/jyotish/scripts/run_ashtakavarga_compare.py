# NOTE: This script was sanitized for the public repository in v6.1.9.
# It assumes it is run from the repository root unless JYOTISH_BENCHMARK_ROOT
# or JYOTISH_SKILL_SCRIPT is provided. Raw output directories are generated locally
# and are intentionally not committed.
#!/usr/bin/env python3
"""Ashtakavarga benchmark.

Compares the local Jyotish skill BPHS Ashtakavarga implementation with PyJHora's
get_ashtaka_varga() over fictional/public smoke samples.
PyJHora is used only as an external benchmark; AGPL code is not copied into the skill.
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
REPORT = OUT / 'jyotish_benchmark_round6_ashtakavarga_compare.md'
MATRIX = OUT / 'ashtakavarga_comparison_matrix.csv'
SKILL_SCRIPTS = Path(__file__).resolve().parents[2] / 'scripts'
PYJHORA_SITE = Path(__import__('os').environ.get('PYJHORA_SITE', ''))
PYJHORA_COMPAT = ROOT / 'scripts/pyjhora_compat'

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
PLANET_TO_ID = {'Sun': 0, 'Moon': 1, 'Mars': 2, 'Mercury': 3, 'Jupiter': 4, 'Venus': 5, 'Saturn': 6, 'Rahu': 7, 'Ketu': 8}
LOCAL_PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Lagna']
PYJHORA_ROW_LABELS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Lagna']


def local_canonical(sample_id):
    return json.loads((CANON / f'{sample_id}.canonical.json').read_text())


def local_ashtakavarga(canon):
    if str(SKILL_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SKILL_SCRIPTS))
    from ashtakavarga import calc_ashtakavarga
    planets = canon['planets']
    asc_idx = SIGNS.index(canon['ascendant']['sign'])
    return calc_ashtakavarga(planets, asc_idx)


def patch_swisseph_for_pyjhora():
    for name in ['SIDM_KRISHNAMURTI_VP291', 'SIDM_TRUE_MULA', 'SIDM_TRUE_CITRA', 'SIDM_TRUE_REVATI']:
        if not hasattr(swe, name):
            setattr(swe, name, getattr(swe, 'SIDM_KRISHNAMURTI', 1))


def pyjhora_ashtakavarga_from_canon(canon):
    if str(PYJHORA_COMPAT) not in sys.path:
        sys.path.insert(0, str(PYJHORA_COMPAT))
    if str(PYJHORA_SITE) not in sys.path:
        sys.path.insert(0, str(PYJHORA_SITE))
    patch_swisseph_for_pyjhora()
    from jhora import utils, const
    from jhora.horoscope.chart import ashtakavarga
    p_to_h = {}
    for pname, pid in PLANET_TO_ID.items():
        p_to_h[pid] = SIGNS.index(canon['planets'][pname]['sign'])
    p_to_h[const._ascendant_symbol] = SIGNS.index(canon['ascendant']['sign'])
    h_to_p = utils.get_house_to_planet_dict_from_planet_to_house_dict(p_to_h)
    bav, sav, pav = ashtakavarga.get_ashtaka_varga(h_to_p)
    return {'bav': bav, 'sav': sav, 'house_to_planet': h_to_p}


def add_row(rows, sample_id, target, field, local_value, target_value):
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


def write_report(rows, per_sample):
    targets = ['pyjhora_sav', 'pyjhora_bav', 'invariants']
    lines = []
    lines.append('# Jyotish benchmark 第六轮：Ashtakavarga BAV/SAV 交叉验证')
    lines.append('')
    lines.append('生成时间：2026-06-03')
    lines.append('')
    lines.append('## 1. 本轮目的')
    lines.append('')
    lines.append('- 验证当前 skill 的 Ashtakavarga BAV/SAV 是否与 PyJHora `get_ashtaka_varga()` 对齐。')
    lines.append('- 同时检查内部不变量：7行星 SAV 总分=337；含 Lagna full SAV 总分=386；各行星 BAV 固定总分正确。')
    lines.append('- 样本仍为10个公开/虚构 smoke case，不包含用户个人资料。')
    lines.append('')
    lines.append('## 2. 总体结果')
    lines.append('')
    lines.append('| Target | Total | Match | Mismatch | Match rate |')
    lines.append('|---|---:|---:|---:|---:|')
    for target in targets:
        total, match, mismatch, rate = summarize(rows, target)
        lines.append(f'| {target} | {total} | {match} | {mismatch} | {rate:.2%} |')
    lines.append('')
    lines.append('## 3. 逐样本摘要')
    lines.append('')
    lines.append('| Sample | SAV match | BAV match | SAV total | Full SAV | Strongest signs | Weakest signs |')
    lines.append('|---|---:|---:|---:|---:|---|---|')
    for item in per_sample:
        lines.append(f"| {item['sample_id']} | {item['sav_match']}/12 | {item['bav_match']}/96 | {item['sav_total']} | {item['full_sav_total']} | {', '.join(item['strongest'])} | {', '.join(item['weakest'])} |")
    lines.append('')
    lines.append('## 4. 仲裁结论')
    lines.append('')
    lines.append('- 若 `pyjhora_sav` 与 `pyjhora_bav` 均为 100%，则 Ashtakavarga BAV/SAV 计算层可暂定通过。')
    lines.append('- Shodhya Pinda 不纳入本轮硬性通过；PyJHora 源码示例本身说明个别书例存在不一致，适合单独做弱口径验证。')
    return '\n'.join(lines)


def main():
    samples = json.loads(DATA.read_text())
    rows = []
    per_sample = []
    for sample in samples:
        sid = sample['id']
        canon = local_canonical(sid)
        local = local_ashtakavarga(canon)
        pyj = pyjhora_ashtakavarga_from_canon(canon)
        local_sav = [local['sav']['scores'][sign] for sign in SIGNS]
        pyj_sav = pyj['sav']
        sav_match = 0
        for idx, sign in enumerate(SIGNS):
            before = len(rows)
            add_row(rows, sid, 'pyjhora_sav', f'sav.{sign}', local_sav[idx], pyj_sav[idx])
            sav_match += 1 if rows[-1]['status'] == 'match' else 0
        bav_match = 0
        for pidx, planet in enumerate(LOCAL_PLANETS):
            local_bav = local['bav'][planet]['bindus']
            pyj_bav = pyj['bav'][pidx]
            for sidx, sign in enumerate(SIGNS):
                add_row(rows, sid, 'pyjhora_bav', f'bav.{planet}.{sign}', local_bav[sidx], pyj_bav[sidx])
                bav_match += 1 if rows[-1]['status'] == 'match' else 0
        add_row(rows, sid, 'invariants', 'sav.total_337', local['sav']['total'], 337)
        add_row(rows, sid, 'invariants', 'full_sav.total_386', local['sav']['full_total_with_lagna'], 386)
        add_row(rows, sid, 'invariants', 'all_bav_valid', local['all_bav_valid'], True)
        per_sample.append({
            'sample_id': sid,
            'sav_match': sav_match,
            'bav_match': bav_match,
            'sav_total': local['sav']['total'],
            'full_sav_total': local['sav']['full_total_with_lagna'],
            'strongest': local['strongest_signs'],
            'weakest': local['weakest_signs'],
        })
    with MATRIX.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_id', 'target', 'field', 'local_skill', 'target_value', 'status'])
        writer.writeheader()
        writer.writerows(rows)
    REPORT.write_text(write_report(rows, per_sample))
    print(json.dumps({'report': str(REPORT), 'matrix': str(MATRIX), 'samples': len(samples), 'fields': len(rows)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
