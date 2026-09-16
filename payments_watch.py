#!/usr/bin/env python3
"""vibecheck payment watcher.

Watches the receive address for incoming USDC on Base and Polygon. On a new
transfer >= the entry price it writes an order file and prints the order id, so
the cron change-detector wakes the vibecheck bot to deliver.

Deterministic, stdlib only, no API key (uses public RPC eth_getLogs).
Idle ticks print IDENTICAL bytes (STABLE:<hash>) so the cron monitor suppresses
the LLM run; only a real payment changes stdout.

Usage: payments_watch.py [--min-usd 19] [--state path] [--dry]
"""
import argparse
import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
VENTURE = pathlib.Path("/Users/carson/Projects/self-funding-agent/ventures/vibecheck")
ORDERS = VENTURE / "orders"
STATE = VENTURE / "data" / "payments_state.json"

TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
RECEIVE_ADDRESS = "0x716D17129a5d41D18D8c51eb118ECb0eDe6B76d5".lower()

CHAINS = {
    "base": {
        "rpc": ["https://mainnet.base.org", "https://base-rpc.publicnode.com"],
        "usdc": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913",
        "decimals": 6,
    },
    "polygon": {
        "rpc": ["https://polygon-rpc.com", "https://polygon-bor-rpc.publicnode.com"],
        "usdc": ["0x3c499c542cef5e3811e1192ce70d8cc03d5c3359",   # native USDC
                 "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"],  # bridged USDC.e
        "decimals": 6,
    },
}
LOOKBACK_BLOCKS = 900  # ~30 min on Base; enough for an idle hourly tick


def rpc(urls, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last = None
    for u in urls:
        try:
            req = urllib.request.Request(u, data=body, headers={
                "Content-Type": "application/json",
                "User-Agent": "vibecheck/1.0 (+https://vibechecksai.github.io/vibecheck/)",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.loads(r.read().decode())
            if "result" in d:
                return d["result"]
            last = d.get("error")
        except Exception as e:  # noqa: BLE001
            last = repr(e)
    raise RuntimeError("rpc failed: %s" % last)


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text())
        except ValueError:
            pass
    return {"chains": {}}


def save_state(st):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(st, indent=2, sort_keys=True))


def scan_chain(name, cfg, st, min_usd):
    latest = int(rpc(cfg["rpc"], "eth_blockNumber", []), 16)
    last = int(st["chains"].get(name, {}).get("block", latest - LOOKBACK_BLOCKS))
    frm = max(last, latest - 5000)
    found = []
    contracts = cfg["usdc"] if isinstance(cfg["usdc"], list) else [cfg["usdc"]]
    for c in contracts:
        logs = rpc(cfg["rpc"], "eth_getLogs", [{
            "address": c, "fromBlock": hex(frm), "toBlock": hex(latest),
            "topics": [TRANSFER_TOPIC, None, "0x" + "0" * 24 + RECEIVE_ADDRESS[2:]],
        }])
        for lg in logs or []:
            try:
                value = int(lg["data"], 16) / (10 ** cfg["decimals"])
                sender = "0x" + lg["topics"][1][-40:]
                tx = lg["transactionHash"]
            except Exception:  # noqa: BLE001
                continue
            if value >= min_usd:
                found.append({"chain": name, "token": c, "usd": round(value, 2),
                              "from": sender, "tx": tx, "block": int(lg["blockNumber"], 16)})
    st.setdefault("chains", {})[name] = {"block": latest}
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-usd", type=float, default=5.0)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    ORDERS.mkdir(parents=True, exist_ok=True)
    st = load_state()
    new_orders = []
    for name, cfg in CHAINS.items():
        try:
            for p in scan_chain(name, cfg, st, args.min_usd):
                oid = p["tx"][:18]
                path = ORDERS / ("%s.json" % oid)
                if path.exists():
                    continue
                order = {"id": oid, "status": "paid", "tier": None,
                         "paid_usd": p["usd"], "payer": p["from"], "tx_hash": p["tx"],
                         "chain": p["chain"], "token": p["token"],
                         "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                         "repo_url": None, "scope": None,
                         "note": "auto-created from on-chain payment; needs repo_url + tier from the customer reply"}
                if not args.dry:
                    path.write_text(json.dumps(order, indent=2))
                new_orders.append(order)
        except Exception as e:  # noqa: BLE001
            sys.stderr.write("scan %s failed: %r\n" % (name, e))
    if not args.dry:
        save_state(st)

    if new_orders:
        for o in new_orders:
            print("ORDER:%s chain=%s usd=%.2f from=%s" % (o["id"], o["chain"], o["paid_usd"], o["payer"]))
    else:
        canon = json.dumps({k: v for k, v in sorted(st.get("chains", {}).items())}, sort_keys=True)
        print("STABLE:%s" % hashlib.sha256(canon.encode()).hexdigest()[:16])
    return 0


if __name__ == "__main__":
    sys.exit(main())
