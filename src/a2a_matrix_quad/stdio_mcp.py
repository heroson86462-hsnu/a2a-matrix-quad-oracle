"""
stdio_mcp.py — Local Zero-Config Stdio MCP + Cloud x402 Bridge (`a2a-matrix-quad-oracle`).
Exposes 2 free offline deterministic tools (#06 ListingShield copy scanner + #08 FMC 541 stop-clock solver)
and 3 cloud-backed deterministic oracle tools (#09 SaaSBench, #07 SiliconOrigin, Matrix discovery).
"""

import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

import httpx

DEFAULT_CLOUD_URL = os.environ.get(
    "A2A_MATRIX_URL",
    "https://a2a-matrix-quad-edge.a2a-data-matrix.workers.dev",
).rstrip("/")
PREPAID_BEARER = os.environ.get("A2A_PREPAID_BEARER", "")
X402_PAYMENT = os.environ.get("A2A_X402_PAYMENT", "")

# 25 Schedule-A / high-litigation stealth wordmarks -> safe generic replacements
STEALTH_TRADEMARKS: List[Tuple[str, str, str, str]] = [
    ("onesie", "Gerber Childrenswear LLC", "HIGH_TRO_FREEZE", "infant bodysuit"),
    ("velcro", "Velcro IP Holdings LLC", "HIGH_TRO_FREEZE", "hook-and-loop strap"),
    ("frisbee", "Wham-O Holding Ltd.", "HIGH_TRO_FREEZE", "flying disc"),
    ("hula hoop", "Wham-O Holding Ltd.", "HIGH_TRO_FREEZE", "fitness waist hoop"),
    ("bubble wrap", "Sealed Air Corp.", "MEDIUM_IP_TAKEDOWN", "air-cushion packing film"),
    ("popsocket", "PopSockets LLC", "HIGH_TRO_FREEZE", "collapsible phone grip"),
    ("taser", "Axon Enterprise Inc.", "HIGH_TRO_FREEZE", "stun device"),
    ("thermos", "Thermos L.L.C.", "MEDIUM_IP_TAKEDOWN", "vacuum insulated flask"),
    ("rubik's", "Spin Master Toys UK Ltd.", "HIGH_TRO_FREEZE", "3x3 speed puzzle cube"),
    ("chapstick", "Haleon US IP LLC", "MEDIUM_IP_TAKEDOWN", "moisturizing lip balm"),
    ("band-aid", "Kenvue Inc.", "MEDIUM_IP_TAKEDOWN", "adhesive bandage strip"),
    ("squishmallow", "Kelly Toys Holdings LLC", "HIGH_TRO_FREEZE", "soft plush pillow toy"),
    ("trx", "Fitness Anywhere LLC", "HIGH_TRO_FREEZE", "suspension trainer strap"),
    ("zumba", "Zumba Fitness LLC", "HIGH_TRO_FREEZE", "latin dance fitness"),
    ("crossfit", "CrossFit LLC", "MEDIUM_IP_TAKEDOWN", "high-intensity interval training"),
    ("jacuzzi", "Jacuzzi Inc.", "MEDIUM_IP_TAKEDOWN", "hydrotherapy whirlpool tub"),
    ("jet ski", "Kawasaki Motors Corp.", "MEDIUM_IP_TAKEDOWN", "personal watercraft"),
    ("ping pong", "Parker Bros / Escalade", "MEDIUM_IP_TAKEDOWN", "table tennis"),
    ("post-it", "3M Company", "MEDIUM_IP_TAKEDOWN", "repositionable sticky notes"),
    ("rollerblade", "Tecnica Group S.p.A.", "MEDIUM_IP_TAKEDOWN", "inline skates"),
    ("sharpie", "Newell Brands Inc.", "HIGH_TRO_FREEZE", "permanent fine-tip marker"),
    ("tupperware", "Tupperware Products S.A.", "MEDIUM_IP_TAKEDOWN", "airtight food storage container"),
    ("styrofoam", "DuPont de Nemours Inc.", "MEDIUM_IP_TAKEDOWN", "extruded polystyrene foam"),
    ("hacky sack", "Wham-O Holding Ltd.", "MEDIUM_IP_TAKEDOWN", "woven footbag"),
    ("kewpie", "Q.P. Corporation", "HIGH_TRO_FREEZE", "japanese style mayonnaise"),
]

