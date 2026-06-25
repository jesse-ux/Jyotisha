# NOTE: This script was sanitized for the public repository in v6.1.9.
# It assumes it is run from the repository root unless JYOTISH_BENCHMARK_ROOT
# or JYOTISH_SKILL_SCRIPT is provided. Raw output directories are generated locally
# and are intentionally not committed.
#!/usr/bin/env python3
import csv
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(os.environ.get('JYOTISH_BENCHMARK_ROOT', Path(__file__).resolve().parents[3])).resolve()
SKILL_SCRIPT = Path(os.environ.get('JYOTISH_SKILL_SCRIPT', REPO_ROOT / 'scripts' / 'jyotish_engine.py')).resolve()
PYTHON = Path(sys.executable)
DATA = ROOT / 'data/benchmark_samples.json'
OUT = ROOT / 'outputs'
RAW = OUT / 'raw'
SHADBALA_OUT = OUT / 'shadbala_invariants'
PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']
NAISARGIKA = {'Sun': 60.0, 'Moon': 51.43, 'Venus': 42.86, 'Jupiter': 34.29, 'Mercury': 25.71, 'Mars': 17.14, 'Saturn': 8.57}
MIN_REQUIRED = {'Sun': 5.0, 'Moon': 6.0, 'Mars': 5.0, 'Mercury': 7.0, 'Jupiter': 6.5, 'Venus': 5.5, 'Saturn': 5.0}


def run_engine(sample, command):
    birth = sample['birth']
    cmd = [
        str(PYTHON), str(SKILL_SCRIPT), command,
        '--year', str(birth['year']),
        '--month', str(birth['month']),
        '--day', str(birth['day']),
        '--hour', str(birth['hour']),
        '--minute', str(birth['minute']),
        '--lat', str(birth['lat']),
        '--lon', str(birth['lon']),
        '--tz', str(birth['tz']),
        '--node-mode', 'mean',
    ]
    if command == 'full-reading':
        today = sample.get('today', '2026-06-03')
        cmd.extend(['--today', today, '--transit-date', today])
    proc = subprocess.run(cmd, text=True, capture_output=True)
    raw_path = RAW / f"{sample['id']}.{command}.shadbala.json"
    if proc.returncode != 0:
        raw_path.write_text(json.dumps({'cmd': cmd, 'returncode': proc.returncode, 'stdout': proc.stdout, 'stderr': proc.stderr}, ensure_ascii=False, indent=2))
        raise RuntimeError(proc.stderr[:500])
    data = json.loads(proc.stdout)
    raw_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return data


def add_row(rows, sample_id, planet, check, local, expected, status, detail=''):
    rows.append({
        'sample_id': sample_id,
        'planet': planet,
        'check': check,
        'local': local,
        'expected': expected,
        'status': status,
        'detail': detail,
    })


def close(a, b, tol=0.05):
    try:
        return abs(float(a) - float(b)) <= tol
    except Exception:
        return False


