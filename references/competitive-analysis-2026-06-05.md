# 竞争对手分析与优化路线图
# Competitive Analysis & Optimization Roadmap

日期：2026-06-05
当前版本：v6.0.23-registry-cleaned

---

## 一、PyJHora 核心优势（计算准确性标杆）

### 已验证的优势
1. **50+ Dasha 类型覆盖**
   - 22 种行星 Dasha（Vimshottari/Ashtottari/Yogini 等）
   - 22 种星座 Dasha（Chara/Narayana/Sudasa 等）
   - 3 种年度 Dasha（Patyayini/Varsha Vimshottari 等）
   - **对比**：当前 skill 约 10-12 种 Dasha，覆盖广度明显不足

2. **多基线测试机制（可借鉴）**
   - `record/compare/none` 三种测试模式
   - LAHIRI 和 TRUE_PUSHYA 双 Ayanamsa 基线
   - 6800+ 测试用例
   - **可借鉴**：建立 `benchmark/baselines/` 目录，固化 JSON 基线

3. **Shadbala 外部校准（我们正在做）**
   - 已对齐 BV Raman 和 VP Jain 书例
   - `get_planet_mean_longitude()` 用于 Chesta Bala
   - `planet_aspect_relationship_table()` 用于 Drik Bala
   - **对比**：我们的 Shadbala 仍是 partial，需要外部校准

4. **配置统一管理**
   - `const.py` + `config.py` 统一管理所有常量
   - **可借鉴**：当前 skill 的 Ayanamsa/node mode/house system 散落在代码里

---

## 二、VedAstro 核心优势（工程化标杆）

### 已验证的优势
1. **MCP Server 支持**
   - 端点：`https://mcp.vedastro.org/api/mcp`
   - 兼容 Claude/Cursor/VS Code
   - **机会**：我们的 skill 是 AI Native 的，但还没有标准 MCP 接口

2. **Docker 一键部署**
   - 镜像：`vedastro/api`
   - **机会**：我们的 skill 目前需要手动安装依赖

3. **200+ API 端点**
   - REST API + Python 包 + .NET 库
   - **对比**：我们只有 CLI，没有 API 层

4. **架构分层清晰**
   - 核心计算库 / API 服务 / 前端 / 测试项目 完全解耦
   - **对比**：我们目前是 monolithic scripts

5. **文档体系完整**
   - API 文档、MCP 接入指南、贡献指南、ADR（架构决策记录）
   - **对比**：我们缺英文 README 和 API 文档

---

## 三、我们的差异化优势（要保持）

1. **Strict Workflow Router**（事业/婚恋/财务分路由）→ VedAstro 没有
2. **Technique Audit Table**（每步声明置信度）→ PyJHora 没有
3. **MEVG 外部验证门控** → 两个对手都没有
4. **能力降级机制**（partial 不硬吹）→ 两个对手都没有
5. **Full-reading 全链路解盘** → 两个对手都没有（只有零散计算）

---

## 四、优化路线图（基于竞争对手分析）

### Phase 0A：计算准确性追赶 PyJHora（P0）

#### 0A.1 建立 Benchmark 基线系统
**借鉴 PyJHora 的多基线测试机制**

目标目录结构：
```
benchmark/
  baselines/
    lahiri/
      shadbala/
        bv_raman_example_1.json
        ...
      dasha/
        vimshottari_sample_1.json
        ...
    true_pushya/
      ...
  scripts/
    run_benchmark.py
    compare_baselines.py
  results/
    2026-06-05_run_1.json
```

#### 0A.2 Shadbala 外部校准（继续）
- 对齐 BV Raman 书例（PyJHora 已验证的用例）
- 对齐 PyJHora 输出
- 目标：从 partial → covered

#### 0A.3 Chara Dasha 重写
- 对标 PyJHora 的 Chara Dasha 实现
- 建立 30 个测试案例
- 目标匹配率 ≥ 95%

#### 0A.4 扩展 Dasha 覆盖
- 当前：~12 种
- 目标：~25 种（覆盖 PyJHora 的 50% 核心 Dasha）
- 优先：Yogini、Shodasottari、Dwadasottari

---

### Phase 0B：工程成熟度追赶 VedAstro（P1）

#### 0B.1 MCP Server 接口
**这是最高杠杆点** —— 我们的 skill 是 AI Native 的，加上 MCP 后可以被 Claude/Cursor 直接调用

目标：
```python
# mcp_server.py
@tool
def calculate_chart(year, month, day, hour, minute, lat, lon, tz):
    ...

@tool
def run_dasha(birth_data, dasha_type="vimshottari"):
    ...

@tool
def full_reading(birth_data, transit_date):
    ...
```

#### 0B.2 Docker 一键部署
```dockerfile
FROM python:3.11-slim
RUN pip install pyswisseph
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "mcp_server.py"]
```

#### 0B.3 英文 README + API 文档
- 安装命令
- 5 分钟快速上手
- Full-reading 示例输出
- Benchmark 结果

