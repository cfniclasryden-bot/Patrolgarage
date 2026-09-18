# Working notes for patrolgarage

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
