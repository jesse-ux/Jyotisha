![PanchangaAPI](https://api.moon-bot.cc/static/logo.png)

# PanchangaAPI

**Vedic Astrology API & MCP Server -- 24 tools, 5 prompts, 3 resources | Swiss Ephemeris precision**

The most accurate and complete Vedic astrology (Jyotish) API available. Purpose-built for AI agents, developers, and astro-applications. Swiss Ephemeris engine with Lahiri ayanamsha, sidereal zodiac, and true planetary positions.

**v4.1** -- KP System, 300+ Yogas, Panchanga Search, Vrata Calendar, Remedies, Choghadiya/Hora, and Ashtakavarga.

[![MCP Badge](https://lobehub.com/badge/mcp/degen0root-panchanga_api)](https://lobehub.com/mcp/degen0root-panchanga_api)
[![Smithery](https://img.shields.io/badge/Smithery-Listed-green)](https://smithery.ai/servers/panchanga/api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Quick Start

### 1. Register

```bash
curl -X POST https://api.moon-bot.cc/register \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'
```

You will receive a verification email. Click the link or use the PIN code to verify.

### 2. Get Your API Key

```bash
curl https://api.moon-bot.cc/register/status/acc_YOUR_ACCOUNT_ID
```

Returns your `api_key` once verified.

### 3. Make a Request

```bash
curl -X POST https://api.moon-bot.cc/panchanga \
  -H "X-API-Key: pnc_YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"datetime": "2026-03-16T06:00:00+05:30", "latitude": 28.6139, "longitude": 77.2090}'
```

---

## MCP Server Capabilities

PanchangaAPI is a full-featured MCP server with **24 tools**, **5 prompt templates**, and **3 resources**.

### Tools (24)

| Tool Name | Description | Credits |
|-----------|-------------|---------|
| `chart.panchanga` | Complete Panchanga -- tithi, nakshatra, yoga, karana, vara + Rahu Kalam, Yamaganda, Gulika | 1 |
| `chart.panchanga_range` | Multi-day Panchanga for a date range | 1/day |
| `chart.panchanga_search` | Search for specific Panchanga combinations (tithi+nakshatra+yoga+vara) | 5 |
| `data.ephemeris` | Planetary positions -- longitude, latitude, speed, sign, nakshatra, retrograde | 1 |
| `chart.kundali` | Full birth chart -- Lagna, 9 grahas, 12 houses, Navamsha, Dasha, Ashtakavarga, 300+ Yogas, Doshas | 3 |
| `prediction.dasha` | Vimshottari Dasha -- Maha + Antar + Pratyantardasha with exact date ranges | 2 |
| `analysis.compatibility` | Ashtakoot 8-fold matching (36-point scale) | 5 |
| `analysis.muhurta` | Ranked auspicious timing windows with quality scores | 1 |
| `prediction.transits` | Planetary transits relative to natal Moon, Sade Sati detection | 2 |
| `chart.vargas` | All 16 divisional charts (D1 through D60) | 3 |
| `analysis.shadbala` | Six-fold planetary strength with component breakdown | 3 |
| `chart.bhava_chalit` | Bhava Chalit chart with house cusps and planet shifts | 3 |
| `prediction.prashna` | Horary (Prashna) astrology -- significators and indication scoring | 2 |
| `prediction.varshaphal` | Solar Return -- Muntha, Year Lord, Tajaka Yogas | 2 |
| `data.festivals` | 50+ Hindu festivals for a given year | 10 |
| `data.festivals_month` | Monthly festival calendar | 1 |
| `analysis.kp_system` | KP System -- sub-lords, significators, cuspal analysis | 3 |
| `data.choghadiya` | Choghadiya muhurta divisions + planetary Hora hours | 1 |
| `data.vrata` | Vrata (fasting) calendar -- Ekadashi, Pradosham, Chaturthi, Amavasya | 5 |
| `data.vrata_month` | Monthly Vrata calendar | 1 |
| `analysis.remedies` | Personalized remedies -- gemstones, mantras, rituals based on chart | 3 |
| `analysis.pancha_pakshi` | Pancha Pakshi (Five Birds) timing system for activity planning | 2 |
| `account.webhook_subscribe` | Subscribe to webhook notifications for account events | free |
| `account.register` | Register for an API key (free, email, or Telegram verification) | free |

### Prompts (5)

| Prompt | Description |
|--------|-------------|
| `daily_horoscope` | Generate a daily Vedic horoscope for a given date and location |
| `birth_chart_reading` | Complete Vedic birth chart (Kundali) interpretation with all components |
| `compatibility_check` | Marriage compatibility analysis using Ashtakoot (8-fold) matching |
| `auspicious_timing` | Find the best time (Muhurta) for an important event |
| `setup_x402_payments` | How to enable automatic x402 USDC payments for this API |

### Resources (3)

| Resource | Type | Description |
|----------|------|-------------|
| OpenAPI Specification | `application/json` | Complete OpenAPI 3.x spec with all endpoints, schemas, and x-pricing extension |
| Skill Manifest | `text/markdown` | Detailed skill description with use cases, pricing, and integration guide |
| Terms of Service | `text/html` | API terms of service and usage policy |

---

## REST API Endpoints

| Method | Path | Credits | Description |
|--------|------|---------|-------------|
| POST | `/panchanga` | 1 | Complete Panchanga -- tithi, nakshatra, yoga, karana, vara + inauspicious periods |
| GET | `/panchanga` | 1 | Same via query parameters |
| POST | `/panchanga/range` | 1/day | Multi-day Panchanga |
| POST | `/panchanga/search` | 5 | Search for specific Panchanga combinations within a date range |
| POST | `/kundali` | 3 | Full birth chart -- Lagna, 9 planets, 12 houses, Navamsha, Dasha, Ashtakavarga, 300+ Yogas, Doshas |
| POST | `/kp` | 3 | KP (Krishnamurthy Paddhati) System -- sub-lords, significators, cuspal analysis |
| POST | `/dasha` | 2 | Vimshottari Dasha -- Maha + Antar + Pratyantardasha with exact date ranges |
| POST | `/compatibility` | 5 | Ashtakoot 8-fold matching (36-point scale) |
| POST | `/muhurta` | 1 | Ranked auspicious timing windows with quality scores |
| POST | `/transits` | 2 | Planetary transits relative to natal Moon, Sade Sati detection |
| POST | `/vargas` | 3 | All 16 divisional charts (D1 through D60) |
| POST | `/shadbala` | 3 | Six-fold planetary strength with component breakdown |
| POST | `/bhava-chalit` | 3 | Bhava Chalit chart with house cusps and planet shifts |
| POST | `/prashna` | 2 | Horary (Prashna) astrology -- significators and indication scoring |
| POST | `/varshaphal` | 2 | Solar Return -- Muntha, Year Lord, Tajaka Yogas |
| POST | `/choghadiya` | 1 | Choghadiya (8 muhurta divisions) + Hora (planetary hours) |
| POST | `/remedies` | 3 | Personalized remedies -- gemstones, mantras, rituals based on chart |
| GET | `/festivals/{year}` | 10 | 50+ Hindu festivals with astronomical basis |
| GET | `/festivals/{year}/{month}` | 1 | Monthly festival calendar |
| GET | `/vrata/{year}` | 5 | Vrata (fasting) calendar -- Ekadashi, Pradosham, Chaturthi, Amavasya, Purnima |
| GET | `/vrata/{year}/{month}` | 1 | Monthly Vrata calendar |
| GET | `/ephemeris` | 1 | Raw planetary positions |

All calculation endpoints accept:

```json
{
  "datetime": "ISO-8601 with timezone, e.g. 2026-03-16T10:30:00+05:30",
  "latitude": 28.6139,
  "longitude": 77.2090
}
```

---

## MCP Integration

PanchangaAPI is available as an MCP server for Claude Desktop, Cursor, and other MCP-compatible clients.

**MCP Endpoint:** `https://api.moon-bot.cc/mcp`
**Protocol:** JSON-RPC 2.0 over Streamable HTTP
**Protocol Version:** 2024-11-05

### Claude Desktop

Add to your `claude_desktop_config.json`:

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

Add to your MCP settings:

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

Any client supporting Streamable HTTP transport:

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

For full MCP protocol documentation, see [MCP.md](MCP.md).

**Listings:**
- [LobeHub MCP Marketplace](https://lobehub.com/mcp/degen0root-panchanga_api)
- [Smithery](https://smithery.ai/servers/panchanga/api)

---

## Payment Methods

### Free Tier

2 requests per day, all endpoints. Register and start using immediately -- no payment required.

### x402 USDC (Automatic)

Send a request without auth. Receive a `402 Payment Required` response with USDC payment instructions. Sign the payment (Base or Solana), retry with `PAYMENT-SIGNATURE` header. Fully automated, zero-friction, no registration needed.

Cost: **$0.03 per credit**.

### Telegram Stars

Purchase credits via [@vastr_bot](https://t.me/vastr_bot) using Telegram Stars. Deep link format:

```
https://t.me/vastr_bot?start=pay_{api_key}_{stars}
```

1 Telegram Star = 0.5 API credits.

### Crypto (NOWPayments)

Pay with 350+ cryptocurrencies (BTC, ETH, USDT, SOL, and more):

```
GET https://api.moon-bot.cc/checkout/{api_key}/{credits}
```

Credits are applied automatically after payment confirmation.

---

## Pricing

| Credits | Price | Per Credit |
|---------|-------|------------|
| Free tier | $0 | 2 requests/day |
| 100 | $3 | $0.03 |
| 500 | $15 | $0.03 |
| 1,000 | $30 | $0.03 |
| 5,000 | $150 | $0.03 |

---

## Use Cases

- **Daily horoscopes** -- Panchanga for tithi, nakshatra, yoga, karana
- **Birth chart readings** -- Full Kundali with 300+ Yogas, Dasha, Ashtakavarga, Doshas
- **Compatibility matching** -- Ashtakoot 8-fold scoring for relationships
- **Event timing** -- Muhurta for weddings, business launches, travel
- **Annual predictions** -- Varshaphal with Tajaka Yogas
- **KP astrology** -- Sub-lord based predictions and ruling planet analysis
- **Financial astrology** -- Transit-based market signals, Dasha cycle analysis
- **Sports prediction** -- Prashna horary for event outcomes
- **Festival & Vrata calendars** -- Hindu festivals and fasting dates with astronomical timing
- **Remedial astrology** -- Personalized gemstone, mantra, and ritual recommendations
- **Intraday timing** -- Choghadiya and Hora for hourly auspiciousness

---

## Links

| Resource | URL |
|----------|-----|
| API Base URL | [api.moon-bot.cc](https://api.moon-bot.cc) |
| OpenAPI Spec | [api.moon-bot.cc/openapi.json](https://api.moon-bot.cc/openapi.json) |
| MCP Endpoint | [api.moon-bot.cc/mcp](https://api.moon-bot.cc/mcp) |
| LobeHub | [lobehub.com/mcp/degen0root-panchanga_api](https://lobehub.com/mcp/degen0root-panchanga_api) |
| Smithery | [smithery.ai/servers/panchanga/api](https://smithery.ai/servers/panchanga/api) |
| ClawHub Skill | [SKILL.md](SKILL.md) |
| Terms | [api.moon-bot.cc/terms](https://api.moon-bot.cc/terms) |

---

## License

[MIT](LICENSE)
