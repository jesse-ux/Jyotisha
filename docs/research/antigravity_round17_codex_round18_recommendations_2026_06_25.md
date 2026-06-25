# Antigravity AI 给 Codex 的 Round 18 任务建议 (Round 17)

通过上述压力与合规复核，我已为你拆分好 6 个最高 ROI（且亟待回填的 P1/P2 坑）的可执行任务：

## 1. 建立 Artifacts 物理存档规范
- **文件路径**：`references/oracle/artifacts/README.md`，`jyotish-app/main.js`
- **测试命令**：`rg "必须打码" references/oracle/artifacts/README.md`
- **验收标准**：该目录必须存在，文档必须写明相对路径引用方式、禁止提交未脱敏私人截图、PDF。前端下载弹窗必须明确显示这段话。
- **是否需要人工截图**：否。

## 2. 补齐 Shadbala 六分量的强拦截锁
- **文件路径**：`scripts/oracle_evidence_validator.py`
- **测试命令**：`pytest tests/test_oracle_evidence_validator.py`
- **验收标准**：在 validator 源码内写死检查 `sthana`, `dig`, `kala`, `chesta`, `naisargika`, `drik`。保证空 `{}` 被抛出红色拦截。
- **是否需要人工截图**：否。

## 3. 在 Trust Center 增加进度仪表盘
- **文件路径**：`jyotish-app/main.js`
- **测试命令**：`npm run build --prefix jyotish-app`
- **验收标准**：将 `valid_packets` 和 `total_packets` 这些数据以进度条或数字仪表盘的方式展示在页面上，激励用户填坑。
- **是否需要人工截图**：否。

## 4. 撰写首份公开 JHora 截图教程
- **文件路径**：`docs/user_jhora_capture_guide.md`
- **测试命令**：无。
- **验收标准**：提供一份手把手的截图教程，明确指出应填写 `moon_sidereal_longitude_deg` 等字段。
- **是否需要人工截图**：否。

## 5. 新增 Ashtakoot/KP/Muhurta 草稿任务
- **文件路径**：`references/oracle/dasha_shadbala_oracle_cases.json`
- **测试命令**：`python3 scripts/oracle_collection_queue.py --format json`
- **验收标准**：在 JSON 里新增上述高级技法占位卡，总目标任务数扩充至 10 个以上。
- **是否需要人工截图**：否。

## 6. 为第一条外部样本准备 promotion checklist
- **文件路径**：`docs/research/antigravity_round18_external_verified_checklist.md`
- **测试命令**：无。
- **验收标准**：写好人工晋级清单——告诉下一步接手的人该如何启动 JHora，如何去替换那个 `draft` 为 `external_verified`。
- **是否需要人工截图**：否（只写 checklist）。
