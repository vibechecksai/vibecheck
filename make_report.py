#!/usr/bin/env python3
"""Turn the corpus scan results into an honest, publishable report.

Writes REPORT.md into the vibecheck venture dir and prints the key stats.
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
results = [json.loads(l) for l in open("/tmp/vc_scan/results.jsonl") if l.strip()]
# dedupe by repo (the corpus list can contain repeats)
_seen = {}
for r in results:
    _seen[r["repo"]] = r
results = list(_seen.values())

# An aggregation repo contains many sub-projects -> not comparable per-project.
AGGS = {"Anil-matcha/awesome-generative-ai-apps"}

per = [r for r in results if r["repo"] not in AGGS]
agg = [r for r in results if r["repo"] in AGGS]


def totals(rows):
    t = {"critical": 0, "high": 0, "medium": 0}
    for r in rows:
        for k, v in r["by_severity"].items():
            t[k] = t.get(k, 0) + v
    return t


tp, ta = totals(per), totals(agg)
clean = sum(1 for r in per if r["total"] == 0)

rule_counts = {}
for r in per:
    for rule in r["rules"]:
        rule_counts[rule] = rule_counts.get(rule, 0) + 1
top_rules = sorted(rule_counts.items(), key=lambda x: -x[1])

lines = []
lines.append(f"# What {len(per)} popular AI-app starter repos fail on\n")
lines.append(f"Measured {os.environ.get('SCAN_DATE', '')} with "
             "[vibecheck](https://vibechecksai.github.io/vibecheck/), a deterministic "
             "static analyser for the production-failure patterns AI-built apps hit.\n")
lines.append("## Method\n")
lines.append(f"- Corpus: {len(per)} popular open-source starter/app repos (shallow clone, default branch).")
lines.append("- One repo excluded from the per-project numbers: "
             "`Anil-matcha/awesome-generative-ai-apps` is a *catalogue* containing many "
             "sub-projects, so its counts are not comparable to a single app.")
lines.append(f"- Scanner: `vibecheck.py` (stdlib-only, deterministic, no network, test/fixture "
             f"paths skipped by default). Run on the tree as published, unmodified.\n")
lines.append("## Headline numbers\n")
lines.append(f"- **{clean} of {len(per)} repos scanned clean** "
             f"({round(100 * clean / len(per))}%).")
lines.append(f"- **{tp['critical'] + tp['high'] + tp['medium']} findings** across the rest: "
             f"**{tp['critical']} critical**, {tp['high']} high, {tp['medium']} medium.")
lines.append(f"- The excluded catalogue repo alone produced {ta['critical'] + ta['high'] + ta['medium']} "
             f"further findings, a hint at what accumulates when many small AI-built projects "
             f"are combined.\n")
lines.append("## What the failures actually are\n")
lines.append("| rule | repos affected | what it means |")
lines.append("|---|---|---|")
DESC = {
    "route-without-auth": "An API route with no authentication check — the classic 'I'll add auth later'.",
    "client-exposed-secret": "A secret-ish variable shipped to the browser bundle via a public prefix.",
    "dangerous-html": "Untrusted content rendered as raw HTML (XSS surface).",
    "hardcoded-secret": "A real credential literal committed in source.",
    "auth-todo": "A `TODO`/stub standing where an auth check should be.",
    "debug-console-secret": "A secret logged to the console.",
    "insecure-cookie": "Session cookie without `httpOnly`/`secure`.",
    "provider-key-literal": "A third-party provider key inline in code.",
    "cors-wildcard": "`Access-Control-Allow-Origin: *` on an authenticated surface.",
}
for rule, n in top_rules:
    lines.append(f"| `{rule}` | {n} | {DESC.get(rule, '')} |")
lines.append("")
lines.append("## Per-repo results\n")
lines.append("| repo | stars | findings | critical | high | medium |")
lines.append("|---|---|---|---|---|---|")
for r in sorted(per, key=lambda x: -x["total"]):
    s = r["by_severity"]
    lines.append(f"| `{r['repo']}` | {r['stars']} | {r['total']} | {s.get('critical',0)} | "
                 f"{s.get('high',0)} | {s.get('medium',0)} |")
lines.append("")
lines.append("## Honest limitations\n")
lines.append("- Static analysis. It reports *patterns*, and a pattern is a prompt to look, "
             "not proof of exploitability. Some flagged routes may be intentionally public.")
lines.append("- The corpus is popular, well-maintained repos — meaning these patterns persist "
             "even where maintainers are competent and the code is publicly visible. That is the "
             "point: the failure is in the *default* the framework or the generator hands you.")
lines.append("- 'Clean' means 'no findings from these rules', not 'secure'.\n")
lines.append("Raw per-repo JSON: `results.jsonl`. Reproduce with `python3 scan_corpus.py`.\n")

out = os.path.join(ROOT, "REPORT.md")
open(out, "w").write("\n".join(lines))
print("\n".join(lines[:40]))
print("\n...wrote", out, f"({len(open(out).read())} chars)")
print("\nSTATS:", {"per_project": tp, "clean": clean, "of": len(per), "top_rules": top_rules[:5]})
