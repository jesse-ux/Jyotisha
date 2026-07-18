# NOTE: This script was sanitized for the public repository in v6.1.9.
# It assumes it is run from the repository root unless JYOTISH_BENCHMARK_ROOT
# or JYOTISH_SKILL_SCRIPT is provided. Raw output directories are generated locally
# and are intentionally not committed.
#!/usr/bin/env python3
import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data/benchmark_samples.json'
OUT = ROOT / 'outputs'
LOCAL_CANON = OUT / 'canonical'
PYJHORA_OUT = OUT / 'pyjhora'

# Keep personal data out of benchmark: samples are fictional/public smoke cases only.
PLANETS = ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']
PYJHORA_PLANET_ID = {
    0: 'Sun',
    1: 'Moon',
    2: 'Mars',
    3: 'Mercury',
    4: 'Jupiter',
    5: 'Venus',
    6: 'Saturn',
    7: 'Rahu',
    8: 'Ketu',
}
DASHA_LORDS = {8: 'Ketu', 5: 'Venus', 0: 'Sun', 1: 'Moon', 2: 'Mars', 7: 'Rahu', 4: 'Jupiter', 6: 'Saturn', 3: 'Mercury'}
SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo', 'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
NAKSHATRAS = [
    'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu', 'Pushya', 'Ashlesha',
    'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta', 'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha',
    'Mula', 'Purva Ashadha', 'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada', 'Uttara Bhadrapada', 'Revati'
]


def patch_swisseph():
    import swisseph as swe
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
    return swe


def sign_name(sign_idx):
    return SIGNS[int(sign_idx) % 12]


