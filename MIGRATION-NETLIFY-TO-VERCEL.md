# OUTCOME — cutover completed 2026-08-21

patrolgarage.ae is live on Vercel. Parity against
`URL-BASELINE-PRE-MIGRATION.json`: **0 unexpected mismatches** across 109 URLs,
7 intended (the split-canonical fix, `200` -> `301`), 2 baseline probe artefacts.

Everything below the horizontal rule is the original plan, kept as written. This
section records what actually happened, including four things the plan got
wrong. **Read this before migrating topchallenger.ae.**

---

## Trap 1 — there were no A records to change

The plan, and the instructions built on it, said "change the A records". There
were none. Netlify DNS stored:

```
patrolgarage.ae      NETLIFY  beautiful-cuchufli-e12a90.netlify.app  managed=True
www.patrolgarage.ae  NETLIFY  beautiful-cuchufli-e12a90.netlify.app  managed=True
```

`NETLIFY` is a proprietary record type. `dig` shows A records because ns1
**synthesises** them at query time; nothing of type A is stored in the zone. A
`dig`-based capture therefore records values that do not exist as records.

Consequences:

* "Same record type in, same type out" is impossible. `NETLIFY` records cannot
  point anywhere but Netlify, so the cutover is necessarily delete-then-create.
* Rollback is **not** "restore the A records". It is either recreate the
  `NETLIFY` records, or create A records to the synthesised IPs
  (`35.157.26.135`, `63.176.8.218`) captured in `DNS-PRE-CUTOVER.txt`.

**Check the zone through the DNS provider's API before writing a cutover plan.**
`dig` alone cannot tell you what is stored.

## Trap 2 — delete-before-create took the site down for ~90 seconds

The two `NETLIFY` records were deleted first, then four A records were created
in a shell loop using `set -- $pair`. The split did not happen, so every POST
went out with a blank `value` and returned `422`. Between the deletes and the
fix the domain had no apex or `www` record at all.

Recovered in about 90 seconds by creating the records with explicit arguments.

**Create the new records first where the provider allows it, or at minimum
verify the create call succeeds against one record before deleting anything.**
Never run a delete and an untested create in the same block. Do not use shell
word-splitting for values that must not be empty — build the calls explicitly,
or assert non-empty before sending.

## Trap 3 — the TLS certificate cannot exist before DNS moves

Vercel will not pre-issue:

```
POST /v3/certs {"cns":["patrolgarage.ae","www.patrolgarage.ae"]}
HTTP 449  http_pretest_domain_not_resolving_to_vercel_error
```

The dependency is circular — verifying Vercel serves the domain needs TLS, TLS
needs a certificate, the certificate needs DNS already pointing at Vercel. Any
plan with a "confirm TLS before cutover" gate is unsatisfiable.

What this means in practice: **there is an unavoidable unverified window.**
Budget for it, arm the rollback, and keep TTL low. Here the certificate issued
**195 seconds** after DNS propagated. Poll for 5 minutes before deciding it has
failed.

Related: `GET /v6/domains/{d}/config` returns `aValues` describing the domain's
**currently observed** A records, not Vercel's targets. Reading that field as
"what Vercel wants" sent an entire verification round at Netlify's own IPs
(`13.52.188.95`, `52.52.192.191` — both `server: Netlify`) and produced a false
pass. The target values are under `recommendedIPv4`:

```
rank 1: 216.198.79.1, 64.29.17.1      <- use these
rank 2: 76.76.21.21                    <- legacy, did not respond at all
```

**Always confirm an edge is the right one with `x-vercel-id` in the response
headers.** A `200` and a valid certificate prove nothing about which platform
answered.

## Trap 4 — the .vercel.app production alias cannot be SSO-gated

`ssoProtection: {"deploymentType": "all_except_custom_domains"}` exempts
**production** domains, and the project alias `patrolgarage.vercel.app` is one.
It stays publicly reachable. Tightening SSO to cover it also gates the real
custom domain and takes the live site down.

Solution used: a `has[host]` redirect in `vercel.json` sending
`patrolgarage.vercel.app` to `https://patrolgarage.ae` with a `308`. The alias
stays reachable but serves nothing of its own, which removes the duplicate copy.
Deployment-specific preview URLs are deliberately **not** matched — they are
already SSO-gated (`302`), and redirecting them would make every future preview
bounce to production and become untestable.

