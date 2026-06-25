# Antigravity AI 准确率闭环剩余断点 (Round 14)

目前系统准确率引擎的状态如下：

| 环节 | 当前状态 | 缺口 | 建议文件 | 验收标准 |
|---|---|---|---|---|
| **Evidence Packet 下载** | 🟢 已闭环 | 无 | `jyotish-app/main.js` | 面板卡片支持正确下载含 Metadata 空位的 Draft JSON。 |
| **Evidence Packet 上传** | 🔴 **断层** | 前后端均无对应入口与路由，填写者报国无门。 | `jyotish-app/main.js`, `scripts/jyotish_api_server.py` | UI 上出现可拖拽上传区域或验证接口能处理 POST 的 JSON 文件。 |
| **Validator 判卷** | 🟡 半闭环 | CLI 支持完善，但 Web 面板无法展示其返回的 `problems` 数组供用户修正。 | 对应前端接口绑定 | 网页直接渲染红色的缺少字段或绿色的过审提示。 |
| **外部截图/工件存档** | 🔴 缺失 | 用户验证通过后，其用于举证的截屏图片与打上 `external_verified` 的 JSON，缺乏标准的落地保存目录与管理逻辑。 | 需新增如 `references/oracle/artifacts/` 目录规范 | 有统一规范，且图片不会四处散落导致隐私泄露。 |
| **JSON Case 晋级** | 🔴 断链 | 即使验证通过，主仓库里的 `dasha_shadbala_oracle_cases.json` 也不会自动把 `draft` 翻转为 `external_verified`，仍需人工 PR。 | `scripts/oracle_collection_queue.py` | 验证通过后能提供一键覆写该 Case 的选项。 |
| **生产调参开关** | 🟢 已闭环 | `production_tuning_allowed` 已死死咬住阀值。 | 无 | 必须满足足够包后才解锁。 |
| **用户端准确率披露** | 🟢 已闭环 | Trust Center 及所有面板均诚实声明了 0 校准进度的残酷现实。 | 无 | 保持高透明度。 |

**闭环建议**：重中之重是打通“上传”与“落地归档”这两关，让手工跑通的数据能在主库里安家落户。
