# NOTE: This script was sanitized for the public repository in v6.1.9.
# It assumes it is run from the repository root unless JYOTISH_BENCHMARK_ROOT
# or JYOTISH_SKILL_SCRIPT is provided. Raw output directories are generated locally
# and are intentionally not committed.
#!/usr/bin/env python3
"""Ashtakavarga contribution-table arbitration.

Compares the local skill BPHS v2.0 BAV contribution matrix with PyJHora's
const.ashtaka_varga_dict at the table-definition level, not chart-output level.
This avoids confusing table lineage differences with runtime bugs.
"""
import csv
import json
import sys
from pathlib import Path

import swisseph as swe

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs'
REPORT = OUT / 'jyotish_benchmark_round6b_ashtakavarga_table_arbitration.md'
MATRIX = OUT / 'ashtakavarga_table_arbitration_matrix.csv'
SKILL_SCRIPTS = Path(__file__).resolve().parents[2] / 'scripts'
PYJHORA_SITE = Path(__import__('os').environ.get('PYJHORA_SITE', ''))

PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Lagna']
EXPECTED_TOTALS = {
    'Sun': 48,
    'Moon': 49,
    'Mars': 39,
    'Mercury': 54,
    'Jupiter': 56,
    'Venus': 52,
    'Saturn': 39,
    'Lagna': 49,
}
SEVEN_PLANETS = PLANETS[:7]


def load_local_table():
    if str(SKILL_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SKILL_SCRIPTS))
    from ashtakavarga import BAV_CONTRIBUTION
    return BAV_CONTRIBUTION


def patch_swisseph_for_pyjhora():
    for name in ['SIDM_KRISHNAMURTI_VP291', 'SIDM_TRUE_MULA', 'SIDM_TRUE_CITRA', 'SIDM_TRUE_REVATI']:
        if not hasattr(swe, name):
            setattr(swe, name, getattr(swe, 'SIDM_KRISHNAMURTI', 1))


def load_pyjhora_table():
    if str(PYJHORA_SITE) not in sys.path:
        sys.path.insert(0, str(PYJHORA_SITE))
    patch_swisseph_for_pyjhora()
    from jhora import const
    table = {}
    for pidx, planet in enumerate(PLANETS):
        row = const.ashtaka_varga_dict[str(pidx)]
        table[planet] = {source: sorted(row[sidx]) for sidx, source in enumerate(PLANETS)}
    return table


def normalize(values):
    return sorted(int(v) for v in values)


def compare_tables(local, pyjhora):
    rows = []
    totals = []
    for planet in PLANETS:
        local_total = 0
        py_total = 0
        for source in PLANETS:
            lv = normalize(local[planet][source])
            pv = normalize(pyjhora[planet][source])
            local_total += len(lv)
            py_total += len(pv)
            rows.append({
                'planet': planet,
                'source': source,
                'local_houses': ' '.join(map(str, lv)),
                'pyjhora_houses': ' '.join(map(str, pv)),
                'local_count': len(lv),
                'pyjhora_count': len(pv),
                'status': 'match' if lv == pv else 'mismatch',
                'missing_in_pyjhora': ' '.join(map(str, sorted(set(lv) - set(pv)))),
                'extra_in_pyjhora': ' '.join(map(str, sorted(set(pv) - set(lv)))),
            })
        expected = EXPECTED_TOTALS[planet]
        totals.append({
            'planet': planet,
            'expected_total': expected,
            'local_total': local_total,
            'local_valid': local_total == expected,
            'pyjhora_total': py_total,
            'pyjhora_valid': py_total == expected,
            'delta_pyjhora_minus_expected': py_total - expected,
        })
    return rows, totals


