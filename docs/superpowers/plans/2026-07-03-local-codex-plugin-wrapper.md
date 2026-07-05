# Local Codex Plugin Wrapper Implementation Plan
> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
**Goal:** Add a minimal local Codex plugin wrapper around the existing Jyotish repo so Codex can install it as a plugin using the repo's current skills and MCP server.
**Architecture:** Keep the repo as source of truth. Add only a `.codex-plugin/plugin.json` manifest that points at existing `skills/` and the existing root `mcp_server.py`. Lock it with one static test and document local install/test steps.
**Tech Stack:** JSON manifest, existing Python MCP server, pytest static checks, Codex local plugin install flow.
## Global Constraints
- Reuse existing `SKILL.md`, `skills/`, and `mcp_server.py`; no duplicate runtime chain.
- Keep plugin scope local-only; no marketplace publishing work.
- Smallest diff wins: one manifest, one test, one short install doc update.

### Task 1: Add plugin manifest coverage
**Files:**
- Modify: `tests/test_runtime_import_boundaries.py` or create focused plugin manifest test if cleaner
- Test: `tests/test_codex_plugin_wrapper.py`
**Interfaces:**
- Consumes: `.codex-plugin/plugin.json`
- Produces: static validation that plugin manifest exists and points at current repo assets
- [ ] **Step 1: Write failing static test**
- [ ] **Step 2: Run test to confirm failure**
- [ ] **Step 3: Add minimal manifest or adjust expectations**
- [ ] **Step 4: Re-run targeted test**

### Task 2: Add minimal local plugin manifest
**Files:**
- Create: `.codex-plugin/plugin.json`
**Interfaces:**
- Consumes: existing `skills/`, root `mcp_server.py`
- Produces: installable local plugin metadata
- [ ] **Step 1: Use plugin spec sample to choose minimal accepted fields**
- [ ] **Step 2: Point `skills` at existing `./skills/`**
- [ ] **Step 3: Inline `mcpServers` config for `mcp_server.py`**
- [ ] **Step 4: Validate manifest with plugin validator**

### Task 3: Document local install/test flow
**Files:**
- Modify: `README.md`
**Interfaces:**
- Consumes: local plugin install command shape
- Produces: copy-paste local install, reinstall, and test commands
- [ ] **Step 1: Add minimal plugin install section**
- [ ] **Step 2: Include reinstall/new-thread note**
- [ ] **Step 3: Run targeted doc/static checks**
