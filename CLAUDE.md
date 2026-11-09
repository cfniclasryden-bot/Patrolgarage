# Working notes for patrolgarage

## THE BLOG PIPELINE IS PAUSED (since 2026-11-09, owner's request)

No PG post publishes until the owner says to re-enable it. Paused together with
topchallenger's, after a customer called the workshop asking for a towbar that
this site's tow bar post had offered ("bring it to us at Patrol Garage"). See
`topchallenger/site/research/BLOG-SERVICE-AUDIT-2026-11-09.md`, Appendix A.

**State as paused (verified 2026-11-09 08:44 UTC):** Railway project
`patrolgarage` (5db32147-4574-49cb-8bfe-4c50b47b764b), service
`patrolgarage-pipeline` (4e6167e9-44c1-4881-b414-5aab2c3db605), env production
(3c2233d7-3297-49af-ae1d-36f0edde084a). Active deployment `bdf4f89b` has **no
cronSchedule** and start command `echo patrolgarage-pipeline PAUSED 2026-11-09 -
see CLAUDE.md`; it ran the echo once and EXITED. The previous deployment
(88cee22c, cron `0 5 * * 1,4`) is REMOVED. Service instance: `cronSchedule:
null`, `nextCronRunAt: null`. `railway.json` carries the same pause.

**Why both the cron AND the start command.** A deployment with no cron and the
real start command runs the pipeline ONCE at deploy time, which publishes a
post. The echo makes every deploy harmless while paused. And a
`serviceInstanceRedeploy` does NOT apply a changed instance setting: it copies
the previous deployment's manifest (found on topchallenger the same morning).
Only `railway up` builds a deployment with the new values. Trust the ACTIVE
DEPLOYMENT's `meta.serviceManifest.deploy`, not the instance fields.

