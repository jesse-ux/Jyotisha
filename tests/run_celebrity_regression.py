#!/usr/bin/env python3
"""
名人案例批量回归测试 v1.2
验证引擎排盘正确性 + 解盘结论匹配度
修复：v1.1 使用的 sign_index/longitude 字段引擎不存在，改用 sign 字段
"""
import json, sys, os, subprocess
from datetime import datetime

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(REPO_ROOT, "scripts", "jyotish_engine.py")
CASES_FILE = os.path.join(REPO_ROOT, "tests", "celebrity_cases.json")

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

SIGNS_CN = ['白羊','金牛','双子','巨蟹','狮子','处女',
            '天秤','天蝎','射手','摩羯','水瓶','双鱼']

EXALTATION = {'Sun':'Aries','Moon':'Taurus','Mars':'Capricorn','Mercury':'Virgo',
              'Jupiter':'Cancer','Venus':'Pisces','Saturn':'Libra'}
DEBILITATION = {'Sun':'Libra','Moon':'Scorpio','Mars':'Cancer','Mercury':'Pisces',
                'Jupiter':'Capricorn','Venus':'Virgo','Saturn':'Aries'}


def run_case(case):
    cmd = [
        sys.executable, ENGINE, "chart",
        "--year", str(case["year"]), "--month", str(case["month"]),
        "--day", str(case["day"]), "--hour", str(case["hour"]),
        "--minute", str(case["minute"]), "--lat", str(case["lat"]),
        "--lon", str(case["lon"]), "--tz", str(case["tz"]),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=REPO_ROOT)
    if result.returncode != 0:
        return {"error": result.stderr[:500]}
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": f"JSON parse error: {result.stdout[:200]}"}


def get_sign_cn(sign_name):
    return SIGNS_CN[SIGNS.index(sign_name)] if sign_name in SIGNS else sign_name


def get_sign_state(planet_name, sign_name):
    """检查行星庙旺落陷，返回格式化字符串"""
    if sign_name == EXALTATION.get(planet_name, ''):
        return '擢升'
    if sign_name == DEBILITATION.get(planet_name, ''):
        return '落陷'
    return ''


def validate_case(case, chart_data):
    """与已知数据做比对 — 使用引擎实际的 sign 字段"""
    checks = []
    
    # 上升比对
    known_lagna = case.get("known_lagna", "")
    if known_lagna:
        actual_lagna = chart_data.get("ascendant", {}).get("sign", "?")
        match = "✅" if actual_lagna == known_lagna else "❌"
        checks.append({"type": "上升", "expected": known_lagna, "actual": actual_lagna, "pass": match == "✅"})
    
    # 太阳比对
    known_sun = case.get("known_sun_sign", "")
    if known_sun:
        sun_sign = chart_data.get("planets", {}).get("Sun", {}).get("sign", "?")
        match = "✅" if sun_sign == known_sun else "❌"
        state = get_sign_state("Sun", sun_sign)
        checks.append({"type": "太阳", "expected": known_sun, "actual": sun_sign, "pass": match == "✅"})
    
    # 月亮比对
    known_moon = case.get("known_moon_sign", "")
    if known_moon:
        moon_sign = chart_data.get("planets", {}).get("Moon", {}).get("sign", "?")
        match = "✅" if moon_sign == known_moon else "❌"
        checks.append({"type": "月亮", "expected": known_moon, "actual": moon_sign, "pass": match == "✅"})
    
    passed = sum(1 for c in checks if c["pass"])
    total = max(len(checks), 1)
    return checks, passed, total


def run_all():
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)
    
    print(f"{'='*100}")
    print(f" 印度占星Skill · 名人案例回归测试 v1.1")
    print(f" 案例数: {len(cases)}")
    print(f" 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*100}")
    
    results = []
    total_known = 0
    total_passed = 0
    
    for i, case in enumerate(cases, 1):
        name = case["name"]
        rating = case.get("file_match_rating", "")
        conclusion = case.get("summary_conclusion", "")
        
        data = run_case(case)
        
        if "error" in data:
            print(f"\n[{i:>2}/{len(cases)}] {name:<22} ❌ 引擎错误")
            results.append({"id": case["id"], "name": name, "status": "error"})
            continue
        
        checks, p, t = validate_case(case, data)
        total_known += t
        total_passed += p
        
        # 符号
        if checks:
            all_pass = all(c["pass"] for c in checks)
            status = "✅" if all_pass else "⚠️"
        else:
            status = "✅"
        
        print(f"\n[{i:>2}/{len(cases)}] {name:<22} {status} 匹配率={rating or 'N/A':>4}")
        for c in checks:
            state_str = get_sign_state(c["type"], c["actual"])
            state_tag = f" ({state_str})" if state_str else ""
            pass_str = "✅" if c["pass"] else "❌"
            print(f"     {c['type']}:预期{get_sign_cn(c['expected'])} 实际{get_sign_cn(c['actual'])}{state_tag} {pass_str}")
        if conclusion:
            print(f"     关键发现: {conclusion[:50]}")
    
    # 汇总
    pass_rate = f"{total_passed/total_known*100:.0f}%" if total_known > 0 else "N/A"
    print(f"\n{'='*100}")
    print(f" 汇总报告")
    print(f"{'='*100}")
    print(f" 总案例: {len(cases)}")
    print(f" 已知比对项: {total_known} 项")
    print(f" 通过: {total_passed} 项")
    print(f" 匹配率: {pass_rate}")
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_cases": len(cases),
        "total_known_checks": total_known,
        "passed_checks": total_passed,
        "pass_rate": pass_rate,
        "results": results,
    }
    
    report_path = os.path.join(REPO_ROOT, "tests", "celebrity_regression_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n 报告已保存: {report_path}")


if __name__ == "__main__":
    run_all()
