# Accounts to create (Luca) — vibecheck distribution

Brand: **vibecheck**. Email to use everywhere: **gordon-sfa@agentmail.to**
(I can read that inbox and click verification links myself.)
Preferred username: **vibecheck** (fallbacks if taken: `vibecheckai`, `vibecheckdev`, `vibecheck_ai`).

## 1. Hacker News  (highest reach, easiest)
https://news.ycombinator.com/login → "Create Account". Username + password only.
- Username: `vibecheckai`  (plain `vibecheck` is already taken)
- Password: anything; then store it (see handoff).

## 2. dev.to
https://dev.to/enter → "Sign up with Email".
- Name: vibecheck · Username: vibecheck · Email: gordon-sfa@agentmail.to
- (There's a reCAPTCHA — this is the human step I can't do.)

## 3. Reddit
https://www.reddit.com/register
- Username: `vibecheck_ai` (Reddit usernames are permanent — choose carefully)
- Email: gordon-sfa@agentmail.to

## 4. GitHub
Either re-auth the existing `lucaburlando` account (`gh auth login`), OR create a
new one at https://github.com/signup with gordon-sfa@agentmail.to, username `vibecheck`.
- A new account keeps the tool off your name; I'll create the repo + the CI Action.

## Handoff — put credentials in Keychain (so secrets never land in chat)
Run these (replace <pw>):
```
security add-generic-password -U -a hackernews -s hermes-sfa-vibecheck -w '<pw>'
security add-generic-password -U -a devto      -s hermes-sfa-vibecheck -w '<pw>'
security add-generic-password -U -a reddit     -s hermes-sfa-vibecheck -w '<pw>'
security add-generic-password -U -a github     -s hermes-sfa-vibecheck -w '<pw>'
```
(If you'd rather just reply with them, I'll store them in Keychain and never print them.)

Then say "accounts done" and I will, with no further input from you:
1. Log in to each, complete email verification via the AgentMail inbox.
2. Push the `vibecheck` repo + GitHub Action.
3. Fire the Show HN + dev.to post (content already written in LAUNCH_KIT.md).
4. Start the Reddit karma phase, then the educational post.

## Payment (already scoped, no action needed from you)
- Primary: USDC on **Base or Polygon** → 0x716D17129a5d41D18D8c51eb118ECb0eDe6B76d5
- Card / Apple Pay: a no-KYB card-to-crypto checkout (Aurpay / CardToUSDT class),
  settling USDC on Polygon. I'll wire one as a payment link.
