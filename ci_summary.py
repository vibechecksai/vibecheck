#!/usr/bin/env python3
"""Render one vibecheck scan into the CI surface a developer actually reads.

Called by action.yml. Reads the JSON output of `vibecheck.py --json`, prints the
human report to stdout, appends a Markdown block to $GITHUB_STEP_SUMMARY (when
set), and exports finding counts to $GITHUB_OUTPUT (when set).

Deterministic, stdlib only, no network. A missing or unparseable findings file
is reported honestly and never raises: a broken scan must not fail the job for
the wrong reason, and must not be dressed up as a clean scan.
"""
import json
import os
import sys

SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
REPORT_URL = "https://vibechecksai.github.io/vibecheck/REPORT.md"


def load(path, scanner_exit):
    try:
        with open(path, encoding="utf-8") as fh:
            rows = json.load(fh)
    except (OSError, ValueError):
        return None
    if not isinstance(rows, list):
        return None
    return [r for r in rows if isinstance(r, dict)]


def _cell(value):
    return str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")


def main(argv):
    if len(argv) < 2:
        sys.stderr.write("usage: ci_summary.py findings.json [offer_url] [scanner_exit]\n")
        return 2
    path = argv[1]
    offer_url = argv[2] if len(argv) > 2 else ""
    scanner_exit = argv[3] if len(argv) > 3 else "0"

    findings = load(path, scanner_exit)
    if findings is None:
        print("vibecheck: the scan produced no findings JSON (scanner exit %s). "
              "See the log above; treat this as an unknown result, not a clean one." % scanner_exit)
        return 0

    counts = {}
    for f in findings:
        counts[str(f.get("severity") or "low").lower()] = counts.get(str(f.get("severity") or "low").lower(), 0) + 1
    ordered = sorted(
        findings,
        key=lambda r: (SEV_ORDER.get(str(r.get("severity") or "").lower(), 9),
                       str(r.get("file") or ""), int(r.get("line") or 0)),
    )
    summary = ", ".join("%d %s" % (counts[s], s) for s in ("critical", "high", "medium", "low") if s in counts)

    if not findings:
        print("vibecheck: no production-readiness issues found. Ship it (after a human look).")
    else:
        print("vibecheck - %d finding(s): %s\n" % (len(findings), summary))
        for f in ordered:
            loc = "%s:%s" % (f.get("file"), f.get("line")) if f.get("line") else f.get("file")
            print("[%-8s] %-22s %s" % (str(f.get("severity") or "").upper(), f.get("rule") or "", loc))
            print("            %s" % (f.get("message") or ""))
            print("            fix: %s" % (f.get("fix") or ""))

    stepsum = os.environ.get("GITHUB_STEP_SUMMARY")
    # Only a scan that found something earns a step summary: an always-on block
    # in every green run is noise, and noisy actions get uninstalled.
    if stepsum and findings:
        lines = ["## vibecheck", "",
                 "**%d finding(s): %s**" % (len(findings), summary), "",
                 "| severity | rule | location | fix |", "| --- | --- | --- | --- |"]
        for f in ordered:
            loc = "%s:%s" % (f.get("file"), f.get("line")) if f.get("line") else f.get("file")
            lines.append("| %s | `%s` | `%s` | %s |" % (
                _cell(str(f.get("severity") or "").upper()), _cell(f.get("rule")),
                _cell(loc), _cell(f.get("fix"))))
        if offer_url and (counts.get("critical") or counts.get("high")):
            lines += ["",
                      "Every finding above names the exact fix. If you would rather hand the work off: "
                      "criticals fixed for $5, full security pass for $19 -> %s "
                      "(paid in USDC on Base; there is no card checkout yet)." % offer_url]
        lines += ["",
                  "Rules and the measured evidence (101 findings across 13 popular AI-app repos): %s" % REPORT_URL]
        with open(stepsum, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")

    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write("findings=%d\n" % len(findings))
            for s in ("critical", "high", "medium"):
                fh.write("%s=%d\n" % (s, counts.get(s, 0)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