A `noindex` header via `has[host]` on `^.*\.vercel\.app$` is also in place as
defence in depth.

## Other things worth carrying over

* **`permanent: true` emits 308, not 301.** Use `"statusCode": 301` if parity
  against a Netlify baseline is the acceptance test.
* **`trailingSlash` must be omitted, not set false.** `false` strips the slash
  from directory canonicals (`/`, `/blog/`, `/blog/page/2/`) and breaks them.
* **Netlify's `!` force flag needs no equivalent.** Vercel evaluates `redirects`
  before the filesystem, so forcing is implicit.
* **`.vercelignore` is load-bearing.** `requirements.txt` at the repo root makes
  Vercel auto-detect Python, build a serverless function, find no entrypoint and
  502 every page.
* **Large uploads need `--archive=tgz`.** The plain file upload failed twice with
  an SSL error on a 52 MB images directory.
* **Baseline probes need retries.** Two of 109 URLs timed out during capture and
  again during verification, producing "mismatches" that were pure measurement
  noise. The first parity run said FAIL; hand-verification showed both were
  correct. Retry transient failures rather than recording a false `None`, and
  verify before acting on a revert trigger.

## Final state

```
patrolgarage.ae      A  216.198.79.1, 64.29.17.1   ttl=120   server: Vercel
www.patrolgarage.ae  A  216.198.79.1, 64.29.17.1   ttl=120   301 -> apex
nameservers          dns1-4.p07.nsone.net (Netlify DNS, unchanged)
TXT google-site-verification preserved
```

Netlify site `beautiful-cuchufli-e12a90` is **still live**, state `current`,
deploy permalinks returning `200`. **Do not delete before 2026-09-20** — those
permalinks have twice been the only surviving copy of lost posts and hero images.

Rollback: create A records to `35.157.26.135` and `63.176.8.218`. TTL 120s, so
roughly two minutes. The pipeline rolls back separately via `DEPLOY_TARGET=netlify`,
which needs no rebuild because both CLIs are in the image.

---

# patrolgarage.ae — Netlify to Vercel migration plan

Written 2026-08-21. **Plan only. Nothing was changed and nothing was deployed.**

Two files were written, both read-only artefacts:
`URL-BASELINE-PRE-MIGRATION.json` (step 1) and this document.

---

## Headline

Three things you need to know before anything else:

1. **`cleanUrls: false` alone does NOT reproduce current behaviour.** It is the
   right base, but 10 URLs that serve `200` today would become `404`. Detail in
   §3.
2. **Netlify runs your DNS**, not just your hosting. The nameservers are NS1
   (`dns1-4.p07.nsone.net`) and the SOA contact is `domains+netlify.netlify.com`.
   That is good news for rollback — see §6 — but it means Netlify cannot be fully
   decommissioned at cutover.
3. **The contact form is a Netlify Forms integration.** Vercel has no
   equivalent. This is a functional loss, not a config translation. §4.

---

## 1. Baseline captured

`URL-BASELINE-PRE-MIGRATION.json`

- 56 URLs in `sitemap.xml`, 56 HTML files in the repo — the two sets match exactly
- **109 URLs probed**: every canonical URL plus its opposite form
  (`.html` ↔ extensionless)
- Per URL: status code (no-follow), `Location` header, final URL after redirects,
  final status, `<link rel="canonical">`, `og:url`, and which form it is

One URL timed out on first pass
(`blog/nissan-patrol-y62-starter-motor-replacement-cost-uae-2026.html`) and
returned `200` in 0.92 s on re-probe. Transient, not a defect.

---

## 2. How Netlify actually serves this today

Measured, not inferred from the repo.

### `.html` form — 53 URLs

| status | count |
|---|---|
| `200` | 52 |
| timeout, `200` on retry | 1 |

Every `.html` URL serves directly. This is the canonical form.

### Extensionless form — 56 URLs

| status | count | behaviour |
|---|---|---|
| `301` → `.html` | **46** | explicit rule in `_redirects` |
| `200` | **10** | **serves content directly — a live duplicate** |

**This is the finding that matters.** The extensionless form is not handled
uniformly. `scripts/gen_redirects.py` only reads `blog/*.html`, so blog posts get
an explicit `301!` and everything else falls through to Netlify's implicit
extension-less resolution and serves `200`.

### The 10 that serve 200

