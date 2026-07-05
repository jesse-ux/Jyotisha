# Vibe Coding Setup

Use Cline as the main AI coding surface for this repo. Use Aider for small low-cost code edits. Use Dyad only for fast front-end prototypes such as 星轨talk pages.

## Cline MCP

Generate config:

```bash
python3 scripts/print_cline_mcp_config.py
```

Install project-local config:

```bash
python3 scripts/print_cline_mcp_config.py --install-project
```

This writes `.cline/mcp.json` with the current checkout path. `.cline/` is local-only and ignored by git.

## Recommended Split

- Cline: main repo work, MCP tools, strict workflow checks.
- Aider: precise low-cost edits with git diffs.
- Dyad: quick UI prototypes, not the main Jyotish runtime.