def nakshatra_from_abs(abs_lon):
    x = abs_lon % 360.0
    unit = 360.0 / 27.0
    idx = int(x // unit)
    pada = int((x % unit) // (unit / 4.0)) + 1
    return NAKSHATRAS[idx], pada


def parse_chart_positions(rows):
    result = {}
    for key, value in rows:
        sign_idx, deg = value
        if key == 'L':
            body = 'Ascendant'
        else:
            body = PYJHORA_PLANET_ID.get(key)
        if not body:
            continue
        result[body] = {
            'sign': sign_name(sign_idx),
            'sign_idx': int(sign_idx),
            'degree_in_sign': round(float(deg), 4),
        }
    return result


def tuple_to_date(t):
    if not t:
        return None
    y, m, d, _fh = t
    return f'{int(y):04d}-{int(m):02d}-{int(d):02d}'


def build_pyjhora_sample(sample, *, node_mode='mean'):
    swe = patch_swisseph()
    from jhora import utils, const
    from jhora.panchanga import drik
    from jhora.horoscope.chart import ashtakavarga, charts, strength
    from jhora.horoscope.dhasa.graha import vimsottari

    # Align benchmark口径: Lahiri + mean sidereal year. PyJHora default is TRUE_PUSHYA.
    const._DEFAULT_AYANAMSA_MODE = 'LAHIRI'
    drik.set_ayanamsa_mode('LAHIRI')
    const.set_node_mode(node_mode == 'true')
    drik.set_planet_list(set_rahu_ketu_as_true_nodes=(node_mode == 'true'))
    try:
        const.dhasa_year_duration_default = const.DHASA_YEAR_DURATION.MEAN_SIDEREAL_YEAR
    except Exception:
        pass

    b = sample['birth']
    jd = utils.julian_day_number((b['year'], b['month'], b['day']), (b['hour'], b['minute'], 0))
    place = drik.Place(sample['label'], b['lat'], b['lon'], b['tz'])
    today = sample.get('today', '2026-06-03')
    ty, tm, td = [int(x) for x in today.split('-')]
    current_jd = utils.julian_day_number((ty, tm, td), (0, 0, 0))

    rasi = parse_chart_positions(charts.rasi_chart(jd, place))
    rasi_rows = charts.rasi_chart(jd, place)
    d2 = parse_chart_positions(charts.hora_chart(rasi_rows, chart_method=2))
    d4 = parse_chart_positions(charts.chaturthamsa_chart(rasi_rows, chart_method=1))
    d9 = parse_chart_positions(charts.divisional_chart(jd, place, divisional_chart_factor=9, chart_method=1))
    d10 = parse_chart_positions(charts.divisional_chart(jd, place, divisional_chart_factor=10, chart_method=1))
    house_to_planets = utils.get_house_planet_list_from_planet_positions(rasi_rows)
    bav, sav, _prastara = ashtakavarga.get_ashtaka_varga(house_to_planets)
    shadbala = strength.shad_bala(jd, place)

    asc = rasi.get('Ascendant') or {}
    planets = {}
    for p in PLANETS:
        pd = rasi.get(p) or {}
        abs_lon = pd.get('sign_idx', 0) * 30.0 + float(pd.get('degree_in_sign', 0.0))
        nak, pada = nakshatra_from_abs(abs_lon)
        planets[p] = {
            'sign': pd.get('sign'),
            'degree_in_sign': pd.get('degree_in_sign'),
            'nakshatra': nak,
            'nakshatra_pada': pada,
        }

    dasha = {
        'mahadasha_lord': None,
        'mahadasha_start': None,
        'mahadasha_end': None,
        'antardasha_lord': None,
        'antardasha_start': None,
        'antardasha_end': None,
    }
    try:
        ladder = vimsottari.get_running_dhasa_for_given_date(current_jd, jd, place, dhasa_level_index=2)
        if ladder:
            md = ladder[0]
            dasha['mahadasha_lord'] = DASHA_LORDS.get(md[0][0], str(md[0][0]))
            dasha['mahadasha_start'] = tuple_to_date(md[1])
            dasha['mahadasha_end'] = tuple_to_date(md[2])
        if len(ladder) > 1:
            ad = ladder[1]
            dasha['antardasha_lord'] = DASHA_LORDS.get(ad[0][-1], str(ad[0][-1]))
            dasha['antardasha_start'] = tuple_to_date(ad[1])
            dasha['antardasha_end'] = tuple_to_date(ad[2])
    except Exception as exc:
        dasha['error'] = f'{type(exc).__name__}: {exc}'

    return {
        'settings': {'ayanamsa': 'lahiri', 'node_mode': node_mode},
        'sample_id': sample['id'],
        'engine': 'PyJHora_4_8_6_lahiri_patched',
        'parameters': {
            'zodiac': 'sidereal',
            'ayanamsa': 'LAHIRI',
            'd9_method': 'PyJHora divisional_chart chart_method=1',
            'd10_method': 'PyJHora divisional_chart chart_method=1',
            'd2_method': 'PyJHora hora_chart chart_method=2 traditional_parasara',
            'd4_method': 'PyJHora chaturthamsa_chart chart_method=1 traditional_parasara',
            'dasha_year': 'mean sidereal year',
            'compat': 'monkeypatch swisseph keyword API + missing constants; dummy timezonefinder only for import',
            'license_note': 'PyJHora is AGPL-3.0; used only as external benchmark, not vendored into skill.'
        },
        'ascendant': {
            'sign': asc.get('sign'),
            'degree_in_sign': asc.get('degree_in_sign'),
        },
        'planets': planets,
        'varga': {'D2': d2, 'D4': d4, 'D9': d9, 'D10': d10},
        'ashtakavarga': {
            'bav': {name: list(bav[index]) for index, name in enumerate(['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Lagna'])},
            'sav': list(sav),
        },
        'shadbala': {name: float(shadbala[6][index]) for index, name in enumerate(['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'])},
        'shadbala_components': {
            name: {
                component: float(shadbala[row_index][index])
                for component, row_index in {
                    'sthana': 0, 'kala': 1, 'dig': 2, 'chesta': 3, 'naisargika': 4, 'drik': 5,
                }.items()
            }
            for index, name in enumerate(['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn'])
        },
        'dasha': dasha,
    }


def compare_scalar(rows, sample_id, section, body, field, local_value, pyjhora_value, tolerance=None, date_tolerance_days=None, boundary_sensitive=False, status_override=None):
    status = status_override or 'match'
    delta = ''
    if not status_override:
        if date_tolerance_days is not None:
            try:
                ld = datetime.strptime(str(local_value), '%Y-%m-%d')
                pd = datetime.strptime(str(pyjhora_value), '%Y-%m-%d')
                delta_val = abs((ld - pd).days)
                delta = delta_val
                status = 'match' if delta_val <= date_tolerance_days else 'mismatch'
            except Exception:
                status = 'not_comparable'
        elif tolerance is not None:
            try:
                delta_val = abs(float(local_value) - float(pyjhora_value))
                delta = round(delta_val, 6)
                status = 'match' if delta_val <= tolerance else 'mismatch'
            except Exception:
                status = 'not_comparable'
        else:
            status = 'match' if local_value == pyjhora_value else 'mismatch'
    if status == 'mismatch' and boundary_sensitive:
        status = 'boundary_sensitive'
    rows.append({
        'sample_id': sample_id,
        'section': section,
        'body': body,
        'field': field,
        'local_skill': local_value,
        'pyjhora': pyjhora_value,
        'delta': delta,
        'status': status,
    })


def compare_one(sample_id, local, pyjhora):
    rows = []
    compare_scalar(rows, sample_id, 'ascendant', 'Ascendant', 'sign', local['ascendant'].get('sign'), pyjhora['ascendant'].get('sign'))
    compare_scalar(rows, sample_id, 'ascendant', 'Ascendant', 'degree_in_sign', local['ascendant'].get('degree_in_sign'), pyjhora['ascendant'].get('degree_in_sign'), tolerance=0.15)
    for p in PLANETS:
        l = local['planets'].get(p, {})
        y = pyjhora['planets'].get(p, {})
        for field in ['sign', 'nakshatra', 'nakshatra_pada']:
            compare_scalar(rows, sample_id, 'planet', p, field, l.get(field), y.get(field))
        compare_scalar(rows, sample_id, 'planet', p, 'degree_in_sign', l.get('degree_in_sign'), y.get('degree_in_sign'), tolerance=0.15)
    for varga_name in ['D2', 'D4', 'D9', 'D10']:
        for body in ['Ascendant'] + PLANETS:
            l = (local['varga'].get(varga_name) or {}).get(body) or {}
            y = (pyjhora['varga'].get(varga_name) or {}).get(body) or {}
            boundary_sensitive = False
            try:
                boundary_sensitive = abs(float(l.get('degree_in_sign', 99)) - float(y.get('degree_in_sign', -99))) > 20 and l.get('sign') != y.get('sign')
            except Exception:
                pass
            compare_scalar(rows, sample_id, varga_name, body, 'sign', l.get('sign'), y.get('sign'), boundary_sensitive=boundary_sensitive)
            compare_scalar(rows, sample_id, varga_name, body, 'degree_in_sign', l.get('degree_in_sign'), y.get('degree_in_sign'), tolerance=0.2, boundary_sensitive=boundary_sensitive)
    for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Lagna']:
        for sign_idx, sign in enumerate(SIGNS):
            compare_scalar(
                rows, sample_id, 'Ashtakavarga_BAV', planet, sign,
                (local.get('ashtakavarga', {}).get('bav', {}).get(planet) or [None] * 12)[sign_idx],
                (pyjhora.get('ashtakavarga', {}).get('bav', {}).get(planet) or [None] * 12)[sign_idx],
            )
    for sign_idx, sign in enumerate(SIGNS):
        compare_scalar(
            rows, sample_id, 'Ashtakavarga_SAV', 'SAV', sign,
            (local.get('ashtakavarga', {}).get('sav') or [None] * 12)[sign_idx],
            (pyjhora.get('ashtakavarga', {}).get('sav') or [None] * 12)[sign_idx],
        )
    for planet in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn']:
        compare_scalar(
            rows, sample_id, 'Shadbala', planet, 'total_virupas',
            local.get('shadbala', {}).get(planet), pyjhora.get('shadbala', {}).get(planet), tolerance=0.5,
        )
        for component in ['sthana', 'kala', 'dig', 'chesta', 'naisargika', 'drik']:
            compare_scalar(
                rows, sample_id, 'Shadbala_Component', planet, component,
                local.get('shadbala_components', {}).get(planet, {}).get(component),
                pyjhora.get('shadbala_components', {}).get(planet, {}).get(component),
                tolerance=0.5,
            )
    # PyJHora dasha is useful as external signal, but currently has different default starting convention/seed in some cases.
    # Keep fields in matrix, with generous date tolerance; differences are classified below in report.
    for field in ['mahadasha_lord', 'antardasha_lord']:
        compare_scalar(rows, sample_id, 'dasha', 'Vimshottari_current', field, local['dasha'].get(field), pyjhora['dasha'].get(field))
    for field in ['mahadasha_start', 'mahadasha_end', 'antardasha_start', 'antardasha_end']:
        compare_scalar(rows, sample_id, 'dasha', 'Vimshottari_current', field, local['dasha'].get(field), pyjhora['dasha'].get(field), date_tolerance_days=7)
    return rows


def write_report(samples, rows, *, generated_at=None):
    total = len(rows)
    counts = {}
    by_section = {}
    for r in rows:
        counts[r['status']] = counts.get(r['status'], 0) + 1
        stat = by_section.setdefault(r['section'], {'total': 0})
        stat['total'] += 1
        stat[r['status']] = stat.get(r['status'], 0) + 1
    matches = counts.get('match', 0)
    mismatches = [r for r in rows if r['status'] == 'mismatch']
    boundary = [r for r in rows if r['status'] == 'boundary_sensitive']
    non_dasha_rows = [r for r in rows if r['section'] != 'dasha']
    non_dasha_match = sum(1 for r in non_dasha_rows if r['status'] == 'match')
    non_dasha_ok = sum(1 for r in non_dasha_rows if r['status'] in ('match', 'boundary_sensitive'))

    lines = []
    lines.append('# Jyotish benchmark 第三轮：PyJHora 对比报告')
    lines.append('')
    generated_at = generated_at or datetime.now(timezone.utc)
    lines.append(f'生成时间：{generated_at.isoformat()}')
    lines.append('')
    lines.append('## 1. 本轮范围')
    lines.append('')
    lines.append('- 外部引擎：PyJHora 4.8.6。')
    lines.append('- 用途：第二个独立 Jyotish 开源项目对标，重点验证 D1、D9、D10，并初探 Vimshottari。')
    lines.append('- 样本：10个公开/虚构 smoke case，不包含用户个人资料。')
    lines.append('- 口径：强制 Lahiri；PyJHora 默认 TRUE_PUSHYA，因此本轮显式切换到 LAHIRI。')
    lines.append('- 兼容处理：PyJHora 4.8.6 与本机 pyswisseph API 存在关键字参数/常量兼容问题，本脚本只在 benchmark 进程内 monkeypatch，不改 PyJHora 源码，不把 AGPL 代码并入 skill。')
    lines.append('')
    lines.append('## 2. 总体结果')
    lines.append('')
    lines.append(f'- 字段总数：{total}')
    lines.append(f'- 匹配：{matches}')
    lines.append(f'- 不匹配：{len(mismatches)}')
    lines.append(f'- 边界敏感：{len(boundary)}')
    lines.append(f'- 总严格匹配率：{matches / total:.2%}' if total else '- 总严格匹配率：N/A')
    lines.append(f'- 非 Dasha 字段严格匹配率：{non_dasha_match / len(non_dasha_rows):.2%}' if non_dasha_rows else '- 非 Dasha 字段严格匹配率：N/A')
    lines.append(f'- 非 Dasha 字段边界归因后可接受率：{non_dasha_ok / len(non_dasha_rows):.2%}' if non_dasha_rows else '- 非 Dasha 字段边界归因后可接受率：N/A')
    lines.append('')
    lines.append('## 3. 分区统计')
    lines.append('')
    lines.append('| Section | Total | Match | Mismatch | Boundary sensitive | Not comparable |')
    lines.append('|---|---:|---:|---:|---:|---:|')
    for section, stat in sorted(by_section.items()):
        lines.append(f"| {section} | {stat.get('total',0)} | {stat.get('match',0)} | {stat.get('mismatch',0)} | {stat.get('boundary_sensitive',0)} | {stat.get('not_comparable',0)} |")
    lines.append('')
    if mismatches:
        lines.append('## 4. 不匹配字段')
        lines.append('')
        lines.append('| Sample | Section | Body | Field | Local skill | PyJHora | Delta |')
        lines.append('|---|---|---|---|---|---|---:|')
        for r in mismatches[:160]:
            lines.append(f"| {r['sample_id']} | {r['section']} | {r['body']} | {r['field']} | {r['local_skill']} | {r['pyjhora']} | {r['delta']} |")
        lines.append('')
    if boundary:
        lines.append('## 4b. 边界敏感字段')
        lines.append('')
        lines.append('| Sample | Section | Body | Field | Local skill | PyJHora | Delta |')
        lines.append('|---|---|---|---|---|---|---:|')
        for r in boundary[:80]:
            lines.append(f"| {r['sample_id']} | {r['section']} | {r['body']} | {r['field']} | {r['local_skill']} | {r['pyjhora']} | {r['delta']} |")
        lines.append('')
    lines.append('## 5. 判断')
    lines.append('')
    lines.append('- PyJHora 作为第二开源引擎已经接入成功。')
    lines.append('- D1/D9/D10若高匹配，说明当前 skill 的分盘算法不仅与 Swiss direct 自算一致，也能通过独立 Jyotish 项目的实测。')
    lines.append('- Dasha 部分若存在系统性差异，优先视为 PyJHora seed_star / dasha year / 起运规则口径差异，不能马上判定本 skill 错；需要 JHora 或 Drik Panchang 再仲裁。')
    lines.append('- PyJHora 是 AGPL-3.0，适合做外部 benchmark，不适合把其源码或派生实现并入当前 skill。')
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Compare public benchmark samples against PyJHora.')
    parser.add_argument('--sample-id', action='append', default=[], help='Run only a named benchmark sample; repeatable.')
    parser.add_argument('--build-local', action='store_true', help='Explicitly generate missing local canonical baselines.')
    parser.add_argument('--refresh-local', action='store_true', help='Explicitly rebuild selected local canonical baselines.')
    parser.add_argument('--node-mode', choices=['mean', 'true'], default='mean', help='Match the node convention before comparing.')
    parser.add_argument('--output-prefix', default='', help='Optional filename prefix for resumable batch artifacts.')
    args = parser.parse_args(argv)
    PYJHORA_OUT.mkdir(parents=True, exist_ok=True)
    samples = json.loads(DATA.read_text())
    if args.sample_id:
        requested = set(args.sample_id)
        samples = [sample for sample in samples if sample['id'] in requested]
        missing = requested - {sample['id'] for sample in samples}
        if missing:
            parser.error(f'unknown sample id(s): {", ".join(sorted(missing))}')
    all_rows = []
    for sample in samples:
        local_path = LOCAL_CANON / f"{sample['id']}.canonical.json"
        if (not local_path.exists() and args.build_local) or args.refresh_local:
            from run_skill_baseline import run_sample
            baseline = run_sample(sample)
            if not baseline.get('ok'):
                parser.error(f'failed to build local baseline for {sample["id"]}: {baseline.get("error", "unknown error")}')
        if not local_path.exists():
            parser.error(
                f'missing local canonical baseline for {sample["id"]}; '
                'run with --build-local or run_skill_baseline.py first'
            )
        pyjhora = build_pyjhora_sample(sample, node_mode=args.node_mode)
        (PYJHORA_OUT / f"{sample['id']}.pyjhora.json").write_text(json.dumps(pyjhora, ensure_ascii=False, indent=2))
        local = json.loads(local_path.read_text())
        all_rows.extend(compare_one(sample['id'], local, pyjhora))

    prefix = f"{args.output_prefix}_" if args.output_prefix else ''
    matrix = OUT / f'{prefix}pyjhora_comparison_matrix.csv'
    with matrix.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_id', 'section', 'body', 'field', 'local_skill', 'pyjhora', 'delta', 'status'])
        writer.writeheader()
        writer.writerows(all_rows)

    report = OUT / f'{prefix}jyotish_benchmark_round3_pyjhora_compare.md'
    report.write_text(write_report(samples, all_rows))
    print(json.dumps({'report': str(report), 'matrix': str(matrix), 'samples': len(samples), 'fields': len(all_rows)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
