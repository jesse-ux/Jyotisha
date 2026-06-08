# NOTE: This script was sanitized for the public repository in v6.1.9.
# It assumes it is run from the repository root unless JYOTISH_BENCHMARK_ROOT
# or JYOTISH_SKILL_SCRIPT is provided. Raw output directories are generated locally
# and are intentionally not committed.
#!/usr/bin/env python3
"""Ashtakavarga book-example arbitration.

Uses the book-example expected BAV/SAV arrays embedded in PyJHora's own
pvr_tests.py and compares both the local skill BPHS v2.0 table and PyJHora's
current table against those examples.
"""
import csv
import json
import sys
from pathlib import Path

import swisseph as swe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
REPORT = OUT / 'jyotish_benchmark_round6c_ashtakavarga_book_examples.md'
MATRIX = OUT / 'ashtakavarga_book_examples_matrix.csv'
SKILL_SCRIPTS = Path(__file__).resolve().parents[2] / 'scripts'
PYJHORA_SITE = Path(__import__('os').environ.get('PYJHORA_SITE', ''))
PYJHORA_COMPAT = ROOT / 'scripts/pyjhora_compat'

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo','Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
PLANETS_WITH_LAGNA = PLANETS + ['Lagna']
ID_TO_PLANET = {'0': 'Sun', '1': 'Moon', '2': 'Mars', '3': 'Mercury', '4': 'Jupiter', '5': 'Venus', '6': 'Saturn'}

EXAMPLES = {
    'pvr_chart_6': {
        'chart': ['8/5','','2/0/3','','6/4','L','7','','','','','1'],
        'expected_bav': [
            [5, 3, 5, 3, 4, 4, 2, 3, 5, 4, 5, 5],
            [3, 2, 5, 3, 6, 3, 4, 5, 5, 5, 3, 5],
            [4, 3, 4, 3, 4, 3, 2, 5, 1, 3, 3, 4],
            [7, 4, 7, 4, 4, 3, 4, 4, 4, 3, 6, 4],
            [4, 3, 5, 6, 3, 7, 4, 3, 5, 6, 5, 5],
            [8, 7, 4, 3, 3, 2, 4, 6, 4, 4, 4, 3],
            [3, 3, 4, 3, 2, 3, 2, 3, 4, 5, 3, 4],
            [5, 5, 6, 3, 6, 3, 1, 7, 3, 4, 3, 3],
        ],
        'expected_sav': [34, 25, 34, 25, 26, 25, 22, 29, 28, 30, 29, 30],
    },
    'pvr_chart_7': {
        'chart': ['6/1/7','','','','','','8/4','L','3/2','0','5',''],
        'expected_bav': [
            [4,2,3,4,6,5,5,3,2,6,6,2],
            [6,3,5,3,5,5,6,3,3,4,4,2],
            [3,2,3,4,2,5,4,3,3,4,3,3],
            [4,6,4,3,4,7,4,5,6,3,5,3],
            [4,4,3,5,6,5,6,4,6,4,3,6],
            [3,5,5,4,6,2,3,6,5,2,7,4],
            [3,2,2,3,5,6,3,4,1,3,6,1],
        ],
        'expected_sav': [27,24,25,26,34,35,31,28,26,26,34,21],
    },
    'pvr_chart_12_sav_only': {
        'chart': ['8','5','','','','L','7','2/4','0/3','1','','6'],
        'expected_bav': None,
        'expected_sav': [24,25,31,28,27,39,33,29,26,22,28,25],
    },
}


def patch_swisseph_for_pyjhora():
    for name in ['SIDM_KRISHNAMURTI_VP291', 'SIDM_TRUE_MULA', 'SIDM_TRUE_CITRA', 'SIDM_TRUE_REVATI']:
        if not hasattr(swe, name):
            setattr(swe, name, getattr(swe, 'SIDM_KRISHNAMURTI', 1))


def load_local_calc():
    if str(SKILL_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SKILL_SCRIPTS))
    from ashtakavarga import calc_ashtakavarga
    return calc_ashtakavarga


def load_pyjhora_calc():
    if str(PYJHORA_COMPAT) not in sys.path:
        sys.path.insert(0, str(PYJHORA_COMPAT))
    if str(PYJHORA_SITE) not in sys.path:
        sys.path.insert(0, str(PYJHORA_SITE))
    patch_swisseph_for_pyjhora()
    from jhora.horoscope.chart import ashtakavarga
    return ashtakavarga.get_ashtaka_varga


def chart_to_local_inputs(chart):
    planets = {}
    asc_idx = None
    for sign_idx, cell in enumerate(chart):
        if not cell:
            continue
        for token in cell.split('/'):
            if token == 'L':
                asc_idx = sign_idx
            elif token in ID_TO_PLANET:
                planets[ID_TO_PLANET[token]] = {'sign': SIGNS[sign_idx]}
    if asc_idx is None:
        raise ValueError('No Lagna in chart')
    return planets, asc_idx


def local_from_chart(chart):
    calc = load_local_calc()
    planets, asc_idx = chart_to_local_inputs(chart)
    result = calc(planets, asc_idx)
    bav = [result['bav'][p]['bindus'] for p in PLANETS_WITH_LAGNA]
    sav = [result['sav']['scores'][s] for s in SIGNS]
    return bav, sav


def pyjhora_from_chart(chart):
    calc = load_pyjhora_calc()
    bav, sav, _ = calc(chart)
    return bav, sav


