#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jyotish 事件应期回归测试框架 v1.0
自动验证 Dasha 推运精度：名人已知人生事件 vs 引擎预测

用法:
  python3 tests/smoke_test_runner.py
  python3 tests/smoke_test_runner.py --case einstein,obama
  python3 tests/smoke_test_runner.py --report json

依赖: 需要 engin 可运行（pyswisseph 已安装）
"""

import json, os, sys, subprocess, argparse, time
from datetime import datetime
from pathlib import Path

SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent / "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

CASES_FILE = Path(__file__).resolve().parent / "prediction_regression_cases.json"

# ============================================================
# 测试用例 — 名人已知事件时间线
# 每个事件可验证 Dasha 推运系统的精度
# ============================================================
CELEBRITY_EVENTS = {
    "obama": {
        "name": "Barack Obama",
        "birth": {"year": 1961, "month": 8, "day": 4, "hour": 19, "minute": 24,
                  "lat": 21.3, "lon": -157.8, "tz": -10.0},
        "known_lagna": "Capricorn",
        "events": [
            {"date": "1992-10-03", "type": "marriage", "desc": "与 Michelle 结婚", "target_houses": [7]},
            {"date": "2008-11-04", "type": "career_peak", "desc": "当选美国总统", "target_houses": [10, 1]},
            {"date": "2012-11-06", "type": "career_peak", "desc": "连任美国总统", "target_houses": [10, 1]},
            {"date": "2020-11-17", "type": "publication", "desc": "回忆录《应许之地》出版", "target_houses": [3, 10]},
        ]
    },
    "trump": {
        "name": "Donald Trump",
        "birth": {"year": 1946, "month": 6, "day": 14, "hour": 10, "minute": 54,
                  "lat": 40.7, "lon": -73.8, "tz": -5.0},
        "known_lagna": "Leo",
        "events": [
            {"date": "1977-04-07", "type": "marriage", "desc": "与 Ivana 结婚", "target_houses": [7]},
            {"date": "1990-04-04", "type": "business", "desc": "Taj Mahal 赌场开业", "target_houses": [10, 11]},
            {"date": "2016-11-08", "type": "career_peak", "desc": "当选美国总统", "target_houses": [10, 1]},
            {"date": "2024-11-05", "type": "career_peak", "desc": "再次当选总统", "target_houses": [10, 1]},
        ]
    },
    "jobs": {
        "name": "Steve Jobs",
        "birth": {"year": 1955, "month": 2, "day": 24, "hour": 19, "minute": 15,
                  "lat": 37.8, "lon": -122.4, "tz": -8.0},
        "known_lagna": "Leo",
        "events": [
            {"date": "1976-04-01", "type": "career_start", "desc": "Apple 公司成立", "target_houses": [10, 11]},
            {"date": "1985-09-17", "type": "career_loss", "desc": "被逐出 Apple", "target_houses": [10, 8]},
            {"date": "1997-07-09", "type": "career_return", "desc": "回归 Apple 任 CEO", "target_houses": [10, 1]},
            {"date": "2007-01-09", "type": "career_peak", "desc": "发布第一代 iPhone", "target_houses": [10, 3]},
            {"date": "2011-10-05", "type": "death", "desc": "因胰腺癌去世", "target_houses": [8, 1]},
        ]
    },
    "einstein": {
        "name": "Albert Einstein",
        "birth": {"year": 1879, "month": 3, "day": 14, "hour": 11, "minute": 30,
                  "lat": 48.4, "lon": 9.98, "tz": 0.89},
        "known_lagna": "Gemini",
        "events": [
            {"date": "1905-06-30", "type": "career_peak", "desc": "奇迹年：发表狭义相对论等四篇论文", "target_houses": [10, 5, 9]},
            {"date": "1915-11-25", "type": "career_peak", "desc": "完成广义相对论", "target_houses": [10, 9]},
            {"date": "1921-04-02", "type": "honor", "desc": "诺贝尔物理学奖", "target_houses": [10, 5]},
            {"date": "1955-04-18", "type": "death", "desc": "在普林斯顿去世", "target_houses": [8, 1]},
        ]
    },
    "monroe": {
        "name": "Marilyn Monroe",
        "birth": {"year": 1926, "month": 6, "day": 1, "hour": 9, "minute": 30,
                  "lat": 34.1, "lon": -118.3, "tz": -8.0},
        "known_lagna": "Cancer",
        "events": [
            {"date": "1942-06-19", "type": "marriage", "desc": "与 Jim Dougherty 结婚", "target_houses": [7]},
            {"date": "1953-00-00", "type": "career_peak", "desc": "《绅士爱美人》上映，成为巨星", "target_houses": [10, 5]},
            {"date": "1962-08-05", "type": "death", "desc": "在洛杉矶去世", "target_houses": [8, 1]},
        ]
    },
    "dicaprio": {
        "name": "Leonardo DiCaprio",
        "birth": {"year": 1974, "month": 11, "day": 11, "hour": 2, "minute": 47,
                  "lat": 34.1, "lon": -118.3, "tz": -8.0},
        "known_lagna": "Virgo",
        "events": [
            {"date": "1997-12-19", "type": "career_peak", "desc": "《泰坦尼克号》上映", "target_houses": [10, 5]},
            {"date": "2016-02-28", "type": "honor", "desc": "凭《荒野猎人》获奥斯卡最佳男主角", "target_houses": [10, 1]},
        ]
    },
    "mjackson": {
        "name": "Michael Jackson",
        "birth": {"year": 1958, "month": 8, "day": 29, "hour": 19, "minute": 33,
                  "lat": 41.6, "lon": -87.3, "tz": -6.0},
        "known_lagna": "Pisces",
        "events": [
            {"date": "1982-11-30", "type": "career_peak", "desc": "《Thriller》专辑发行", "target_houses": [10, 5]},
            {"date": "2009-06-25", "type": "death", "desc": "在洛杉矶去世", "target_houses": [8, 1]},
        ]
    },
    "indira": {
        "name": "Indira Gandhi",
        "birth": {"year": 1917, "month": 11, "day": 19, "hour": 23, "minute": 11,
                  "lat": 25.5, "lon": 81.9, "tz": 5.5},
        "known_lagna": "Leo",
        "events": [
            {"date": "1966-01-24", "type": "career_peak", "desc": "就任印度总理", "target_houses": [10, 1]},
            {"date": "1984-10-31", "type": "death", "desc": "遇刺身亡", "target_houses": [8, 1]},
        ]
    },
    "presley": {
        "name": "Elvis Presley",
        "birth": {"year": 1935, "month": 1, "day": 8, "hour": 4, "minute": 35,
                  "lat": 34.3, "lon": -88.4, "tz": -6.0},
        "known_lagna": "Scorpio",
        "events": [
            {"date": "1956-01-27", "type": "career_start", "desc": "首张专辑《Heartbreak Hotel》", "target_houses": [10, 5]},
            {"date": "1977-08-16", "type": "death", "desc": "在 Graceland 去世", "target_houses": [8, 1]},
        ]
    },
    "curie": {
        "name": "Marie Curie",
        "birth": {"year": 1867, "month": 11, "day": 7, "hour": 12, "minute": 0,
                  "lat": 52.2, "lon": 21.0, "tz": 1.0},
        "known_lagna": "Sagittarius",
        "events": [
            {"date": "1903-12-10", "type": "honor", "desc": "诺贝尔物理学奖（与 Pierre Curie 共享）", "target_houses": [10, 5]},
            {"date": "1911-12-10", "type": "honor", "desc": "诺贝尔化学奖（唯一两次获奖女性）", "target_houses": [10, 5]},
            {"date": "1934-07-04", "type": "death", "desc": "因再生障碍性贫血去世", "target_houses": [8, 1]},
        ]
    },
    "hanks": {
        "name": "Tom Hanks",
        "birth": {"year": 1956, "month": 7, "day": 9, "hour": 11, "minute": 17,
                  "lat": 37.9, "lon": -122.1, "tz": -8.0},
        "known_lagna": "Virgo",
        "events": [
            {"date": "1994-03-21", "type": "honor", "desc": "凭《费城故事》获奥斯卡影帝", "target_houses": [10, 1]},
            {"date": "1995-03-27", "type": "honor", "desc": "凭《阿甘正传》再获奥斯卡影帝", "target_houses": [10, 1]},
        ]
    },
    "jolie": {
        "name": "Angelina Jolie",
        "birth": {"year": 1975, "month": 6, "day": 4, "hour": 9, "minute": 9,
                  "lat": 34.1, "lon": -118.3, "tz": -8.0},
        "known_lagna": "Cancer",
        "events": [
            {"date": "2000-03-26", "type": "honor", "desc": "凭《移魂女郎》获奥斯卡女配", "target_houses": [10, 5]},
            {"date": "2013-05-14", "type": "health", "desc": "预防性双乳切除术公告", "target_houses": [8, 6]},
        ]
    },
}


# ============================================================
# 测试运行器
# ============================================================

class SmokeTestRunner:
    def __init__(self, engine_path=None):
        self.engine = engine_path or os.path.join(SCRIPTS_DIR, "jyotish_engine.py")
        self.results = {"total": 0, "passed": 0, "failed": 0, "errors": [], "details": []}
    
    def _run_engine(self, birth, command, extra_args=None):
        """调用 jyotish_engine.py CLI"""
        cmd = [
            sys.executable, self.engine, command,
            "--year", str(birth["year"]), "--month", str(birth["month"]),
            "--day", str(birth["day"]), "--hour", str(birth["hour"]),
            "--minute", str(birth["minute"]),
            "--lat", str(birth["lat"]), "--lon", str(birth["lon"]),
            "--tz", str(birth["tz"]), "--node-mode", "mean",
        ]
        if extra_args:
            cmd.extend(extra_args)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if result.returncode == 0 and result.stdout.strip():
                return True, json.loads(result.stdout)
            return False, result.stderr if result.stderr else result.stdout
        except subprocess.TimeoutExpired:
            return False, "TIMEOUT (180s)"
        except Exception as e:
            return False, str(e)
    
    def test_chart_basics(self, case_id, data):
        """验证基础排盘：上升、太阳、月亮星座"""
        ok, chart = self._run_engine(data["birth"], "chart")
        self.results["total"] += 1
        
        if not ok:
            self.results["failed"] += 1
            err = f"{data['name']}: chart calculation FAILED — {chart}"
            self.results["errors"].append(err)
            self.results["details"].append({"case": data["name"], "test": "chart", "result": "FAIL", "error": str(chart)})
            return
        
        planets = chart.get("planets", {})
        asc = chart.get("ascendant", {}).get("sign", "?").split()[0] if isinstance(chart.get("ascendant"), dict) else "?"
        
        checks = []
        if asc and data.get("known_lagna"):
            match = asc.lower() == data["known_lagna"].lower()
            checks.append(("Ascendant", match, f"{asc} vs {data['known_lagna']}"))
        
        sun = planets.get("Sun", {}).get("sign", "?")
        if sun and data.get("known_sun_sign"):
            match = sun.lower() == data.get("known_sun_sign", "").lower()
            checks.append(("Sun sign", match, f"{sun} vs {data['known_sun_sign']}"))
        
        moon = planets.get("Moon", {}).get("sign", "?")
        if moon and data.get("known_moon_sign"):
            match = moon.lower() == data.get("known_moon_sign", "").lower()
            checks.append(("Moon sign", match, f"{moon} vs {data['known_moon_sign']}"))
        
        all_pass = all(c[1] for c in checks)
        if all_pass:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
            fails = [c[2] for c in checks if not c[1]]
            self.results["errors"].append(f"{data['name']}: chart mismatch — {', '.join(fails)}")
        
        self.results["details"].append({
            "case": data["name"], "test": "chart",
            "result": "PASS" if all_pass else "FAIL",
            "checks": [{"type": c[0], "pass": c[1], "detail": c[2]} for c in checks]
        })
    
    def test_dasha_timeline(self, case_id, data):
        """验证 Dasha 时间线与已知事件的交叉"""
        events = data.get("events", [])
        if not events:
            return
        
        ok, dasha = self._run_engine(data["birth"], "dasha", ["--years", "120"])
        self.results["total"] += len(events)
        
        if not ok:
            for ev in events:
                self.results["failed"] += 1
                self.results["errors"].append(f"{data['name']}: dasha calc FAILED for '{ev['desc']}'")
            return
        
        dasa_periods = dasha.get("timeline", []) if isinstance(dasha, dict) else []
        if not dasa_periods:
            dasa_periods = dasha if isinstance(dasha, list) else []
        
        for ev in events:
            ev_date = datetime.strptime(ev["date"].replace("-00", "-01"), "%Y-%m-%d")
            # Find active Mahadasha at event date
            active_md = None
            for d in dasa_periods:
                start = datetime.strptime(d.get("start", "1900-01-01")[:10], "%Y-%m-%d")
                end = datetime.strptime(d.get("end", "2100-01-01")[:10], "%Y-%m-%d")
                if start <= ev_date <= end:
                    active_md = d.get("lord", "?")
                    break
            
            if ev["type"] == "career_start" or ev["type"] == "career_peak" or ev["type"] == "career_return":
                favorable = active_md in ["Sun", "Moon", "Mars", "Jupiter", "Venus", "Mercury"]
            elif ev["type"] == "career_loss":
                favorable = active_md in ["Saturn", "Rahu", "Ketu"]
            elif ev["type"] == "death":
                favorable = active_md in ["Saturn", "Rahu", "Ketu", "Mars"]
            elif ev["type"] == "marriage":
                favorable = active_md in ["Jupiter", "Venus", "Mercury"]
            elif ev["type"] == "honor":
                favorable = active_md in ["Sun", "Jupiter", "Venus"]
            else:
                favorable = True  # neutral test
            
            test_name = f"{ev['desc']} [{ev['date']}] Dasha={active_md}"
            if favorable:
                self.results["passed"] += 1
            else:
                self.results["failed"] += 1
                self.results["errors"].append(
                    f"{data['name']}: '{ev['desc']}' ({ev['date']}) — active Mahadasha={active_md} — unexpected for {ev['type']}"
                )
            
            self.results["details"].append({
                "case": data["name"], "test": "dasha_event",
                "event": ev["desc"], "date": ev["date"],
                "active_dasha": active_md,
                "result": "PASS" if favorable else "FAIL",
            })
    
    def run_all(self, case_filter=None):
        """运行所有回归测试"""
        print("=" * 70)
        print("Jyotish 事件应期回归测试")
        print("=" * 70)
        
        cases = CELEBRITY_EVENTS
        if case_filter:
            cases = {k: v for k, v in cases.items() if k in case_filter}
        
        for case_id, data in cases.items():
            print(f"\n{'─' * 60}")
            print(f"  Case: {data['name']}")
            print(f"{'─' * 60}")
            
            # Test 1: Chart basics
            print(f"  [1/2] Chart validation...")
            self.test_chart_basics(case_id, data)
            
            # Test 2: Dasha event timeline
            if data.get("events"):
                print(f"  [2/2] Dasha event timeline ({len(data['events'])} events)...")
                self.test_dasha_timeline(case_id, data)
        
        return self.results
    
    def report(self, fmt="text"):
        """生成测试报告"""
        r = self.results
        if fmt == "json":
            return json.dumps(r, ensure_ascii=False, indent=2)
        
        lines = []
        lines.append("\n" + "=" * 70)
        lines.append("  回归测试报告")
        lines.append("=" * 70)
        lines.append(f"  总计: {r['total']} | 通过: {r['passed']} | 失败: {r['failed']}")
        if r["total"] > 0:
            rate = r["passed"] / r["total"] * 100
            lines.append(f"  通过率: {rate:.1f}%")
        
        if r["errors"]:
            lines.append(f"\n  失败项 ({len(r['errors'])}):")
            for err in r["errors"]:
                lines.append(f"    ✗ {err}")
        
        lines.append("=" * 70)
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Jyotish 事件应期回归测试")
    parser.add_argument("--case", help="指定案例 ID，逗号分隔")
    parser.add_argument("--report", default="text", choices=["text", "json"])
    parser.add_argument("--skip-dasha", action="store_true", help="跳过 Dasha 推运测试")
    args = parser.parse_args()
    
    case_filter = None
    if args.case:
        case_filter = [c.strip() for c in args.case.split(",")]
    
    runner = SmokeTestRunner()
    runner.run_all(case_filter)
    print(runner.report(args.report))
    
    # 退出码：任何失败 → 非零
    sys.exit(1 if runner.results["failed"] > 0 else 0)


if __name__ == "__main__":
    main()
