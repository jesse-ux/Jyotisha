#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cmd_solar_return: Solar Return (Varshaphala) CLI 子命令
Jyotish Vedic Astrology Skill — v6.0.18

用法:
  python3 jyotish_engine.py solar-return --year REDACTED_YEAR --month 4 --day 17 \
      --hour 14 --minute 45 --lat 36.4667 --lon 114.2 --tz 8 --target-year 2026
"""

import sys
import os
from typing import Dict, Any


def cmd_solar_return(args: Any) -> Dict[str, Any]:
    """
    solar-return 子命令：计算太阳返照盘 + 完整 Varshaphala 分析。

    参数 (来自 args):
        year, month, day, hour, minute: 出生时间
        lat, lon, tz: 出生地点/时区
        target_year: 目标年份（计算该年太阳返照）

    返回:
        dict: solar_return_full_report() 的结果
    """
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from solar_return import solar_return_full_report
    except ImportError as e:
        return {"error": f"solar_return 模块导入失败: {e}"}

    if not hasattr(args, 'target_year') or args.target_year is None:
        return {"error": "solar-return 需要 --target-year 参数",
                "hint": "指定目标年份，如 --target-year 2026"}

    return solar_return_full_report(
        args.year, args.month, args.day,
        args.hour, args.minute,
        args.lat, args.lon, args.tz,
        args.target_year,
    )


if __name__ == '__main__':
    # 独立测试入口
    import argparse
    from datetime import datetime

    parser = argparse.ArgumentParser(description='Solar Return 测试')
    parser.add_argument('--year', type=int, required=True)
    parser.add_argument('--month', type=int, required=True)
    parser.add_argument('--day', type=int, required=True)
    parser.add_argument('--hour', type=int, default=12)
    parser.add_argument('--minute', type=int, default=0)
    parser.add_argument('--lat', type=float, required=True)
    parser.add_argument('--lon', type=float, required=True)
    parser.add_argument('--tz', type=float, default=0.0)
    parser.add_argument('--target-year', type=int, required=True)
    a = parser.parse_args()

    result = cmd_solar_return(a)
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
