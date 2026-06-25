"""
cmd_muhurta.py  v6.0.21 — muhurta 子命令实现

用法：
  python jyotish_engine.py muhurta --date 2026-06-15 --activity marriage
  python jyotish_engine.py muhurta --date 2026-06-15  (全部活动)
  python jyotish_engine.py muhurta --scan-days 7 --activity business  (扫描7天)

对于完整解盘（full-reading），也会附带当日 Muhurta 基本信息。
"""

from __future__ import annotations
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ayanamsa_utils import sidereal_flags


def _weekday_to_vara(py_weekday: int) -> int:
    """Python weekday (0=Mon) → Vara index (0=Sun)"""
    return (py_weekday + 1) % 7


def _get_sun_moon_lons(year: int, month: int, day: int,
                       hour: int = 12, ayanamsa_name: str = 'lahiri') -> tuple:
    """获取太阳/月亮恒星黄经。优先 swisseph，退化为近似算法。"""
    try:
        import swisseph as swe
        jd_ut = swe.julday(year, month, day, hour)
        flags = sidereal_flags(swe, ayanamsa_name)
        sun_res = swe.calc_ut(jd_ut, swe.SUN, flags)
        moon_res = swe.calc_ut(jd_ut, swe.MOON, flags)
        return sun_res[0], moon_res[0], True
    except Exception:
        pass
    # 近似算法
    from muhurta import _approx_sun_moon_lon
    sun_lon, moon_lon = _approx_sun_moon_lon(year, month, day)
    return sun_lon, moon_lon, False


def _format_panchanga_summary(panchanga: Dict) -> List[str]:
    lines = []
    p = panchanga
    lines.append(f"  Tithi:     {p['tithi']['full_name']} ({p['tithi']['quality']})")
    lines.append(f"  Nakshatra: {p['nakshatra']['nakshatra']} [{p['nakshatra']['type']}] ({p['nakshatra']['quality']})")
    lines.append(f"  Yoga:      {p['yoga']['yoga']} ({p['yoga']['quality']})")
    lines.append(f"  Karana:    {p['karana']['karana']} ({p['karana']['quality']})")
    lines.append(f"  Vara:      {p['vara']['vara']} / {p['vara']['vara_lord']} ({p['vara']['quality']})")
    lines.append(f"  Hora:      {p['hora']['hora_lord']} ({p['hora']['quality']})")
    lines.append(f"  综合评分:  {p['overall_quality']} ({p['overall_score']:.0%}，吉 {p['auspicious_count']}/{p['total_elements']})")
    if p['warnings']:
        for w in p['warnings']:
            lines.append(f"  {w}")
    return lines


def _format_activity_checks(activity_checks: Dict, target_activity: Optional[str] = None) -> List[str]:
    lines = []
    ACTIVITY_NAMES_ZH = {
        'marriage': '婚礼/伴侣（Vivaha）',
        'business': '开业/签约（Vyapar）',
        'travel':   '出行（Yatra）',
        'medical':  '手术/医疗（Chikitsa）',
        'education': '学习/入学（Vidyarambha）',
    }
    for act, chk in activity_checks.items():
        if target_activity and act != target_activity:
            continue
        zh_name = ACTIVITY_NAMES_ZH.get(act, act)
        verdict = chk.get('verdict', '未知')
        icon = '✅' if '大吉' in verdict or ('吉' in verdict and '不宜' not in verdict) else \
               '⚠️' if '一般' in verdict or '中' in verdict else '❌'
        lines.append(f"  {icon} {zh_name}: {verdict}")
        if chk.get('notes'):
            for note in chk['notes'][:3]:
                lines.append(f"     → {note}")
    return lines


def cmd_muhurta(args, chart_data: Optional[Dict] = None) -> int:
    """
    Muhurta 子命令主入口。
    
    args 属性：
        args.date: '2026-06-15'（查询日期，默认今天）
        args.activity: 活动类型（可选，默认全部）
        args.scan_days: 扫描天数（可选，>1 时扫描多天）
        args.hour_from_sunrise: 从日出起算的小时（默认 6h）
    """
    from muhurta import muhurta_full_report, ACTIVITY_RULES

    # 解析日期
    if hasattr(args, 'date') and args.date:
        try:
            query_dt = datetime.strptime(args.date, '%Y-%m-%d')
        except ValueError:
            print(f"[ERROR] 日期格式错误: {args.date}，请用 YYYY-MM-DD")
            return 1
    else:
        query_dt = datetime.now()

    hour_from_sunrise = getattr(args, 'hour_from_sunrise', 6.0)
    target_activity = getattr(args, 'activity', None)
    scan_days = getattr(args, 'scan_days', 1)
    ayanamsa_name = getattr(args, 'ayanamsa', 'lahiri')

    activities = list(ACTIVITY_RULES.keys())
    if target_activity and target_activity not in activities:
        print(f"[ERROR] 未知活动: {target_activity}。支持: {', '.join(activities)}")
        return 1

    print("=" * 64)
    print("🕐  Muhurta 择时分析（印度吉凶历）")
    print("=" * 64)

    dates_to_check = [query_dt + timedelta(days=i) for i in range(max(1, int(scan_days)))]

    for dt in dates_to_check:
        sun_lon, moon_lon, has_swe = _get_sun_moon_lons(
            dt.year, dt.month, dt.day, int(hour_from_sunrise + 6),  # rough solar hour
            ayanamsa_name=ayanamsa_name,
        )
        vara_idx = _weekday_to_vara(dt.weekday())
        date_str = dt.strftime('%Y-%m-%d')

        report = muhurta_full_report(
            sun_lon=sun_lon,
            moon_lon=moon_lon,
            weekday=vara_idx,
            hour_from_sunrise=hour_from_sunrise,
            query_date_str=date_str,
            activities=activities,
        )

        precision_note = '' if has_swe else '（近似值，±2°精度）'
        print(f"\n📅 {date_str} {precision_note}")
        print(f"   Sun: {sun_lon:.1f}°  Moon: {moon_lon:.1f}°")
        print()

        print("── Panchanga 五要素 ──")
        for line in _format_panchanga_summary(report['panchanga']):
            print(line)
        print()

        print("── Abhijit Muhurta ──")
        abh = report['abhijit_muhurta']
        print(f"  {abh['description']}")
        print(f"  持续: {abh['duration_minutes']} 分钟 | {abh['warning']}")
        print()

        print("── 活动适宜性 ──")
        for line in _format_activity_checks(report['activity_checks'], target_activity):
            print(line)
        print()

        summary = report['summary']
        best = summary.get('best_activities', [])
        avoid = summary.get('avoid_activities', [])
        if best:
            print(f"  ✨ 适宜: {', '.join(best)}")
        if avoid:
            print(f"  🚫 不宜: {', '.join(avoid)}")

        if len(dates_to_check) > 1:
            print("-" * 40)

    print()
    print("━" * 64)
    print("注意事项：")
    print("  1. 本分析基于恒星黄经（Lahiri Ayanamsa），为 Parashari 传统")
    print("  2. 精确 Muhurta 还需考虑出生盘 Lagna 与目标时间的相位关系")
    print("  3. 建议结合 Ascendant 力量、吉星位置做综合判断")
    if not has_swe:
        print("  4. ⚠️ 当前使用近似算法（swisseph 未安装），精度约 ±2°")
    print("━" * 64)
    return 0
