# Antigravity AI MIT 可复制资产再筛选 (Round 30)

## 常数库“合法抢劫”清单

1. **`references/open_source_sources/jyotishganit/jyotishganit/core/constants.py`**
   - 提取: `ATHIMITRA: 22.5` 等 Shadbala 细分自然强弱分值。
   - 提取: D1-D60 的高阶分盘计算常量数组。
2. **`dashaflow/muhurtha.py`** 
   - 提取: 判断哪几天禁止结婚或出行的字典逻辑，它已经是高度提纯的 Python Dict。
3. **`VedAstro/Ashtakoot` (需要去原库找，当前可能不在本机)**
   - 提取: `Varna Kuta`, `Nadi Kuta` 的敌对打分多维数组。
4. **`jaimini-tropical` (MIT 协议)**
   - 提取: `core/dashas.py` 里的顺行/逆行算表，用于 Jaimini Chara Dasha 计算。

*我们在拷贝时，只需提取常数 `CONST_X = [...]`，切勿拷贝它的类封装和路由定义，因为我们有自己的 Pydantic 风格。*

## 状态
`已成立`