def validate_shadbala(sample, shadbala, full_reading):
    rows = []
    sid = sample['id']
    planets = shadbala.get('planets', {})
    fr_shadbala = full_reading.get('modules', {}).get('shadbala', {})
    fr_planets = fr_shadbala.get('planets', {})

    add_row(rows, sid, 'module', 'method_present', bool(shadbala.get('method')), True, 'match' if shadbala.get('method') else 'mismatch')
    add_row(rows, sid, 'module', 'seven_planets_present', sorted(planets.keys()), sorted(PLANETS), 'match' if sorted(planets.keys()) == sorted(PLANETS) else 'mismatch')
    add_row(rows, sid, 'module', 'ranking_permutation', sorted(shadbala.get('ranking', [])), sorted(PLANETS), 'match' if sorted(shadbala.get('ranking', [])) == sorted(PLANETS) else 'mismatch')

    totals_for_rank = []
    for pname in PLANETS:
        pdata = planets.get(pname, {})
        fpdata = fr_planets.get(pname, {})
        sthana = pdata.get('sthana_bala', {})
        kala = pdata.get('kala_bala', {})
        required_fields = [
            'sthana_bala', 'dig_bala', 'kala_bala', 'chesta_bala', 'naisargika_bala',
            'drik_bala', 'total_virupas', 'total_rupas', 'min_required', 'ishta_bala_pct',
            'strength_level', 'rank'
        ]
        missing = [field for field in required_fields if field not in pdata]
        add_row(rows, sid, pname, 'required_fields', missing, [], 'match' if not missing else 'mismatch')

        component_sum = (
            float(sthana.get('total', 0)) + float(pdata.get('dig_bala', 0)) + float(kala.get('total', 0)) +
            float(pdata.get('chesta_bala', 0)) + float(pdata.get('naisargika_bala', 0)) + float(pdata.get('drik_bala', 0))
        )
        total_virupas = pdata.get('total_virupas')
        add_row(rows, sid, pname, 'total_virupas_sum', total_virupas, round(component_sum, 2), 'match' if close(total_virupas, component_sum, 0.08) else 'mismatch')
        add_row(rows, sid, pname, 'total_rupas_conversion', pdata.get('total_rupas'), round(float(total_virupas) / 60.0, 4) if total_virupas is not None else None, 'match' if total_virupas is not None and close(pdata.get('total_rupas'), float(total_virupas) / 60.0, 0.005) else 'mismatch')
        min_req = MIN_REQUIRED[pname]
        add_row(rows, sid, pname, 'min_required_constant', pdata.get('min_required'), min_req, 'match' if close(pdata.get('min_required'), min_req, 0.001) else 'mismatch')
        expected_ishta = float(pdata.get('total_rupas', 0)) / min_req * 100.0
        add_row(rows, sid, pname, 'ishta_pct_formula', pdata.get('ishta_bala_pct'), round(expected_ishta, 1), 'match' if close(pdata.get('ishta_bala_pct'), expected_ishta, 0.15) else 'mismatch')

        range_checks = {
            'sthana.ucha_bala_range': (sthana.get('ucha_bala'), 0, 60),
            'sthana.ojayugma_enum': (sthana.get('ojayugma_bala'), {0, 15}, None),
            'sthana.kendra_enum': (sthana.get('kendra_bala'), {15.0, 30.0, 60.0}, None),
            'sthana.drekkana_enum': (sthana.get('drekkana_bala'), {0, 15}, None),
            'dig_bala_range': (pdata.get('dig_bala'), 0, 60),
            'kala.total_range': (kala.get('total'), 0, 225),
            'chesta_bala_range': (pdata.get('chesta_bala'), 0, 60),
            'drik_bala_range': (pdata.get('drik_bala'), -60, 60),
        }
        for check, spec in range_checks.items():
            val = spec[0]
            if isinstance(spec[1], set):
                ok = val in spec[1]
                expected = sorted(spec[1])
            else:
                lo, hi = spec[1], spec[2]
                ok = val is not None and lo <= float(val) <= hi
                expected = f'{lo}..{hi}'
            add_row(rows, sid, pname, check, val, expected, 'match' if ok else 'mismatch')

        add_row(rows, sid, pname, 'naisargika_constant', pdata.get('naisargika_bala'), NAISARGIKA[pname], 'match' if close(pdata.get('naisargika_bala'), NAISARGIKA[pname], 0.001) else 'mismatch')
        add_row(rows, sid, pname, 'full_reading_total_match', fpdata.get('total_rupas'), pdata.get('total_rupas'), 'match' if close(fpdata.get('total_rupas'), pdata.get('total_rupas'), 0.001) else 'mismatch')
        add_row(rows, sid, pname, 'full_reading_rank_match', fpdata.get('rank'), pdata.get('rank'), 'match' if fpdata.get('rank') == pdata.get('rank') else 'mismatch')
        totals_for_rank.append((pname, float(pdata.get('total_rupas', -999)), pdata.get('rank')))

    sorted_rank = [p for p, _, _ in sorted(totals_for_rank, key=lambda item: item[1], reverse=True)]
    add_row(rows, sid, 'module', 'ranking_sorted_by_total', shadbala.get('ranking'), sorted_rank, 'match' if shadbala.get('ranking') == sorted_rank else 'mismatch')
    add_row(rows, sid, 'module', 'strongest_matches_rank', shadbala.get('strongest'), sorted_rank[0] if sorted_rank else None, 'match' if shadbala.get('strongest') == (sorted_rank[0] if sorted_rank else None) else 'mismatch')
    add_row(rows, sid, 'module', 'weakest_matches_rank', shadbala.get('weakest'), sorted_rank[-1] if sorted_rank else None, 'match' if shadbala.get('weakest') == (sorted_rank[-1] if sorted_rank else None) else 'mismatch')

    fr_total = fr_shadbala.get('total_shadbala')
    expected_total = round(sum(float(planets[p].get('total_rupas', 0)) for p in PLANETS), 2)
    add_row(rows, sid, 'module', 'full_reading_total_shadbala', fr_total, expected_total, 'match' if close(fr_total, expected_total, 0.01) else 'mismatch')
    add_row(rows, sid, 'module', 'full_reading_total_min_required', fr_shadbala.get('total_min_required'), round(sum(MIN_REQUIRED.values()), 2), 'match' if close(fr_shadbala.get('total_min_required'), sum(MIN_REQUIRED.values()), 0.01) else 'mismatch')
    return rows


