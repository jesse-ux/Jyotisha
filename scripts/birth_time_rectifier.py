#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
出生时间矫正模块 v1.0
基于 vedic-astro-skills (MIT) rectifier方法论 + BPHS标准

核心方法：
1. 事件回溯法 — 收集10-25个生命事件，通过Dasha/Transit反向校准
2. Lagna边界检测 — 0-3度或27-30度自动触发
3. 分盘敏感度 — 根据矫正后精度决定分盘启用范围
4. 双Lagna对比 — 相邻星座双盘交叉验证
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

SIGNS = ['Aries','Taurus','Gemini','Cancer','Leo','Virgo',
         'Libra','Scorpio','Sagittarius','Capricorn','Aquarius','Pisces']

# 关键人生事件与宫位/Dasha的映射
EVENT_HOUSE_MAP = {
    'marriage': {'primary': 7, 'secondary': [2, 11], 'karaka': 'Venus'},
    'child_birth': {'primary': 5, 'secondary': [9], 'karaka': 'Jupiter'},
    'career_start': {'primary': 10, 'secondary': [6, 2], 'karaka': 'Saturn'},
    'career_change': {'primary': 10, 'secondary': [6, 8], 'karaka': 'Saturn'},
    'promotion': {'primary': 10, 'secondary': [5, 9], 'karaka': 'Jupiter'},
    'relocation': {'primary': 4, 'secondary': [12, 9], 'karaka': 'Rahu'},
    'education_end': {'primary': 5, 'secondary': [9, 4], 'karaka': 'Jupiter'},
    'father_death': {'primary': 9, 'secondary': [8, 4], 'karaka': 'Sun'},
    'mother_death': {'primary': 4, 'secondary': [8, 2], 'karaka': 'Moon'},
    'accident': {'primary': 8, 'secondary': [6, 1], 'karaka': 'Mars'},
    'health_crisis': {'primary': 6, 'secondary': [8, 1], 'karaka': 'Saturn'},
    'windfall': {'primary': 2, 'secondary': [11, 5], 'karaka': 'Jupiter'},
    'financial_loss': {'primary': 12, 'secondary': [8, 6], 'karaka': 'Saturn'},
    'spiritual_awakening': {'primary': 9, 'secondary': [12, 5], 'karaka': 'Ketu'},
}

# 矫正精度与分盘启用矩阵
ACCURACY_MATRIX = {
    'minute': {'D1': True, 'D9': True, 'D10': True, 'D5': True, 'D4': True, 'D7': 'warn', 'D30': False, 'D60': False},
    '15min': {'D1': True, 'D9': True, 'D10': 'warn', 'D5': 'warn', 'D4': 'warn', 'D7': False},
    '1hour': {'D1': True, 'D9': 'warn'},
    'unknown': {'D1': True, 'D9': 'warn'},
    'rectified': {'D1': True, 'D9': True, 'D10': True, 'D5': True, 'D4': True, 'D7': 'warn', 'D30': False},
}


def check_lagna_boundary(asc_degree: float) -> Tuple[bool, str]:
    """检查Lagna是否接近星座边界（0-3度或27-30度）"""
    deg_in_sign = asc_degree % 30
    if deg_in_sign <= 3.0:
        return True, f'Lagna接近星座起点({deg_in_sign:.1f}°)，时间敏感度高'
    if deg_in_sign >= 27.0:
        return True, f'Lagna接近星座终点({deg_in_sign:.1f}°)，可能跨星座'
    return False, ''


def get_effective_accuracy(declared_accuracy: str, time_source: str) -> str:
    """根据用户声明精度和时间来源计算有效精度"""
    ACCURACY_RULES = {
        ('minute', 'hospital'): 'minute',
        ('minute', 'family_clear'): '5min',
        ('minute', 'family_vague'): '15min',
        ('15min', '*'): '15min',
        ('1hour', '*'): '1hour',
        ('unknown', '*'): 'unknown',
    }
    for (acc, src), result in ACCURACY_RULES.items():
        if (acc == declared_accuracy or acc == '*') and (src == time_source or src == '*'):
            return result
    return declared_accuracy


