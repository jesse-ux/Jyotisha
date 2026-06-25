# Antigravity AI Git 远端同步替代路径方案 (Round 26)

当 SSH (Port 22) 因为大防火墙或网络拥堵频繁超时，导致 `push` 失败堆积时，我们设计如下 Fallback：

| 方案 | 具体指令/概念 |
|---|---|
| 1. 现状 | `codex/release-hygiene-ci` 比 `origin` ahead 1。但我们积压了一堆 Untracked。 |
| 2. 方案 A: 切换为 HTTPS | `git remote set-url origin https://github.com/732642856/yinduzhanxing.git`。 |
| 3. HTTPS 凭证 | HTTPS Push 需要用到 Personal Access Token (PAT)。不能写在代码里。 |
| 4. 方案 B: SSH in 443 | `ssh -T -p 443 git@ssh.github.com`。 |
| 5. 方案 C: git config 替换 | `git config --global url."https://github.com/".insteadOf git@github.com:`。 |
| 6. 代码安全 | 任何情况下绝对不要把 Github PAT 存入任何 Markdown。 |
| 7. 方案 D: Proxy | `git config --global http.proxy http://127.0.0.1:xxx` 如果本机有代理。 |
| 8. 方案 E: 仅本地化 | 如果就是推不上去，就在本地进行频繁 `commit`，依靠本地版本历史防丢。 |
| 9. Push 分支 | 我们当前在推 `codex/release-hygiene-ci`，这不是主干，稍微安全点。 |
| 10. `git ls-remote` | 本轮已验证 `https` 的 ls-remote 可以非常顺畅地拉到几十个 tag。这说明 HTTPS 网络完全通畅。 |
| 11. Codex 任务 1 | 🟢 Codex可做 | 使用 HTTPS remote 尝试 `git push origin codex/release-hygiene-ci`。 |
| 12. Codex 任务 2 | 🟢 Codex可做 | 如果没有配置凭证导致失败，就只做本地 `commit` 保护，并在 README 留一行给人类用户的待 push 提醒。 |
| 13. Codex 任务 3 | 🟢 Codex可做 | 确认把目前的 Round 25 和 26 全部暂存。 |
| 14. 副手下轮 1 | 🟢 副手继续做 | 监控每次终端 push 指令执行的 stdout 耗时。 |
| 15. 副手下轮 2 | 🟢 副手继续做 | 如果 push 还是超时，写一个备用的打包脚本，把新增的修改打成 patch 文件。 |
| 16. 需要人工 | 🟢 需人工 | 要在终端里输入一下 Github Token 才能用 HTTPS 推上去。 |
| 17. 不要乱改 | 🔴 未成立 | 本任务明确说不改代码，不乱 push。 |
| 18. 本地分支 | 目前就是 `codex/` 分支。 |
| 19. 网络环境 | 明确：SSH 22 极其不稳定，HTTPS 是神。 |
| 20. 最终建议 | 依靠本地 `commit` + HTTPS。 |
