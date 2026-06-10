# MCP Integration Guide

PanchangaAPI implements the Model Context Protocol (MCP) via Streamable HTTP transport, making **22 Vedic astrology tools**, **5 prompt templates**, and **3 resources** available to MCP-compatible clients.

## Endpoint

```
POST https://api.moon-bot.cc/mcp
```

**Protocol:** JSON-RPC 2.0 over Streamable HTTP
**Protocol Version:** 2024-11-05
**Authentication:** `X-API-Key` header with your API key
**Session:** Server returns `Mcp-Session-Id` header on `initialize` -- include it in subsequent requests.

---

## Server Capabilities

```json
{
  "tools": {},
  "resources": {},
  "prompts": {}
}
```

| Capability | Count | Description |
|------------|-------|-------------|
| Tools | 22 | Vedic astrology calculations + account registration |
| Prompts | 5 | Pre-built prompt templates for common use cases |
| Resources | 3 | OpenAPI spec, skill manifest, terms of service |

---

## Client Configuration

### Claude Desktop

Add to `~/.config/claude/claude_desktop_config.json` (Linux) or `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "panchanga": {
      "url": "https://api.moon-bot.cc/mcp",
      "headers": {
        "X-API-Key": "pnc_YOUR_KEY"
      }
    }
  }
}
```

### Cursor

Add to your Cursor MCP settings (Settings > MCP Servers):

```json
{
  "panchanga": {
    "url": "https://api.moon-bot.cc/mcp",
    "headers": {
      "X-API-Key": "pnc_YOUR_KEY"
    }
  }
}
```

### Windsurf / Continue / Other MCP Clients

```json
{
  "panchanga-api": {
    "url": "https://api.moon-bot.cc/mcp",
    "transport": "streamable-http",
    "headers": {
      "X-API-Key": "pnc_YOUR_KEY"
    }
  }
}
```

### Smithery

Install directly from Smithery:

[smithery.ai/servers/panchanga/api](https://smithery.ai/servers/panchanga/api)

---

## Available Tools (22)

All tools accept `datetime` (ISO-8601 with timezone), `latitude`, and `longitude` parameters unless noted otherwise.

| Tool Name | Description | Credits |
|-----------|-------------|---------|
| `chart.panchanga` | Complete Panchanga -- tithi, nakshatra, yoga, karana, vara + Rahu Kalam, Yamaganda, Gulika | 1 |
| `chart.panchanga_range` | Multi-day Panchanga for a date range | 1/day |
| `chart.panchanga_search` | Search for Panchanga combinations (tithi+nakshatra+yoga+vara criteria) | 5 |
| `data.ephemeris` | Planetary positions -- longitude, latitude, speed, sign, nakshatra, retrograde | 1 |
| `chart.kundali` | Full birth chart -- Lagna, 9 grahas, 12 houses, Navamsha, Dasha, Ashtakavarga, 300+ Yogas, Doshas | 3 |
| `prediction.dasha` | Vimshottari Dasha timeline -- Maha + Antar + Pratyantardasha | 2 |
| `analysis.compatibility` | Ashtakoot 8-fold matching for two birth charts (36-point scale) | 5 |
| `analysis.muhurta` | Find ranked auspicious timing windows with quality scores | 1 |
| `prediction.transits` | Planetary transits relative to natal Moon, Sade Sati detection | 2 |
| `chart.vargas` | All 16 divisional charts (D1 through D60) | 3 |
| `analysis.shadbala` | Six-fold planetary strength with component breakdown | 3 |
| `chart.bhava_chalit` | Bhava Chalit chart with house cusps and planet shifts | 3 |
| `prediction.prashna` | Horary astrology -- significators, indication scoring, guidance | 2 |
| `prediction.varshaphal` | Solar Return -- Muntha, Year Lord, Tajaka Yogas | 2 |
| `data.festivals` | 50+ Hindu festivals for a given year | 10 |
| `data.festivals_month` | Monthly festival calendar | 1 |
| `analysis.kp_system` | KP System -- sub-lords, significators, cuspal analysis | 3 |
| `data.choghadiya` | Choghadiya muhurta divisions + Hora planetary hours | 1 |
| `data.vrata` | Vrata (fasting) calendar -- Ekadashi, Pradosham, Chaturthi, Amavasya | 5 |
| `data.vrata_month` | Monthly Vrata calendar | 1 |
| `analysis.remedies` | Personalized remedies -- gemstones, mantras, rituals based on chart | 3 |
| `account.register` | Register for an API key (free, email, or Telegram) | free |

### Tool Annotations

All calculation tools include MCP annotations:

```json
{
  "readOnlyHint": true,
  "destructiveHint": false,
  "idempotentHint": true,
  "openWorldHint": false
}
```

The `account.register` tool has `readOnlyHint: false` and `idempotentHint: false` since it creates state.

---

## Prompts (5)

| Prompt | Arguments | Description |
|--------|-----------|-------------|
| `daily_horoscope` | date, latitude, longitude | Generate a daily Vedic horoscope |
| `birth_chart_reading` | birth_datetime, latitude, longitude | Complete Kundali interpretation |
| `compatibility_check` | person1_datetime, person2_datetime, latitude, longitude | Ashtakoot marriage matching |
| `auspicious_timing` | event_type, after_date, latitude, longitude | Find best Muhurta for an event |
| `setup_x402_payments` | (none) | Guide for enabling x402 USDC auto-payments |

---

## Resources (3)

| URI | Name | MIME Type |
|-----|------|-----------|
| `https://api.moon-bot.cc/openapi.json` | OpenAPI Specification | application/json |
| `https://api.moon-bot.cc/static/SKILL.md` | Skill Manifest | text/markdown |
| `https://api.moon-bot.cc/terms` | Terms of Service | text/html |

---

## Protocol Flow

### 1. Initialize

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "my-client",
      "version": "1.0.0"
    }
  }
}
```

Response includes `Mcp-Session-Id` header.

### 2. Send Initialized Notification

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

### 3. List Tools

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list"
}
```

### 4. List Prompts

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "prompts/list"
}
```

### 5. List Resources

```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/list"
}
```

### 6. Call a Tool

```json
{
  "jsonrpc": "2.0",
  "id": 5,
  "method": "tools/call",
  "params": {
    "name": "chart.panchanga",
    "arguments": {
      "datetime": "2026-03-16T06:00:00+05:30",
      "latitude": 28.6139,
      "longitude": 77.2090
    }
  }
}
```

### 7. Get a Prompt

```json
{
  "jsonrpc": "2.0",
  "id": 6,
  "method": "prompts/get",
  "params": {
    "name": "setup_x402_payments"
  }
}
```

---

## Getting an API Key

Register for free (2 requests/day):

```bash
curl -X POST https://api.moon-bot.cc/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
```

Purchase credits via [NOWPayments crypto](https://api.moon-bot.cc/checkout/{api_key}/{credits}), [Telegram Stars](https://t.me/vastr_bot), or x402 USDC auto-payment.
