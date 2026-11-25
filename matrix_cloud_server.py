"""
matrix_cloud_server.py — Unified Production Cloud Host for Wave 2/3 Oracles (#06, #09, #08, #07)
Single zero-cold-start container running on Fly.io (`nrt` + persistent `/data`) behind Cloudflare Edge.
"""

import asyncio
from contextlib import asynccontextmanager, suppress
from datetime import datetime, timezone
import importlib.util
import json
import os
import sqlite3
import sys
from typing import Any, Dict, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, PlainTextResponse
from pydantic import BaseModel

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from matrix_live_harvesters import run_all_sequential_harvesters  # noqa: E402

DATA_DIR = os.environ.get("MATRIX_DATA_DIR", os.path.join(ROOT_DIR, "data"))
os.makedirs(DATA_DIR, exist_ok=True)
TREASURY_WALLET = os.environ.get("A2A_TREASURY_WALLET", "0x5ab8fBd41e0691876fE3cC3b0dF62A901C2cD044")


def _load_oracle(rel_path: str, mod_name: str):
    full_path = os.path.join(ROOT_DIR, rel_path)
    spec = importlib.util.spec_from_file_location(mod_name, full_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.init_db()
    return mod


mod_06 = _load_oracle("06-listingshield/app.py", "cloud_mod_06_listingshield")
mod_09 = _load_oracle("09-saasbench/app.py", "cloud_mod_09_saasbench")
mod_08 = _load_oracle("08-demurrage-audit/app.py", "cloud_mod_08_demurrage")
mod_07 = _load_oracle("07-siliconorigin/app.py", "cloud_mod_07_silicon")

MATRIX_ORACLES = [
    {
        "relay_order": 1,
        "slug": "listingshield",
        "mount": "/listingshield",
        "service": "ListingShield AI",
        "wave": "WAVE_2_MONETIZATION",
        "price_usdc": 0.015,
        "tool_name": "preflight_listing_tro_and_empco",
        "summary": "Schedule-A TRO stealth wordmarks + multilingual EU EmpCo 2024/825 anti-greenwashing scanner.",
    },
    {
        "relay_order": 2,
        "slug": "saasbench",
        "mount": "/saasbench",
        "service": "SaaSBench AI",
        "wave": "WAVE_2_MONETIZATION",
        "price_usdc": 0.500,
        "tool_name": "benchmark_saas_quote_and_ai_surcharges",
        "summary": "Public GSA/DIR/G-Cloud floor SaaS unit prices, k>=3 federated cohorts & anti-AI/MCP surcharge redlines.",
    },
    {
        "relay_order": 3,
        "slug": "demurrage",
        "mount": "/demurrage",
        "service": "DemurrageAudit AI",
        "wave": "WAVE_2_MONETIZATION",
        "price_usdc": 0.150,
        "tool_name": "audit_container_demurrage_fmc541",
        "summary": "US FMC 46 CFR Part 541 30-day bar, mandatory fields validator & port lockout stop-clock solver.",
    },
    {
        "relay_order": 4,
        "slug": "siliconorigin",
        "mount": "/siliconorigin",
        "service": "SiliconOrigin AI",
        "wave": "WAVE_3_VERTICAL_MOAT",
        "price_usdc": 0.050,
        "tool_name": "verify_ic_pcn_and_section5949_origin",
        "summary": "Unstructured OEM PCN/EOL wafer fab diffusion trace under NDAA Section 5949 + clean-fab DigiKey drop-ins.",
    },
]

MATRIX_HARVEST_STATUS: Dict[str, Any] = {
    "runs_completed": 0,
    "last_run_at": None,
    "last_summary": None,
    "last_error": None,
}


def _collect_db_counts() -> Dict[str, int]:
    counts = {
        "stealth_marks": 0,
        "empco_terms": 0,
        "saas_skus": 0,
        "demurrage_cases": 0,
        "silicon_mpns": 0,
    }
    try:
        c06 = sqlite3.connect(mod_06.DB_PATH)
        counts["stealth_marks"] = c06.execute("SELECT COUNT(*) FROM stealth_marks").fetchone()[0]
        counts["empco_terms"] = c06.execute("SELECT COUNT(*) FROM empco_terms").fetchone()[0]
        c06.close()
        c09 = sqlite3.connect(mod_09.DB_PATH)
        counts["saas_skus"] = c09.execute("SELECT COUNT(*) FROM saas_benchmarks").fetchone()[0]
        c09.close()
        c08 = sqlite3.connect(mod_08.DB_PATH)
        counts["demurrage_cases"] = c08.execute("SELECT COUNT(*) FROM dd_invoice_cases").fetchone()[0]
        c08.close()
        c07 = sqlite3.connect(mod_07.DB_PATH)
        counts["silicon_mpns"] = c07.execute("SELECT COUNT(*) FROM ic_provenance_rules").fetchone()[0]
        c07.close()
    except Exception:
        pass
    return counts


async def _sequential_auto_harvest_loop(interval_sec: int) -> None:
    await asyncio.sleep(2.0)
    while True:
        try:
            summary = await asyncio.to_thread(run_all_sequential_harvesters)
            MATRIX_HARVEST_STATUS["runs_completed"] = int(MATRIX_HARVEST_STATUS["runs_completed"]) + 1
            MATRIX_HARVEST_STATUS["last_run_at"] = datetime.now(timezone.utc).isoformat()
            MATRIX_HARVEST_STATUS["last_summary"] = summary
            MATRIX_HARVEST_STATUS["last_error"] = None
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            MATRIX_HARVEST_STATUS["last_error"] = f"{type(exc).__name__}: {exc}"
        await asyncio.sleep(max(60, interval_sec))


@asynccontextmanager
async def lifespan(app: FastAPI):
    interval_sec = int(os.environ.get("MATRIX_AUTO_HARVEST_INTERVAL_SEC", "7200"))
    task = asyncio.create_task(_sequential_auto_harvest_loop(interval_sec))
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(
    title="A2A Data Matrix — Unified Quad-Oracle Cloud Server (#06, #09, #08, #07)",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Payment-Required", "X-Payment-Response", "X-Risk-Preview", "X-Idempotency-Replayed"],
)

app.mount("/listingshield", mod_06.app)
app.mount("/saasbench", mod_09.app)
app.mount("/demurrage", mod_08.app)
app.mount("/siliconorigin", mod_07.app)


@app.get("/healthz")
def healthz():
    return {
        "status": "ok",
        "warm": True,
        "treasury_wallet": TREASURY_WALLET,
        "counts": _collect_db_counts(),
        "harvest_status": MATRIX_HARVEST_STATUS,
    }


@app.get("/.well-known/mcp.json")
def well_known_mcp():
    return {
        "mcpDiscoveryVersion": "2026-07-28",
        "name": "a2a-matrix-quad-oracle",
        "issuer": "A2A Data Matrix Holdings Inc. (Founder: Edmund Hu)",
        "statelessStreamableHttp": True,
        "endpoint": "/mcp",
        "paymentProtocol": "x402-optimistic-eip3009",
        "treasuryWallet": TREASURY_WALLET,
        "oracles": MATRIX_ORACLES,
    }


@app.get("/.well-known/x402-manifest.json")
def well_known_x402():
    return {
        "x402Version": 1,
        "issuer": "A2A Data Matrix Holdings Inc.",
        "network": "base-mainnet",
        "asset": "USDC",
        "payTo": TREASURY_WALLET,
        "facilitator": os.environ.get("X402_FACILITATOR_URL", "https://facilitator.payai.network"),
        "endpoints": [
            {"path": "/listingshield/api/v1/listingshield/verify", "priceUsdc": 0.015},
            {"path": "/saasbench/api/v1/saasbench/verify", "priceUsdc": 0.500},
            {"path": "/demurrage/api/v1/demurrage/verify", "priceUsdc": 0.150},
            {"path": "/siliconorigin/api/v1/silicon/verify", "priceUsdc": 0.050},
        ],
    }


@app.get("/llms.txt", response_class=PlainTextResponse)
def llms_txt():
    lines = [
        "# A2A Data Matrix Holdings — Quad-Oracle Production Endpoint (#06, #09, #08, #07)",
        f"> Treasury Wallet (Base USDC): {TREASURY_WALLET}",
        "> Unified MCP Streamable HTTP: POST /mcp",
        "",
        "## Available Oracles (Sequential Rollout Priority)",
    ]
    for o in MATRIX_ORACLES:
        lines.append(
            f"- [Relay {o['relay_order']}] {o['service']} ({o['price_usdc']} USDC) | Sub-mount: {o['mount']} | MCP tool: {o['tool_name']} — {o['summary']}"
        )
    return "\n".join(lines) + "\n"


@app.post("/v1/admin/trigger-harvest")
async def trigger_harvest():
    summary = await asyncio.to_thread(run_all_sequential_harvesters)
    MATRIX_HARVEST_STATUS["runs_completed"] = int(MATRIX_HARVEST_STATUS["runs_completed"]) + 1
    MATRIX_HARVEST_STATUS["last_run_at"] = datetime.now(timezone.utc).isoformat()
    MATRIX_HARVEST_STATUS["last_summary"] = summary
    MATRIX_HARVEST_STATUS["last_error"] = None
    return summary


class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Optional[Any] = 1
    method: str
    params: Optional[Dict[str, Any]] = None


_TOOL_ROUTER = {
    "preflight_listing_tro_and_empco": mod_06,
    "benchmark_saas_quote_and_ai_surcharges": mod_09,
    "audit_container_demurrage_fmc541": mod_08,
    "verify_ic_pcn_and_section5949_origin": mod_07,
}


@app.post("/mcp")
def unified_quad_mcp(req: MCPRequest):
    if req.method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req.id,
            "result": {
                "protocolVersion": "2026-07-28",
                "serverInfo": {"name": "a2a-matrix-quad-oracle", "version": "2.0.0", "stateless": True},
                "capabilities": {"tools": {}},
            },
        }
    if req.method == "tools/list":
        tools = [
            {
                "name": "discover_matrix_oracles",
                "description": "Discover all 4 A2A Data Matrix cloud oracles (#06 ListingShield, #09 SaaSBench, #08 DemurrageAudit, #07 SiliconOrigin) and pricing.",
                "inputSchema": {
                    "type": "object",
                    "properties": {"domain_filter": {"type": "string"}},
                },
            }
        ]
        for target_mod in (mod_06, mod_09, mod_08, mod_07):
            sub_resp = target_mod.mcp_endpoint(target_mod.MCPRequest(jsonrpc="2.0", id=req.id, method="tools/list"))
            tools.extend(sub_resp["result"]["tools"])
        return {"jsonrpc": "2.0", "id": req.id, "result": {"tools": tools}}

    if req.method == "tools/call":
        params = req.params or {}
        tool_name = str(params.get("name", "discover_matrix_oracles"))
        args = params.get("arguments") or {}
        if tool_name == "discover_matrix_oracles":
            filt = str(args.get("domain_filter", "")).lower()
            matched = [o for o in MATRIX_ORACLES if not filt or filt in o["slug"] or filt in o["summary"].lower()]
            return {"jsonrpc": "2.0", "id": req.id, "result": {"content": [{"type": "text", "text": json.dumps(matched, indent=2)}]}}

        target_mod = _TOOL_ROUTER.get(tool_name)
        if target_mod is None:
            return {"jsonrpc": "2.0", "id": req.id, "error": {"code": -32602, "message": f"Unknown tool '{tool_name}'"}}
        return target_mod.mcp_endpoint(
            target_mod.MCPRequest(jsonrpc="2.0", id=req.id, method="tools/call", params={"name": tool_name, "arguments": args})
        )

    return {"jsonrpc": "2.0", "id": req.id, "error": {"code": -32601, "message": "Method not found"}}


