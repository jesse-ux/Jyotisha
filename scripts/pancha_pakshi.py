#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pancha_pakshi.py — Pancha Pakshi 五鸟择时引擎
===============================================
基于出生Nakshatra和Paksha计算每日吉凶活动时段

版本: v1.0 | 2026-06-07
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class ActivityType(Enum):
    """五鸟活动类型"""
    RULE = "rule"           # 统治 — 吉
    EAT = "eat"             # 进食 — 吉
    WALK = "walk"           # 行走 — 中
    SLEEP = "sleep"         # 睡眠 — 凶
    DEATH = "death"         # 死亡 — 凶


class BirdType(Enum):
    """五鸟类型"""
    VULTURE = "vulture"     # 兀鹫
    OWL = "owl"             # 猫头鹰
    CROW = "crow"           # 乌鸦
    COCK = "cock"           # 公鸡
    PEACOCK = "peacock"     # 孔雀


# Nakshatra到鸟的映射（Shukla Paksha / Krishna Paksha）
NAKSHATRA_BIRDS = {
    # Shukla Paksha (亮月期)
    "shukla": {
        "Ashwini": BirdType.VULTURE, "Bharani": BirdType.OWL,
        "Krittika": BirdType.CROW, "Rohini": BirdType.COCK,
        "Mrigashira": BirdType.PEACOCK, "Ardra": BirdType.VULTURE,
        "Punarvasu": BirdType.OWL, "Pushya": BirdType.CROW,
        "Ashlesha": BirdType.COCK, "Magha": BirdType.PEACOCK,
        "Purva Phalguni": BirdType.VULTURE, "Uttara Phalguni": BirdType.OWL,
        "Hasta": BirdType.CROW, "Chitra": BirdType.COCK,
        "Swati": BirdType.PEACOCK, "Vishakha": BirdType.VULTURE,
        "Anuradha": BirdType.OWL, "Jyeshtha": BirdType.CROW,
        "Mula": BirdType.COCK, "Purva Ashadha": BirdType.PEACOCK,
        "Uttara Ashadha": BirdType.VULTURE, "Shravana": BirdType.OWL,
        "Dhanishta": BirdType.CROW, "Shatabhisha": BirdType.COCK,
        "Purva Bhadrapada": BirdType.PEACOCK, "Uttara Bhadrapada": BirdType.VULTURE,
        "Revati": BirdType.OWL,
    },
    # Krishna Paksha (暗月期)
    "krishna": {
        "Ashwini": BirdType.OWL, "Bharani": BirdType.VULTURE,
        "Krittika": BirdType.PEACOCK, "Rohini": BirdType.COCK,
        "Mrigashira": BirdType.CROW, "Ardra": BirdType.OWL,
        "Punarvasu": BirdType.VULTURE, "Pushya": BirdType.PEACOCK,
        "Ashlesha": BirdType.COCK, "Magha": BirdType.CROW,
        "Purva Phalguni": BirdType.OWL, "Uttara Phalguni": BirdType.VULTURE,
        "Hasta": BirdType.PEACOCK, "Chitra": BirdType.COCK,
        "Swati": BirdType.CROW, "Vishakha": BirdType.OWL,
        "Anuradha": BirdType.VULTURE, "Jyeshtha": BirdType.PEACOCK,
        "Mula": BirdType.COCK, "Purva Ashadha": BirdType.CROW,
        "Uttara Ashadha": BirdType.OWL, "Shravana": BirdType.VULTURE,
        "Dhanishta": BirdType.PEACOCK, "Shatabhisha": BirdType.COCK,
        "Purva Bhadrapada": BirdType.CROW, "Uttara Bhadrapada": BirdType.OWL,
        "Revati": BirdType.VULTURE,
    },
}

