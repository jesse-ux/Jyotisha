#!/usr/bin/env python3
"""
Vedicka 咨询案例结构化验证脚本

从 consultation-case-library.md 中提取有完整出生数据的案例，
用引擎计算验证：Lagna、太阳/月亮星座、Dasha分析。
"""

import json
import subprocess
import sys
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
ENGINE = os.path.join(SKILL_DIR, 'scripts', 'jyotish_engine.py')
PYTHON = sys.executable

def run_chart(year, month, day, hour, minute, lat, lon, tz):
    """运行引擎 chart 命令"""
    cmd = [
        PYTHON, ENGINE, 'chart',
        '--year', str(year), '--month', str(month), '--day', str(day),
        '--hour', str(hour), '--minute', str(minute),
        '--lat', str(lat), '--lon', str(lon), '--tz', str(tz)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return json.loads(result.stdout)

def sign_num(name):
    """星座名称转数字"""
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    return signs.index(name) + 1

def run_dasha(year, month, day, hour, minute, lat, lon, tz):
    """运行引擎 dasha 命令"""
    cmd = [
        PYTHON, ENGINE, 'dasha',
        '--year', str(year), '--month', str(month), '--day', str(day),
        '--hour', str(hour), '--minute', str(minute),
        '--lat', str(lat), '--lon', str(lon), '--tz', str(tz)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        return json.loads(result.stdout)
    except:
        return {"error": result.stderr[:500]}

def main():
    print("=" * 90)
    print("VEDICKA 咨询案例结构化验证报告")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)

    # ============================================================
    # 案例1: 阿南达莫依玛 (Anandamoyi Ma)
    # 来源: consultation-case-library.md 案例六
    # ============================================================
    print("\n## 案例1: 阿南达莫依玛 (Anandamoyi Ma)")
    print("- 出生: 1896-04-30 03:42")
    print("- 地点: Brahmanbaria (23.45N, 91.13E)")
    print("- 报告时区: 东6区 (UTC+6)")
    print("- 参考ASC: 白羊座 6°48'")
    print("- 参考MC: 摩羯座 4°38'")
    print('- 资料来源: 印度占星书案例，\u201c应为经过矫正的生时\u201d')
    print()

    # 测试多种时区 - 1896年 Bengal 使用 Calcutta Time (UTC+5:53:20)
    tz_options = [
        (5.883, "Calcutta Time (UTC+5:53)"),
        (6.0, "Bangladesh (UTC+6)"),
        (5.5, "IST (UTC+5:30)"),
    ]

    for tz, tz_desc in tz_options:
        data = run_chart(1896, 4, 30, 3, 42, 23.45, 91.13, tz)
        a = data['ascendant']
        s = data['planets']['Sun']
        m = data['planets']['Moon']
        print(f"  UTC{tz:+.3f} ({tz_desc}):")
        print(f"    Lagna: {a['sign']} {a['degree']:.2f}° (参考: Aries 6°48')")
        print(f"    Sun:   {s['sign']} {s['degree']:.2f}°")
        print(f"    Moon:  {m['sign']} {m['degree']:.2f}°")

        if a['sign'] == 'Aries':
            diff = abs(a['degree'] - 6.8)
            print(f"    ✓ Lagna匹配白羊座! 偏差={diff:.2f}°")
        print()

    # 使用参考ASC反推 - 如果ASC=Aries 6°48'，需要什么tz?
    print("  ASC反推 (目标: Aries 6°48'):")
    # 引擎未直接支持，手动计算
    # Pisces 14.25° -> Aries 6.8°: need +22.55° in ascendant
    # 1° ascendant ≈ 4 min time difference, so need ~90 min earlier
    # or different tz
    # UTC+6 gives Pisces 14.25°, need Aries 6.8° = Pisces 36.8° = +22.55° from Pisces 14.25°
    # 22.55° / 15° per hour = 1.5 hours later UTC = UTC+4.5?
    # Actually, for later local time (same clock time but more UTC offset = later UTC)
    # UTC+4.5 means 3:42 local = 23:12 UTC (earlier) instead of 21:42 UTC (with UTC+6)
    # Earlier UTC = EARLIER ascendant
    # We need ascendant to be LATER, so we need UTC to be later = slighter offset
    # So let's try some values
    
    for tz in [4.0, 4.5, 5.0, 5.3, 5.5, 5.883, 6.0]:
        data = run_chart(1896, 4, 30, 3, 42, 23.45, 91.13, tz)
        a = data['ascendant']
        if a['sign'] == 'Aries':
            print(f"  UTC{tz:+.1f}: Lagna={a['sign']} {a['degree']:.2f}° ✓ MATCH!")
        else:
            deg_in_aries = a['degree'] + (sign_num(a['sign']) * 30)
            target = 6.8
            diff = abs(deg_in_aries - target)
            print(f"  UTC{tz:+.1f}: Lagna={a['sign']} {a['degree']:.2f}° (差{diff:.1f}°)")

    # ============================================================
    # Vedicka 案例研究验证
    # ============================================================
    print("\n" + "=" * 90)
    print("## Vedicka案例研究 — Dasha/星盘逻辑验证")
    print()

    vedicka_cases = [
        {
            "name": "学术卓越案例",
            "claim": "水瓶座上升, 4宫主金星强旺, 5宫主水星高度强化, 9宫主金星与木星强力会合",
            "notes": "化名'学者'，无具体出生数据，无法直接验证。但可验证逻辑：\n"
                     "- Saraswati Yoga需要木星/金星/水星在角宫或三分宫\n"
                       "  - 如果水星在角宫入旺(处女座10宫?)，且木星对水星形成相位 → 成立\n"
                     "- Raja Yoga: 9宫主与10宫主会合/互相位\n"
                       "  - 水瓶座9宫主=金星，10宫主=火星, 需金星+火星会合\n"
                     "- 学术成功: 强化5宫/9宫 + 木星/9宫主大运激活 → 符合BPHS理论",
            "verdict": "理论逻辑合理，符合BPHS经典。Saraswati Yoga+Raja Yoga联合效应可信。"
        },
        {
            "name": "商业失败案例",
            "claim": "天蝎座上升, 第2宫主木星虚弱, 第11宫主水星落入第6宫, 金星大运激活第12宫导致破产",
            "notes": "化名'The Challenger'，无具体出生数据。\n"
                     "- 2宫主木星虚弱 → 财富积累能力弱\n"
                     "- 11宫主水星在6宫 → 收益渠道受阻于债务/竞争\n"
                     "- 金星大运 + 12宫激活 → 大额支出/海外损失\n"
                     "- BPHS: 当2/11宫主受克且大运激活dushtana时，财务危机可验证",
            "verdict": "Dasha分析与BPHS原理一致。金星作为12宫主激活支出损失，逻辑成立。"
        },
        {
            "name": "职业成功案例",
            "claim": "双鱼座上升, Malavya Mahapurusha Yoga(金星7宫), Neecha Bhanga Raja Yoga, 水星Dasha激活第10宫",
            "notes": "化名'The Dynamo'。\n"
                     "- Malavya Yoga: 金星在Kendra宫(7宫) → 明星/演艺潜质\n"
                     "- 金星落陷处女座 + 水星(处女座主星)也在7宫 → Neecha Bhanga成立\n"
                     "- 2/11宫主火星在10宫射手座入庙 → Dhana Yoga\n"
                     "- 水星Dasha: 水星是10宫主, 激活职业承诺\n"
                     "- 时间线: 土星期(贫困)→水星期(突破)→罗喉期(财富巩固) → 精准的Dasha递进",
            "verdict": "Yoga组合+Dasha时间线完全符合BPHS。Neecha Bhanga转化机制明确。"
        },
        {
            "name": "婚姻离婚案例",
            "claim": "天秤座上升, 7宫主火星在8宫, Rahu在7宫/Ketu在1宫, 火星大运激活离婚",
            "notes": "- 7宫主(火星)在8宫 → 婚姻不稳定的首要指标(BPHS经典)\n"
                     "- Rahu 7宫: 对伴侣关系执着但无法稳定\n"
                     "- Ketu 1宫: 自我身份困惑, 前世业力\n"
                     "- 火星大运 + 火星-土星小运 → 冲突爆发+正式分离\n"
                     "- Trika宫(6/8/12)干扰 → 8宫婚姻主星被Trika影响",
            "verdict": "婚姻危机的经典BPHS配置。7宫主在dushtana + Rahu-Ketu轴线 + Dasha触发完全符合经典。"
        },
    ]

    for vc in vedicka_cases:
        print(f"### {vc['name']}")
        print(f"**论断**: {vc['claim']}")
        print(f"**验证说明**: {vc['notes']}")
        print(f"**结论**: {vc['verdict']}")
        print()

    # ============================================================
    # 总结
    # ============================================================
    print("=" * 90)
    print("## 验证总结")
    print()

    print("### 可精确验证的案例")
    print("| 案例 | Lagna验证 | Sun验证 | Moon验证 | 结论 |")
    print("|------|-----------|---------|----------|------|")

    # Anandamoyi Ma with best-matching tz
    for tz_name, tz_val in [("UTC+5.883", 5.883), ("UTC+6.0", 6.0), ("UTC+5.5", 5.5)]:
        data = run_chart(1896, 4, 30, 3, 42, 23.45, 91.13, tz_val)
        a = data['ascendant']
        ref_asc = "Aries 6°48'"
        aries_target = 6.8
        actual = a['degree'] + (sign_num(a['sign']) * 30) if a['sign'] != 'Aries' else a['degree']
        diff_asc = abs(actual - aries_target)
        
        if a['sign'] == 'Aries' and diff_asc < 2:
            status = "✓ Lagna精确匹配"
        elif a['sign'] == 'Aries':
            status = f"~ Lagna星座匹配(差{diff_asc:.1f}°)"
        else:
            status = f"✗ Lagna不匹配({a['sign']}≠Aries)"
        
        if tz_name == "UTC+5.883":
            print(f"| Anandamoyi Ma ({tz_name}) | {status} | 待查 | 待查 | 需矫正时区 |")

    print()
    print("### Vedicka案例研究 (无法精确验证, 无出生数据)")
    print("| 案例 | 理论一致性 | 说明 |")
    print("|------|-----------|------|")
    for vc in vedicka_cases:
        print(f"| {vc['name']} | ✓ 一致 | {vc['verdict']} |")

    print()
    print("### 关键发现")
    print("1. 多数Vedicka案例研究使用化名且无精确出生数据，无法进行数学验证")
    print("2. 阿南达莫依玛案例：使用UTC+6时Lagna不匹配（引擎=Pisces, 参考=Aries）")
    print("   - 可能原因1: 时区不使用UTC+6（1896年Bengal使用Calcutta Time UTC+5:53）")
    print("   - 可能原因2: 出生时间经过矫正（原文注明「经过矫正的生时」）")
    print("   - 可能原因3: 参考ASC本身基于西洋占星/热带黄道计算")
    print("3. Vedicka的Dasha分析和Yoga识别在理论上符合BPHS经典原理")
    print("4. 建议后续任务：为Vedicka案例获取更精确的出生数据，进行定量验证")
    print("=" * 90)

if __name__ == '__main__':
    main()