def write_report(rows):
    total = len(rows)
    matches = sum(1 for r in rows if r['status'] == 'match')
    mismatches = [r for r in rows if r['status'] == 'mismatch']
    by_check = {}
    for r in rows:
        by_check.setdefault(r['check'], {'total': 0, 'match': 0, 'mismatch': 0})
        by_check[r['check']]['total'] += 1
        by_check[r['check']][r['status']] = by_check[r['check']].get(r['status'], 0) + 1

    lines = []
    lines.append('# Jyotish benchmark 第九轮 Shadbala 内部不变量报告')
    lines.append('')
    lines.append(f'生成时间：{date.today().isoformat()}')
    lines.append('')
    lines.append('## 1. 范围')
    lines.append('')
    lines.append('- 样本：10个公开/虚构 smoke case，不包含真实用户个人资料。')
    lines.append('- 对比对象：`shadbala` 子命令与 `full-reading.modules.shadbala`。')
    lines.append('- 验证类型：结构完整性、六重力量组件范围、总分公式、Rupa/Virupa换算、排名一致性、full-reading输出一致性。')
    lines.append('- 重要边界：本轮不是外部软件绝对值对标；当前本地未找到稳定可用的完整 Shadbala 外部基准，因此只能证明内部一致性，不能证明传统公式完全一致。')
    lines.append('')
    lines.append('## 2. 总体结果')
    lines.append('')
    lines.append(f'- 检查总数：{total}')
    lines.append(f'- 通过：{matches}')
    lines.append(f'- 失败：{len(mismatches)}')
    lines.append(f'- 通过率：{matches / total:.2%}' if total else '- 通过率：N/A')
    lines.append('')
    lines.append('## 3. 分检查项结果')
    lines.append('')
    lines.append('| Check | Total | Match | Mismatch |')
    lines.append('|---|---:|---:|---:|')
    for check, stat in sorted(by_check.items()):
        lines.append(f"| {check} | {stat['total']} | {stat.get('match', 0)} | {stat.get('mismatch', 0)} |")
    lines.append('')
    if mismatches:
        lines.append('## 4. 失败样例')
        lines.append('')
        lines.append('| Sample | Planet | Check | Local | Expected | Detail |')
        lines.append('|---|---|---|---|---|---|')
        for r in mismatches[:120]:
            lines.append(f"| {r['sample_id']} | {r['planet']} | {r['check']} | {r['local']} | {r['expected']} | {r['detail']} |")
        lines.append('')
    lines.append('## 5. 结论')
    lines.append('')
    if mismatches:
        lines.append('- Shadbala 内部一致性存在失败项，应先修复输出或公式聚合。')
    else:
        lines.append('- Shadbala 输出结构、总分聚合、Rupa/Virupa换算、排名、full-reading一致性均通过内部不变量验证。')
    lines.append('- 本报告验证内部绝对值不变量：每颗星 total_virupas 等于 Sthana/Dig/Kala/Chesta/Naisargika/Drik 六项合计，且 total_rupas = total_virupas / 60。')
    lines.append('- 这不是外部软件逐项对标；传统 Parashara Shadbala 的最终置信度仍需要 JHora/PyJHora/PDF oracle 做逐项差异审计。')
    report = OUT / 'jyotish_benchmark_round9_shadbala_invariants.md'
    report.write_text('\n'.join(lines))
    return report


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    SHADBALA_OUT.mkdir(parents=True, exist_ok=True)
    samples = json.loads(DATA.read_text())
    all_rows = []
    for sample in samples:
        shadbala = run_engine(sample, 'shadbala')
        full_reading = run_engine(sample, 'full-reading')
        (SHADBALA_OUT / f"{sample['id']}.shadbala.json").write_text(json.dumps(shadbala, ensure_ascii=False, indent=2))
        all_rows.extend(validate_shadbala(sample, shadbala, full_reading))
    csv_path = OUT / 'shadbala_invariants_matrix.csv'
    with csv_path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_id', 'planet', 'check', 'local', 'expected', 'status', 'detail'])
        writer.writeheader()
        writer.writerows(all_rows)
    report = write_report(all_rows)
    print(json.dumps({
        'rows': len(all_rows),
        'matches': sum(1 for r in all_rows if r['status'] == 'match'),
        'mismatches': sum(1 for r in all_rows if r['status'] == 'mismatch'),
        'csv': str(csv_path),
        'report': str(report),
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