@app.get("/", response_class=HTMLResponse)
def cloud_command_center():
    counts = _collect_db_counts()
    return f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head><meta charset="UTF-8" /><title>A2A Data Matrix — Quad-Oracle Cloud Command Center</title><script src="https://cdn.tailwindcss.com"></script></head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans p-8">
  <div class="max-w-6xl mx-auto space-y-8">
    <header class="border-b border-slate-800 pb-6 flex flex-wrap justify-between items-end gap-4">
      <div>
        <span class="px-3 py-1 text-xs font-semibold bg-emerald-500/20 text-emerald-300 rounded-full border border-emerald-500/40">Production Cloud · Zero Cold-Start · Base USDC x402</span>
        <h1 class="text-4xl font-extrabold mt-3 text-white">A2A Data Matrix — Quad-Oracle Cloud</h1>
        <p class="text-slate-400 mt-1">Treasury Wallet: <span class="font-mono text-cyan-300">{TREASURY_WALLET}</span></p>
      </div>
      <div class="text-right text-xs text-slate-400 font-mono space-y-1">
        <div>Unified MCP: <span class="text-indigo-400">POST /mcp</span></div>
        <div><a href="/.well-known/mcp.json" class="underline text-cyan-400">/.well-known/mcp.json</a> · <a href="/healthz" class="underline text-emerald-400">/healthz</a> · <a href="/llms.txt" class="underline text-slate-300">/llms.txt</a></div>
      </div>
    </header>
    <section class="grid grid-cols-2 md:grid-cols-5 gap-4">
      <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl"><div class="text-xs text-slate-400">TRO Marks (#06)</div><div class="text-2xl font-bold text-emerald-400 mt-1">{counts['stealth_marks']}</div></div>
      <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl"><div class="text-xs text-slate-400">EmpCo Terms (#06)</div><div class="text-2xl font-bold text-emerald-300 mt-1">{counts['empco_terms']}</div></div>
      <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl"><div class="text-xs text-slate-400">SaaS SKUs (#09)</div><div class="text-2xl font-bold text-violet-400 mt-1">{counts['saas_skus']}</div></div>
      <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl"><div class="text-xs text-slate-400">Port Terminals (#08)</div><div class="text-2xl font-bold text-cyan-400 mt-1">{counts['demurrage_cases']}</div></div>
      <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl"><div class="text-xs text-slate-400">IC MPNs (#07)</div><div class="text-2xl font-bold text-amber-400 mt-1">{counts['silicon_mpns']}</div></div>
    </section>
    <section class="grid md:grid-cols-2 gap-6">
      <a href="/listingshield/" class="block bg-slate-900 hover:bg-slate-800 border border-emerald-500/40 rounded-2xl p-6 transition">
        <span class="text-xs font-mono text-emerald-300">RELAY 1 · #06 · /listingshield/ · 0.015 USDC</span>
        <h2 class="text-2xl font-bold mt-1">ListingShield AI</h2>
        <p class="text-sm text-slate-400 mt-2">美國 Schedule-A 流氓商標暗樁 ＋ 歐盟 EmpCo (2024/825) 反漂綠多語系即時過濾閘道。</p>
      </a>
      <a href="/saasbench/" class="block bg-slate-900 hover:bg-slate-800 border border-violet-500/40 rounded-2xl p-6 transition">
        <span class="text-xs font-mono text-violet-300">RELAY 2 · #09 · /saasbench/ · 0.500 USDC</span>
        <h2 class="text-2xl font-bold mt-1">SaaSBench AI</h2>
        <p class="text-sm text-slate-400 mt-2">USAspending / GSA / G-Cloud 公部門決標底價對標 ＋ 反 AI/MCP 超額計費紅線條款庫。</p>
      </a>
      <a href="/demurrage/" class="block bg-slate-900 hover:bg-slate-800 border border-cyan-500/40 rounded-2xl p-6 transition">
        <span class="text-xs font-mono text-cyan-300">RELAY 3 · #08 · /demurrage/ · 0.150 USDC</span>
        <h2 class="text-2xl font-bold mt-1">DemurrageAudit AI</h2>
        <p class="text-sm text-slate-400 mt-2">US eCFR Title 46 (`46 CFR §541`) 海運延滯費免責時鐘 ＋ 30 天逾期失權抓漏引擎。</p>
      </a>
      <a href="/siliconorigin/" class="block bg-slate-900 hover:bg-slate-800 border border-amber-500/40 rounded-2xl p-6 transition">
        <span class="text-xs font-mono text-amber-300">RELAY 4 · #07 · /siliconorigin/ · 0.050 USDC + Affiliate</span>
        <h2 class="text-2xl font-bold mt-1">SiliconOrigin AI</h2>
        <p class="text-sm text-slate-400 mt-2">半導體 PCN/EOL 停產變更與 NDAA §5949 晶圓代工溯源 ＋ 乾淨晶圓廠 DigiKey 平替導購。</p>
      </a>
    </section>
  </div>
</body>
</html>"""


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
