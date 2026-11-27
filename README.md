<!--
mcp-name: io.github.heroson86462-hsnu/a2a-matrix-quad-oracle
-->

# A2A Data Matrix Quad-Oracle (`a2a-matrix-quad-oracle`)

**4-in-1 Deterministic Commercial Compliance, Regulatory & Procurement Oracles for AI Agents** (zero runtime LLM cost, `<5ms` deterministic evaluation, Streamable-HTTP MCP + `stdio` `uvx` + Base USDC `x402`).

[![PyPI](https://img.shields.io/pypi/v/a2a-matrix-quad-oracle)](https://pypi.org/project/a2a-matrix-quad-oracle/)
[![MCP Registry](https://img.shields.io/badge/MCP_Registry-io.github.heroson86462--hsnu%2Fa2a--matrix--quad--oracle-00b4d8)](https://registry.modelcontextprotocol.io)
[![x402 Ready](https://img.shields.io/badge/HTTP%20402-x402%20USDC-10b981)](https://a2a-matrix-quad-edge.a2a-data-matrix.workers.dev/.well-known/x402-manifest.json)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## Included Deterministic Oracles

| Relay | Oracle | Deterministic Scope | Pricing (`x402` Base USDC) |
| :--- | :--- | :--- | :--- |
| **#06** | **ListingShield AI** | US Schedule-A TRO stealth wordmarks (`25+` active marks) + EU EmpCo Directive `2024/825` multilingual anti-greenwashing guard (`18` EN/DE/FR phrases) | Free offline `stdio` scan / `0.015 USDC` cloud |
| **#09** | **SaaSBench AI** | `15` Enterprise SaaS SKUs anchored by US GSA Advantage / USAspending / Texas DIR / UK G-Cloud floors + anti-AI/MCP overage redlines | `0.500 USDC` (free 402 teaser) |
| **#08** | **DemurrageAudit AI** | US eCFR Title 46 (`46 CFR Part 541`) 30-day billing bar forfeiture (`§541.7`), `§541.6` mandatory invoice fields, & terminal lockout stop-clock | Free offline `stdio` calc / `0.150 USDC` cloud |
| **#07** | **SiliconOrigin AI** | Unstructured OEM PCN/EOL tracking & US NDAA **Section 5949** wafer fab provenance (`15` high-frequency ICs) + clean-fab DigiKey drop-ins | `0.050 USDC` + authorized affiliate links |

---

## Option 1: Zero-Install Remote Streamable-HTTP MCP

Add directly to Claude Desktop, Cursor, Windsurf, or Antigravity:

```json
{
  "mcpServers": {
    "a2a-matrix-quad-oracle": {
      "type": "streamable-http",
      "url": "https://a2a-matrix-quad-edge.a2a-data-matrix.workers.dev/mcp"
    }
  }
}
```

## Option 2: Free Local `stdio` MCP (`uvx`)

Includes offline zero-cost `scan_listing_copy_locally` and `check_fmc541_demurrage_stopclock` plus cloud-oracle bridges:

```json
{
  "mcpServers": {
    "a2a-matrix-quad-oracle": {
      "command": "uvx",
      "args": ["a2a-matrix-quad-oracle"]
    }
  }
}
```

---

## Live Cloud Endpoints & Interactive Sandbox

* **Interactive Cloud Command Center**: https://a2a-matrix-quad-edge.a2a-data-matrix.workers.dev/
* **Discovery**: `/.well-known/mcp.json` · `/.well-known/x402-manifest.json` · `/llms.txt` · `/healthz`
* **Companion Runtime Security Firewall (Wave 1)**: [`agenttrust-kye`](https://github.com/heroson86462-hsnu/agenttrust-kye) (`uvx agenttrust-kye`)

Built by **A2A Data Matrix Holdings Inc.** · Maintainer: Edmund Hu (`edmundhu@helloyunivia.com`)