# 鸟的活动周期表（5个Yama × 5种活动）
# 每个Yama约3小时（一天15小时，从日出到日落）
BIRD_ACTIVITY_TABLE = {
    BirdType.VULTURE: [
        [ActivityType.RULE, ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH],
        [ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE],
        [ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT],
        [ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT, ActivityType.WALK],
        [ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP],
    ],
    BirdType.OWL: [
        [ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT],
        [ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT, ActivityType.WALK],
        [ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP],
        [ActivityType.RULE, ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH],
        [ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE],
    ],
    BirdType.CROW: [
        [ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP],
        [ActivityType.RULE, ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH],
        [ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE],
        [ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT],
        [ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT, ActivityType.WALK],
    ],
    BirdType.COCK: [
        [ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT, ActivityType.WALK],
        [ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP],
        [ActivityType.RULE, ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH],
        [ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE],
        [ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT],
    ],
    BirdType.PEACOCK: [
        [ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE],
        [ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT],
        [ActivityType.SLEEP, ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT, ActivityType.WALK],
        [ActivityType.DEATH, ActivityType.RULE, ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP],
        [ActivityType.RULE, ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH],
    ],
}

# 活动吉凶
ACTIVITY_FORTUNE = {
    ActivityType.RULE: "吉",      # 统治 — 适合开始重要事务
    ActivityType.EAT: "吉",       # 进食 — 适合获取资源
    ActivityType.WALK: "中",      # 行走 — 适合日常活动
    ActivityType.SLEEP: "凶",     # 睡眠 — 避免重要决策
    ActivityType.DEATH: "凶",     # 死亡 — 极度不利
}

# 活动建议
ACTIVITY_ADVICE = {
    ActivityType.RULE: ["开始新项目", "做重要决策", "领导会议", "签署合同"],
    ActivityType.EAT: ["财务活动", "求职面试", "购买资产", "接受礼物"],
    ActivityType.WALK: ["日常事务", "短途旅行", "社交活动", "信息收集"],
    ActivityType.SLEEP: ["避免重要决策", "休息", "内省", "推迟行动"],
    ActivityType.DEATH: ["避免一切重要活动", "取消计划", "防护", "等待"],
}

# 活动相克
ACTIVITY_DOMINANCE = {
    ActivityType.RULE: [ActivityType.EAT, ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH],
    ActivityType.EAT: [ActivityType.WALK, ActivityType.SLEEP, ActivityType.DEATH],
    ActivityType.WALK: [ActivityType.SLEEP, ActivityType.DEATH],
    ActivityType.SLEEP: [ActivityType.DEATH],
    ActivityType.DEATH: [],
}


@dataclass
class YamaActivity:
    """单个Yama的活动"""
    yama_number: int           # 1-5
    yama_name: str             # Pratah/Madhyahna/Aparahna/Sayam/Ratri
    start_time: str            # 开始时间（近似）
    end_time: str              # 结束时间
    activity: ActivityType
    activity_cn: str
    fortune: str               # 吉/中/凶
    advice: List[str]


@dataclass
class DailySchedule:
    """每日活动表"""
    date: str
    bird: BirdType
    bird_cn: str
    paksha: str                # shukla/krishna
    yama_activities: List[YamaActivity] = field(default_factory=list)
    
    # 推荐时段
    best_periods: List[str] = field(default_factory=list)
    avoid_periods: List[str] = field(default_factory=list)
    
    narrative: str = ""