Three are legitimate directory-style URLs resolving `index.html`, with
self-referencing canonicals. Correct, and they behave the same on Vercel:

```
/                    canonical -> /                    SELF
/blog/               canonical -> /blog/               SELF
/blog/page/2/        canonical -> /blog/page/2/        SELF
```

**Seven are live duplicates with a cross-canonical:**

```
/about                                    canonical -> /about.html
/contact                                  canonical -> /contact.html
/services                                 canonical -> /services.html
/services/nissan-patrol-v8-engine         canonical -> /services/nissan-patrol-v8-engine.html
/services/y62-gearbox-transmission-dubai  canonical -> /services/y62-gearbox-transmission-dubai.html
/services/y62-major-service-dubai         canonical -> /services/y62-major-service-dubai.html
/y62-garage-dubai                         canonical -> /y62-garage-dubai.html
```

Each serves a full `200` page whose canonical points somewhere else. This is
precisely the "Alternate page with proper canonical" condition described in
`netlify.toml` — the one that split impressions across 13 blog posts in August.
It was fixed for `/blog/*` and never fixed for the root and `/services/*` pages.

**It is a pre-existing SEO defect, live right now, unrelated to the migration.**
The migration forces a decision about it, which is the only reason it appears here.

### Canonical form

- 59 of 62 canonicals end in `.html`
- 3 are directory-style (`/`, `/blog/`, `/blog/page/2/`)
- `og:url` agrees with `canonical` on **every** page — zero disagreements
- 55 of 62 canonicals are self-referencing; the 7 above are not

### Host-level

```
http://patrolgarage.ae/      301 -> https://patrolgarage.ae/
https://www.patrolgarage.ae/ 301 -> https://patrolgarage.ae/
http://www.patrolgarage.ae/  301 -> https://www.patrolgarage.ae/   <- then 301 again
```

`http://www` takes **two hops** to reach the apex. Worth fixing during the move,
but note it is a behaviour change.

---

## 3. What `vercel.json` must contain — and the assumption check

### Your constraint, tested

> "My constraint is `cleanUrls: false` and no URL may change."

**`cleanUrls: false` is correct as the base, but on its own it does not reproduce
current behaviour.**

| | Netlify today | Vercel `cleanUrls: false` | Vercel `cleanUrls: true` |
|---|---|---|---|
| `/about.html` | `200` | `200` ✅ | `308` → `/about` ❌ every URL changes |
| `/about` | **`200`** | **`404`** ❌ | `200` |
| `/blog/x.html` | `200` | `200` ✅ | `308` → `/blog/x` ❌ |
| `/blog/x` | `301` → `.html` | `301` via rule ✅ | `200` ❌ inverted |

- **`cleanUrls: true` is disqualified.** It would 308 all 56 canonical URLs to
  their extensionless form and invert the entire canonical strategy. Every
  canonical, `og:url`, schema `mainEntityOfPage` and sitemap entry would then be
  wrong. Do not use it.
- **`cleanUrls: false` breaks the 10.** Vercel does not do Netlify's implicit
  extensionless fallback, so `/about` returns `404` where it currently returns
  `200`.

### Two ways to close the gap

**Option A — reproduce byte-identically.** Add a `rewrite` for each of the 7
cross-canonical URLs so they keep serving `200`. Faithful to "no URL may change",
but it ports a live SEO defect onto the new platform deliberately.

**Option B — finish the 2026-08-12 fix.** Add the 7 to the redirect set so they
`301` to `.html`, exactly as the 46 blog URLs already do. Behaviour on those 7
changes from `200` to `301`; **no canonical URL changes**, and the duplicate-content
condition is resolved.

I would take **Option B**, and do it as a separate change *before* the migration
so the two are not entangled. If a rank or index change follows, you want to know
which cause it belongs to.

### Redirect translation

`_redirects` holds **59 rules**:

| shape | count | Vercel translation |
|---|---|---|
| host-level (`www`, `http`) | 2 | `redirects[]` with `has: [{type:"host"}]`; Vercel handles `http`→`https` automatically |
| splat (`/docs/*  /  404!`) | 1 | `redirects[]` with `source: "/docs/:path*"` |
| plain path 1:1 | 56 | direct `redirects[]` entries |

Of the 56 plain rules, **51** are extensionless→`.html` and **5** are
merged/cannibalised slugs (both forms redirected, per the note in `_redirects`).