# 18 multilingual EN/DE/FR EU EmpCo Directive 2024/825 Annex I banned claims (requires_iso14024, guidance)
EMPCO_CLAIMS: List[Tuple[str, bool, str]] = [
    ("eco-friendly", True, "Replace with audited metric or attach ISO 14024 Type-I Ecolabel ID"),
    ("umweltfreundlich", True, "German generic green claim banned in EU without ISO 14024 ecolabel"),
    ("éco-responsable", True, "French generic green claim banned in EU without EU Ecolabel / ISO 14024"),
    ("biodegradable", True, "Remove unqualified claim unless EN 13432 certified timeframe stated"),
    ("biologisch abbaubar", True, "German unqualified biodegradability banned without certified standard"),
    ("climate neutral", False, "PROHIBITED_PER_SE: Carbon-offset neutrality claims banned in EU"),
    ("klimaneutral", False, "PROHIBITED_PER_SE: German offset-based climate neutrality banned"),
    ("carbon neutral", False, "PROHIBITED_PER_SE: Carbon-offset neutrality claims banned in EU"),
    ("neutre en carbone", False, "PROHIBITED_PER_SE: French offset-based carbon neutrality banned"),
    ("net zero", False, "Substantiate with third-party verified transition plan & Scope 1-3 milestones"),
    ("environmentally friendly", True, "Replace with measurable recycled content percentage"),
    ("100% green", True, "Remove generic green claim; specify audited material ratio"),
    ("ecological", True, "Ban on uncertified generic ecological statements in EU"),
    ("planet-friendly", True, "Replace with specific packaging reduction or ISO 14024 cert"),
    ("nature's friend", True, "Remove unsubstantiated marketing phrasing"),
    ("greenhouse gas neutral", False, "PROHIBITED_PER_SE: Cannot claim GHG neutrality via external offsets"),
    ("climate positive", False, "PROHIBITED_PER_SE: Offset-based climate positive claim prohibited"),
    ("eco-safe", True, "Replace with exact REACH/RoHS or test standard ID"),
]


def scan_listing_copy_locally(
    title: str,
    bullet_points: str = "",
    target_market: str = "EU",
    has_iso14024_cert: bool = False,
) -> Dict[str, Any]:
    """Deterministic offline boundary scanner for US Schedule-A TRO wordmarks & EU EmpCo 2024/825 claims."""
    combined = f"{title}\n{bullet_points}"
    market = target_market.upper()
    tro_hits: List[Dict[str, str]] = []
    empco_hits: List[Dict[str, Any]] = []
    sanitized_title = title

    for term, owner, severity, replacement in STEALTH_TRADEMARKS:
        pat = re.compile(rf"(?<!\w){re.escape(term)}(?!\w)", re.IGNORECASE)
        if pat.search(combined):
            tro_hits.append(
                {
                    "matched_mark": term,
                    "owner": owner,
                    "severity": severity,
                    "safe_generic_replacement": replacement,
                }
            )
            sanitized_title = pat.sub(replacement, sanitized_title)

    for phrase, certifiable, guidance in EMPCO_CLAIMS:
        pat = re.compile(rf"(?<!\w){re.escape(phrase)}(?!\w)", re.IGNORECASE)
        if pat.search(combined) and market == "EU":
            if has_iso14024_cert and certifiable:
                continue
            empco_hits.append(
                {
                    "prohibited_phrase": phrase,
                    "directive_citation": "EU EmpCo 2024/825 Annex I",
                    "certifiable_with_iso14024": certifiable,
                    "safe_rewrite_guidance": guidance,
                }
            )
            sanitized_title = pat.sub("", sanitized_title)

    sanitized_title = re.sub(r"\s{2,}", " ", sanitized_title).strip(" -&,")
    safe = len(tro_hits) == 0 and len(empco_hits) == 0
    return {
        "mode": "LOCAL_OFFLINE_DETERMINISTIC_TRIE",
        "target_market": market,
        "has_iso14024_cert": has_iso14024_cert,
        "safe_to_publish": safe,
        "risk_verdict": "SAFE_TO_PUBLISH" if safe else "BLOCK_HIGH_FREEZE_OR_FINE_RISK",
        "tro_stealth_trademarks_hit": tro_hits,
        "eu_empco_violations_hit": empco_hits,
        "auto_sanitized_title": sanitized_title,
    }