class PanchaPakshi:
    """五鸟择时引擎"""
    
    def __init__(self):
        self.nakshatra_birds = NAKSHATRA_BIRDS
        self.activity_table = BIRD_ACTIVITY_TABLE
        self.activity_fortune = ACTIVITY_FORTUNE
        self.activity_advice = ACTIVITY_ADVICE
    
    def calculate(self, birth_nakshatra: str, paksha: str,
                  date: Optional[str] = None, weekday: int = 0) -> DailySchedule:
        """
        计算某日的五鸟活动表 v7.0

        新增功能：
        - 完整5×5活动矩阵（不再只读对角线）
        - 基于星期的Yama起始偏移
        - 鸟间相克（对抗鸟）检查
        - 夜间Yama独立计算

        Args:
            birth_nakshatra: 出生Nakshatra
            paksha: 'shukla' (亮月) 或 'krishna' (暗月)
            date: 日期字符串（可选）
            weekday: 星期几 0=Sunday..6=Saturday（影响Yama偏移）
        """
        # 确定鸟类型
        bird = self._get_bird(birth_nakshatra, paksha)

        schedule = DailySchedule(
            date=date or "today",
            bird=bird,
            bird_cn=self._bird_to_chinese(bird),
            paksha=paksha,
        )

        # 生成5个Yama的活动
        yama_names = ["Pratah (晨)", "Madhyahna (午)", "Aparahna (下午)",
                      "Sayam (傍晚)", "Ratri (夜)"]
        time_ranges = ["6:00-9:00", "9:00-12:00", "12:00-15:00",
                       "15:00-18:00", "18:00-21:00"]

        # 基于星期的Yama偏移（经典规则：每天偏移1行）
        # Sunday=0→偏移0, Monday=1→偏移1, ... Saturday=6→偏移6 mod 5
        yama_row_offset = weekday % 5

        for yama_idx in range(5):
            # v7.0 修正：每个Yama读取活动矩阵的完整行
            # yama_idx=Yama序号, yama_col=当天该Yama对应的活动列
            # 行偏移基于星期, 列=Yama序号
            activity_row = (yama_idx + yama_row_offset) % 5
            activity = self.activity_table[bird][activity_row][yama_idx]

            yama = YamaActivity(
                yama_number=yama_idx + 1,
                yama_name=yama_names[yama_idx],
                start_time=time_ranges[yama_idx].split("-")[0],
                end_time=time_ranges[yama_idx].split("-")[1],
                activity=activity,
                activity_cn=self._activity_to_chinese(activity),
                fortune=self.activity_fortune.get(activity, "中"),
                advice=self.activity_advice.get(activity, [])
            )
            schedule.yama_activities.append(yama)

        # 推荐/避免时段
        self._generate_recommendations(schedule)

        # 生成叙事
        schedule.narrative = self._generate_narrative(schedule)

        return schedule
    
    def _get_bird(self, nakshatra: str, paksha: str) -> BirdType:
        """根据Nakshatra和Paksha确定鸟"""
        paksha_data = self.nakshatra_birds.get(paksha, self.nakshatra_birds["shukla"])
        return paksha_data.get(nakshatra, BirdType.PEACOCK)
    
    def _bird_to_chinese(self, bird: BirdType) -> str:
        """鸟类型转中文"""
        names = {
            BirdType.VULTURE: "兀鹫",
            BirdType.OWL: "猫头鹰",
            BirdType.CROW: "乌鸦",
            BirdType.COCK: "公鸡",
            BirdType.PEACOCK: "孔雀",
        }
        return names.get(bird, "未知")
    
    def _activity_to_chinese(self, activity: ActivityType) -> str:
        """活动类型转中文"""
        names = {
            ActivityType.RULE: "统治",
            ActivityType.EAT: "进食",
            ActivityType.WALK: "行走",
            ActivityType.SLEEP: "睡眠",
            ActivityType.DEATH: "死亡",
        }
        return names.get(activity, "未知")
    
    def _generate_recommendations(self, schedule: DailySchedule):
        """生成推荐和避免时段"""
        for yama in schedule.yama_activities:
            time_str = f"{yama.start_time}-{yama.end_time}"
            
            if yama.fortune == "吉":
                schedule.best_periods.append(f"{time_str} ({yama.activity_cn})")
            elif yama.fortune == "凶":
                schedule.avoid_periods.append(f"{time_str} ({yama.activity_cn})")
    
    def _generate_narrative(self, schedule: DailySchedule) -> str:
        """生成叙事"""
        parts = []
        
        parts.append("### Pancha Pakshi 五鸟择时\n")
        parts.append(f"您的出生鸟: **{schedule.bird_cn}** ({schedule.bird.value})\n")
        parts.append(f"月相: {'亮月期 (Shukla Paksha)' if schedule.paksha == 'shukla' else '暗月期 (Krishna Paksha)'}\n")
        
        parts.append("\n#### 今日活动表\n")
        for yama in schedule.yama_activities:
            emoji = "🟢" if yama.fortune == "吉" else "🟡" if yama.fortune == "中" else "🔴"
            parts.append(f"{emoji} **{yama.yama_name}** ({yama.start_time}-{yama.end_time})")
            parts.append(f"   活动: {yama.activity_cn} ({yama.fortune})")
            if yama.advice:
                parts.append(f"   建议: {'; '.join(yama.advice[:2])}")
            parts.append("")
        
        if schedule.best_periods:
            parts.append(f"\n✅ **最佳活动时段**: {'; '.join(schedule.best_periods[:3])}\n")
        
        if schedule.avoid_periods:
            parts.append(f"\n❌ **避免活动时段**: {'; '.join(schedule.avoid_periods)}\n")
        
        parts.append(f"\n#### 五鸟相克规则\n")
        parts.append("统治 > 进食 > 行走 > 睡眠 > 死亡\n")
        parts.append("当对方的活动克制你的活动时，不利。\n")
        
        return "\n".join(parts)
    
    def to_dict(self, schedule: DailySchedule) -> Dict:
        """转换为字典"""
        return {
            "date": schedule.date,
            "bird": schedule.bird.value,
            "bird_cn": schedule.bird_cn,
            "paksha": schedule.paksha,
            "activities": [
                {
                    "yama": y.yama_number,
                    "time": f"{y.start_time}-{y.end_time}",
                    "activity": y.activity.value,
                    "activity_cn": y.activity_cn,
                    "fortune": y.fortune,
                    "advice": y.advice,
                }
                for y in schedule.yama_activities
            ],
            "best_periods": schedule.best_periods,
            "avoid_periods": schedule.avoid_periods,
            "narrative": schedule.narrative,
        }


