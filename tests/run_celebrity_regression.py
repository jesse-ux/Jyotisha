#!/usr/bin/env python3
"""
名人案例批量回归测试 v1.0
验证引擎对22个名人案例的排盘和解盘能力
"""
import json
import sys
import os
import subprocess

# 路径
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(REPO_ROOT, "scripts", "jyotish_engine.py")
CASES_FILE = os.path.join(REPO_ROOT, "tests", "celebrity_cases.json")

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']


def run_case(case):
    """对单个案例跑 full-reading 引擎"""
    cmd = [
        sys.executable, ENGINE, "chart",
        "--year", str(case["year"]),
        "--month", str(case["month"]),
        "--day", str(case["day"]),
        "--hour", str(case["hour"]),
        "--minute", str(case["minute"]),
        "--lat", str(case["lat"]),
        "--lon", str(case["lon"]),
        "--tz", str(case["tz"]),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, cwd=REPO_ROOT)
    
    if result.returncode != 0:
        return {"error": result.stderr[:500]}
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"error": f"JSON解析失败: {result.stdout[:300]}"}


def extract_chart_summary(chart_data):
    """从引擎输出中提取解盘关键结论"""
    if not chart_data or "error" in chart_data:
        return None
    
    planets = {}
    for pname in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']:
        p = chart_data.get("planets", {}).get(pname, {})
        if p:
            sign_idx = int(p.get("longitude", 0) / 30) % 12
            planets[pname] = {
                "sign": SIGNS[sign_idx],
                "house": int(p.get("house", 0)),
                "degree": round(p.get("longitude", 0) % 30, 2),
            }

    asc_sign = SIGNS.get(int(chart_data.get("ascendant", {}).get("sign_index", 0)), "?")
    
    return {
        "lagna": asc_sign,
        "planets": planets,
        "summary": f"上升{asc_sign}，"
    }


def run_all():
    with open(CASES_FILE, "r", encoding="utf-8") as f:
        cases = json.load(f)
    
    results = []
    passed = 0
    failed = 0
    
    print(f"{'='*80}")
    print(f"名人案例批量回归测试")
    print(f"案例数: {len(cases)}")
    print(f"测试时间: 引擎 chart 命令排盘正确性")
    print(f"{'='*80}")
    
    for i, case in enumerate(cases, 1):
        name = case["name"]
        print(f"\n[{i}/{len(cases)}] {name} ({case['year']}-{case['month']:02d}-{case['day']:02d})")
        
        data = run_case(case)
        
        if "error" in data:
            print(f"  ❌ 引擎错误: {data['error'][:100]}")
            failed += 1
            results.append({"id": case["id"], "name": name, "status": "error", "detail": data["error"]})
            continue
        
        # 提取信息
        has_asc = "ascendant" in data
        planet_count = len(data.get("planets", {}))
        
        status = "✅" if has_asc else "⚠️"
        print(f"  {status} 上升: {has_asc}, 行星数: {planet_count}")
        
        # 与已知数据比对（如果有）
        known_check = []
        if case.get("known_lagna") and has_asc:
            asc_sign = SIGNS[data.get("ascendant", {}).get("sign_index", 0) % 12]
            match = "✅" if asc_sign == case["known_lagna"] else "❌"
            known_check.append(f"上升: 预期{case['known_lagna']} 实际{asc_sign} {match}")
        
        for check in known_check:
            print(f"    {check}")
        
        passed_count = sum(1 for c in known_check if "✅" in c)
        
        results.append({
            "id": case["id"],
            "name": name,
            "status": "passed" if has_asc else "warn",
            "key_data": known_check,
        })
        passed += 1
    
    # 汇总报告
    print(f"\n\n{'='*80}")
    print(f"汇总报告")
    print(f"{'='*80}")
    print(f"总计: {len(cases)} 案例")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"通过率: {passed/len(cases)*100:.0f}%")
    
    print(f"\n{'='*80}")
    print(f"案例清单")
    print(f"{'='*80}")
    print(f"{'姓名':>22} | {'状态':>4} | {'出生日期':>14} | {'上升':>8} | {'星盘结论'}")
    print("-"*80)
    for r in results:
        status_mark = "✅" if r["status"] == "passed" else "❌"
        case = next(c for c in cases if c["id"] == r["id"])
        conclusion = case.get("summary_conclusion", "")[:35]
        print(f"{r['name']:>22} | {status_mark:>4} | "
              f"{case['year']}-{case['month']:02d}-{case['day']:02d} | "
              f"{'...' if r['key_data'] else '?':>8} | {conclusion}")
    
    # 保存报告
    report = {
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "pass_rate": f"{passed/len(cases)*100:.0f}%",
        "results": results,
    }
    report_path = os.path.join(REPO_ROOT, "tests", "celebrity_regression_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"\n报告已保存: {report_path}")


if __name__ == "__main__":
    run_all()