def solve_fmc541_demurrage_stopclock(
    billed_days: int = 8,
    daily_rate_usd: float = 325.0,
    days_from_charge_to_invoice: int = 37,
    missing_541_6_fields_count: int = 0,
    verified_gate_or_empty_lockout_days: int = 4,
    billed_party_role: str = "CONSIGNEE",
    port_code: str = "USLAX",
) -> Dict[str, Any]:
    """Deterministic US FMC 46 CFR Part 541 stop-clock & statutory forfeiture calculator."""
    billed_total = round(max(0, billed_days) * daily_rate_usd, 2)
    improper_party = billed_party_role.upper() == "TRUCKER_OR_BROKER_NON_CONTRACTING"
    bar_30day = days_from_charge_to_invoice > 30
    incomplete_541_6 = missing_541_6_fields_count > 0

    defenses: List[str] = []
    if improper_party:
        defenses.append("46 CFR §541.4: Billed party is non-contracting trucker/broker; 100% void.")
    if bar_30day:
        defenses.append(
            f"46 CFR §541.7(a) & §541.8: Issued {days_from_charge_to_invoice}d after last charge (>30d); zero obligation to pay."
        )
    if incomplete_541_6:
        defenses.append(
            f"46 CFR §541.6: Missing {missing_541_6_fields_count} mandatory invoice elements; payment hold applies."
        )
    if verified_gate_or_empty_lockout_days > 0:
        defenses.append(
            f"46 CFR §545.5 / Incentive Principle: {verified_gate_or_empty_lockout_days} terminal lockout days excluded."
        )

    if improper_party or bar_30day or incomplete_541_6:
        chargeable_days = 0
        legally_payable = 0.0
    else:
        chargeable_days = max(0, billed_days - max(0, verified_gate_or_empty_lockout_days))
        legally_payable = round(chargeable_days * daily_rate_usd, 2)

    disputed_waiver = round(max(0.0, billed_total - legally_payable), 2)
    return {
        "mode": "LOCAL_OFFLINE_FMC_46CFR541",
        "port_code": port_code.upper(),
        "billed_total_usd": billed_total,
        "legally_payable_usd": legally_payable,
        "disputed_waiver_usd": disputed_waiver,
        "chargeable_days_after_stopclock": chargeable_days,
        "fmc_46cfr541_flags": {
            "improper_billed_party_541_4": improper_party,
            "fmc_541_7_30day_bar_triggered": bar_30day,
            "fmc_541_6_incomplete_invoice_hold": incomplete_541_6,
            "verified_lockout_days_deducted": verified_gate_or_empty_lockout_days,
        },
        "statutory_defenses": defenses,
    }


def _call_cloud_get(path: str, params: Optional[Dict[str, Any]] = None) -> str:
    headers: Dict[str, str] = {"User-Agent": "A2AMatrixStdioClient/2.0"}
    if PREPAID_BEARER:
        headers["X-Prepaid-Bearer"] = PREPAID_BEARER
    elif X402_PAYMENT:
        headers["X-Payment"] = X402_PAYMENT
    try:
        with httpx.Client(timeout=8.0) as client:
            r = client.get(f"{DEFAULT_CLOUD_URL}{path}", params=params, headers=headers)
            return r.text
    except Exception as exc:
        return json.dumps({"error": "CLOUD_ORACLE_UNREACHABLE", "detail": str(exc)})