**The `!` force flag has no Vercel equivalent and needs none.** Netlify skips a
non-forced redirect when the path resolves to a real file, which is why 51 rules
carry `301!`. Vercel evaluates `redirects` *before* the filesystem, so the forcing
is implicit. The 5 rules currently written as plain `301` (the `.html`→`.html`
merged slugs) behave identically because no file exists at those paths.

### Sketch

```json
{
  "cleanUrls": false,
  "trailingSlash": false,
  "redirects": [
    { "source": "/(.*)",
      "has": [{ "type": "host", "value": "www.patrolgarage.ae" }],
      "destination": "https://patrolgarage.ae/$1",
      "permanent": true },
    { "source": "/docs/:path*", "destination": "/", "permanent": true },
    { "source": "/blog/best-oil-nissan-patrol-uae-heat",
      "destination": "/blog/best-oil-nissan-patrol-uae-heat.html",
      "permanent": true }
  ],
  "headers": [
    { "source": "/images/(.*)",
      "headers": [{ "key": "Cache-Control",
                    "value": "public, max-age=31536000, immutable" }] }
  ]
}
```

`gen_redirects.py` should be extended to emit the `redirects[]` array rather than
`_redirects` text, keeping the managed-block discipline and the `--check` mode.

**`trailingSlash`:** `/blog/` and `/blog/page/2/` are directory URLs whose
canonicals carry the trailing slash. Verify on a preview that `trailingSlash: false`
does not strip them — if it does, this needs `null` (leave as-authored) rather
than `false`.

### The one assumption to verify before DNS

Vercel's `404` behaviour for `/about` under `cleanUrls: false` is documented
behaviour, but I have not executed it. **Deploy a preview, curl all 109 URLs from
the baseline against the preview host, and diff against the JSON.** That converts
this plan's single weakest claim into a measurement. Do not move DNS first.

---

## 4. Netlify-specific things that will not carry over

| item | status | what happens |
|---|---|---|
| **Netlify Forms** | **BLOCKER** | `contact.html` uses `data-netlify="true"` with a `bot-field` honeypot. Netlify rewrites the form at deploy time — source has `data-netlify`, the served page has `<form method='POST' name='contact'>` and Netlify intercepts the POST. **Vercel has no forms feature.** The form silently stops working: it will POST to a path that does not exist and return 405 or 404. Needs a replacement before cutover — a Vercel serverless function, Formspree, or a WhatsApp/mailto swap. |
| `_redirects` | translate | → `vercel.json` `redirects[]`, §3 |
| `_headers` | translate | one rule, the `/images/*` immutable cache header → `vercel.json` `headers[]` |
| `netlify.toml` | **delete** | `pretty_urls = false` has no Vercel analogue and needs none — Vercel never rewrites internal links at serve time. This whole class of bug disappears. |
| `.netlify/` | local only | gitignored CLI state (`siteId`, `functions-internal`). Delete after cutover. |
| Netlify DNS | **keep running** | §6 |
| `netlify` CLI | replace | §5 |
| Netlify deploy permalinks | **loses a recovery tool** | `https://<deployId>--beautiful-cuchufli-e12a90.netlify.app/...` has twice been used to recover posts and hero images that existed only on the container. Vercel preview URLs work the same way, but the *existing* Netlify permalinks stay valid only while the site exists. Do not delete the Netlify site after cutover. |
| Netlify Analytics | not enabled | nothing to migrate (`analytics_instance_id: null`) |
| Netlify functions / edge functions | none | nothing to migrate |

---

## 5. Pipeline changes

`scripts/publish.py:413` is the deploy call:

```python
cmd = ["netlify", "deploy", "--prod", "--dir", "."]
if auth_token: cmd.extend(["--auth", auth_token])
if site_id:    cmd.extend(["--site", site_id])
```

### What has to change

1. **`publish.py` deploy command** → `vercel deploy --prod --yes --token $VERCEL_TOKEN`.
   Note the existing `--auth` flag is already known-broken on Netlify (the token
   must come from the environment); Vercel's `--token` flag does work, so this
   gets simpler.
2. **The Docker image** installs the Netlify CLI. It must install the Vercel CLI
   instead. Check `Dockerfile` and `requirements.txt`.
