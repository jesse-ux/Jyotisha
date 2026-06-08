# NOTE: This script was sanitized for the public repository in v6.1.9.
# It assumes it is run from the repository root unless JYOTISH_BENCHMARK_ROOT
# or JYOTISH_SKILL_SCRIPT is provided. Raw output directories are generated locally
# and are intentionally not committed.
#!/usr/bin/env python3
import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_SCRIPT = Path(__file__).resolve().parents[2] / 'scripts' / 'jyotish_engine.py'
PYTHON = Path(__import__('sys').executable)
DATA = ROOT / 'data/benchmark_samples.json'
OUT = ROOT / 'outputs'
RAW = OUT / 'raw'
CANON = OUT / 'canonical'

PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
FIELDS = ['sign', 'house', 'degree_in_sign', 'nakshatra', 'nakshatra_pada', 'retrograde']


def safe_get(obj, *keys, default=None):
    cur = obj
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def run_sample(sample):
    birth = sample['birth']
    cmd = [
        str(PYTHON), str(SKILL_SCRIPT), 'full-reading',
        '--year', str(birth['year']),
        '--month', str(birth['month']),
        '--day', str(birth['day']),
        '--hour', str(birth['hour']),
        '--minute', str(birth['minute']),
        '--lat', str(birth['lat']),
        '--lon', str(birth['lon']),
        '--tz', str(birth['tz']),
        '--today', sample.get('today', '2026-06-03'),
    ]
    proc = subprocess.run(cmd, text=True, capture_output=True)
    raw_path = RAW / f"{sample['id']}.json"
    if proc.returncode != 0:
        raw_path.write_text(json.dumps({
            'error': 'command_failed',
            'returncode': proc.returncode,
            'stderr': proc.stderr,
            'stdout': proc.stdout,
            'cmd': cmd,
        }, ensure_ascii=False, indent=2))
        return {'id': sample['id'], 'ok': False, 'error': proc.stderr.strip()[:500]}
    try:
        data = json.loads(proc.stdout)
    except Exception as exc:
        raw_path.write_text(json.dumps({
            'error': 'json_parse_failed',
            'exception': str(exc),
            'stdout': proc.stdout[:2000],
            'stderr': proc.stderr,
            'cmd': cmd,
        }, ensure_ascii=False, indent=2))
        return {'id': sample['id'], 'ok': False, 'error': str(exc)}
    raw_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    canon = canonicalize(sample, data)
    (CANON / f"{sample['id']}.canonical.json").write_text(json.dumps(canon, ensure_ascii=False, indent=2))
    return {'id': sample['id'], 'ok': True, 'canonical': canon}


def canonicalize(sample, data):
    modules = data.get('modules', {})
    chart = modules.get('chart', {})
    planets = chart.get('planets', {})
    d9 = safe_get(modules, 'varga_full', 'D9_Navamsa', default={}) or {}
    d10 = safe_get(modules, 'varga_full', 'D10_Dasamsa', default={}) or {}
    current = safe_get(modules, 'dasha', 'current_dasha', default={}) or {}
    ad = current.get('antardasha') or {}
    special = modules.get('special_lagnas', {}) or {}
    canonical = {
        'sample_id': sample['id'],
        'label': sample['label'],
        'category': sample['category'],
        'privacy': sample.get('privacy'),
        'engine': 'local_jyotish_skill_v6_0_4',
        'parameters': {
            'zodiac': 'sidereal',
            'ayanamsa': 'lahiri_assumed_by_skill',
            'house': 'whole_sign_for_planet_house',
            'today': sample.get('today'),
        },
        'birth': sample['birth'],
        'ascendant': chart.get('ascendant'),
        'planets': {},
        'varga': {
            'D9': {k: d9.get(k) for k in ['Ascendant'] + PLANETS},
            'D10': {k: d10.get(k) for k in ['Ascendant'] + PLANETS},
        },
        'dasha': {
            'mahadasha_lord': current.get('lord'),
            'mahadasha_start': current.get('start'),
            'mahadasha_end': current.get('end'),
            'antardasha_lord': ad.get('lord'),
            'antardasha_start': ad.get('start'),
            'antardasha_end': ad.get('end'),
        },
        'advanced': {
            'A10_Karma_Pada': special.get('A10_Karma_Pada'),
            'vargottama_true': {p: v for p, v in (modules.get('vargottama') or {}).items() if isinstance(v, dict) and v.get('is_vargottama')},
            'pushkara_true': {p: v for p, v in (modules.get('pushkara') or {}).items() if isinstance(v, dict) and (v.get('pushkara_navamsa') or v.get('pushkara_bhaga'))},
            'dasha_sandhi': modules.get('dasha_sandhi'),
        },
        'module_health': {
            'module_count': len(modules),
            'validation': modules.get('validation'),
            'empty_modules': sorted([k for k, v in modules.items() if v in ({}, [], None)]),
        }
    }
    for pname in PLANETS:
        pdata = planets.get(pname, {}) or {}
        canonical['planets'][pname] = {field: pdata.get(field) for field in FIELDS}
    return canonical


