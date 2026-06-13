#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Divisional Charts Extended - D2-D60完整分盘宫位图计算器
印度占星 Shodasavarga（16分盘）+ 扩展分盘系统

核心功能：
- 计算D1-D60所有分盘的行星位置
- 生成每个分盘的12宫位行星分布图
- 支持BPHS标准算法
- 提供分盘上升点计算
- 输出可视化宫位图数据

参考文献：
- Brihat Parashara Hora Shastra (BPHS) Chapter 6
- Phaladeepika by Mantreswara
- Jataka Parijata by Vaidyanatha Dikshita
"""

from typing import Dict, List, Tuple
from enum import Enum

class VargaType(Enum):
    """分盘类型枚举"""
    D1 = (1, "Rashi", "本命盘")
    D2 = (2, "Hora", "财富")
    D3 = (3, "Drekkana", "兄弟姐妹")
    D4 = (4, "Chaturthamsa", "财产/运气")
    D5 = (5, "Panchamsa", "名声/权力")
    D6 = (6, "Shashthamsa", "健康/敌人")
    D7 = (7, "Saptamsa", "子女")
    D8 = (8, "Ashtamsa", "突发事件")
    D9 = (9, "Navamsa", "配偶/灵性")
    D10 = (10, "Dasamsa", "事业")
    D11 = (11, "Rudramsa", "破坏/转化")
    D12 = (12, "Dwadasamsa", "父母")
    D16 = (16, "Shodasamsa", "交通工具/舒适")
    D20 = (20, "Vimsamsa", "灵性修行")
    D24 = (24, "Chaturvimsamsa", "教育/学习")
    D27 = (27, "Bhamsa", "力量/弱点")
    D30 = (30, "Trimsamsa", "不幸/困难")
    D40 = (40, "Khavedamsa", "吉凶效果")
    D45 = (45, "Akshavedamsa", "全面判断")
    D60 = (60, "Shashtiamsa", "前世业力")
    D81 = (81, "Navamsa-Navamsa", "D9之D9精微分盘")
    D108 = (108, "Dwadasamsa-Navamsa", "D12之D9精微分盘")
    D144 = (144, "Dwadasamsa-Dwadasamsa", "D12之D12精微分盘")
    
    def __init__(self, division: int, name: str, meaning: str):
        self.division = division
        self.varga_name = name
        self.meaning = meaning

class DivisionalChartsCalculator:
    """分盘计算器"""
    
    SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
    
    # 星座分类
    MOVABLE_SIGNS = [0, 3, 6, 9]      # Aries, Cancer, Libra, Capricorn
    FIXED_SIGNS = [1, 4, 7, 10]       # Taurus, Leo, Scorpio, Aquarius
    DUAL_SIGNS = [2, 5, 8, 11]        # Gemini, Virgo, Sagittarius, Pisces
    
    ODD_SIGNS = [0, 2, 4, 6, 8, 10]   # 奇数星座
    EVEN_SIGNS = [1, 3, 5, 7, 9, 11]  # 偶数星座
    
    def __init__(self):
        pass
    
    def calculate_all_vargas(self, planet_positions: Dict[str, float],
                            asc_degree: float) -> Dict[str, Dict]:
        """
        计算所有分盘的行星位置
        
        Args:
            planet_positions: {行星名: 黄道度数(0-360)}
            asc_degree: 上升点黄道度数(0-360)
        
        Returns:
            {分盘名: {
                "planets": {行星名: {"sign": 星座, "degree": 度数, "house": 宫位}},
                "ascendant": {"sign": 星座, "degree": 度数},
                "house_chart": [宫位1的行星列表, 宫位2的行星列表, ...]
            }}
        """
        results = {}
        
        # 计算所有分盘
        for varga_type in VargaType:
            varga_result = self._calculate_single_varga(
                varga_type, planet_positions, asc_degree
            )
            results[varga_type.varga_name] = varga_result
        
        return results
    
    def _calculate_single_varga(self, varga_type: VargaType,
                                planet_positions: Dict[str, float],
                                asc_degree: float) -> Dict:
        """计算单个分盘"""
        division = varga_type.division
        
        # 计算分盘上升点
        varga_asc = self._calculate_varga_position(asc_degree, division)
        varga_asc_sign = int(varga_asc // 30)
        varga_asc_degree = varga_asc % 30
        
        # 计算所有行星的分盘位置
        varga_planets = {}
        for planet, degree in planet_positions.items():
            varga_pos = self._calculate_varga_position(degree, division)
            varga_sign = int(varga_pos // 30)
            varga_degree = varga_pos % 30
            
            # 计算宫位（从上升点开始）
            house = ((varga_sign - varga_asc_sign) % 12) + 1
            
            varga_planets[planet] = {
                "sign": self.SIGNS[varga_sign],
                "sign_index": varga_sign,
                "degree": round(varga_degree, 4),
                "house": house,
                "absolute_degree": round(varga_pos, 4)
            }
        
        # 生成宫位图（12个宫位，每个宫位包含的行星列表）
        house_chart = [[] for _ in range(12)]
        for planet, data in varga_planets.items():
            house_chart[data["house"] - 1].append(planet)
        
        return {
            "division": division,
            "name": varga_type.varga_name,
            "meaning": varga_type.meaning,
            "ascendant": {
                "sign": self.SIGNS[varga_asc_sign],
                "sign_index": varga_asc_sign,
                "degree": round(varga_asc_degree, 4)
            },
            "planets": varga_planets,
            "house_chart": house_chart
        }
    
    def _calculate_varga_position(self, degree: float, division: int) -> float:
        """
        计算分盘位置（BPHS标准算法）
        
        Args:
            degree: 黄道度数(0-360)
            division: 分盘数(2-60)
        
        Returns:
            分盘中的黄道度数(0-360)
        """
        # 获取星座索引和星座内度数
        sign_index = int(degree // 30)
        sign_degree = degree % 30
        
        # 根据不同分盘使用不同算法
        if division == 2:
            return self._calculate_d2(sign_index, sign_degree)
        elif division == 3:
            return self._calculate_d3(sign_index, sign_degree)
        elif division == 4:
            return self._calculate_d4(sign_index, sign_degree)
        elif division == 5:
            return self._calculate_d5(sign_index, sign_degree)
        elif division == 6:
            return self._calculate_d6(sign_index, sign_degree)
        elif division == 7:
            return self._calculate_d7(sign_index, sign_degree)
        elif division == 8:
            return self._calculate_d8(sign_index, sign_degree)
        elif division == 9:
            return self._calculate_d9(sign_index, sign_degree)
        elif division == 10:
            return self._calculate_d10(sign_index, sign_degree)
        elif division == 11:
            return self._calculate_d11(sign_index, sign_degree)
        elif division == 12:
            return self._calculate_d12(sign_index, sign_degree)
        elif division == 16:
            return self._calculate_d16(sign_index, sign_degree)
        elif division == 20:
            return self._calculate_d20(sign_index, sign_degree)
        elif division == 24:
            return self._calculate_d24(sign_index, sign_degree)
        elif division == 27:
            return self._calculate_d27(sign_index, sign_degree)
        elif division == 30:
            return self._calculate_d30(sign_index, sign_degree)
        elif division == 40:
            return self._calculate_d40(sign_index, sign_degree)
        elif division == 45:
            return self._calculate_d45(sign_index, sign_degree)
        elif division == 60:
            return self._calculate_d60(sign_index, sign_degree)
        elif division == 81:
            return self._calculate_d81(sign_index, sign_degree)
        elif division == 108:
            return self._calculate_d108(sign_index, sign_degree)
        elif division == 144:
            return self._calculate_d144(sign_index, sign_degree)
        else:
            # 通用算法（适用于其他分盘）
            return self._calculate_generic_varga(sign_index, sign_degree, division)
    
    def _calculate_d2(self, sign_index: int, sign_degree: float) -> float:
        """D2 Hora - 财富分盘"""
        # 奇数星座：0-15度→Leo，15-30度→Cancer
        # 偶数星座：0-15度→Cancer，15-30度→Leo
        if sign_index in self.ODD_SIGNS:
            if sign_degree < 15:
                return 4 * 30 + sign_degree * 2  # Leo
            else:
                return 3 * 30 + (sign_degree - 15) * 2  # Cancer
        else:
            if sign_degree < 15:
                return 3 * 30 + sign_degree * 2  # Cancer
            else:
                return 4 * 30 + (sign_degree - 15) * 2  # Leo
    
    def _calculate_d3(self, sign_index: int, sign_degree: float) -> float:
        """D3 Drekkana - 兄弟姐妹分盘"""
        # 每个星座分为3个10度区间
        # 第1个10度→本星座，第2个10度→第5个星座，第3个10度→第9个星座
        drekkana = int(sign_degree // 10)
        offset = [0, 4, 8][drekkana]
        varga_sign = (sign_index + offset) % 12
        varga_degree = (sign_degree % 10) * 3
        return varga_sign * 30 + varga_degree
    
    def _calculate_d4(self, sign_index: int, sign_degree: float) -> float:
        """D4 Chaturthamsa - 财产/运气分盘"""
        # 每个星座分为4个7.5度区间
        part = int(sign_degree // 7.5)
        varga_sign = (sign_index + part * 3) % 12
        varga_degree = (sign_degree % 7.5) * 4
        return varga_sign * 30 + varga_degree
    
    def _calculate_d7(self, sign_index: int, sign_degree: float) -> float:
        """D7 Saptamsa - 子女分盘"""
        # 每个星座分为7个约4.286度区间
        part = int(sign_degree // (30/7))
        if sign_index in self.ODD_SIGNS:
            varga_sign = (sign_index + part) % 12
        else:
            varga_sign = (sign_index + 6 + part) % 12
        varga_degree = (sign_degree % (30/7)) * 7
        return varga_sign * 30 + varga_degree
    
    def _calculate_d9(self, sign_index: int, sign_degree: float) -> float:
        """D9 Navamsa - 配偶/灵性分盘（最重要的分盘）"""
        # 每个星座分为9个3.333度区间
        part = int(sign_degree // (30/9))
        
        # 根据星座类型确定起始点 (BPHS标准)
        # Movable(白羊/巨蟹/天秤/摩羯)=从本星座开始
        # Fixed(金牛/狮子/天蝎/水瓶)=从第5个星座开始(+4)
        # Dual(双子/处女/射手/双鱼)=从第9个星座开始(+8)
        if sign_index in self.MOVABLE_SIGNS:
            start = sign_index
        elif sign_index in self.FIXED_SIGNS:
            start = (sign_index + 4) % 12
        else:  # DUAL_SIGNS
            start = (sign_index + 8) % 12
        
        varga_sign = (start + part) % 12
        varga_degree = (sign_degree % (30/9)) * 9
        return varga_sign * 30 + varga_degree
    
    def _calculate_d10(self, sign_index: int, sign_degree: float) -> float:
        """D10 Dasamsa - 事业分盘"""
        # 每个星座分为10个3度区间
        part = int(sign_degree // 3)
        if sign_index in self.ODD_SIGNS:
            varga_sign = (sign_index + part) % 12
        else:
            varga_sign = (sign_index + 8 + part) % 12
        varga_degree = (sign_degree % 3) * 10
        return varga_sign * 30 + varga_degree
    
    def _calculate_d12(self, sign_index: int, sign_degree: float) -> float:
        """D12 Dwadasamsa - 父母分盘"""
        # 每个星座分为12个2.5度区间
        part = int(sign_degree // 2.5)
        varga_sign = (sign_index + part) % 12
        varga_degree = (sign_degree % 2.5) * 12
        return varga_sign * 30 + varga_degree
    
    def _calculate_d16(self, sign_index: int, sign_degree: float) -> float:
        """D16 Shodasamsa - 交通工具/舒适分盘"""
        # 每个星座分为16个1.875度区间
        part = int(sign_degree // 1.875)
        if sign_index in self.MOVABLE_SIGNS:
            start = sign_index
        elif sign_index in self.FIXED_SIGNS:
            start = (sign_index + 4) % 12
        else:
            start = (sign_index + 8) % 12
        varga_sign = (start + part) % 12
        varga_degree = (sign_degree % 1.875) * 16
        return varga_sign * 30 + varga_degree
    
    def _calculate_d20(self, sign_index: int, sign_degree: float) -> float:
        """D20 Vimsamsa - 灵性修行分盘"""
        # 每个星座分为20个1.5度区间
        part = int(sign_degree // 1.5)
        if sign_index in self.MOVABLE_SIGNS:
            start = sign_index
        elif sign_index in self.FIXED_SIGNS:
            start = (sign_index + 8) % 12
        else:
            start = (sign_index + 4) % 12
        varga_sign = (start + part) % 12
        varga_degree = (sign_degree % 1.5) * 20
        return varga_sign * 30 + varga_degree
    
    def _calculate_d24(self, sign_index: int, sign_degree: float) -> float:
        """D24 Chaturvimsamsa - 教育/学习分盘"""
        # 每个星座分为24个1.25度区间
        part = int(sign_degree // 1.25)
        if sign_index in self.ODD_SIGNS:
            varga_sign = (4 + part) % 12  # 从Leo开始
        else:
            varga_sign = (3 + part) % 12  # 从Cancer开始
        varga_degree = (sign_degree % 1.25) * 24
        return varga_sign * 30 + varga_degree
    
    def _calculate_d27(self, sign_index: int, sign_degree: float) -> float:
        """D27 Bhamsa - 力量/弱点分盘"""
        # 每个星座分为27个1.111度区间
        part = int(sign_degree // (30/27))
        if sign_index in self.ODD_SIGNS:
            start = sign_index
        else:
            start = (sign_index + 8) % 12
        varga_sign = (start + part) % 12
        varga_degree = (sign_degree % (30/27)) * 27
        return varga_sign * 30 + varga_degree
    
    def _calculate_d30(self, sign_index: int, sign_degree: float) -> float:
        """D30 Trimsamsa - 不幸/困难分盘（特殊算法）"""
        # D30使用特殊的不等分算法
        # 奇数星座：Mars(5°), Saturn(5°), Jupiter(8°), Mercury(7°), Venus(5°)
        # 偶数星座：Venus(5°), Mercury(7°), Jupiter(8°), Saturn(5°), Mars(5°)
        
        if sign_index in self.ODD_SIGNS:
            if sign_degree < 5:
                varga_sign = 0  # Aries (Mars)
                varga_degree = sign_degree * 6
            elif sign_degree < 10:
                varga_sign = 10  # Aquarius (Saturn)
                varga_degree = (sign_degree - 5) * 6
            elif sign_degree < 18:
                varga_sign = 8  # Sagittarius (Jupiter)
                varga_degree = (sign_degree - 10) * 3.75
            elif sign_degree < 25:
                varga_sign = 2  # Gemini (Mercury)
                varga_degree = (sign_degree - 18) * 4.286
            else:
                varga_sign = 1  # Taurus (Venus)
                varga_degree = (sign_degree - 25) * 6
        else:
            if sign_degree < 5:
                varga_sign = 1  # Taurus (Venus)
                varga_degree = sign_degree * 6
            elif sign_degree < 12:
                varga_sign = 2  # Gemini (Mercury)
                varga_degree = (sign_degree - 5) * 4.286
            elif sign_degree < 20:
                varga_sign = 8  # Sagittarius (Jupiter)
                varga_degree = (sign_degree - 12) * 3.75
            elif sign_degree < 25:
                varga_sign = 10  # Aquarius (Saturn)
                varga_degree = (sign_degree - 20) * 6
            else:
                varga_sign = 0  # Aries (Mars)
                varga_degree = (sign_degree - 25) * 6
        
        return varga_sign * 30 + varga_degree
    
    def _calculate_d40(self, sign_index: int, sign_degree: float) -> float:
        """D40 Khavedamsa - 吉凶效果分盘"""
        # 每个星座分为40个0.75度区间
        part = int(sign_degree // 0.75)
        if sign_index in self.MOVABLE_SIGNS:
            start = sign_index
        elif sign_index in self.FIXED_SIGNS:
            start = (sign_index + 8) % 12
        else:
            start = (sign_index + 4) % 12
        varga_sign = (start + part) % 12
        varga_degree = (sign_degree % 0.75) * 40
        return varga_sign * 30 + varga_degree
    
    def _calculate_d45(self, sign_index: int, sign_degree: float) -> float:
        """D45 Akshavedamsa - 全面判断分盘"""
        # 每个星座分为45个0.667度区间
        part = int(sign_degree // (30/45))
        if sign_index in self.ODD_SIGNS:
            start = sign_index
        else:
            start = (sign_index + 8) % 12
        varga_sign = (start + part) % 12
        varga_degree = (sign_degree % (30/45)) * 45
        return varga_sign * 30 + varga_degree
    
    def _calculate_d60(self, sign_index: int, sign_degree: float) -> float:
        """D60 Shashtiamsa - 前世业力分盘（最精细的分盘）"""
        # 每个星座分为60个0.5度区间
        part = int(sign_degree // 0.5)
        varga_sign = (sign_index + part) % 12
        varga_degree = (sign_degree % 0.5) * 60
        return varga_sign * 30 + varga_degree

    def _calculate_d81(self, sign_index: int, sign_degree: float) -> float:
        """D81 Navamsa-Navamsa — D9的D9精微分盘"""
        # 先计算D9位置
        d9_lon = self._calculate_d9(sign_index, sign_degree)
        d9_sign = int(d9_lon / 30) % 12
        d9_deg = d9_lon % 30
        # 再对D9结果计算一次D9
        return self._calculate_d9(d9_sign, d9_deg)

    def _calculate_d108(self, sign_index: int, sign_degree: float) -> float:
        """D108 Dwadasamsa-Navamsa — D12的D9精微分盘"""
        d9_lon = self._calculate_d9(sign_index, sign_degree)
        d9_sign = int(d9_lon / 30) % 12
        d9_deg = d9_lon % 30
        return self._calculate_d12(d9_sign, d9_deg)

    def _calculate_d144(self, sign_index: int, sign_degree: float) -> float:
        """D144 Dwadasamsa-Dwadasamsa — D12的D12精微分盘"""
        d12_lon = self._calculate_d12(sign_index, sign_degree)
        d12_sign = int(d12_lon / 30) % 12
        d12_deg = d12_lon % 30
        return self._calculate_d12(d12_sign, d12_deg)
    
    def _calculate_d5(self, sign_index: int, sign_degree: float) -> float:
        """D5 Panchamsa - 名声/权力分盘"""
        part = int(sign_degree // 6)
        if sign_index in self.ODD_SIGNS:
            varga_sign = (sign_index + part) % 12
        else:
            varga_sign = (sign_index + 8 + part) % 12
        varga_degree = (sign_degree % 6) * 5
        return varga_sign * 30 + varga_degree
    
    def _calculate_d6(self, sign_index: int, sign_degree: float) -> float:
        """D6 Shashthamsa - 健康/敌人分盘"""
        part = int(sign_degree // 5)
        if sign_index in self.ODD_SIGNS:
            varga_sign = (sign_index + part) % 12
        else:
            varga_sign = (sign_index + 6 + part) % 12
        varga_degree = (sign_degree % 5) * 6
        return varga_sign * 30 + varga_degree
    
    def _calculate_d8(self, sign_index: int, sign_degree: float) -> float:
        """D8 Ashtamsa - 突发事件分盘"""
        part = int(sign_degree // 3.75)
        if sign_index in self.ODD_SIGNS:
            varga_sign = (sign_index + part) % 12
        else:
            varga_sign = (sign_index + 8 + part) % 12
        varga_degree = (sign_degree % 3.75) * 8
        return varga_sign * 30 + varga_degree
    
    def _calculate_d11(self, sign_index: int, sign_degree: float) -> float:
        """D11 Rudramsa - 破坏/转化分盘"""
        part = int(sign_degree // (30/11))
        if sign_index in self.ODD_SIGNS:
            varga_sign = (sign_index + part) % 12
        else:
            varga_sign = (sign_index + 8 + part) % 12
        varga_degree = (sign_degree % (30/11)) * 11
        return varga_sign * 30 + varga_degree
    
    def _calculate_generic_varga(self, sign_index: int, sign_degree: float, division: int) -> float:
        """通用分盘算法（适用于其他分盘）"""
        part = int(sign_degree // (30/division))
        varga_sign = (sign_index + part) % 12
        varga_degree = (sign_degree % (30/division)) * division
        return varga_sign * 30 + varga_degree
    
    def generate_house_chart_ascii(self, house_chart: List[List[str]]) -> str:
        """
        生成ASCII格式的宫位图
        
        Args:
            house_chart: 12个宫位的行星列表
        
        Returns:
            ASCII格式的宫位图字符串
        """
        # 北印度风格宫位图（菱形）
        chart = f"""
        ┌─────────┬─────────┬─────────┐
        │  12     │   1     │   2     │
        │ {self._format_planets(house_chart[11]):7} │ {self._format_planets(house_chart[0]):7} │ {self._format_planets(house_chart[1]):7} │
        ├─────────┼─────────┼─────────┤
        │  11     │         │   3     │
        │ {self._format_planets(house_chart[10]):7} │   ASC   │ {self._format_planets(house_chart[2]):7} │
        ├─────────┼─────────┼─────────┤
        │  10     │   9     │   4     │
        │ {self._format_planets(house_chart[9]):7} │ {self._format_planets(house_chart[8]):7} │ {self._format_planets(house_chart[3]):7} │
        ├─────────┼─────────┼─────────┤
        │   9     │   8     │   5     │
        │ {self._format_planets(house_chart[8]):7} │ {self._format_planets(house_chart[7]):7} │ {self._format_planets(house_chart[4]):7} │
        ├─────────┼─────────┼─────────┤
        │   8     │   7     │   6     │
        │ {self._format_planets(house_chart[7]):7} │ {self._format_planets(house_chart[6]):7} │ {self._format_planets(house_chart[5]):7} │
        └─────────┴─────────┴─────────┘
        """
        return chart
    
    def _format_planets(self, planets: List[str]) -> str:
        """格式化行星列表为简写"""
        if not planets:
            return "       "
        
        # 行星简写
        abbrev = {
            "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
            "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa",
            "Rahu": "Ra", "Ketu": "Ke"
        }
        
        short = [abbrev.get(p, p[:2]) for p in planets]
        return " ".join(short)[:7].ljust(7)


    # ============================================================
    # D2 Hora Variants (6 variants per BPHS / classical tradition)
    # ============================================================

    def _calculate_d2_variant(self, sign_index: int, sign_degree: float,
                              variant: str) -> float:
        """
        D2 Hora variants — BPHS + classical tradition provides 6 Hora methods:

        1. 'parashara' (default): Odd→Leo/Cancer, Even→Cancer/Leo
        2. 'pariveshta': Circular traversal — each Hora mapped to successive signs
        3. 'parivritta': Reversal method — even signs reverse the Hora order
        4. 'parivritta_trayodamsa': 13-part circular — each 30/13° maps to sign
        5. 'surya_chandra': Sun-Hora = odd signs → Sun sign (Leo),
           Moon-Hora = even signs → Moon sign (Cancer), but assignment by Rashi lord
        6. 'ahoratra': Day-night method — day births Sun Hora first,
           night births Moon Hora first

        Args:
            sign_index: 0-based rashi index
            sign_degree: degree within sign (0-30)
            variant: one of the 6 variant names

        Returns:
            divisional longitude (0-360)
        """
        is_odd = sign_index in self.ODD_SIGNS
        half = 15.0

        if variant == 'parashara':
            # Default BPHS — already implemented as _calculate_d2
            return self._calculate_d2(sign_index, sign_degree)

        elif variant == 'pariveshta':
            # Pariveshta (circular): Each Hora maps to the next sign in order
            # Odd signs: 0-15° → sign itself, 15-30° → next sign
            # Even signs: 0-15° → sign itself, 15-30° → next sign
            if sign_degree < half:
                varga_sign = sign_index
                varga_degree = sign_degree * 2
            else:
                varga_sign = (sign_index + 1) % 12
                varga_degree = (sign_degree - half) * 2
            return varga_sign * 30 + varga_degree

        elif variant == 'parivritta':
            # Parivritta (reversal): Even signs reverse the mapping
            # Odd: 0-15→Leo, 15-30→Cancer  |  Even: 0-15→Cancer, 15-30→Leo
            # Same as Parashara but with even-sign degree order reversed
            if is_odd:
                if sign_degree < half:
                    return 4 * 30 + sign_degree * 2  # Leo
                else:
                    return 3 * 30 + (sign_degree - half) * 2  # Cancer
            else:
                # Reversed: first half maps to Cancer, second to Leo
                # BUT degree within half is reversed: (30 - sign_degree)
                if sign_degree < half:
                    return 3 * 30 + (half - sign_degree) * 2  # Cancer reversed
                else:
                    return 4 * 30 + (30 - sign_degree) * 2  # Leo reversed

        elif variant == 'parivritta_trayodamsa':
            # Parivritta-Trayodamsa: 13-division Hora
            # Each 30/13 ≈ 2.3077° maps to successive signs from a base
            amsa = 30.0 / 13
            part = int(sign_degree / amsa)
            # Start from sign's own position, traverse 13 parts
            varga_sign = (sign_index + part) % 12
            varga_degree = (sign_degree - part * amsa) * 13
            return varga_sign * 30 + varga_degree

        elif variant == 'surya_chandra':
            # Surya-Chandra: Assignment by Rashi lord ownership
            # If planet is in Sun-ruled (Leo) or Moon-ruled (Cancer) portion
            # Odd signs: 0-15° → Sun hora → Leo, 15-30° → Moon hora → Cancer
            # Even signs: 0-15° → Moon hora → Cancer, 15-30° → Sun hora → Leo
            # Same mapping as Parashara but emphasizes Sun/Moon rulership
            if is_odd:
                if sign_degree < half:
                    varga_sign = 4  # Leo (Sun)
                else:
                    varga_sign = 3  # Cancer (Moon)
            else:
                if sign_degree < half:
                    varga_sign = 3  # Cancer (Moon)
                else:
                    varga_sign = 4  # Leo (Sun)
            varga_degree = (sign_degree % half) * 2
            return varga_sign * 30 + varga_degree

        elif variant == 'ahoratra':
            # Ahoratra (day-night): Day births prioritize Sun Hora,
            # Night births prioritize Moon Hora
            # For computation purposes (no birth time context available),
            # this uses the same mapping as Parashara but documents the
            # interpretive difference — practitioners should note day/night
            # Actually: same calculation as Parashara, the difference is
            # in interpretation (which Hora is stronger based on birth time)
            return self._calculate_d2(sign_index, sign_degree)

        else:
            raise ValueError(f"Unknown D2 variant: {variant}. "
                           f"Use: parashara/pariveshta/parivritta/"
                           f"parivritta_trayodamsa/surya_chandra/ahoratra")

    # ============================================================
    # D3 Drekkana Variants (4 variants per classical tradition)
    # ============================================================

    def _calculate_d3_variant(self, sign_index: int, sign_degree: float,
                              variant: str) -> float:
        """
        D3 Drekkana variants — 4 classical methods:

        1. 'parashara' (default): 0-10→same, 10-20→+4, 20-30→+8
        2. 'parivritta_trayodamsa': 13-sign circular traversal
        3. 'somaja': Moon-born method — starts from Cancer for 1st Drekkana
        4. 'khara': Harsh method — starts from 5th sign for even signs

        Args:
            sign_index: 0-based rashi index
            sign_degree: degree within sign (0-30)
            variant: one of the 4 variant names

        Returns:
            divisional longitude (0-360)
        """
        drekkana = int(sign_degree // 10)
        deg_in_drekkana = sign_degree % 10

        if variant == 'parashara':
            # Default — already implemented as _calculate_d3
            return self._calculate_d3(sign_index, sign_degree)

        elif variant == 'parivritta_trayodamsa':
            # Parivritta-Trayodamsa D3: 13-sign circular
            # Each 10° block maps to a sign starting from the rashi,
            # traversing forward by 4 each time but in a 13-sign cycle
            amsa = 30.0 / 13
            part = int(sign_degree / amsa)
            varga_sign = (sign_index + part) % 12
            varga_degree = (sign_degree - part * amsa) * 13
            return varga_sign * 30 + varga_degree

        elif variant == 'somaja':
            # Somaja (Moon-born): 1st Drekkana from Cancer (sign 3)
            # For all signs, the three Drekkanas map to:
            #   1st: Cancer (3), 2nd: Scorpio (7), 3rd: Pisces (11)
            # This is the "night" or Chandra-oriented Drekkana
            moon_signs = [3, 7, 11]  # Cancer, Scorpio, Pisces
            varga_sign = moon_signs[drekkana]
            varga_degree = deg_in_drekkana * 3
            return varga_sign * 30 + varga_degree

        elif variant == 'khara':
            # Khara: For odd signs → same as Parashara
            # For even signs → starts from 5th sign ahead
            if sign_index in self.ODD_SIGNS:
                offset = [0, 4, 8][drekkana]
                varga_sign = (sign_index + offset) % 12
            else:
                # Even signs: 1st Drekkana from +5, 2nd from +9, 3rd from +1
                offset = [5, 9, 1][drekkana]
                varga_sign = (sign_index + offset) % 12
            varga_degree = deg_in_drekkana * 3
            return varga_sign * 30 + varga_degree

        else:
            raise ValueError(f"Unknown D3 variant: {variant}. "
                           f"Use: parashara/parivritta_trayodamsa/somaja/khara")

    # ============================================================
    # Composite Divisional Charts (D-m×n)
    # ============================================================

    def calc_composite_varga(self, degree: float, outer_div: int,
                            inner_div: int) -> Dict:
        """
        Calculate composite divisional chart (D-m×n).

        This applies the outer division first, then applies the inner
        division to the result of the outer.

        Example: calc_composite_varga(lon, 9, 12) = D108 (D9 of D12)
                 calc_composite_varga(lon, 12, 12) = D144 (D12 of D12)
                 calc_composite_varga(lon, 9, 9) = D81 (D9 of D9)

        Args:
            degree: ecliptic longitude (0-360)
            outer_div: first (outer) division factor
            inner_div: second (inner) division factor

        Returns:
            {
                'composite_div': outer * inner,
                'sign': sign name,
                'sign_idx': 0-based sign index,
                'degree': degree within composite sign,
                'absolute_degree': absolute longitude in composite chart
            }
        """
        # Step 1: Apply outer division
        outer_result = self._calculate_varga_position(degree, outer_div)
        outer_sign = int(outer_result // 30)
        outer_deg = outer_result % 30

        # Step 2: Apply inner division to the outer result
        inner_result = self._calculate_varga_position(outer_result, inner_div)
        inner_sign = int(inner_result // 30)
        inner_deg = inner_result % 30

        return {
            'composite_div': outer_div * inner_div,
            'outer_div': outer_div,
            'inner_div': inner_div,
            'sign': self.SIGNS[inner_sign],
            'sign_idx': inner_sign,
            'degree': round(inner_deg, 4),
            'absolute_degree': round(inner_result, 4),
            'intermediate': {
                'outer_sign': self.SIGNS[outer_sign],
                'outer_degree': round(outer_deg, 4)
            }
        }

    # ============================================================
    # Custom D-N (N from 2 to 300)
    # ============================================================

    def calc_custom_varga(self, degree: float, n: int) -> Dict:
        """
        Calculate custom D-N divisional chart for any N (2-300).

        This matches JHora's custom D-N(1~300) feature.

        For standard N values (2-60), the BPHS-specific algorithms are used.
        For N > 60 or non-standard N, the general algorithm is used:
        - Odd signs: D-N sign = (rashi + part) % 12
        - Even signs: D-N sign = (rashi + offset + part) % 12
          where offset depends on N's relationship to 12

        Args:
            degree: ecliptic longitude (0-360)
            n: division factor (2-300)

        Returns:
            {
                'div': n,
                'sign': sign name,
                'sign_idx': 0-based sign index,
                'degree': degree within divisional sign,
                'part_index': which amsa (0-indexed),
                'absolute_degree': absolute longitude
            }
        """
        if n < 2 or n > 300:
            raise ValueError(f"Division factor N must be 2-300, got {n}")

        # For known standard divisions, use BPHS-precise algorithms
        standard_divs = {2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 20,
                        24, 27, 30, 40, 45, 60, 81, 108, 144}
        if n in standard_divs:
            varga_pos = self._calculate_varga_position(degree, n)
        else:
            # General custom algorithm
            sign_index = int(degree // 30)
            sign_degree = degree % 30
            varga_pos = self._custom_varga_general(sign_index, sign_degree, n)

        varga_sign = int(varga_pos // 30)
        varga_deg = varga_pos % 30

        # Calculate part index
        amsa_size = 30.0 / n
        sign_index = int(degree // 30)
        sign_degree = degree % 30
        part_index = int(sign_degree / amsa_size)

        return {
            'div': n,
            'sign': self.SIGNS[varga_sign],
            'sign_idx': varga_sign,
            'degree': round(varga_deg, 4),
            'part_index': part_index,
            'absolute_degree': round(varga_pos, 4),
            'amsa_size': round(amsa_size, 6)
        }

    def _custom_varga_general(self, sign_index: int, sign_degree: float,
                              n: int) -> float:
        """
        General custom varga algorithm for non-standard N values.

        Uses the standard rule:
        - Odd signs: (rashi + part) % 12
        - Even signs: (rashi + offset + part) % 12
          where offset is determined by the mathematical relationship:
          - If N is divisible by 12: offset = N/2 (midpoint traversal)
          - If N is odd: offset = 6 (septuple traversal like D7)
          - If N is even but not divisible by 12: offset = 8 (like D10)

        The degree within the amsa is scaled by N to fill 0-30.
        """
        amsa = 30.0 / n
        part = int(sign_degree / amsa)
        is_odd = sign_index in self.ODD_SIGNS

        if is_odd:
            varga_sign = (sign_index + part) % 12
        else:
            # Determine offset based on N's mathematical properties
            if n % 12 == 0:
                offset = (n // 2) % 12
            elif n % 2 == 1:
                offset = 6  # Septuple-like traversal
            else:
                offset = 8  # Dasamsa-like traversal
            varga_sign = (sign_index + offset + part) % 12

        varga_degree = (sign_degree - part * amsa) * n
        # Clamp degree to [0, 30)
        if varga_degree >= 30:
            varga_degree = varga_degree % 30
        return varga_sign * 30 + varga_degree

    # ============================================================
    # Batch variant calculation
    # ============================================================

    def calc_varga_with_variant(self, degree: float, div: int,
                                variant: str = None) -> Dict:
        """
        Calculate varga position, optionally using a named variant.

        For D2: variants are 'parashara', 'pariveshta', 'parivritta',
                'parivritta_trayodamsa', 'surya_chandra', 'ahoratra'
        For D3: variants are 'parashara', 'parivritta_trayodamsa',
                'somaja', 'khara'
        For other divisions: variant is ignored (standard algorithm)

        Args:
            degree: ecliptic longitude (0-360)
            div: division factor
            variant: optional variant name

        Returns:
            dict with sign, sign_idx, degree, variant info
        """
        sign_index = int(degree // 30)
        sign_degree = degree % 30

        if div == 2 and variant:
            varga_pos = self._calculate_d2_variant(sign_index, sign_degree, variant)
            used_variant = variant
        elif div == 3 and variant:
            varga_pos = self._calculate_d3_variant(sign_index, sign_degree, variant)
            used_variant = variant
        else:
            varga_pos = self._calculate_varga_position(degree, div)
            used_variant = 'parashara'  # default

        varga_sign = int(varga_pos // 30)
        varga_deg = varga_pos % 30

        return {
            'div': div,
            'sign': self.SIGNS[varga_sign],
            'sign_idx': varga_sign,
            'degree': round(varga_deg, 4),
            'variant': used_variant,
            'absolute_degree': round(varga_pos, 4)
        }

    def list_available_variants(self) -> Dict:
        """List all available divisional chart variants."""
        return {
            'D2': {
                'name': 'Hora',
                'variants': {
                    'parashara': 'BPHS standard (odd→Leo/Cancer, even→Cancer/Leo)',
                    'pariveshta': 'Circular traversal (each Hora → next sign)',
                    'parivritta': 'Reversal method (even signs reverse degree order)',
                    'parivritta_trayodamsa': '13-part circular division',
                    'surya_chandra': 'Sun/Moon rulership emphasis',
                    'ahoratra': 'Day-night method (interpretive variant)',
                }
            },
            'D3': {
                'name': 'Drekkana',
                'variants': {
                    'parashara': 'BPHS standard (0-10→same, 10-20→+4, 20-30→+8)',
                    'parivritta_trayodamsa': '13-sign circular traversal',
                    'somaja': 'Moon-born (Cancer/Scorpio/Pisces)',
                    'khara': 'Harsh method (even signs start from +5)',
                }
            },
            'composite': {
                'description': 'Apply outer div then inner div to result',
                'examples': ['D9×D12=D108', 'D12×D12=D144', 'D9×D9=D81'],
                'method': 'calc_composite_varga(degree, outer_div, inner_div)',
            },
            'custom': {
                'description': 'Any D-N where N is 2-300',
                'examples': ['D150', 'D300', 'D81'],
                'method': 'calc_custom_varga(degree, n)',
            }
        }


# 示例用法
if __name__ == "__main__":
    calculator = DivisionalChartsCalculator()

    # 示例数据：行星位置（黄道度数）
    planet_positions = {
        "Sun": 15.5,        # Aries 15.5°
        "Moon": 125.3,      # Leo 5.3°
        "Mars": 285.7,      # Capricorn 15.7°
        "Mercury": 25.2,    # Aries 25.2°
        "Jupiter": 95.8,    # Cancer 5.8°
        "Venus": 335.4,     # Pisces 5.4°
        "Saturn": 245.6,    # Sagittarius 5.6°
        "Rahu": 185.9,      # Libra 5.9°
        "Ketu": 5.9         # Aries 5.9°
    }

    asc_degree = 10.0  # Aries 10°

    # 1. 标准分盘计算
    print("=" * 60)
    print("1. 标准分盘计算")
    print("=" * 60)
    all_vargas = calculator.calculate_all_vargas(planet_positions, asc_degree)
    for varga_name in ["Rashi", "Navamsa"]:
        varga_data = all_vargas[varga_name]
        print(f"\n{varga_name} (D{varga_data['division']}) - {varga_data['meaning']}")
        print(f"上升: {varga_data['ascendant']['sign']} {varga_data['ascendant']['degree']:.2f}°")

    # 2. D2 Hora 变体
    print("\n" + "=" * 60)
    print("2. D2 Hora 6种变体")
    print("=" * 60)
    test_lon = 15.5  # Aries 15.5°
    for v in ['parashara', 'pariveshta', 'parivritta', 'parivritta_trayodamsa',
              'surya_chandra', 'ahoratra']:
        result = calculator._calculate_d2_variant(0, 15.5, v)
        sign = calculator.SIGNS[int(result // 30)]
        deg = result % 30
        print(f"  {v:25} → {sign:12} {deg:.2f}°")

    # 3. D3 Drekkana 变体
    print("\n" + "=" * 60)
    print("3. D3 Drekkana 4种变体")
    print("=" * 60)
    for v in ['parashara', 'parivritta_trayodamsa', 'somaja', 'khara']:
        result = calculator._calculate_d3_variant(0, 15.5, v)
        sign = calculator.SIGNS[int(result // 30)]
        deg = result % 30
        print(f"  {v:25} → {sign:12} {deg:.2f}°")

    # 4. 复合分盘
    print("\n" + "=" * 60)
    print("4. 复合分盘 (D-m×n)")
    print("=" * 60)
    for outer, inner in [(9, 12), (12, 12), (9, 9), (10, 12)]:
        result = calculator.calc_composite_varga(test_lon, outer, inner)
        print(f"  D{outer}×D{inner}=D{outer*inner}: "
              f"{result['sign']} {result['degree']:.2f}°")

    # 5. 自定义 D-N
    print("\n" + "=" * 60)
    print("5. 自定义 D-N (2-300)")
    print("=" * 60)
    for n in [2, 9, 60, 150, 300]:
        result = calculator.calc_custom_varga(test_lon, n)
        print(f"  D{n:3d}: {result['sign']:12} {result['degree']:.2f}°  "
              f"(amsa={result['amsa_size']:.4f}°)")

    # 6. 可用变体列表
    print("\n" + "=" * 60)
    print("6. 可用变体列表")
    print("=" * 60)
    variants = calculator.list_available_variants()
    for div_key, info in variants.items():
        print(f"\n  {div_key}: {info.get('name', info.get('description', ''))}")
        if 'variants' in info:
            for vk, vdesc in info['variants'].items():
                print(f"    - {vk}: {vdesc}")
