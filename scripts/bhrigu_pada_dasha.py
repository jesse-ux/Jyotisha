"""
Bhrigu Pada Dasha（Bhrigu 足步 Dasha）计算引擎 v1.0
Jyotish Vedic Astrology Skill - Bhrigu Pada Dasha Module

来源：公众号文章「4印度占星」，Bhrigu 体系下的行星推进法
重要：Pada Dasha 精确公式因 Bhrigu 子流派而异，本实现为通用近似版。
      实战中应与 Vimshottari/Chara Dasha 交叉验证。

核心概念：
- Bhrigu Pada Dasha 是基于行星推进（Progression）的 Dasha 系统
- 与西方占星的 Secondary Progression 类似：每年推进一定度数
- 主要用于婚姻时机预测，也可用于其他人生重大事件
- 与 BCP（Bhrigu Chakra Paddhati 自然周期法）互补

计算要点（因流派而异，以下为通用近似）：
1. 起始点：基于命盘中特定行星的 Pada（足迹/投射点）
2. 推进速率：每年推进一定度数（通用近似：1°/年，类似 Secondary Progression）
3. 星座序列：按特定顺序（近似：从起始星座开始，按正常星座顺序）
4. D9 验证：Pada Dasha 的结果需在 D9 中验证

本实现提供：
- 通用近似推进计算（用于婚姻时机粗略定位）
- 与婚姻计数法（Marriage Counting Method）的整合接口
- D9 验证框架（需 D9 数据）

限制：
- 精确推进速率因 Bhrigu 子流派而异，本实现使用 1°/年近似
- 起始点确定规则因流派而异，本实现使用 Moon 作为默认起始点
- 实战中必须用 Vimshottari/Chara Dasha 交叉验证
"""

import math

# ── 基础常量 ──
SIGN_NAMES = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
              'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']
SIGN_CN = ['白羊座','金牛座','双子座','巨蟹座','狮子座','处女座',
           '天秤座','天蝎座','射手座','摩羯座','水瓶座','双鱼座']
SIGN_LORDS = ['Mars','Venus','Mercury','Moon','Sun','Mercury',
              'Venus','Mars','Jupiter','Saturn','Saturn','Jupiter']

def sign_of(lon):
    """经度 -> 星座序号 (0-11)"""
    return int((lon % 360) / 30)

def norm(lon):
    """归一化到 0-360"""
    return lon % 360

def lon_cn(lon):
    """经度 -> 中文星座名+度数"""
    s = sign_of(lon)
    d = lon % 30
    return f"{SIGN_CN[s]} {int(d)}°{int((d%1)*60)}'"

# ── Bhrigu Pada Dasha 核心计算 ──

def calc_pada_dasha_basic(birth_moon_lon, birth_date_jd, target_date_jd, 
                          progression_rate=1.0, start_planet='Moon'):
    """
    通用近似 Bhrigu Pada Dasha 计算
    
    Parameters:
    - birth_moon_lon: 出生月亮经度（Sidereal）
    - birth_date_jd: 出生 Julian Day
    - target_date_jd: 目标时间 Julian Day
    - progression_rate: 推进速率（度/年），默认 1.0（近似 Secondary Progression）
    - start_planet: 起始行星，默认 'Moon'（通用近似）
    
    Returns:
    - dict: {progressed_lon, progressed_sign, years_elapsed, interpretation}
    """
    # 计算经过年数
    days_elapsed = target_date_jd - birth_date_jd
    years_elapsed = days_elapsed / 365.25
    
    # 推进经度 = 起始经度 + 年数 × 推进速率
    progressed_lon = norm(birth_moon_lon + years_elapsed * progression_rate)
    progressed_sign = sign_of(progressed_lon)
    
    return {
        'progressed_longitude': round(progressed_lon, 4),
        'progressed_sign': SIGN_NAMES[progressed_sign],
        'progressed_sign_cn': SIGN_CN[progressed_sign],
        'years_elapsed': round(years_elapsed, 2),
        'progression_rate': progression_rate,
        'note': '通用近似版，精确公式因 Bhrigu 子流派而异'
    }

