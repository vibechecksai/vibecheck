# What 13 popular AI-app starter repos fail on

Measured 2026-09-16 with [vibecheck](https://vibechecksai.github.io/vibecheck/), a deterministic static analyser for the production-failure patterns AI-built apps hit.

## Method

- Corpus: 13 popular open-source starter/app repos (shallow clone, default branch).
- One repo excluded from the per-project numbers: `Anil-matcha/awesome-generative-ai-apps` is a *catalogue* containing many sub-projects, so its counts are not comparable to a single app.
- Scanner: `vibecheck.py` (stdlib-only, deterministic, no network, test/fixture paths skipped by default). Run on the tree as published, unmodified.

## Headline numbers

- **4 of 13 repos scanned clean** (31%).
- **101 findings** across the rest: **50 critical**, 18 high, 33 medium.
- The excluded catalogue repo alone produced 269 further findings, a hint at what accumulates when many small AI-built projects are combined.

## What the failures actually are

| rule | repos affected | what it means |
|---|---|---|
| `route-without-auth` | 6 | An API route with no authentication check — the classic 'I'll add auth later'. |
| `client-exposed-secret` | 5 | A secret-ish variable shipped to the browser bundle via a public prefix. |
| `dangerous-html` | 5 | Untrusted content rendered as raw HTML (XSS surface). |
| `auth-todo` | 1 | A `TODO`/stub standing where an auth check should be. |
| `cors-wildcard` | 1 | `Access-Control-Allow-Origin: *` on an authenticated surface. |
| `hardcoded-secret` | 1 | A real credential literal committed in source. |

## Per-repo results (anonymised)

Projects are anonymised: the counts are static-analysis output and a pattern is a prompt to look, not proof of exploitability. Naming a specific project on unverified counts would be unfair to its maintainers, so the aggregate and rule tables above carry the finding and the raw data stays available for verification.

| project | stars | findings | critical | high | medium |
|---|---|---|---|---|---|
| repo A | 26746 | 67 | 36 | 6 | 25 |
| repo B | 817 | 13 | 10 | 2 | 1 |
| repo C | 1324 | 7 | 1 | 3 | 3 |
| repo D | 1560 | 4 | 0 | 4 | 0 |
| repo E | 3052 | 3 | 0 | 2 | 1 |
| repo F | 1690 | 3 | 0 | 0 | 3 |
| repo G | 844 | 2 | 2 | 0 | 0 |
| repo H | 5110 | 1 | 1 | 0 | 0 |
| repo I | 3417 | 1 | 0 | 1 | 0 |
| repo J | 2138 | 0 | 0 | 0 | 0 |
| repo K | 1679 | 0 | 0 | 0 | 0 |
| repo L | 838 | 0 | 0 | 0 | 0 |
| repo M | 29404 | 0 | 0 | 0 | 0 |

## Honest limitations

- Static analysis. It reports *patterns*, and a pattern is a prompt to look, not proof of exploitability. Some flagged routes may be intentionally public.
- The corpus is popular, well-maintained repos — meaning these patterns persist even where maintainers are competent and the code is publicly visible. That is the point: the failure is in the *default* the framework or the generator hands you.
- 'Clean' means 'no findings from these rules', not 'secure'.

Raw per-repo JSON: `results.jsonl`. Reproduce with `python3 scan_corpus.py`.