#### 0B.4 配置统一管理
- 提取硬编码的 Ayanamsa/node mode/house system
- 创建 `config.py` 或 `constants.py`

---

### Phase 0C：差异化优势巩固（P1）

#### 0C.1 Strict Workflow Router 文档化
- 把当前的 strict workflow 规则整理成 MD 文档
- 让用户知道"为什么事业问题要走 career_timing_strict 而不是 full_reading_strict"

#### 0C.2 Technique Audit Table 可视化
- 当前是文本输出
- 目标：生成 HTML 审计报告，彩色标注 covered/partial/missing

#### 0C.3 MEVG 门控扩展
- 当前：部分解释层有 MEVG 标注
- 目标：所有 high-stakes prediction 都必须有 MEVG 来源标注

---

## 五、立即可执行的最小下一步（明天就能开始）

### 选项 A：建立 Benchmark 基线系统（计算准确性）
**耗时**：2-3 天
**价值**：为后续所有算法优化提供量化依据
**输出**：
1. `benchmark/baselines/` 目录结构
2. 3-5 个 Shadbala 基线 JSON（对齐 BV Raman）
3. `benchmark/scripts/run_benchmark.py` 雏形

### 选项 B：MCP Server 接口（工程成熟度）
**耗时**：3-5 天
**价值**：让 skill 可以被 Claude/Cursor 直接调用，大幅提升可用性
**输出**：
1. `mcp_server.py`（基础工具：calculate_chart、run_dasha、full_reading）
2. `README.md` 更新 MCP 使用说明
3. 测试：用 Claude Desktop 调用 MCP 工具

### 选项 C：英文 README + 快速上手文档（开源影响力）
**耗时**：1-2 天
**价值**：降低使用门槛，吸引社区贡献
**输出**：
1. `README_EN.md`（英文版 README）
2. `docs/quickstart.md`（5 分钟快速上手）
3. `docs/api_reference.md`（API 参考）

---

## 六、推荐执行顺序

**我的建议**：先选项 C（英文文档），再选项 B（MCP Server），最后选项 A（Benchmark 基线）

理由：
1. 英文文档最快出成果，且是后续所有工作的基础
2. MCP Server 是差异化优势（PyJHora/VedAstro 有 API，但我们是 AI Native + MCP，更贴合 AI 工作流）
3. Benchmark 基线是最花时间的，需要静下心来对着书例一个个对齐

---

## 七、具体任务拆解（基于选项 B：MCP Server）

### Task 1：学习 MCP 协议
- 阅读 Anthropic MCP 文档
- 研究 VedAstro 的 MCP Server 实现（`https://mcp.vedastro.org/api/mcp`）
- 确定：用 `mcp` Python SDK 还是自己实现

### Task 2：设计工具接口
```python
tools = [
    {
        "name": "calculate_chart",
        "description": "Calculate Vedic birth chart",
        "parameters": {
            "year": "Birth year",
            "month": "Birth month",
            ...
        }
    },
    {
        "name": "run_dasha",
        "description": "Calculate Dasha periods",
        ...
    },
    {
        "name": "full_reading",
        "description": "Generate full Jyotish reading",
        ...
    }
]
```

### Task 3：实现 MCP Server
- 用 `mcp` Python SDK
- 包装现有 `jyotish_engine.py` 的功能
- 支持 stdio 传输（Claude Desktop）和 HTTP 传输（远程调用）

### Task 4：测试与文档
- 用 Claude Desktop 测试 MCP 工具调用
- 写 `docs/mcp_usage.md`
- 更新 `README.md` 添加 MCP 使用说明

---

## 八、资源预估

| 任务 | 耗时 | 难度 | 价值 |
|------|------|------|------|
| 英文 README | 1-2 天 | 低 | 高（降低使用门槛） |
| MCP Server | 3-5 天 | 中 | 很高（AI Native 差异化） |
| Benchmark 基线 | 5-7 天 | 高 | 高（计算准确性基础） |
| Docker 部署 | 2-3 天 | 低 | 中（工程成熟度） |
| 配置统一管理 | 1-2 天 | 低 | 中（代码质量） |

---

## 九、结论

**PyJHora 的优势**（我们要追赶）：
- Dasha 覆盖广度（50+ 种）
- 多基线测试机制
- Shadbala 外部校准

**VedAstro 的优势**（我们要借鉴）：
- MCP Server（我们要做得更好，因为我们是 AI Native）
- Docker 部署
- 完整文档体系

**我们的优势**（要保持并扩大）：
- Strict Workflow Router
- Technique Audit Table
- MEVG 外部验证门控
- 能力降级机制
- Full-reading 全链路解盘

**下一步推荐**：
1. 先写英文 README（最快出成果）
2. 再做 MCP Server（差异化优势，且 PyJHora/VedAstro 的 MCP 是通用 API，我们的是 AI Native 解盘工作流）
3. 最后做 Benchmark 基线（最需要静心，但价值极高）

---

**附件**：已创建 `references/competitive-analysis-2026-06-05.md`（本文档）