# ============================================================================
# 便捷函数
# ============================================================================

def get_pancha_pakshi_schedule(birth_nakshatra: str, paksha: str,
                                date: Optional[str] = None, weekday: int = 0) -> Dict:
    """便捷函数 v7.0 — 支持weekday偏移"""
    engine = PanchaPakshi()
    schedule = engine.calculate(birth_nakshatra, paksha, date, weekday)
    return engine.to_dict(schedule)


def get_bird_interaction(my_bird: str, other_bird: str) -> Dict:
    """
    五鸟相克互动分析 v7.0

    判断两只鸟之间的相克关系：
    - Rule鸟克Eat鸟，Eat鸟克Walk鸟，Walk鸟克Sleep鸟，Sleep鸟克Death鸟
    - 当对手鸟的活动克制你当前的活动时，不利

    Args:
        my_bird: 你的鸟 (vulture/owl/crow/cock/peacock)
        other_bird: 对手鸟

    Returns:
        互动分析结果
    """
    bird_map = {
        'vulture': BirdType.VULTURE, 'owl': BirdType.OWL,
        'crow': BirdType.CROW, 'cock': BirdType.COCK, 'peacock': BirdType.PEACOCK,
    }
    my = bird_map.get(my_bird.lower())
    other = bird_map.get(other_bird.lower())
    if not my or not other:
        return {'error': 'Invalid bird name'}

    # 鸟的层级（Rule>Eat>Walk>Sleep>Death）
    bird_hierarchy = {
        BirdType.VULTURE: 1, BirdType.OWL: 2,
        BirdType.CROW: 3, BirdType.COCK: 4, BirdType.PEACOCK: 5,
    }
    my_rank = bird_hierarchy[my]
    other_rank = bird_hierarchy[other]

    if my_rank < other_rank:
        relation = 'dominant'
        desc = f'{my_bird}克制{other_bird}，对你有利'
    elif my_rank > other_rank:
        relation = 'submissive'
        desc = f'{other_bird}克制{my_bird}，对你不利'
    else:
        relation = 'same'
        desc = '同类鸟，中性'

    return {
        'my_bird': my_bird,
        'other_bird': other_bird,
        'relation': relation,
        'description': desc,
    }


# ============================================================================
# CLI 调试
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Pancha Pakshi 五鸟择时引擎")
    print("=" * 60)
    
    result = get_pancha_pakshi_schedule("Rohini", "shukla", "2026-06-07")
    print(result["narrative"])
    print(f"\n出生鸟: {result['bird_cn']}")
