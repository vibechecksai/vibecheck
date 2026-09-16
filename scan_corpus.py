#!/usr/bin/env python3
"""Scan a corpus of popular AI-built / boilerplate repos with vibecheck and aggregate.

Produces real, measured statistics for a public write-up. Shallow clones only.
Writes: /tmp/vc_scan/results.jsonl (one JSON per repo) and prints a summary.
"""
import json
import os
import subprocess
import sys

REPOS_FILE = "/tmp/vc_scan/repos.json"
WORK = "/tmp/vc_scan/repos"
SCANNER = "/Users/carson/Projects/self-funding-agent/ventures/vibecheck/vibecheck.py"
OUT = "/tmp/vc_scan/results.jsonl"

# Curated: starter templates + AI app repos most representative of "AI-built apps"
WANTED = [
    "steven-tey/precedent", "theodorusclarence/ts-nextjs-tailwind-starter",
    "michaelshimeles/nextjs-starter-kit", "ixartz/Next-JS-Landing-Page-Starter-Template",
    "Blazity/next-saas-starter", "NextJSTemplates/startup-nextjs", "reliverse/relivator",
    "moinulmoin/chadnext", "olafsulich/fullstack-nextjs-ecommerce",
    "agustinusnathaniel/nextarter-chakra", "imbhargav5/nextbase-nextjs-supabase-starter",
    "Anil-matcha/awesome-generative-ai-apps", "onlook-dev/onlook",
    "zarazhangrui/frontend-slides", "theodorusclarence/ts-nextjs-tailwind-starter",
]

os.makedirs(WORK, exist_ok=True)
repos = {r["full_name"]: r for r in json.load(open(REPOS_FILE))}
targets = [r for r in WANTED if r in repos] or list(repos)[:12]

results = []
with open(OUT, "w") as fh:
    for full in targets:
        meta = repos.get(full, {})
        dest = os.path.join(WORK, full.replace("/", "__"))
        if not os.path.isdir(dest):
            try:
                subprocess.run(["git", "clone", "--depth", "1", "--quiet",
                                f"https://github.com/{full}.git", dest],
                               timeout=180, capture_output=True)
            except Exception as e:  # noqa: BLE001
                print(f"clone-fail {full}: {type(e).__name__}", flush=True)
                continue
        if not os.path.isdir(dest):
            print(f"clone-fail {full}", flush=True)
            continue
        try:
            p = subprocess.run([sys.executable, SCANNER, dest, "--json"],
                               capture_output=True, text=True, timeout=180)
            data = json.loads(p.stdout) if p.stdout.strip() else {}
        except Exception as e:  # noqa: BLE001
            print(f"scan-fail {full}: {type(e).__name__}", flush=True)
            continue
        findings = data if isinstance(data, list) else data.get("findings", data.get("results", []))
        sev = {}
        for f in findings:
            s = (f.get("severity") or "unknown").lower()
            sev[s] = sev.get(s, 0) + 1
        rec = {
            "repo": full,
            "stars": meta.get("stars"),
            "lang": meta.get("lang"),
            "total": len(findings),
            "by_severity": sev,
            "rules": sorted({f.get("rule") or f.get("id") or "?" for f in findings}),
        }
        results.append(rec)
        fh.write(json.dumps(rec) + "\n")
        fh.flush()
        print(f"{rec['total']:>3} findings | {full} | {sev}", flush=True)

print("\n=== SUMMARY ===")
print("repos scanned:", len(results))
print("clean:", sum(1 for r in results if r["total"] == 0))
agg = {}
for r in results:
    for k, v in r["by_severity"].items():
        agg[k] = agg.get(k, 0) + v
print("severity totals:", agg)
rule_counts = {}
for r in results:
    for rule in r["rules"]:
        rule_counts[rule] = rule_counts.get(rule, 0) + 1
print("top rules (repos affected):", sorted(rule_counts.items(), key=lambda x: -x[1])[:12])