def calc_pada_dasha_marriage_timing(birth_moon_lon, birth_date_jd, 
                                     target_date_jd, d9_7lord_sign=None):
    """
    Bhrigu Pada Dasha 婚姻时机计算（通用近似）
    
    逻辑：
    1. 计算目标时间的推进月亮位置
    2. 检查推进月亮是否与 D1/D9 的婚姻相关点形成联系
    3. D9 验证：推进月亮在 D9 中的位置
    
    Parameters:
    - birth_moon_lon: 出生月亮 Sidereal 经度
    - birth_date_jd: 出生 JD
    - target_date_jd: 目标时间 JD
    - d9_7lord_sign: D9 中 7 宫主的星座 (0-11)，用于验证
    
    Returns:
    - dict: 婚姻时机分析
    """
    # 推进月亮
    prog = calc_pada_dasha_basic(birth_moon_lon, birth_date_jd, target_date_jd)
    prog_sign = sign_of(prog['progressed_longitude'])
    
    # 婚姻相关点（通用近似）
    # 1. 推进月亮与 D1 7 宫主的联系
    # 2. 推进月亮与 Venus 的联系
    # 3. 推进月亮进入 D9 7 宫主星座
    
    analysis = {
        'progressed_moon': prog,
        'marriage_indicators': {}
    }
    
    # 指示词 1：推进月亮在 D9 7 宫主星座
    if d9_7lord_sign is not None:
        analysis['marriage_indicators']['d9_7lord_sign'] = SIGN_NAMES[d9_7lord_sign]
        analysis['marriage_indicators']['progressed_moon_in_d9_7lord_sign'] = (prog_sign == d9_7lord_sign)
    
    # 指示词 2：推进月亮在 Venus 星座（通用近似）
    # Venus 星座需要从外部传入，这里只提供框架
    
    return analysis

def bhrigu_pada_dasha_full_report(birth_moon_lon, birth_date_jd, 
                                   d9_7lord_sign=None, d9_planets=None):
    """
    Bhrigu Pada Dasha 完整报告（通用近似版）
    
    Parameters:
    - birth_moon_lon: 出生月亮经度
    - birth_date_jd: 出生 JD
    - d9_7lord_sign: D9 7 宫主星座 (0-11)
    - d9_planets: D9 行星数据 {name: longitude}
    
    Returns:
    - dict: 完整报告
    """
    report = {
        'method': 'Bhrigu Pada Dasha (通用近似版)',
        'source': '公众号文章「4印度占星」',
        'note': '精确公式因 Bhrigu 子流派而异，本实现为通用近似。实战需与 Vimshottari/Chara Dasha 交叉验证。',
        'birth_moon': {
            'longitude': round(birth_moon_lon, 4),
            'sign': SIGN_NAMES[sign_of(birth_moon_lon)],
            'sign_cn': SIGN_CN[sign_of(birth_moon_lon)]
        }
    }
    
    # 示例：计算几个关键年龄的推进月亮位置
    sample_ages = [20, 24, 25, 26, 28, 30, 32]
    progressions = {}
    for age in sample_ages:
        target_jd = birth_date_jd + age * 365.25
        prog = calc_pada_dasha_basic(birth_moon_lon, birth_date_jd, target_jd)
        progressions[f'age_{age}'] = prog
    report['sample_progressions'] = progressions
    
    # D9 验证框架
    if d9_7lord_sign is not None:
        report['d9_verification'] = {
            'd9_7lord_sign': SIGN_NAMES[d9_7lord_sign],
            'note': 'D9 验证：Pada Dasha 推进结果需在 D9 中确认'
        }
    
        # 检查样本年龄中哪些的推进月亮在 D9 7 宫主星座
        marriage_windows = []
        for age_str, prog_data in progressions.items():
            if sign_of(prog_data['progressed_longitude']) == d9_7lord_sign:
                age = int(age_str.split('_')[1])
                marriage_windows.append(age)
        report['d9_verification']['marriage_windows'] = marriage_windows
    
    return report

# ── CLI 入口 ──
if __name__ == '__main__':
    import argparse, datetime
    
    parser = argparse.ArgumentParser(description='Bhrigu Pada Dasha Calculator (Approximate)')
    parser.add_argument('--moon', type=float, help='Birth Moon longitude (sidereal)')
    parser.add_argument('--jd', type=float, help='Birth Julian Day')
    parser.add_argument('--d9-7lord-sign', type=int, help='D9 7th lord sign (0-11)')
    parser.add_argument('--test', action='store_true', help='Run test')
    
    args = parser.parse_args()
    
    if args.test or (args.moon is None):
        # 测试用例：月亮 120°（巨蟹座 0°），出生 JD 2449080.5
        test_moon = 120.0
        test_jd = 2449080.5
        result = bhrigu_pada_dasha_full_report(test_moon, test_jd, d9_7lord_sign=3)
        print(json.dumps(result, indent=2, ensure_ascii=False) if False else None)
        
        print("=== Bhrigu Pada Dasha 测试报告 ===")
        print(f"出生月亮: {lon_cn(test_moon)}")
        print(f"\n样本推进（1°/年近似）:")
        for age_str, prog in result['sample_progressions'].items():
            age = age_str.split('_')[1]
            print(f"  {age}岁: {lon_cn(prog['progressed_longitude'])}")
        if result.get('d9_verification'):
            print(f"\nD9 验证: 7宫主在 {result['d9_verification']['d9_7lord_sign']}")
            print(f"婚姻窗口: {result['d9_verification']['marriage_windows']}")
    else:
        result = bhrigu_pada_dasha_full_report(args.moon, args.jd, args.d9_7lord_sign)
        import json
        print(json.dumps(result, indent=2, ensure_ascii=False))
