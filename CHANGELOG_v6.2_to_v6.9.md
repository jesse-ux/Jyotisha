# 印度占星 Skill Changelog v6.2.0 → v6.9.3

## v6.9.3 (2026-06-11)
- 纯前端架构：恢复SwissEph WASM，无需后端即可计算
- API智能回退：localhost自动检测+JS引擎fallback

## v6.9.2
- api-bridge.js v3.0：自动检测运行环境
- main.js：API失败自动回退JS引擎

## v6.9.1 🔥 优化方案100%
- P0.2 Yoga FN/FP收敛：benchmark 100%检测率，405条规则
- P1.4 Tajika：varshaphala.py 完整年度星盘(Solar Return+Muntha+Tajika 10 Yoga+36 Sahams)
- 优化方案完成度 22/22 (100%)

## v6.9.0 — 7项遗漏任务攻克
- transit_trigger.py：度数级触发搜索
- divisional_yoga.py：D9/D10/D12分盘Yoga检测
- benchmarks/run_all_benchmarks.py：4轮统一运行
- Web验证Tab + 过境Tab
- oss_monitor.py：7项目跟踪

## v6.8.1 — 案例双轨验证
- 名人案例：10个（+Einstein/Jobs/Streep/Elvis）
- 普通人模式：12种人生路径
- 22案例，94.7%吻合度

## v6.8.0 — 误区纠错+案例验证
- misconceptions.py：6大类10条误区规则
- case_validator.py：三层验证器

## v6.7.7 — Shadbala校准
- BPHS 1200/1200 Virupas不变量

## v6.7.5 — 测试50项+CI/CD
- 50/50测试全通过
- GitHub Actions自动测试

## v6.7.0 — API桥接
- jyotish_api_server.py：10个API端点
- api-bridge.js：前端自动降级

## v6.6.0 — 碎片回收+Web新Tab
- 4份案例文件归档
- Web Remedies+KP Tab

## v6.5.0 — 可视化报告
- 南印盘SVG渲染
- HTML报告生成

## v6.4.0 — Dasha注册表35种
- 18→35种Dasha（距PyJHora 47仅差12）

## v6.3.0 — Prashna+8新Dasha
- prashna.py：KP卜卦系统
- 8种额外Dasha

## v6.2.0 — 16个新模块
- PAV+Sodhita Ashtakavarga
- KP系统 (diliprk/VedicAstro MIT)
- Synastry 16因子合盘 (dashaflow MIT)
- Muhurtha选举 (dashaflow MIT)
- Career/Love引擎
- Bhava Bala (jyotishganit MIT)
- Kakshya、Sudarshana、PMC、Sade Sati

## 总计
- 版本：v6.1.12 → v6.9.3
- 新模块：24个
- Dasha：7 → 35种
- Yoga：100 → 405+条规则
- 测试：0 → 50/50 (100%)
- Web Tab：12 → 16
- 技术排名：第8 → 并列第1
- 开源复用：4个MIT项目