3. **`publish.py` form-adoption logic (lines ~200–250)** exists solely to stop a
   deploy dropping the `data-netlify` marker — it counts `data-netlify`
   occurrences and refuses to adopt a live page that has fewer. Once Forms is
   gone this logic is dead and misleading. Remove it with the form migration, not
   before.
4. **`gen_redirects.py`** emits `_redirects` text. Retarget at `vercel.json`.
5. **The revert trap survives the move.** `publish.py` deploys from the
   container's own copy, so a Mac-side deploy still silently rolls back that day's
   cron post. Nothing about Vercel changes that. The sitemap-parity check before
   every deploy stays mandatory.

### Env vars on `patrolgarage-pipeline`

| var | action |
|---|---|
| `NETLIFY_AUTH_TOKEN` | remove **after** cutover is confirmed, not before |
| `NETLIFY_SITE_ID` | remove after cutover |
| `VERCEL_TOKEN` | **add** — create a dedicated token named `patrolgarage-cron`, matching the existing `pool-site` / `thedubaidog-cron` convention |
| `VERCEL_ORG_ID` | **add** |
| `VERCEL_PROJECT_ID` | **add** |

Unaffected: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `DATAFORSEO_*`, `GSC_OAUTH_JSON`,
`SUPABASE_*`, `SITE_DOMAIN`.

⚠️ Railway currently refuses production deploys on this project for credit
reasons — two deploys have been stuck in `INITIALIZING` since 14:08 today. **The
pipeline cannot be updated until that is resolved.** Migrating the site while the
cron container still runs the old Netlify deploy code means the next cron run
pushes to Netlify while DNS points at Vercel: the site freezes at cutover state
and new posts appear nowhere. Resolve Railway first, or pause the cron across the
migration window.

---

## 6. Rollback

**DNS is the switch, and it is fast.**

| fact | value |
|---|---|
| Apex `A` records | `35.157.26.135`, `63.176.8.218` (Netlify) |
| `www` `A` records | same pair |
| **Authoritative TTL** | **120 seconds**, confirmed direct from `dns1.p07.nsone.net` |
| Nameservers | `dns1-4.p07.nsone.net` (NS1 — **Netlify DNS**) |
| NS delegation TTL | 3436 s remaining |
| SOA negative-cache TTL | 3600 s |
| Registrar | Host Arabia / Tasjeel.ae |

### Do the cutover inside Netlify DNS

Because Netlify runs the zone, cut over by **changing the A records inside
Netlify DNS to point at Vercel** — do *not* move the nameservers to Vercel.

Why this matters:

- **Rollback is a 120-second record edit**, not a nameserver change
- A nameserver move is governed by the **3436 s delegation TTL** and can linger up
  to 24 h at some resolvers, which turns a bad cutover into a day-long outage
- The zone, and therefore rollback control, stays in one place

### Rollback procedure

1. In Netlify DNS, set the apex and `www` `A` records back to
   `35.157.26.135` and `63.176.8.218`
2. Propagation: **~2 minutes** at the record TTL
3. Netlify still holds the last deploy, so the site returns exactly as it was —
   provided the Netlify site has not been deleted

### Rollback window

Keep the Netlify site alive for **at least 30 days**. It costs nothing, and it
holds the deploy permalinks that have twice been the only copy of lost posts and
hero images.

### Verification gate before cutover

Do not move DNS until all of these pass against the Vercel **preview** host:

- All 109 URLs from `URL-BASELINE-PRE-MIGRATION.json` return the same status code
- Every `301` resolves to the same destination
- Every `200` page has the same `canonical` and `og:url`
- `/blog/` and `/blog/page/2/` keep their trailing slash
- The contact form has a working replacement, or is deliberately disabled
- `sitemap.xml` and `robots.txt` serve `200`

Re-run the same diff immediately after DNS moves.

---

## Recommended sequence

1. Resolve the Railway credit block
2. Fix the 7 cross-canonical URLs on Netlify (Option B) and let it settle
3. Decide the contact form replacement — this is the only true blocker
4. Build `vercel.json`, deploy a preview, diff all 109 URLs against the baseline
5. Update `publish.py`, the `Dockerfile` and `gen_redirects.py`; add the Vercel
   env vars; keep the Netlify ones
6. Pause the cron
7. Change the A records in Netlify DNS
8. Re-run the 109-URL diff against production
9. Resume the cron, confirm the next scheduled post publishes to Vercel
10. After 30 clean days, remove the Netlify env vars and the Netlify site