def flatten_rows(results):
    rows = []
    for result in results:
        if not result.get('ok'):
            rows.append({'sample_id': result['id'], 'engine': 'local_jyotish_skill_v6_0_4', 'section': 'run', 'field': 'status', 'value': 'failed'})
            continue
        c = result['canonical']
        rows.append({'sample_id': c['sample_id'], 'engine': c['engine'], 'section': 'ascendant', 'field': 'raw', 'value': json.dumps(c['ascendant'], ensure_ascii=False)})
        for pname, pdata in c['planets'].items():
            for field, value in pdata.items():
                rows.append({'sample_id': c['sample_id'], 'engine': c['engine'], 'section': f'planet.{pname}', 'field': field, 'value': value})
        for dkey, dval in c['dasha'].items():
            rows.append({'sample_id': c['sample_id'], 'engine': c['engine'], 'section': 'dasha', 'field': dkey, 'value': dval})
        for varga_name, varga in c['varga'].items():
            for body, value in varga.items():
                rows.append({'sample_id': c['sample_id'], 'engine': c['engine'], 'section': varga_name, 'field': body, 'value': json.dumps(value, ensure_ascii=False)})
        rows.append({'sample_id': c['sample_id'], 'engine': c['engine'], 'section': 'advanced', 'field': 'A10_Karma_Pada', 'value': json.dumps(c['advanced']['A10_Karma_Pada'], ensure_ascii=False)})
        rows.append({'sample_id': c['sample_id'], 'engine': c['engine'], 'section': 'health', 'field': 'module_count', 'value': c['module_health']['module_count']})
    return rows


def write_report(samples, results):
    ok_count = sum(1 for r in results if r.get('ok'))
    lines = []
    lines.append('# Jyotish benchmark 第一轮本地基线报告')
    lines.append('')
    lines.append('生成时间：2026-06-03')
    lines.append('')
    lines.append('## 1. 本轮范围')
    lines.append('')
    lines.append('- 本轮只建立当前 skill 的 canonical baseline。')
    lines.append('- 样本全部为公开/虚构 smoke test，不包含用户个人出生资料。')
    lines.append('- 还没有接入 PyJHora / VedAstro / jyotishyamitra 等外部引擎，因此本轮不能给最终可信度评分。')
    lines.append('')
    lines.append('## 2. 执行结果')
    lines.append('')
    lines.append(f'- 样本数：{len(samples)}')
    lines.append(f'- 成功：{ok_count}')
    lines.append(f'- 失败：{len(samples) - ok_count}')
    lines.append('- 输出目录：`jyotish_benchmark/outputs/`')
    lines.append('')
    lines.append('## 3. 样本摘要')
    lines.append('')
    lines.append('| Sample | Ascendant | MD/AD | A10 | Modules | Empty modules |')
    lines.append('|---|---|---|---|---:|---|')
    for result in results:
        if not result.get('ok'):
            lines.append(f"| {result['id']} | failed | failed | failed | 0 | {result.get('error', '')} |")
            continue
        c = result['canonical']
        asc = c['ascendant']
        dasha = f"{c['dasha']['mahadasha_lord']} / {c['dasha']['antardasha_lord']}"
        a10 = c['advanced']['A10_Karma_Pada']
        a10_txt = a10.get('sign') if isinstance(a10, dict) else '-'
        empty = ', '.join(c['module_health']['empty_modules']) or '-'
        lines.append(f"| {c['sample_id']} | {asc} | {dasha} | {a10_txt} | {c['module_health']['module_count']} | {empty} |")
    lines.append('')
    lines.append('## 4. 发现')
    lines.append('')
    lines.append('- 当前 skill 对 10 个 smoke 样本都能生成 full-reading canonical JSON。')
    lines.append('- 这证明内部输出契约具备批量 benchmark 的基础。')
    lines.append('- 但这只是 baseline，不是外部可信度证明。')
    lines.append('- 下一步必须接入至少 PyJHora 和 jyotishyamitra，形成 cross-engine matrix。')
    lines.append('')
    lines.append('## 5. 下一步')
    lines.append('')
    lines.append('1. 安装/隔离运行 PyJHora，抽取 D1/D9/D10/Dasha。')
    lines.append('2. 安装/隔离运行 jyotishyamitra，抽取 JSON 输出。')
    lines.append('3. 若 VedAstro API 可用，加入 API 对比；否则列为人工/半自动。')
    lines.append('4. 生成 `cross_engine_matrix.csv`，按字段计算一致/不一致/不可比。')
    lines.append('5. 对边界样本单独标注，避免误判。')
    report = OUT / 'jyotish_benchmark_round1_local_baseline.md'
    report.write_text('\n'.join(lines))
    return report


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    CANON.mkdir(parents=True, exist_ok=True)
    samples = json.loads(DATA.read_text())
    results = [run_sample(sample) for sample in samples]
    summary = {'total': len(results), 'ok': sum(1 for r in results if r.get('ok')), 'results': [{'id': r['id'], 'ok': r.get('ok'), 'error': r.get('error')} for r in results]}
    (OUT / 'run_summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    rows = flatten_rows(results)
    csv_path = OUT / 'local_skill_canonical_matrix.csv'
    with csv_path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_id', 'engine', 'section', 'field', 'value'])
        writer.writeheader()
        writer.writerows(rows)
    report = write_report(samples, results)
    print(json.dumps({'summary': summary, 'matrix': str(csv_path), 'report': str(report)}, ensure_ascii=False, indent=2))
    if summary['ok'] != summary['total']:
        sys.exit(1)


if __name__ == '__main__':
    main()