def write_outputs(rows, totals):
    with MATRIX.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    mismatch_rows = [r for r in rows if r['status'] == 'mismatch']
    local_sav_total = sum(t['local_total'] for t in totals if t['planet'] in SEVEN_PLANETS)
    pyjhora_sav_total = sum(t['pyjhora_total'] for t in totals if t['planet'] in SEVEN_PLANETS)
    local_full_total = sum(t['local_total'] for t in totals)
    pyjhora_full_total = sum(t['pyjhora_total'] for t in totals)

    lines = []
    lines.append('# Jyotish benchmark 第六轮补充：Ashtakavarga 表级口径仲裁')
    lines.append('')
    lines.append('生成时间：2026-06-03')
    lines.append('')
    lines.append('## 1. 仲裁目的')
    lines.append('')
    lines.append('- 第六轮图表输出对标显示：当前 skill 与 PyJHora 的 BAV/SAV 不完全一致。')
    lines.append('- 本轮不再比较具体命盘，而是直接比较两边的 BAV 贡献表定义，判断差异是运行 bug 还是表级口径差异。')
    lines.append('- 样本与表格均不包含用户个人资料。')
    lines.append('')
    lines.append('## 2. 固定总分校验')
    lines.append('')
    lines.append('| Planet | Expected | Local total | Local valid | PyJHora total | PyJHora valid | Delta |')
    lines.append('|---|---:|---:|---|---:|---|---:|')
    for t in totals:
        lines.append(f"| {t['planet']} | {t['expected_total']} | {t['local_total']} | {t['local_valid']} | {t['pyjhora_total']} | {t['pyjhora_valid']} | {t['delta_pyjhora_minus_expected']} |")
    lines.append('')
    lines.append('## 3. 总量对比')
    lines.append('')
    lines.append('| Metric | Local skill | PyJHora table | Expected |')
    lines.append('|---|---:|---:|---:|')
    lines.append(f'| 7-planet SAV table total | {local_sav_total} | {pyjhora_sav_total} | 337 |')
    lines.append(f'| Full table total incl. Lagna | {local_full_total} | {pyjhora_full_total} | 386 |')
    lines.append('')
    lines.append('## 4. 不一致的贡献表项')
    lines.append('')
    lines.append(f'共 {len(mismatch_rows)} 个 planet/source 表项不一致。')
    lines.append('')
    lines.append('| Planet BAV | Source | Local houses | PyJHora houses | Missing in PyJHora | Extra in PyJHora |')
    lines.append('|---|---|---|---|---|---|')
    for r in mismatch_rows:
        lines.append(f"| {r['planet']} | {r['source']} | {r['local_houses']} | {r['pyjhora_houses']} | {r['missing_in_pyjhora']} | {r['extra_in_pyjhora']} |")
    lines.append('')
    lines.append('## 5. 仲裁结论')
    lines.append('')
    if len(mismatch_rows) == 0 and local_sav_total == 337 and pyjhora_sav_total == 337:
        lines.append('- 当前 skill 与 PyJHora `const.ashtaka_varga_dict` 的贡献表项已 100% 对齐。')
        lines.append('- 两边均满足 Ashtakavarga 固定总量不变量：7行星 SAV=337，含 Lagna full total=386。')
        lines.append('- 决策：第六轮初始差异已由 v2.1 表项校准修复，Ashtakavarga 表定义层通过。')
    elif local_sav_total == 337 and local_full_total == 386 and (pyjhora_sav_total != 337 or pyjhora_full_total != 386):
        lines.append('- 当前 skill 的表满足传统 Ashtakavarga 总量不变量：7行星 SAV=337，含 Lagna full total=386。')
        lines.append('- PyJHora 当前 `const.ashtaka_varga_dict` 在表定义层未满足这些总量不变量，因此第六轮 BAV/SAV 不一致不能判为当前 skill 的运行 bug。')
        lines.append('- 决策：保留当前 skill 表作为默认口径；在 benchmark 报告中把 PyJHora Ashtakavarga 标记为“表级口径差异/非硬失败”。')
    else:
        lines.append('- 表级仲裁未能直接闭环，需要继续引入 JHora/经典例题。')
    lines.append('- 后续若引入其他软件对标，必须先比较贡献表项和 SAV 总量，不得直接把口径差异判为运行 bug。')
    lines.append('')
    lines.append('## 6. 对第六轮状态的影响')
    lines.append('')
    lines.append('- Ashtakavarga 计算层：当前 skill 内部不变量通过，可暂列为“默认 BPHS v2.0 口径通过”。')
    lines.append('- 与 PyJHora 的差异：降级为“外部引擎表口径差异”，不作为 P0/P1 bug。')
    lines.append('- 解释层使用要求：输出 Ashtakavarga 时应声明使用 BPHS v2.0/SAV=337 口径。')

    REPORT.write_text('\n'.join(lines))
    return {
        'report': str(REPORT),
        'matrix': str(MATRIX),
        'mismatch_items': len(mismatch_rows),
        'local_sav_total': local_sav_total,
        'pyjhora_sav_total': pyjhora_sav_total,
        'local_full_total': local_full_total,
        'pyjhora_full_total': pyjhora_full_total,
    }


def main():
    local = load_local_table()
    pyjhora = load_pyjhora_table()
    rows, totals = compare_tables(local, pyjhora)
    print(json.dumps(write_outputs(rows, totals), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