**`railway up` timed out client-side twice** ("error sending request ... /up ...
operation timed out") on this 225 MB tree. The first attempt left a FAILED
deployment; the second had in fact uploaded and built fine. After a timeout,
check `deployments(first:3, ...)` before retrying.

**To re-enable (only when the owner asks):**

1. In `railway.json` restore `"startCommand": "python3 scripts/cron_entry.py"`
   and `"cronSchedule": "0 5 * * 1,4"` (Mon/Thu 05:00 UTC). Commit and push.
2. Set the instance to match FIRST (GraphQL, `User-Agent: railwayapp/4.56.1`):
   `serviceInstanceUpdate(serviceId:"4e6167e9-44c1-4881-b414-5aab2c3db605",
   environmentId:"3c2233d7-3297-49af-ae1d-36f0edde084a", input:{cronSchedule:"0 5 * * 1,4",
   startCommand:"python3 scripts/cron_entry.py", restartPolicyType:NEVER})`.
   With the cron set, the deploy waits for the tick instead of publishing at once.
3. `cd ~/Desktop/Projects/patrolgarage && railway up --ci` (cd in the same command).
4. Verify: the new active deployment's manifest shows the cron and
   `cron_entry.py`, and the service instance `nextCronRunAt` is the next Mon/Thu
   05:00 UTC.
5. The topic blocklist (`scripts/topic_blocklist.py`) and the offer guard
   (`scripts/test_no_offers.py`) added the same day stay in force after re-enabling.

## GH_TOKEN on patrolgarage-pipeline is SHARED and TEMPORARY — replace it

The `GH_TOKEN` set on the Railway service `patrolgarage-pipeline` on 2026-09-18
is **not** a token minted for this project. It is a fine-grained PAT scoped to
**All repositories** — it reaches all 25 repos on `cfniclasryden-bot` with
write, and **it has no expiry**.

**The same token is live on five services:**

    topchallenger-pipeline        GH_TOKEN   sha256 51a254482e33
    klimatizace-most/blog         GH_TOKEN   sha256 51a254482e33
    klimatizace-usti/blog         GH_TOKEN   sha256 51a254482e33
    praha-klima/blog              GH_TOKEN   sha256 51a254482e33
    patrolgarage-pipeline         GH_TOKEN   sha256 51a254482e33   <- added 2026-09-18

    (klimatizace-teplice/blog uses a DIFFERENT token, sha256 944aa9d879e7,
     correctly scoped to 4 repos. That one is the pattern to copy.)

    (praha-klima/update-pipeline carries the CLASSIC PAT, sha256 2d8b5548ea9a,
     scope `repo`, also no expiry. That one is worse and is out of scope here,
     but do not add to it.)

**So rotating or revoking it breaks all five pipelines at once**, on whatever
day that happens, and the breakage is loud here but silent elsewhere: on this
service `sync_to_origin()` exits 2 and nothing publishes, which you will see as
a failed Railway run. On the klima services the failure mode is a skipped post.
If you revoke it for an incident on one site, remember you have just disarmed
four others.

It was accepted deliberately, as an explicit stopgap, because a new credential
could not be minted at the time (no browser access to GitHub) and the
alternative was leaving this pipeline unable to publish at all. It should be
replaced with a fine-grained PAT scoped to `Patrolgarage` only,
`Contents: Read and write`, with an expiry set. The swap is a one-line Railway
variable change and needs no redeploy — `sync_to_origin()` reads `GH_TOKEN`
fresh on every run.

The token was verified against THIS repo before use: authenticates as
`cfniclasryden-bot`, reaches `cfniclasryden-bot/Patrolgarage`, and has real
write access — proven by pushing a throwaway branch and deleting it, not by
trusting the API's `permissions` block, which reports the *account's* role and
not the token's capability. A read-only token would have reproduced the
container-only-post bug silently.

## Git is the source of truth as of 2026-09-18 — and the container fails closed

`run_pipeline.py` calls `publish.sync_to_origin()` as step zero, which resets
the tree to `origin/main` before anything is generated. `publish()` then
commits and **pushes before it deploys**; a failed push aborts the deploy.

**Why:** this pipeline used to write posts into a disposable container, commit
them to a `.git` that `COPY . .` had baked in at the last `railway up`, and
deploy to the host. It never pulled and never pushed, so those commits were
read by nobody and died with the container. Six posts were lost that way and
recovered by hand in `0cd6d2b` and `d1564b1`; `de863e4`, `3e4599f` and
`eb0881d` are the same class. On 2026-09-18 `origin/main` was 53 commits and
two months behind local — which is why origin had to be pushed current BEFORE
the sync landed. A `reset --hard` against that origin would have deployed a
July site over production.

**With no `GH_TOKEN` in the container the run halts at step zero**: exit code 2,
no Supabase call, no generation, no commit, no deploy. That is deliberate. A
skipped post is recoverable; a stale-tree deploy is not.

`ensure_static_pages()` is now skipped whenever the tree came from origin. It
adopts the LIVE copy of a diverged root page, which was the right fix while the
container could not learn about a human edit — but with a real git sync "live
wins" would let a stale deployed page overwrite a committed change. Delete it
once the sync has run clean for a week.

## Deploy target is Vercel

`DEPLOY_TARGET=vercel` is set explicitly on the Railway service and the live
site answers with `server: Vercel`. The Netlify branch in `publish.py` is kept
deliberately as a rollback — one Railway variable, no rebuild — and both CLIs
are installed in the image for that reason. Note the rollback is not complete:
no page carries `data-netlify` any more and there is no `<form>` on
`/contact.html` at all, so the `data-netlify` preservation logic in
`publish.py` is inert.

## This site has NO premises

It books the work; a partner workshop fulfils it. Commit `89a64ee` stripped
address, geo and `openingHoursSpecification` from 39 schema blocks for that
reason. `/nissan-patrol-abu-dhabi.html` is a **service-area** page on the same
basis: it names Abu Dhabi and Mussafah and says "the work is done in Mussafah",
and claims no address, hours or map. Do not name the partner workshop, and do
not reintroduce a premises claim for a second emirate.
