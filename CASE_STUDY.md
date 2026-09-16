# Case study: 9 findings → 0 on an AI-built app

This is a real before/after, run end to end with the tool in this repo. The app
is a representative "vibe-coded" project: a Next.js-style API route, a payments
module, and a client module.

## Before

```text
$ python3 vibecheck.py .
vibecheck — 9 findings: 3 critical, 4 high, 2 medium

[CRITICAL] env-not-ignored          .env
[CRITICAL] conn-string-credentials  .env:2
[CRITICAL] client-exposed-secret    lib/client.ts:1
[HIGH    ] route-without-auth       app/api/users/route.ts:1
[HIGH    ] auth-todo                lib/payments.ts:1
[HIGH    ] tls-verification-off     lib/payments.ts:3
[HIGH    ] eval-exec                lib/payments.ts:4
[MEDIUM  ] cors-wildcard            lib/client.ts:2
[MEDIUM  ] debug-console-secret     lib/payments.ts:5
```

## The fixes

**1. Unauthenticated route + SQL injection** (`app/api/users/route.ts`)

```ts
// before
export async function POST(req) {
  const body = await req.json();
  const q = "INSERT INTO users (email) VALUES ('" + body.email + "')";
  await db.query(q);
  return Response.json({ ok: true });
}

// after
export async function POST(req) {
  const session = await getServerSession();
  if (!session?.user) return new Response("Unauthorized", { status: 401 });
  const { email } = await req.json();
  if (typeof email !== "string" || !email.includes("@"))
    return Response.json({ error: "invalid email" }, { status: 400 });
  await db.query("INSERT INTO users (email) VALUES ($1)", [email]);
  return Response.json({ ok: true });
}
```

**2. Secret in the browser bundle + wildcard CORS** (`lib/client.ts`) — the key
moved server-side behind an API route; CORS restricted to an allowlist.

**3. Key in source, TLS off, `eval`, secret logging** (`lib/payments.ts`) — the
key now comes from the environment, TLS verification stays on, `eval` is gone,
and the secret is no longer logged.

**4. `.env` hygiene** — `.env` added to `.gitignore`; the connection string no
longer embeds `user:password` inline (credentials are separate runtime vars).

## After

```text
$ python3 vibecheck.py .
vibecheck: no production-readiness issues found. Ship it (after a human look).

$ echo $?
0
```

**Result: 9 findings (3 critical, 4 high) → 0.**

---

This is the work sold as the **Security & production pass** ($150): secrets
rotated and moved out of source, auth on every mutating route, parameterized
queries, TLS and CORS corrected, cookie flags fixed, and a re-scan proving zero
critical/high remain. Backed by a guarantee: if any critical or high finding
remains in the agreed scope, you don't pay.
