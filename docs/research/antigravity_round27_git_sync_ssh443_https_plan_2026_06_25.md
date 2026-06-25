# Antigravity AI Git 远端同步 SSH-443/HTTPS 实操计划 (Round 27)

由于 SSH(22) 的网络脆弱性，我们必须有可靠的 Push Fallback。**本计划仅记录，不执行。**

| 步骤 | 具体操作与命令行 |
|---|---|
| 1. 验证目标 | `git ls-remote https://github.com/732642856/yinduzhanxing.git` (已成功，HTTPS畅通)。 |
| 2. 方案 A: HTTPS PAT | 需要用户生成一个具有 repo 权限的 Github PAT (Personal Access Token)。 |
| 3. URL 格式 | `https://<token>@github.com/732642856/yinduzhanxing.git`。 |
| 4. 配置 Remote | `git remote set-url origin https://github.com/732642856/yinduzhanxing.git`。 |
| 5. 凭证缓存 | `git config credential.helper cache`。 |
| 6. 方案 B: SSH 443 端口 | 编辑 `~/.ssh/config`，加入 `Host github.com` -> `Hostname ssh.github.com` -> `Port 443`。 |
| 7. 方案 C: git update-ref | 如果大推拉失败，可用于强制对齐本地引用 (不推荐日常用)。 |
| 8. 代码卫生 | PAT **绝对不可**写入 `task_plan.md`，**绝对不可**被 AI 捕获记录。 |
| 9. 执行者 | 只能由物理人类在他们的真实 Terminal 中直接输入凭证。 |
| 10. `Ahead 1` 处理 | 当前 `codex/release-hygiene-ci` 领先远端，可直接 push。 |
| 11. Codex 任务 1 | 🟢 Codex可做 | 在报告中留下指引，让用户自己去敲带有密码的 `push` 命令。 |
| 12. Codex 任务 2 | 🟢 Codex可做 | 坚决不向我们要 PAT。 |
| 13. Codex 任务 3 | 🟢 Codex可做 | 在遇到超时时，友善提示用户切换网络或转 HTTPS。 |
| 14. 副手下轮 1 | 🟢 副手可做 | 给出一个 3 步走的全套本地 commit 脚本，防止 push 失败导致改动丢失。 |
| 15. 副手下轮 2 | 🟢 副手可做 | 教导大模型不要傻乎乎一直 retry 导致资源耗尽。 |
| 16. 副手下轮 3 | 🟢 副手可做 | 如果真的脱机了，设计一个生成 `.patch` 包并通过邮件发送的工作流概念。 |
| 17. 需要人工 | 🟢 需人工 | 要人类填密码/Token。 |
| 18. 分支确认 | 推送目标：`codex/release-hygiene-ci`。 |
| 19. Git Diff | 推送前必须 `git diff --check`。 |
| 20. 代理设置 | 可结合 `export http_proxy` 加速。 |
| 21. Git Trace | 疑难杂症可用 `GIT_CURL_VERBOSE=1` 排查。 |
| 22. CI 隔离 | 远端的 Github Actions 不受此困扰。 |
| 23. 失败代价 | 报告不会丢，因为已经本地落盘了。 |
| 24. Push 命令 | `git push origin codex/release-hygiene-ci`。 |
| 25. 总结 | 这是我们突破物理网络封锁的终极后备方案。 |
