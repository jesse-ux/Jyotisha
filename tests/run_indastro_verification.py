#!/usr/bin/env python3
"""Indastro 验证脚本 - 对比引擎输出与 Indastro.com 参考值"""

import json
import subprocess
import sys
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
ENGINE = os.path.join(SKILL_DIR, 'scripts', 'jyotish_engine.py')
CASES_FILE = os.path.join(SCRIPT_DIR, 'indastro_cases.json')

def run_engine(year, month, day, hour, minute, lat, lon, tz):
    cmd = [
        sys.executable, ENGINE, 'chart',
        '--year', str(year), '--month', str(month), '--day', str(day),
        '--hour', str(hour), '--minute', str(minute),
        '--lat', str(lat), '--lon', str(lon), '--tz', str(tz)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout)

def format_degree(sign, deg):
    return f"{sign} {deg:.2f}°"

def main():
    with open(CASES_FILE) as f:
        cases = json.load(f)
    
    results = []
    passes = 0
    fails = 0
    
    print("=" * 90)
    print("INDSTRO 验证报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)
    print(f"{'案例':<20s} | {'tz':>5s} | {'状态':<6s} | Lagna (引擎 vs Indastro)")
    print("-" * 90)
    
    for c in cases:
        try:
            data = run_engine(
                c['year'], c['month'], c['day'],
                c['hour'], c['minute'],
                c['lat'], c['lon'], c['tz']
            )
        except Exception as e:
            print(f"{c['name']:<20s} | {c['tz']:+5.1f} | ERROR  | {e}")
            continue
        
        eng = {
            'lagna': data['ascendant']['sign'],
            'lagna_deg': data['ascendant']['degree'],
            'sun': data['planets']['Sun']['sign'],
            'sun_deg': data['planets']['Sun']['degree'],
            'moon': data['planets']['Moon']['sign'],
            'moon_deg': data['planets']['Moon']['degree'],
        }
        
        lagna_ok = eng['lagna'] == c['expected_lagna']
        sun_ok = eng['sun'] == c['expected_sun']
        moon_ok = eng['moon'] == c['expected_moon']
        all_ok = lagna_ok and sun_ok and moon_ok
        
        if all_ok:
            passes += 1
        else:
            fails += 1
        
        status = 'PASS' if all_ok else 'FAIL'
        
        # Build lagna comparison
        if 'expected_lagna_degree' in c:
            lagna_str = f"{eng['lagna']} {eng['lagna_deg']:.2f}° vs {c['expected_lagna']} {c['expected_lagna_degree']:.2f}°"
        else:
            lagna_str = f"{eng['lagna']} vs {c['expected_lagna']}"
        
        print(f"{c['name']:<20s} | {c['tz']:+5.1f} | {status:<6s} | {lagna_str}")
        
        # Details for failures
        if not all_ok:
            issues = []
            if not lagna_ok:
                issues.append(f"Lagna: {eng['lagna']} ≠ {c['expected_lagna']}")
            if not sun_ok:
                issues.append(f"Sun: {eng['sun']} ≠ {c['expected_sun']}")
            if not moon_ok:
                issues.append(f"Moon: {eng['moon']} ≠ {c['expected_moon']}")
            for issue in issues:
                print(f"  {'':20s}   {'':6s}   ✗ {issue}")
            if 'tz_note' in c:
                print(f"  {'':20s}   {'':6s}   ℹ {c['tz_note'][:100]}")
    
    print("-" * 90)
    total = passes + fails
    print(f"总计: {total} | 通过: {passes} | 失败: {fails} | 通过率: {passes/total*100:.1f}%")
    print("=" * 90)
    
    # Detailed report
    print("\n## 失败案例详情\n")
    for c in cases:
        try:
            data = run_engine(
                c['year'], c['month'], c['day'],
                c['hour'], c['minute'],
                c['lat'], c['lon'], c['tz']
            )
        except:
            continue
        
        eng = {
            'lagna': data['ascendant']['sign'],
            'lagna_deg': data['ascendant']['degree'],
            'sun': data['planets']['Sun']['sign'],
            'sun_deg': data['planets']['Sun']['degree'],
            'moon': data['planets']['Moon']['sign'],
            'moon_deg': data['planets']['Moon']['degree'],
        }
        
        if eng['lagna'] != c['expected_lagna'] or eng['sun'] != c['expected_sun'] or eng['moon'] != c['expected_moon']:
            print(f"### {c['name']} ({c['id']})")
            print(f"- 出生: {c['year']}-{c['month']:02d}-{c['day']:02d} {c['hour']:02d}:{c['minute']:02d} UTC{c['tz']:+.0f}")
            print(f"- 坐标: ({c['lat']}, {c['lon']})")
            print(f"- Lagna: 引擎={format_degree(eng['lagna'], eng['lagna_deg'])} | Indastro={c['expected_lagna']}")
            if 'expected_lagna_degree' in c:
                print(f"  差值: {abs(eng['lagna_deg'] - c['expected_lagna_degree']):.2f}°")
            print(f"- Sun: 引擎={format_degree(eng['sun'], eng['sun_deg'])} | Indastro={c['expected_sun']}")
            print(f"- Moon: 引擎={format_degree(eng['moon'], eng['moon_deg'])} | Indastro={c['expected_moon']}")
            if 'tz_note' in c:
                print(f"- 时区说明: {c['tz_note']}")
            print()

if __name__ == '__main__':
    main()