def handle_jsonrpc_message(msg: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    method = msg.get("method", "")
    req_id = msg.get("id")

    if req_id is None and method.startswith("notifications/"):
        return None

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": "a2a-matrix-quad-oracle", "version": "2.0.1"},
                "capabilities": {"tools": {}},
            },
        }

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "scan_listing_copy_locally",
                        "description": "Free offline pre-publish guard: scans e-commerce titles & ad copy against 25 US Schedule-A TRO stealth wordmarks and 18 multilingual EU EmpCo (2024/825) greenwashing phrases.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string"},
                                "bullet_points": {"type": "string", "default": ""},
                                "target_market": {"type": "string", "default": "EU"},
                                "has_iso14024_cert": {"type": "boolean", "default": False},
                            },
                            "required": ["title"],
                        },
                    },
                    {
                        "name": "check_fmc541_demurrage_stopclock",
                        "description": "Free offline US FMC 46 CFR Part 541 ocean container demurrage & detention stop-clock and 30-day billing bar forfeiture calculator.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "billed_days": {"type": "integer", "default": 8},
                                "daily_rate_usd": {"type": "number", "default": 325.0},
                                "days_from_charge_to_invoice": {"type": "integer", "default": 37},
                                "missing_541_6_fields_count": {"type": "integer", "default": 0},
                                "verified_gate_or_empty_lockout_days": {"type": "integer", "default": 4},
                                "billed_party_role": {"type": "string", "default": "CONSIGNEE"},
                                "port_code": {"type": "string", "default": "USLAX"},
                            },
                        },
                    },
                    {
                        "name": "benchmark_saas_renewal_quote",
                        "description": "Queries SaaSBench Cloud Oracle for GSA/DIR/G-Cloud unit price floors, commercial P25/P50/P75 percentiles, and anti-AI/MCP surcharge redlines (returns free 402 teaser if unpaid).",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "sku_slug": {"type": "string", "default": "crm-enterprise-plus-ai-agent-addon"},
                                "seat_count": {"type": "integer", "default": 100},
                                "quoted_unit_price_usd": {"type": "number", "default": 145.0},
                            },
                            "required": ["sku_slug"],
                        },
                    },
                    {
                        "name": "verify_ic_section5949_provenance",
                        "description": "Queries SiliconOrigin Cloud Oracle for unstructured PCN/EOL wafer-fab provenance under US NDAA Section 5949 and clean-fab DigiKey drop-in links.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "mpn_slug": {"type": "string", "default": "pmic-buck-regulator-dual-fab-pcn"},
                                "contract_regime": {"type": "string", "default": "US_NDAA_5949"},
                            },
                            "required": ["mpn_slug"],
                        },
                    },
                    {
                        "name": "discover_a2a_matrix_oracles",
                        "description": "Fetches live health, indexed record counts, and x402 discovery metadata from the A2A Data Matrix Quad-Oracle cloud gateway.",
                        "inputSchema": {"type": "object", "properties": {}},
                    },
                ]
            },
        }

    if method == "tools/call":
        params = msg.get("params") or {}
        tool_name = params.get("name")
        args = params.get("arguments") or {}

        if tool_name == "scan_listing_copy_locally":
            res = scan_listing_copy_locally(
                title=str(args.get("title", "")),
                bullet_points=str(args.get("bullet_points", "")),
                target_market=str(args.get("target_market", "EU")),
                has_iso14024_cert=bool(args.get("has_iso14024_cert", False)),
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}}

        if tool_name == "check_fmc541_demurrage_stopclock":
            res = solve_fmc541_demurrage_stopclock(
                billed_days=int(args.get("billed_days", 8)),
                daily_rate_usd=float(args.get("daily_rate_usd", 325.0)),
                days_from_charge_to_invoice=int(args.get("days_from_charge_to_invoice", 37)),
                missing_541_6_fields_count=int(args.get("missing_541_6_fields_count", 0)),
                verified_gate_or_empty_lockout_days=int(args.get("verified_gate_or_empty_lockout_days", 4)),
                billed_party_role=str(args.get("billed_party_role", "CONSIGNEE")),
                port_code=str(args.get("port_code", "USLAX")),
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}}

        if tool_name == "benchmark_saas_renewal_quote":
            txt = _call_cloud_get(
                "/saasbench/api/v1/saasbench/verify",
                {
                    "sku_slug": str(args.get("sku_slug", "crm-enterprise-plus-ai-agent-addon")),
                    "seat_count": int(args.get("seat_count", 100)),
                    "quoted_unit_price_usd": float(args.get("quoted_unit_price_usd", 145.0)),
                },
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": txt}]}}

        if tool_name == "verify_ic_section5949_provenance":
            txt = _call_cloud_get(
                "/siliconorigin/api/v1/silicon/verify",
                {
                    "mpn_slug": str(args.get("mpn_slug", "pmic-buck-regulator-dual-fab-pcn")),
                    "contract_regime": str(args.get("contract_regime", "US_NDAA_5949")),
                },
            )
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": txt}]}}

        if tool_name == "discover_a2a_matrix_oracles":
            txt = _call_cloud_get("/healthz")
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": txt}]}}

        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"}}

    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}}


def main() -> None:
    """Line-delimited JSON-RPC 2.0 stdio MCP entrypoint."""
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
            resp = handle_jsonrpc_message(msg)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except Exception as exc:
            err = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(exc)}}
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
