# Antigravity AI 成品可用性路径复查 (Round 3)

## 普通用户可用结论

**`usable_with_local_api`**
结合本地部署的 API 后台，目前的形态已经能够为普通占星师或爱好者提供可信赖的端到端基础排盘与高优证据解读服务。静态 PWA/Demo 可作为流量入口和界面展示使用。

## 路径复查明细

- **README 启动路径**：说明清楚，分为 Local Dev、Docker Compose、Static demo 三档，指导明确。
- **Trust Center 与边界声明**：Trust Center 中不仅展示了本地 API 健康状态，且 `README.md` 也通过 `static_demo_boundary_visible` 等文案明确了静态体验模式和隐私本地闭环的界限。
- **无 API 的行动提示**：前端在没有 API 响应时会触发内置回退计算逻辑并在界面与 Console 输出明确的降级提示。
- **核心全链路可用性**：有本地 API 时，无论是参数传递、保存/导出功能，还是带有 Multi-Ayanamsa 的完整解盘及 AI Prompt Pack 加载，都能成功渲染，数据结构也无丢失，满足了排盘核心闭环。
- **头像展示优化**：产品化核心 UI 素材 `/brand-avatar.png` 体积仅 417KB，且 CSS 已规范至 `28px`，不再拖慢首屏加载。

## 距离成品项目的缺口清单 (P0/P1/P2)

| 缺口分类 | 严重度 | 缺口内容及描述 |
|---|---|---|
| **核心算法池** | **P1** | **Shadbala/Dasha 真值 Oracle 尚未完备**。当前处于依赖内部算法防御置信度的阶段，需继续补充外部 `external_verified` 的真值靶心用于长线回归，否则不宜进入重度商业化。 |
| **前端交互** | **P2** | 缺少更多维的图表可视化（例如：南印度图样式、D-chart 的具体绘制）。对于重度 C 端，仅依靠数据面板和 AI Prompt Pack 略显单薄。 |
| **生态打通** | **P2** | 部署方式对纯小白用户（非开发者）仍有较高门槛，如未发布开箱即用的一键执行安装包 (Executable Binary / Electron wrapper)。 |

## 准确率边界评估

- **基础黄经/D1/D9**：**当前可信度高**。与 Swiss Ephemeris 核心对齐，且成功支持 Lahiri、Raman、KP 等主流岁的完全闭环。
- **Shadbala**：**相对力量可信，绝对力量受限**。六重绝对值 (absolute Rupa) 已打通，但仍需外部 Oracle 进行最后校准对齐。
- **Dasha**：**时间框架可信，起点仍需靶心**。基础逻辑可靠，但类似 JHora 中的精微细长校准等还需依靠样本驱动。
- **AI 解读**：**无幻觉可信度高**。得益于 `ai_prompt_pack`，AI 直接基于后端发出的不可变证据 (`evidence_snapshot`) 行事，杜绝了自编排盘逻辑的失控风险。
