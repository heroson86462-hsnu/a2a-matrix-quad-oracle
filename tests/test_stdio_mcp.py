import json

from a2a_matrix_quad.stdio_mcp import handle_jsonrpc_message


def test_initialize_and_tools_list():
    init_resp = handle_jsonrpc_message({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    assert init_resp is not None and init_resp["result"]["serverInfo"]["name"] == "a2a-matrix-quad-oracle"

    list_resp = handle_jsonrpc_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
    assert list_resp is not None
    tools = list_resp["result"]["tools"]
    assert len(tools) == 5
    names = {t["name"] for t in tools}
    assert {
        "scan_listing_copy_locally",
        "check_fmc541_demurrage_stopclock",
        "benchmark_saas_renewal_quote",
        "verify_ic_section5949_provenance",
        "discover_a2a_matrix_oracles",
    } == names


def test_scan_listing_copy_locally_catches_tro_and_empco():
    resp = handle_jsonrpc_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "scan_listing_copy_locally",
                "arguments": {
                    "title": "Eco-friendly Velcro baby onesie",
                    "bullet_points": "100% biodegradable",
                    "target_market": "EU",
                    "has_iso14024_cert": False,
                },
            },
        }
    )
    assert resp is not None
    data = json.loads(resp["result"]["content"][0]["text"])
    assert data["safe_to_publish"] is False
    assert len(data["tro_stealth_trademarks_hit"]) >= 2
    assert len(data["eu_empco_violations_hit"]) >= 1
    assert "hook-and-loop strap" in data["auto_sanitized_title"]
    assert "infant bodysuit" in data["auto_sanitized_title"]


def test_check_fmc541_demurrage_stopclock_30_day_bar():
    resp = handle_jsonrpc_message(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "check_fmc541_demurrage_stopclock",
                "arguments": {
                    "billed_days": 8,
                    "daily_rate_usd": 325.0,
                    "days_from_charge_to_invoice": 35,
                    "missing_541_6_fields_count": 0,
                    "verified_gate_or_empty_lockout_days": 2,
                },
            },
        }
    )
    assert resp is not None
    data = json.loads(resp["result"]["content"][0]["text"])
    assert data["legally_payable_usd"] == 0.0
    assert data["disputed_waiver_usd"] == 2600.0
    assert data["fmc_46cfr541_flags"]["fmc_541_7_30day_bar_triggered"] is True