def add(rows, example, engine, kind, field, got, expected):
    rows.append({
        'example': example,
        'engine': engine,
        'kind': kind,
        'field': field,
        'got': got,
        'expected': expected,
        'status': 'match' if got == expected else 'mismatch',
    })


def summarize(rows, engine, kind=None):
    subset = [r for r in rows if r['engine'] == engine and (kind is None or r['kind'] == kind)]
    total = len(subset)
    match = sum(1 for r in subset if r['status'] == 'match')
    return total, match, total - match, match / total if total else 0.0


def main():
    rows = []
    per_example = []
    for name, ex in EXAMPLES.items():
        chart = ex['chart']
        local_bav, local_sav = local_from_chart(chart)
        py_bav, py_sav = pyjhora_from_chart(chart)
        if ex['expected_bav'] is not None:
            # Some examples provide only seven planetary BAV rows; compare only expected rows.
            for pidx, expected_row in enumerate(ex['expected_bav']):
                planet = PLANETS_WITH_LAGNA[pidx]
                for sidx, expected in enumerate(expected_row):
                    add(rows, name, 'local_skill', 'bav', f'{planet}.{SIGNS[sidx]}', local_bav[pidx][sidx], expected)
                    add(rows, name, 'pyjhora', 'bav', f'{planet}.{SIGNS[sidx]}', py_bav[pidx][sidx], expected)
        for sidx, expected in enumerate(ex['expected_sav']):
            add(rows, name, 'local_skill', 'sav', SIGNS[sidx], local_sav[sidx], expected)
            add(rows, name, 'pyjhora', 'sav', SIGNS[sidx], py_sav[sidx], expected)
        per_example.append({
            'example': name,
            'local_bav': summarize([r for r in rows if r['example'] == name], 'local_skill', 'bav'),
            'pyjhora_bav': summarize([r for r in rows if r['example'] == name], 'pyjhora', 'bav'),
            'local_sav': summarize([r for r in rows if r['example'] == name], 'local_skill', 'sav'),
            'pyjhora_sav': summarize([r for r in rows if r['example'] == name], 'pyjhora', 'sav'),
        })

    with MATRIX.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    lines = []
    lines.append('# Jyotish benchmark 第六轮补充：Ashtakavarga 公开书例仲裁')
    lines.append('')
    lines.append('生成时间：2026-06-03')
    lines.append('')
    lines.append('## 1. 仲裁目的')
    lines.append('')
    lines.append('- 使用 PyJHora `pvr_tests.py` 中嵌入的 PVR 书例 expected BAV/SAV 数组，比较当前 skill 与 PyJHora 哪个更贴近这些公开例题。')
    lines.append('- 这不是复制 PyJHora 代码；只把其测试文件中的 expected arrays 当成外部书例 benchmark。')
    lines.append('- 图表是公开/书例 chart，不包含用户个人资料。')
    lines.append('')
    lines.append('## 2. 总体结果')
    lines.append('')
    lines.append('| Engine | Kind | Total | Match | Mismatch | Match rate |')
    lines.append('|---|---|---:|---:|---:|---:|')
    for engine in ['local_skill', 'pyjhora']:
        for kind in ['bav', 'sav']:
            total, match, mismatch, rate = summarize(rows, engine, kind)
            lines.append(f'| {engine} | {kind} | {total} | {match} | {mismatch} | {rate:.2%} |')
    lines.append('')
    lines.append('## 3. 逐书例摘要')
    lines.append('')
    lines.append('| Example | Local BAV | PyJHora BAV | Local SAV | PyJHora SAV |')
    lines.append('|---|---:|---:|---:|---:|')
    for item in per_example:
        lb = item['local_bav']; pb = item['pyjhora_bav']; ls = item['local_sav']; ps = item['pyjhora_sav']
        lines.append(f"| {item['example']} | {lb[1]}/{lb[0]} | {pb[1]}/{pb[0]} | {ls[1]}/{ls[0]} | {ps[1]}/{ps[0]} |")
    lines.append('')
    lines.append('## 4. 仲裁结论')
    lines.append('')
    lt, lm, lmis, lr = summarize(rows, 'local_skill')
    pt, pm, pmis, pr = summarize(rows, 'pyjhora')
    if lm == lt and pm == pt:
        lines.append('- 当前 skill 与 PyJHora 对 PVR 公开书例均达到 100% 匹配。')
        lines.append('- 这说明 v2.1 Moon/Venus 贡献表项校准已修复第六轮初始差异；Ashtakavarga BAV/SAV 可列为通过。')
    elif pm > lm:
        lines.append('- PyJHora 当前 Ashtakavarga 贡献表对这些 PVR 书例的贴合度明显高于当前 skill。')
        lines.append('- 这说明第六轮暴露的 Moon/Venus 表项差异不宜只归因为“PyJHora 口径不同”；当前 skill 的贡献表需要降级为可疑，并考虑改为 PyJHora/PVR 书例口径。')
        lines.append('- 建议下一步：把 `scripts/ashtakavarga.py` 的差异表项改为 PyJHora/PVR 口径，重跑第六轮、第六轮补充和 regression。')
    else:
        lines.append('- 当前 skill 对书例贴合度不低于 PyJHora，可保留当前口径。')
    REPORT.write_text('\n'.join(lines))
    print(json.dumps({'report': str(REPORT), 'matrix': str(MATRIX), 'rows': len(rows), 'local_matches': lm, 'pyjhora_matches': pm}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