def get_enabled_vargas(accuracy: str) -> Dict[str, str]:
    """根据矫正精度获取可用的分盘列表"""
    matrix = ACCURACY_MATRIX.get(accuracy, ACCURACY_MATRIX['unknown'])
    result = {}
    for varga, status in matrix.items():
        if status is True:
            result[varga] = 'enabled'
        elif status == 'warn':
            result[varga] = 'enabled_with_warning'
        else:
            result[varga] = 'disabled'
    return result


def calculate_confidence(events_matched: int, events_total: int,
                         accuracy: str, lagna_boundary: bool) -> Dict:
    """
    计算矫正置信度。
    
    Args:
        events_matched: 匹配的事件数
        events_total: 总事件数
        accuracy: 矫正精度
        lagna_boundary: 是否在Lagna边界
    
    Returns:
        置信度评估
    """
    match_rate = events_matched / events_total if events_total > 0 else 0
    base_confidence = match_rate * 100
    
    # 精度加成
    if accuracy in ('minute', '5min'):
        base_confidence = min(100, base_confidence + 10)
    
    # Lagna边界扣除
    if lagna_boundary:
        base_confidence = max(0, base_confidence - 15)
    
    if base_confidence >= 90:
        level = 'high'
        assessment = '矫正置信度高，分盘分析可用'
    elif base_confidence >= 70:
        level = 'medium'
        assessment = '矫正置信度中等，主力盘(D1/D9)可用，高级分盘需谨慎'
    elif base_confidence >= 50:
        level = 'low'
        assessment = '矫正置信度偏低，建议只用D1分析'
    else:
        level = 'insufficient'
        assessment = '矫正证据不足，建议收集更多事件后重试'
    
    return {
        'confidence': round(base_confidence, 1),
        'level': level,
        'assessment': assessment,
        'events_matched': events_matched,
        'events_total': events_total,
    }


def recommend_event_types(planet_positions: Dict) -> List[str]:
    """
    根据星盘配置推荐适合验证的事件类型。
    
    信号越强的领域，事件回溯命中率越高。
    """
    recommendations = []
    
    # 检查婚姻信号
    if planet_positions.get('Venus', {}).get('house') in (1, 4, 7, 10):
        recommendations.append('marriage')
    if planet_positions.get('Jupiter', {}).get('house') in (5, 9):
        recommendations.append('child_birth')
    if planet_positions.get('Saturn', {}).get('house') in (10, 6):
        recommendations.append('career_start')
    if planet_positions.get('Rahu', {}).get('house') in (4, 9, 12):
        recommendations.append('relocation')
    if planet_positions.get('Mars', {}).get('house') in (8, 6, 1):
        recommendations.append('accident')
    if planet_positions.get('Jupiter', {}).get('house') in (2, 11):
        recommendations.append('windfall')
    
    # 最少返回3个
    if len(recommendations) < 3:
        recommendations.extend(['career_change', 'education_end', 'relocation'])
    
    return recommendations[:8]  # 最多8个推荐


def suggest_correction_direction(asc_degree: float, lagna_boundary: bool,
                                 events_early: int, events_late: int) -> str:
    """
    建议矫正方向（提前或延后）。
    """
    if not lagna_boundary:
        return 'Lagna不在边界，时间偏差可能较小'
    
    if events_early > events_late:
        direction = '提前'
        minutes = abs(events_early - events_late) * 3
        return f'事件偏早，建议: 出生时间**提前**约{minutes}分钟'
    elif events_late > events_early:
        direction = '延后'
        minutes = abs(events_late - events_early) * 3
        return f'事件偏晚，建议: 出生时间**延后**约{minutes}分钟'
    else:
        return '事件时序正常，无需大幅调整'
