# 日级应期 holdout 人工标签指南

目标：给研究仓提供真实、独立、可复验的正/负样本。你不需要会编程，只需要提供来源清楚的事实材料。

## 需要收集什么

每条标签只回答一个问题：

某人在某个日期区间，某类事件是否发生？

可用标签：

- `target_event`：事件发生了。
- `no_target_event`：有公开资料支持该区间没有发生这个目标事件。

## 优先领域

1. 事业：任命、创办公司、上市、获奖、重大作品发布。
2. 婚恋：结婚、离婚、订婚、公开伴侣关系变化。
3. 财富：上市、重大融资、破产、重大资产事件。

暂不优先健康/死亡，噪音和伦理风险高。

## 合格来源

优先：

- 官方 biography / timeline
- Britannica / Nobel / company official timeline
- 出版传记中可核对页码或章节的时间线
- IMDb / MusicBrainz / company history 等结构化公开资料

不合格：

- “没搜到新闻所以没发生”
- ChatGPT 生成内容
- 无来源论坛故事
- 已被本项目观察过的旧控制日期
- 模糊说法：“那一年很平静”

## 最小可用规模

pilot 阶段：

- 3 个公开人物
- 每人 1 个领域
- 每人 1 个正样本窗口
- 每人 2 个负样本窗口

正式升级门槛：

- 至少 20 个独立案例
- 至少 80 个独立负样本区间
- 标签冻结后才允许评分

## 填写方式

生成空模板：

```bash
python3 scripts/day_level_holdout_template.py --output /tmp/holdout_annotation_template.json
```

把公开来源、日期区间、事件说明填进去，再交给 intake：

```bash
python3 scripts/day_level_negative_holdout_intake.py references/real_case_calibration/day_level_holdout_v3_preregistration.json --row-json '{"case_id":"..."}'
```

## 结论边界

没有真实独立负样本前：

- 可以输出候选日期排序；
- 可以说明触发信号；
- 不能说“精确日期预测已验证”。
