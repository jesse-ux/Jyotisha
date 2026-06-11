# RishiAI MCP Server

[![PyPI version](https://img.shields.io/pypi/v/rishi-ai-mcp.svg?cache=1)](https://pypi.org/project/rishi-ai-mcp/)
[![CI](https://github.com/adarshj322/rishi-ai-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/adarshj322/rishi-ai-mcp/actions/workflows/ci.yml)
[![Python versions](https://img.shields.io/pypi/pyversions/rishi-ai-mcp.svg?cache=1)](https://pypi.org/project/rishi-ai-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A [Model Context Protocol](https://modelcontextprotocol.io/) server that exposes **Vedic astrology tools** powered by the [DashaFlow](https://github.com/adarshj322/dashaflow) calculation engine.

Works with **any MCP-compatible client** — VS Code Copilot, Cursor, Claude Desktop, Claude Code, Gemini CLI, Codex, Antigravity, OpenCode, OpenClaw, Pi agent, or any custom app that speaks MCP.

https://github.com/user-attachments/assets/9c183b94-bb54-4af6-867c-fa3daeef2d03

## Install

```bash
pip install rishi-ai-mcp
```

## Quick Start

```bash
rishi-ai-mcp                    # console entry point (after pip install)
python rishi_ai_mcp.py          # or run directly from source
```

Communicates over **stdio**. Any MCP client that can spawn a subprocess and speak MCP can use it — no IDE required.

---

## Setup

Clone this repo into your workspace to get the MCP config + RishiAI agent rules for your IDE:

```bash
git clone https://github.com/adarshj322/rishi-ai-mcp.git
```

The repo includes ready-to-use configs for three IDEs:

### VS Code / GitHub Copilot

- `.vscode/mcp.json` — auto-configures the MCP server
- `.github/copilot-instructions.md` — RishiAI persona (always-on)
- `.agents/skills/*/SKILL.md` — 14 workflow skills (auto-triggered by topic, or invoke via `/skill-name`)

VS Code Copilot reads `.github/copilot-instructions.md` for always-on instructions and `.agents/skills/` for skills. Just open the cloned folder and the tools + persona + skills are active.

### Cursor

- `.cursor/mcp.json` — auto-configures the MCP server
- `.cursor/rules/rishi-ai.mdc` — RishiAI persona (always-on core rule)
- `.agents/skills/*/SKILL.md` — 14 workflow skills (shared, Cursor reads `.agents/skills/` natively)

Open the cloned folder in Cursor and the tools + persona + skills are active.

### Antigravity

- `.agents/rules/rishi-ai.md` — RishiAI persona (always-on)
- `.agents/skills/*/SKILL.md` — 14 workflow skills
- `.agents/workflows/*.md` — 14 slash-command workflows

Antigravity reads `.agents/` natively. Configure the MCP server in your Antigravity settings:

```
command: uvx
args: rishi-ai-mcp
```

### Other MCP Clients (Claude Desktop, Claude Code, Gemini CLI, etc.)

Any MCP-compatible client can connect using the same server. Add to your client's MCP config:

```json
{
  "mcpServers": {
    "vedic-astrology": {
      "command": "uvx",
      "args": ["rishi-ai-mcp"]
    }
  }
}
```

For the RishiAI persona, use `system_prompt.md` as a reference and adapt it to your client's instruction format.

### Standalone / Custom Client

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

params = StdioServerParameters(command="uvx", args=["rishi-ai-mcp"])

async with stdio_client(params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        result = await session.call_tool("cast_vedic_chart", {
            "dob": "1990-04-15", "time": "14:30",
            "lat": 28.6139, "lon": 77.2090, "timezone": "Asia/Kolkata"
        })
        print(result)
```

---

## MCP Tools

### `cast_vedic_chart`

Generates a complete Vedic natal chart.

| Parameter | Type | Description |
|-----------|------|-------------|
| `dob` | string | Date of birth — `"YYYY-MM-DD"` |
| `time` | string | Time of birth — `"HH:MM"` (24-hour) |
| `lat` | float | Birth latitude (e.g. `28.6139` for Delhi) |
| `lon` | float | Birth longitude (e.g. `77.2090` for Delhi) |
| `timezone` | string | IANA timezone (e.g. `"Asia/Kolkata"`) |
| `query_date` | string | Optional — date for Dasha lookup, defaults to today |

**Returns:** JSON with `metadata`, `panchang`, `lagna` (with D2–D60 signs), `planets` (with dignity, combustion, Shadbala, all 14 Varga signs, aspects), `dashas` (5 levels: Maha/Antar/Pratyantar/Sukshma/Prana + timeline), `yogas` (24 types), `ashtakavarga` (SAV + BAV + Prashtara), `jaimini_karakas`, `shadbala` (with Ishta/Kashta Phala), `bhava_chalit`, `avasthas`, `kaal_sarpa`, `graha_yuddha`, `gandanta`, `arudha_padas` (A1–A12), `upapada`, `karakamsha`.

### `cast_transit_chart`

Calculates planetary transits overlaid on a natal chart.

| Parameter | Type | Description |
|-----------|------|-------------|
| `transit_date` | string | Date to compute transits — `"YYYY-MM-DD"` |
| `dob` | string | Date of birth — `"YYYY-MM-DD"` |
| `time` | string | Time of birth — `"HH:MM"` (24-hour) |
| `lat` | float | Birth latitude |
| `lon` | float | Birth longitude |
| `timezone` | string | Optional — defaults to `"Asia/Kolkata"` |

**Returns:** JSON with transit `planets` (sign, degree, nakshatra, `sav_points`, house from Lagna/Moon), `sade_sati` status and phase, and `rahu_ketu_axis`.

### `calculate_compatibility_tool`

Calculates 16-factor compatibility + Kuja Dosha. Person 1 = Male, Person 2 = Female.

| Parameter | Type | Description |
|-----------|------|-------------|
| `dob1`, `time1`, `lat1`, `lon1`, `tz1` | various | Birth details for Person 1 (Male) |
| `dob2`, `time2`, `lat2`, `lon2`, `tz2` | various | Birth details for Person 2 (Female) |

**Returns:** 8 Ashtakoot kutas (36 pts), additional kutas (Mahendra, Stree Deergha, Vedha, Rajju, BadConstellations, LagnaHouse7, SexEnergy), exception logic, and Kuja Dosha analysis.

### `check_muhurtha_tool`

Evaluates whether a date/time is auspicious for a specific activity (electional astrology).

| Parameter | Type | Description |
|-----------|------|-------------|
| `activity` | string | One of: `marriage`, `travel`, `business`, `education`, `house_entry`, `medical` |
| `date` | string | Date to evaluate — `"YYYY-MM-DD"` |
| `time` | string | Time to evaluate — `"HH:MM"` (24-hour) |
| `lat` | float | Location latitude |
| `lon` | float | Location longitude |
| `timezone` | string | IANA timezone string |

**Returns:** JSON with `verdict`, `score`, `positive_factors`, `negative_factors`, `panchang_suddhi`, and `marriage_doshas` (for marriage activity).

### `analyze_career_chart`

Analyzes career potential using the 10th house, D10 Dashamsha, and planetary significations.

| Parameter | Type | Description |
|-----------|------|-------------|
| `dob` | string | Date of birth — `"YYYY-MM-DD"` |
| `time` | string | Time of birth — `"HH:MM"` (24-hour) |
| `lat` | float | Birth latitude |
| `lon` | float | Birth longitude |
| `timezone` | string | IANA timezone string |

**Returns:** JSON with `tenth_house` info, `d10_indicators`, `career_themes`, and `strength_factors`.

---

## RishiAI Agent Persona

The repo includes the **RishiAI** persona — a Vedic astrologer AI that interprets chart data using BPHS methodology.

| IDE | Always-on Rule | Skills |
|-----|---------------|--------|
| **VS Code Copilot** | `.github/copilot-instructions.md` | `.agents/skills/*/SKILL.md` (12 skills) |
| **Cursor** | `.cursor/rules/rishi-ai.mdc` | `.agents/skills/*/SKILL.md` (12 skills) |
| **Antigravity** | `.agents/rules/rishi-ai.md` | `.agents/skills/*/SKILL.md` + `.agents/workflows/*.md` |
| **Other clients** | Adapt from `system_prompt.md` | Adapt workflow steps from `.agents/workflows/` |

All IDEs share skills from `.agents/skills/` using the [Agent Skills](https://agentskills.io/) open standard.

### Workflows

| Command | Description |
|---------|-------------|
| `/full-reading` | Complete natal chart reading |
| `/career-analysis` | Career and professional guidance |
| `/marriage-analysis` | Marriage timing and compatibility |
| `/relationship-analysis` | Relationship dynamics |
| `/children-analysis` | Children and progeny |
| `/finance-analysis` | Wealth and financial prospects |
| `/health-analysis` | Health tendencies and remedies |
| `/education-analysis` | Education and learning |
| `/spiritual-analysis` | Spiritual path and practices |
| `/muhurtha-analysis` | Electional astrology timing |
| `/physicalIntimacy-analysis` | Physical compatibility |
| `/geopolitics-analysis` | Mundane astrology |
| `/past-life-analysis` | Past life karma and karmic debts |
| `/spouse-profiling` | Detailed spouse blueprint — looks, personality, archetype |

---

## Architecture

```
rishi_ai_mcp.py            MCP entry point — 5 tools, pip-installable
  └── dashaflow (pip)      Calculation engine
        ├── vedic_calculator   Swiss Ephemeris core
        ├── constants          Zodiac, nakshatras, dignities
        ├── nakshatra          Nakshatra lookup
        ├── panchang           Tithi, Vara, Yoga, Karana
        ├── yoga               24 yoga types + Kaal Sarpa, Graha Yuddha, Gandanta
        ├── dasha              Vimshottari 5-level
        ├── dignity            Dignity, combustion, digbala
        ├── ashtakavarga       SAV, BAV, Prashtara
        ├── jaimini            Karakas, Arudha Padas, Upapada, Karakamsha
        ├── shadbala           Six-fold strength + Ishta/Kashta
        ├── matchmaking        16-factor compatibility + Kuja Dosha
        ├── muhurtha           Electional astrology
        └── career             D10 career analysis

.vscode/mcp.json           VS Code Copilot MCP config
.github/
  └── copilot-instructions.md  Always-on rule (VS Code Copilot)
.cursor/
  ├── mcp.json             Cursor MCP config
  └── rules/rishi-ai.mdc   Always-on core rule (Cursor)
.agents/                   Shared across all IDEs
  ├── rules/rishi-ai.md   Always-on agent rule (Antigravity)
  ├── skills/              14 workflow skills (SKILL.md per folder)
  └── workflows/           14 slash-command workflows (Antigravity)
system_prompt.md           Universal reference prompt (for other clients)
```

## Prerequisites

- **Python 3.10+**
- **dashaflow** — installed automatically as dependency
- **mcp** — installed automatically as dependency

## License

MIT
