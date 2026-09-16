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

## Per-repo results

| repo | stars | findings | critical | high | medium |
|---|---|---|---|---|---|
| `onlook-dev/onlook` | 26746 | 67 | 36 | 6 | 25 |
| `imbhargav5/nextbase-nextjs-supabase-starter` | 817 | 13 | 10 | 2 | 1 |
| `moinulmoin/chadnext` | 1324 | 7 | 1 | 3 | 3 |
| `reliverse/relivator` | 1560 | 4 | 0 | 4 | 0 |
| `michaelshimeles/nextjs-starter-kit` | 3052 | 3 | 0 | 2 | 1 |
| `Blazity/next-saas-starter` | 1690 | 3 | 0 | 0 | 3 |
| `olafsulich/fullstack-nextjs-ecommerce` | 844 | 2 | 2 | 0 | 0 |
| `steven-tey/precedent` | 5110 | 1 | 1 | 0 | 0 |
| `theodorusclarence/ts-nextjs-tailwind-starter` | 3417 | 1 | 0 | 1 | 0 |
| `ixartz/Next-JS-Landing-Page-Starter-Template` | 2138 | 0 | 0 | 0 | 0 |
| `NextJSTemplates/startup-nextjs` | 1679 | 0 | 0 | 0 | 0 |
| `agustinusnathaniel/nextarter-chakra` | 838 | 0 | 0 | 0 | 0 |
| `zarazhangrui/frontend-slides` | 29404 | 0 | 0 | 0 | 0 |

## Honest limitations

- Static analysis. It reports *patterns*, and a pattern is a prompt to look, not proof of exploitability. Some flagged routes may be intentionally public.
- The corpus is popular, well-maintained repos — meaning these patterns persist even where maintainers are competent and the code is publicly visible. That is the point: the failure is in the *default* the framework or the generator hands you.
- 'Clean' means 'no findings from these rules', not 'secure'.

Raw per-repo JSON: `results.jsonl`. Reproduce with `python3 scan_corpus.py`.
