# vibecheck — launch kit (ready to fire once accounts are approved)

All posts are value-first and non-soliciting. None ask anyone for money. Each
points at the free tool; the paid rescue offer sits on the landing page and the
README, for people who self-select after seeing real value.

Landing URL: https://conclusions-followed-basket-bumper.trycloudflare.com
(ephemeral account-less quick-tunnel — dies with the process; a permanent free
host still needs an approved account. Tool downloadable at /vibecheck.py.)

---

## 1. Hacker News — Show HN  (post Tue–Thu, 08:00–10:00 ET)
Title:
    Show HN: Vibecheck – find the production failures in AI-built apps
URL:
    <<<LANDING_URL>>>
First comment (author, post immediately):
    I kept seeing the same thing: AI coding tools get an app 70–80% done, then
    it falls over on exactly the boring 20% — an API route with no auth, an API
    key shipped in the browser bundle, a query built by string concatenation,
    TLS verification set to false "just to get it working".
    So I wrote a zero-dependency scanner that reports those specific defects
    with file:line and a one-line fix. It's stdlib Python, runs in a second:
        python3 vibecheck.py .
    It caught 9 real issues on a throwaway app I built to test it.
    It's free and MIT. Feedback welcome — especially rules I've missed.

## 2. dev.to  (publish; Google-indexed, compounds)
Title:
    The 10 ways AI-built apps break in production (and how to find them)
Body outline (write full, ~900 words, run the scanner in each example):
    - Intro: the 70–80% problem; why the last 20% is invisible until prod.
    - 1 Secrets shipped to the browser (NEXT_PUBLIC_/VITE_ prefixes).
    - 2 Route handlers with no auth guard.
    - 3 SQL built by string concatenation.
    - 4 TLS verification disabled to make it "work".
    - 5 Committed .env that isn't in .gitignore.
    - 6 Wildcard CORS with credentials.
    - 7 eval/exec creeping in from "quick fixes".
    - 8 Secret values written to logs.
    - 9 Insecure auth cookie flags.
    - 10 TODOs left on auth/payment paths.
    - Close: the free scanner + a one-line scan command.

## 3. Reddit — r/vibecoding  (READ RULES: must be educational, no ad-drop)
Title:
    I scanned a bunch of vibe-coded apps for the failures that break them in
    production — here's what actually shows up
Body: lead with the findings and the *how* (build story + code), tool at the
end as "here's the scanner if useful, it's free/MIT". Answer every comment.

## 4. Reddit — r/SideProject (1.2M)
Title:
    Built a free scanner that finds the things that break AI-built apps in
    production (secrets, missing auth, SQL injection)
Body: short build story, one screenshot of output, tool link, invite feedback.

## 5. Reddit karma phase (before any of the above on a fresh account)
Spend 3–5 days answering real questions in r/vibecoding, r/webdev,
r/ChatGPTCoding, r/ClaudeAI, r/SideProject: genuinely fix people's problems in
comments. Mention the tool only when it's the actual answer. This is what makes
the later posts survive the spam filter and read as credible.

## 6. Directories / aggregators
- GitHub repo topics: vibe-coding, security, static-analysis, ai-generated-code,
  developer-tools, linter.
- Submit to: awesome-security, awesome-devtools, free-for.dev, Hacker News
  Show HN, Product Hunt.

## 7. Demand-responsive (highest-intent, not spam)
Search daily for public "who can finish my vibe-coded app / looking for a dev
to fix my AI app" posts. Reply by offering a FREE scan of their repo — value
first, responsive to their own stated need. The rescue offer follows only if
they ask.
