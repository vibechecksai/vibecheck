#!/usr/bin/env python3
"""vibecheck — find the production failures in AI-built ("vibe-coded") apps.

AI builders get an app 70-80% done; the last 20-30% that survives real users is
where it breaks: hardcoded secrets, API routes with no auth, SQL injection,
disabled TLS, wildcard CORS, secrets shipped to the browser, no input
validation. vibecheck scans a project and reports those specific defects with a
file:line, a severity, and a one-line fix.

Zero dependencies. Stdlib only. Deterministic.

Usage:
    python3 vibecheck.py [PATH] [--json] [--fail-on critical|high|none]

Exit codes: 0 = no findings at/above the fail threshold, 1 = findings, 2 = error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict

# Files/dirs we never scan.
SKIP_DIRS = {".git", "node_modules", ".next", "dist", "build", "venv", ".venv",
             "__pycache__", ".turbo", "coverage", ".cache", "vendor"}
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip",
            ".gz", ".mp4", ".mp3", ".woff", ".woff2", ".ttf", ".lock", ".map",
            ".min.js", ".svg"}
SRC_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".py", ".rb", ".go",
           ".php", ".java", ".env", ".yaml", ".yml", ".json", ".txt", ".sh",
           ".toml", ".ini", ".config", ""}
MAX_BYTES = 2_000_000

# Test/fixture paths are skipped by default: planted "secrets" and example URLs in
# tests are not real leaks, and flagging them is the fastest way to lose a user's
# trust. Opt back in with --include-tests.
TEST_RE = re.compile(
    r"(^|/)(tests?|spec|specs|__tests__|testdata|fixtures?|mocks?|examples?)(/|$)"
    r"|\.(test|spec)\.[A-Za-z0-9]+$|(^|/)test_|_test\.(py|go|rb)$")
INCLUDE_TESTS = False

SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


@dataclass
class Finding:
    rule: str
    severity: str
    file: str
    line: int
    message: str
    fix: str


def _iter_files(root: str):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in SKIP_EXT:
                continue
            if ext not in SRC_EXT:
                continue
            p = os.path.join(dirpath, fn)
            try:
                if os.path.getsize(p) > MAX_BYTES:
                    continue
            except OSError:
                continue
            yield p


# --- rule definitions: (rule, severity, regex, message, fix) -----------------
LINE_RULES = [
    ("hardcoded-secret", "critical",
     re.compile(r"(?i)\b(api[_-]?key|apikey|secret|token|passwd|password|private[_-]?key|access[_-]?key)\b"
                r"\s*[:=]\s*['\"][A-Za-z0-9_\-/+.]{16,}['\"]"),
     "Hardcoded credential/secret literal in source.",
     "Move to an environment variable / secret manager; rotate the exposed value."),
    ("aws-access-key", "critical",
     re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b"),
     "Looks like an AWS access key id committed in source.",
     "Remove, rotate the key, and load from the environment."),
    ("private-key-block", "critical",
     re.compile(r"-----BEGIN (RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
     "A private key is embedded in the repo.",
     "Remove immediately and rotate; never commit private keys."),
    ("conn-string-credentials", "critical",
     re.compile(r"(?i)\b[a-z][a-z0-9+.\-]*://[^/\s:@]+:[^/\s:@]+@"),
     "Connection string contains inline user:password credentials.",
     "Use env vars for DB credentials; rotate the exposed password."),
    ("client-exposed-secret", "critical",
     re.compile(r"(NEXT_PUBLIC_|VITE_|REACT_APP_|PUBLIC_)[A-Z0-9_]*"
                r"(SECRET|TOKEN|KEY|PASSWORD|PRIVATE)[A-Z0-9_]*"),
     "A secret-looking var is exposed to the browser bundle (public prefix).",
     "Rename without the public prefix and proxy the call server-side."),
    ("sql-string-concat", "high",
     re.compile(r"(?i)(execute|query|raw|prepare)\s*\(\s*(['\"`]|f['\"])"
                r".*(SELECT|INSERT|UPDATE|DELETE).*(\+|%|\{|\$\{)"),
     "SQL built by string concatenation/interpolation (injection risk).",
     "Use parameterized queries / bound placeholders."),
    ("tls-verification-off", "high",
     re.compile(r"(?i)(verify\s*=\s*False|rejectUnauthorized\s*:\s*false|"
                r"strictSSL\s*:\s*false|NODE_TLS_REJECT_UNAUTHORIZED\s*[:=]\s*['\"]?0)"),
     "TLS certificate verification is disabled.",
     "Re-enable verification; if a self-signed cert is needed, pin the CA."),
    ("cors-wildcard", "medium",
     re.compile(r"(?i)Access-Control-Allow-Origin['\"]?\s*[:=]\s*['\"]\*['\"]"),
     "CORS allows any origin (with credentials this is a data-exfil hole).",
     "Restrict to an explicit allowlist of origins."),
    ("eval-exec", "high",
     re.compile(r"(?<![\w.])(eval|exec)\s*\("),
     "Dynamic code execution (eval/exec) — common RCE vector.",
     "Replace with a safe parser; never eval untrusted input."),
    ("debug-console-secret", "medium",
     re.compile(r"(?i)(console\.(log|debug)|print)\s*\([^)]*"
                r"(secret|token|password|api[_-]?key|authorization)"),
     "Logging a secret value to console/stdout.",
     "Remove the log or redact the value."),
    ("dangerous-html", "medium",
     re.compile(r"dangerouslySetInnerHTML|v-html\s*="),
     "Unsanitized raw HTML injection point.",
     "Sanitize the HTML (e.g. DOMPurify) or render as text."),
    ("auth-todo", "high",
     re.compile(r"(?i)(TODO|FIXME|HACK|XXX).{0,40}\b(auth|login|permission|"
                r"authoriz|payment|billing|admin|role)"),
     "An unimplemented TODO/FIXME sits on an auth/payment path.",
     "Resolve before shipping; this is exactly the 20% that breaks in prod."),
    ("insecure-cookie", "medium",
     re.compile(r"(?i)httpOnly\s*:\s*false|secure\s*:\s*false|SameSite\s*[:=]\s*['\"]?None"),
     "Auth cookie is missing HttpOnly/Secure or set to SameSite=None.",
     "Set HttpOnly, Secure, and SameSite=Lax/Strict."),
]

# Auth-ish markers that mean 'this route is guarded'.
AUTH_MARKERS = re.compile(
    r"(?i)\b(getServerSession|getSession|requireAuth|requireUser|isAuthenticated|"
    r"auth\s*\(|verifyToken|jwt\.verify|checkAuth|withAuth|authenticate|"
    r"@login_required|@requires_auth|CurrentUser|Depends\s*\(\s*get_current_user)")
# Files that look like server route handlers. Must be an actual route shape:
# Next.js "export async function GET", a framework decorator (@app/@router.route),
# or Express-style app.get('/path'). A plain "def get(...)" is NOT a route.
ROUTE_MARKER = re.compile(
    r"(?i)(export\s+(async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE)\b"
    r"|@(app|router|api|bp|blueprint|server)\.(get|post|put|patch|delete|route)\b"
    r"|(app|router|server)\.(get|post|put|patch|delete)\s*\(\s*['\"`]/)")


_PLACEHOLDER_USERS = re.compile(
    r"(?i)(user|username|test|foo|bar|your[a-z_]*|changeme|"
    r"password|pass|secret|token|xxx+|name|email|login)")
_PLACEHOLDER_PW = re.compile(
    r"(?i)(pass|password|secret|token|changeme|xxx+|redacted|pwd|placeholder|admin|root|user|test)")
_EXAMPLE_HOSTS = ("example.", "localhost", "127.0.0.1", "0.0.0.0", ".test",
                  ".invalid", ".example")


def _placeholder_conn_string(line: str) -> bool:
    """True when a user:pass@host URL is a placeholder/example, not a real leak."""
    m = re.search(r"://([^/\s:@'\"]+):([^/\s:@'\"]+)@([^/\s:'\"/]+)", line)
    if not m:
        return True
    user, pw, host = m.group(1), m.group(2), m.group(3).lower()
    if any(h in host for h in _EXAMPLE_HOSTS):
        return True
    if _PLACEHOLDER_USERS.fullmatch(user) or _PLACEHOLDER_PW.fullmatch(pw):
        return True
    return False


def scan_file(path: str, root: str):
    rel = os.path.relpath(path, root)
    if not INCLUDE_TESTS and TEST_RE.search(rel):
        return []
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return []
    findings = []
    lines = text.splitlines()
    for rule, sev, rx, msg, fix in LINE_RULES:
        for i, ln in enumerate(lines, 1):
            if rx.search(ln):
                if rule == "conn-string-credentials" and _placeholder_conn_string(ln):
                    continue
                findings.append(Finding(rule, sev, rel, i, msg, fix))
    # route-without-auth heuristic (per file)
    if ROUTE_MARKER.search(text) and not AUTH_MARKERS.search(text):
        for i, ln in enumerate(lines, 1):
            if ROUTE_MARKER.search(ln):
                findings.append(Finding(
                    "route-without-auth", "high", rel, i,
                    "A route handler file has no visible auth/session check.",
                    "Add an auth guard at the top of every mutating route."))
                break
    return findings


def check_env_hygiene(root: str):
    findings = []
    env = os.path.join(root, ".env")
    gi = os.path.join(root, ".gitignore")
    if os.path.isfile(env):
        ignored = False
        if os.path.isfile(gi):
            try:
                ignored = any(l.strip().rstrip("/") in (".env", ".env*", "*.env")
                              for l in open(gi, encoding="utf-8", errors="replace"))
            except OSError:
                pass
        if not ignored:
            findings.append(Finding(
                "env-not-ignored", "critical", ".env", 0,
                "A .env file exists but is not listed in .gitignore.",
                "Add '.env' to .gitignore and confirm it was never committed."))
    return findings


def run(root: str):
    all_findings = []
    for p in _iter_files(root):
        all_findings.extend(scan_file(p, root))
    all_findings.extend(check_env_hygiene(root))
    all_findings.sort(key=lambda f: (SEV_ORDER.get(f.severity, 9), f.file, f.line))
    return all_findings


def main(argv=None):
    ap = argparse.ArgumentParser(prog="vibecheck", description=__doc__)
    ap.add_argument("path", nargs="?", default=".")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--include-tests", action="store_true",
                    help="also scan test/fixture files (off by default)")
    ap.add_argument("--fail-on", choices=["critical", "high", "medium", "none"],
                    default="critical")
    args = ap.parse_args(argv)
    global INCLUDE_TESTS
    INCLUDE_TESTS = args.include_tests

    if not os.path.isdir(args.path):
        sys.stderr.write("not a directory: %s\n" % args.path)
        return 2

    findings = run(args.path)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        if not findings:
            print("vibecheck: no production-readiness issues found. Ship it (after a human look).")
        else:
            by_sev = {}
            for f in findings:
                by_sev.setdefault(f.severity, 0)
                by_sev[f.severity] += 1
            summary = ", ".join("%d %s" % (by_sev[s], s)
                                for s in ("critical", "high", "medium", "low")
                                if s in by_sev)
            print("vibecheck — %d finding(s): %s\n" % (len(findings), summary))
            for f in findings:
                loc = "%s:%d" % (f.file, f.line) if f.line else f.file
                print("[%-8s] %-22s %s" % (f.severity.upper(), f.rule, loc))
                print("            %s" % f.message)
                print("            fix: %s" % f.fix)
    if args.fail_on == "none":
        return 0
    floor = SEV_ORDER[args.fail_on]
    return 1 if any(SEV_ORDER.get(f.severity, 9) <= floor for f in findings) else 0


if __name__ == "__main__":
    raise SystemExit(main())
