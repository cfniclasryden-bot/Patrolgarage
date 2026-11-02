# Blog re-measure: topchallenger.ae and patrolgarage.ae, 2 Nov 2026

Read-only re-measure against `research/BLOG-AUDIT-2026-10-23.md` (in topchallenger-site). No site file was changed and nothing was deployed. The same file is committed to both repos. Both were pulled first: topchallenger-site at `f2281e1`, patrolgarage at `d36f291`, and both match origin.

## Summary

1. **Neither site has published a post since 23 Oct.** Every logged pipeline run since 26 Oct failed at "generate hero image": 4 runs on TC, which requeued 2 keywords, and 1 logged run on PG, with no row at all for its 29 Oct and 2 Nov runs. The schedule question is moot until that is fixed.
2. **TC's blog impressions doubled per day** (30.6 → 62.2) and its clicks went from 0.36 to 0.89 a day. It still produced **0 leads** in 10 days, against 20 from TC's other pages.
3. **The two-week fade still holds for every TC post that has completed four weeks.** All 13 eligible posts are down more than 50% (median 7% of launch rate), and all 13 are unchanged from the audit.
4. **The fade does not hold, so far, for the 8 TC posts Google first showed on 7–10 Oct.** At days 14–21 they keep a median 83% of their launch rate, against 12% for earlier posts at the same age. They reach day 28 on 3–6 Nov.
5. **PG's blog is flat:** 467 → 460 impressions a day and 5.4 → 4.8 clicks a day. It produced 2 of 14 leads in 10 days (10 of 31 in the audit window).
6. **PG's generic no-city posts are growing** (176 → 240 impressions a day) and not-starting doubled after day 14. They still convert poorly: 3 lifetime leads from 18 posts.
7. **PG's 21 per-part cost posts have stopped earning.** Together: 9.6 impressions a day, 2 clicks and 0 leads in the new window. They have 8 leads lifetime, 3 of them from the tow bar post.
8. **The Abu Dhabi posts have their first clicks but no leads.** TC's 4 posts: 112 impressions and 2 clicks in 9 days. PG's 3: 55 and 2. Limp-mode, the oldest, holds 108% of its launch rate over days 14–19.
9. **The audit's "Y62 guide grew 10.8 → 54.7 a day" was inflated by one week.** In week 40, 1,589 impressions came from a single query, "nissan patrol y61 y62 y63 present". Outside that spike the guide runs at 250–345 impressions a week and is not falling.
10. **Answers:** TC should drop from Mon/Wed/Fri to Monday only. PG should write no new per-part cost posts. Both queues should change order, led by the new keyword research. See §5.

## How the numbers were made

- **Windows.**
  - "Then" is the audit's L28, 24 Sep–21 Oct (28 days).
  - "Now" is 23–31 Oct for GSC (9 days), because 31 Oct is the last final day. For GA4 it is 23 Oct–1 Nov (10 days).
  - Windows differ in length, so the comparisons use per-day rates.
- **Search Console:** `sc-domain:` properties, final data, through `patrolgarage/scripts/gsc_client.py`. Every URL form of a post (`.html`, clean, `#anchor`, query string) is added together, as in the audit. Blog totals cover every `/blog/` URL.
- **Index status:** URL Inspection API, run 2 Nov on all 32 TC and 58 PG canonical URLs.
  - All return HTTP 200.
  - Where Google has chosen a canonical, it equals the declared one; it has chosen none for the two unindexed posts.
- **Leads:** `whatsapp_click` + `phone_click` in sessions that landed on the post (GA4 549854107 for TC, 536974272 for PG). Same exclusions as the audit:
  - TC sessions tagged Internal Traffic
  - datacentre cities
  - any hour with 4+ lead events from one city, device and channel

  That rule found only the 5 Oct 15:00 burst, plus the audit's earlier ones. **Nothing in the new window was excluded.** PG still has no internal-traffic filter in Testing or Active state, so its figures rely on the burst rule alone.
- **Fade, strict (the audit's test):**
  - Eligible posts have at least 28 days since first impression and at least 20 impressions in their first 14 days.
  - The test compares impressions a day in days 0–13 with impressions a day from day 14 to 31 Oct.
- **Fade, like-for-like (new):** impressions a day in days 14–21 against days 0–13. It covers every post at least 22 days past its first impression with at least 20 impressions in its first 14 days, so young and old posts are compared at the same age.
- **Pipeline state:** the Supabase `pipeline_runs` and `articles` tables (read only) and `railway status`. Railway run logs returned nothing from the CLI, so the hero-image error text was not read. Both OpenAI keys answer `/v1/models` with 200. They are different keys, and both started failing on the same day.

---

## 1. What happened since 23 Oct

| Site | Runs since 23 Oct | Result |
|---|---|---|
| TC (Mon/Wed/Fri) | 26 Oct, 28 Oct, 30 Oct, 2 Nov | All four failed at "generate hero image". "y62 transmission warning light abu dhabi" (26, 28 Oct) and "y62 white smoke exhaust abu dhabi" (30 Oct, 2 Nov) were each requeued after two failures. |
| PG (Mon/Thu) | 26 Oct logged; 29 Oct and 2 Nov not logged | "nissan patrol long term ownership abu dhabi" failed at "generate hero image" on 26 Oct. There is no `pipeline_runs` row for 29 Oct or 2 Nov, so those runs died before logging, or did not start. The Railway deployment shows CRASHED with cron `0 5 * * 1,4`. |

**Posts published since 23 Oct:**
- TC: only that day's y62-engine-knocking-noise-abu-dhabi, which is indexed and has 17 impressions and 1 click.
- PG: none. The newest is 22 Oct's nissan-patrol-brake-problems, indexed, with 77 impressions and 1 click in 9 days.

**Hand changes since the audit:**
- PG merged nissan-patrol-service-dubai-complete-guide into nissan-patrol-service-cost-dubai on 23 Oct (`f517226`). The old URL 301s live.
- The service-cost post ran at about 11 impressions a day both before and after the merge (10–22 Oct vs 23–31 Oct). Its audit-window average of 19.3 a day includes higher September days, so the merge shows no effect either way yet.
- TC's commits since the audit did touch posts:
  - On 28 Oct, `10c1f1e` added about 85 lines (indexing links and branch schema) to each of the 4 Abu Dhabi posts.
  - 9 other posts got one-line link edits.
  - The Abu Dhabi posts' 29–31 Oct figures therefore come after that change. Three days is too short to attribute anything to it.

## 2. topchallenger.ae

**Site:**

| | Then (per day) | Now (per day) |
|---|---|---|
| Blog impressions | 30.6 | 62.2 |
| Blog clicks | 0.36 | 0.89 |
| Non-blog impressions | 92.8 | 95.8 |
| Non-blog clicks | 2.82 | 2.67 |
| Leads | 1.5 (1 of 43 from the blog) | 2.0 (0 of 20 from the blog) |
| Blog-landing sessions | 3.7 | 4.7 |

The blog's growth did not come at the service pages' expense: non-blog impressions are flat.

### Every post

| Post | Published | Index (2 Nov) | 24 Sep–21 Oct: clicks / impr / pos | 23–31 Oct: clicks / impr / pos | Impr/day then → now | WA/phone then → now | Fade |
|---|---|---|---|---|---|---|---|
| y62-cooling-ac-problems-dubai | 2026-08-04 | Indexed | 1 / 9 / 6.2 | 0 / 7 / 7.7 | 0.3 → 0.8 | 0/0 → 0/0 | 2.8 → 0.5 (0.18) |
| y62-gearbox-shudder-dubai | 2026-08-04 | Indexed | 0 / 2 / 10.0 | 0 / 1 / 6.0 | 0.1 → 0.1 | 0/0 → 0/0 | too few (1 in first 14 d) |
| y62-gearbox-transmission-problems-dubai | 2026-08-04 | Indexed | 0 / 7 / 5.7 | 0 / 2 / 8.0 | 0.2 → 0.2 | 0/0 → 0/0 | 8.9 → 0.3 (0.04) |
| y62-service-diagnostics-dubai | 2026-08-04 | Indexed | 0 / 9 / 9.4 | 0 / 4 / 5.5 | 0.3 → 0.4 | 0/0 → 0/0 | 2.8 → 0.5 (0.18) |
| y62-service-interval-dubai-heat | 2026-08-04 | Indexed | 0 / 4 / 6.2 | 0 / 0 / – | 0.1 → 0.0 | 0/0 → 0/0 | 3.4 → 0.6 (0.17) |
| y62-engine-problems-dubai | 2026-08-17 | Indexed | 0 / 4 / 6.2 | 0 / 2 / 8.5 | 0.1 → 0.2 | 0/0 → 0/0 | 6.7 → 0.2 (0.03) |
| y62-transmission-fluid-change-interval-dubai | 2026-08-17 | Indexed | 0 / 5 / 6.2 | 0 / 0 / – | 0.2 → 0.0 | 0/0 → 0/0 | 13.9 → 0.3 (0.02) |
| y62-suspension-hbmc-problems-dubai | 2026-08-24 | Indexed | 1 / 13 / 8.5 | 0 / 2 / 4.5 | 0.5 → 0.2 | 1/0 → 0/0 | 4.1 → 0.5 (0.11) |
| y62-transmission-slipping-dubai | 2026-08-24 | Indexed | 0 / 0 / – | 0 / 3 / 11.7 | 0.0 → 0.3 | 0/0 → 0/0 | too few (5 in first 14 d) |
| y62-transmission-overheating-dubai | 2026-08-26 | Indexed | 0 / 8 / 3.6 | 0 / 1 / 3.0 | 0.3 → 0.1 | 0/0 → 0/0 | 6.1 → 0.2 (0.04) |
| y62-ac-not-cold-at-idle-dubai | 2026-08-28 | Indexed | 0 / 10 / 5.6 | 0 / 1 / 4.0 | 0.4 → 0.1 | 0/0 → 0/0 | 5.3 → 0.4 (0.08) |
| y62-radiator-sand-blockage-dubai | 2026-08-31 | Indexed | 0 / 8 / 6.0 | 0 / 0 / – | 0.3 → 0.0 | 0/0 → 0/0 | too few (4 in first 14 d) |
| y62-major-service-what-is-included-dubai | 2026-09-02 | **Discovered, not indexed** | 0 / 0 / – | 0 / 0 / – | 0.0 → 0.0 | 0/0 → 0/0 | never shown |
| y62-check-engine-light-diagnosis-dubai | 2026-09-04 | Indexed | 2 / 124 / 5.6 | 2 / 68 / 4.0 | 4.4 → 7.6 | 0/0 → 0/0 | d14–21: 8.9 → 7.75 (0.88), not yet eligible |
| best-engine-oil-for-y62-dubai | 2026-09-06 | Indexed | 0 / 100 / 5.7 | 2 / 52 / 3.3 | 3.6 → 5.8 | 0/0 → 0/0 | d14–21: 6.5 → 5.88 (0.9), not yet eligible |
| y62-engine-oil-consumption-dubai | 2026-09-06 | Indexed | 0 / 62 / 5.0 | 0 / 33 / 6.2 | 2.2 → 3.7 | 0/0 → 0/0 | d14–21: 4.4 → 3.5 (0.79), not yet eligible |
| y62-alignment-after-desert-driving-dubai | 2026-09-17 | Indexed | 0 / 18 / 8.3 | 0 / 0 / – | 0.6 → 0.0 | 0/0 → 0/0 | 1.9 → 0.1 (0.07) |
| y62-desert-driving-preparation-uae | 2026-09-17 | Indexed | 1 / 39 / 5.3 | 0 / 1 / 6.0 | 1.4 → 0.1 | 0/0 → 0/0 | 4.2 → 0.3 (0.06) |
| y62-dune-bashing-damage-uae | 2026-09-17 | Indexed | 0 / 23 / 5.8 | 0 / 0 / – | 0.8 → 0.0 | 0/0 → 0/0 | 1.5 → 0.3 (0.20) |
| y62-engine-repair-cost-dubai | 2026-09-18 | Indexed | 0 / 29 / 11.3 | 0 / 1 / 8.0 | 1.0 → 0.1 | 0/0 → 0/0 | 2.8 → 0.1 (0.04) |
| y62-coolant-leak-dubai | 2026-09-21 | Indexed | 0 / 38 / 5.0 | 0 / 22 / 5.6 | 1.4 → 2.4 | 0/0 → 0/0 | d14–21: 3.4 → 2.25 (0.67), not yet eligible |
| y62-suspension-sagging-dubai | 2026-09-23 | Indexed | 2 / 60 / 5.5 | 0 / 49 / 5.5 | 2.1 → 5.4 | 0/0 → 0/0 | d14–21: 4.7 → 5.38 (1.14), not yet eligible |
| y62-suspension-repair-cost-dubai | 2026-09-25 | Indexed | 0 / 50 / 4.2 | 0 / 18 / 5.5 | 1.8 → 2.0 | 0/0 → 0/0 | d14–21: 3.9 → 2.12 (0.54), not yet eligible |
| y62-overheating-dubai-summer | 2026-09-30 | Indexed | 0 / 61 / 4.9 | 0 / 31 / 5.6 | 2.2 → 3.4 | 0/0 → 0/0 | d14–21: 5.1 → 3.88 (0.75), not yet eligible |
| y62-suspension-noise-speed-bumps-dubai | 2026-10-07 | Indexed | 2 / 47 / 4.8 | 2 / 38 / 4.1 | 1.7 → 4.2 | 0/0 → 0/0 | d14–21: 3.7 → 4.12 (1.11), not yet eligible |
| y62-liwa-trip-preparation-uae | 2026-10-09 | Indexed | 0 / 9 / 4.6 | 0 / 12 / 5.2 | 0.3 → 1.3 | 0/0 → 0/0 | day 20 of first shown, too new |
| y62-limp-mode-abu-dhabi | 2026-10-12 | Indexed | 0 / 42 / 5.2 | 1 / 32 / 4.0 | 1.5 → 3.6 | 0/0 → 0/0 | day 20 of first shown, too new |
| y62-tyre-pressure-for-sand-uae | 2026-10-14 | Indexed | 1 / 59 / 6.4 | 0 / 69 / 5.9 | 2.1 → 7.7 | 0/0 → 0/0 | day 17 of first shown, too new |
| y62-ac-blowing-hot-air-abu-dhabi | 2026-10-16 | Indexed | 0 / 6 / 6.3 | 0 / 47 / 5.3 | 0.2 → 5.2 | 0/0 → 0/0 | day 12 of first shown, too new |
| y62-gearbox-delayed-engagement-abu-dhabi | 2026-10-19 | Indexed | 0 / 10 / 5.8 | 0 / 16 / 5.1 | 0.4 → 1.8 | 0/0 → 0/0 | day 12 of first shown, too new |
| y62-diff-lock-in-sand-uae | 2026-10-21 | Indexed | 0 / 0 / – | 0 / 31 / 4.7 | 0.0 → 3.4 | 0/0 → 0/0 | day 5 of first shown, too new |
| y62-engine-knocking-noise-abu-dhabi | 2026-10-23 | Indexed | 0 / 0 / – | 1 / 17 / 5.2 | 0.0 → 1.9 | 0/0 → 0/0 | day 4 of first shown, too new |

- **Fade column:**
  - Eligible posts show launch → later impressions a day, with the ratio.
  - Younger posts show the days 14–21 like-for-like ratio.
- **Not indexed: 1 post.** y62-major-service-what-is-included-dubai is now **Discovered, not indexed**, 61 days after publishing (it was "unknown to Google" on 23 Oct). It has never had an impression.
- **Leads:** none from any TC post in the new window. Lifetime blog leads are still 2: ac-not-cold-at-idle and suspension-hbmc-problems.

### The two-week fade on TC

**Strict test: unchanged.** The same 13 posts are eligible, and all 13 are down more than 50%. The median is 0.07, against 0.09 in the audit.

**Like-for-like (days 14–21 vs days 0–13):** the posts first shown in October behave differently.

| First shown | Posts | Median days 14–21 / launch | Range |
|---|---|---|---|
| 14 Aug – 20 Sep | 13 | 0.12 | 0.00–0.91 |
| 7–10 Oct | 8 | **0.83** | 0.54–1.14 |

The October group is every September post Google only began showing 30+ days after publishing:
- best-engine-oil 0.90
- check-engine-light 0.88
- engine-oil-consumption 0.79
- overheating-dubai-summer 0.75
- suspension-noise-speed-bumps 1.11
- suspension-repair-cost 0.54
- coolant-leak 0.67
- suspension-sagging 1.14

They account for most of the blog's doubling. Two caveats:
- **The pattern is not explained.** The data shows that it happened, not why. A late first showing may mean Google tested these posts later and more slowly.
- **Clicks haven't followed.** The 8 posts have 6 clicks and 0 leads in the new window, at average positions of 3.3–6.2.

The strict test can include them from 3–6 Nov. Until then, "the fade holds on TC without exception" is true only for posts first shown before October.

### Abu Dhabi posts (TC)

| Post | First shown | Lifetime clicks / impr | 23–31 Oct impr | Later / launch ratio | Leads |
|---|---|---|---|---|---|
| y62-limp-mode-abu-dhabi | 12 Oct | 1 / 76 | 32 | 1.08 (days 14–19) | 0 |
| y62-ac-blowing-hot-air-abu-dhabi | 20 Oct | 1 / 70 | 47 | too new (day 12) | 0 |
| y62-gearbox-delayed-engagement-abu-dhabi | 20 Oct | 0 / 29 | 16 | too new (day 12) | 0 |
| y62-engine-knocking-noise-abu-dhabi | 28 Oct | 1 / 17 | 17 | too new (day 4) | 0 |

- **As a group:** 2.1 → 12.4 impressions a day, the first 3 clicks, and 0 leads. All four are too young to compare with the Dubai posts at the same age.
- **Limp-mode** reaches day 28 on 8 Nov, the audit's check date.

## 3. patrolgarage.ae

**Site:**

| | Then (per day) | Now (per day) |
|---|---|---|
| Blog impressions | 466.7 | 460.2 |
| Blog clicks | 5.36 | 4.78 |
| Leads | 1.11 (10 of 31 from the blog) | 1.40 (2 of 14 from the blog) |
| Blog-landing sessions | 8.4 | 7.9 |

The two blog leads in the new window both came from WhatsApp, one each on nissan-patrol-losing-power and the Y62 complete guide.

### Every post

| Post | Published | Index (2 Nov) | 24 Sep–21 Oct: clicks / impr / pos | 23–31 Oct: clicks / impr / pos | Impr/day then → now | WA/phone then → now | Fade |
|---|---|---|---|---|---|---|---|
| nissan-patrol-ac-problems-dubai.html | 2026-05-10 | Indexed | 1 / 99 / 5.4 | 0 / 29 / 5.9 | 3.5 → 3.2 | 0/0 → 0/0 | 1.6 → 4.1 (2.50) |
| nissan-patrol-mechanic-al-quoz.html | 2026-05-10 | Indexed | 0 / 2 / 7.5 | 0 / 2 / 4.0 | 0.1 → 0.2 | 0/0 → 0/0 | day 12 of first shown, too new |
| nissan-patrol-off-road-uae.html | 2026-05-10 | Indexed | 1 / 146 / 6.6 | 0 / 34 / 6.1 | 5.2 → 3.8 | 0/0 → 0/0 | 2.1 → 3.0 (1.40) |
| nissan-patrol-pre-purchase-inspection.html | 2026-05-10 | Indexed | 1 / 47 / 5.1 | 0 / 13 / 6.2 | 1.7 → 1.4 | 0/0 → 0/0 | too few (9 in first 14 d) |
| nissan-patrol-service-cost-dubai.html | 2026-05-10 | Indexed | 4 / 541 / 4.9 | 1 / 94 / 5.9 | 19.3 → 10.4 | 0/0 → 0/0 | 14.2 → 11.9 (0.84) |
| nissan-patrol-y61-dubai-complete-guide.html | 2026-05-10 | Indexed | 6 / 355 / 7.1 | 2 / 102 / 8.4 | 12.7 → 11.3 | 0/0 → 0/0 | 5.7 → 8.8 (1.54) |
| nissan-patrol-y61-vs-y62-dubai.html | 2026-05-10 | Indexed | 7 / 324 / 6.0 | 2 / 140 / 10.8 | 11.6 → 15.6 | 0/0 → 0/0 | 1.8 → 7.9 (4.40) |
| nissan-patrol-y62-dubai-complete-guide.html | 2026-05-10 | Indexed | 12 / 3244 / 6.0 | 4 / 485 / 7.3 | 115.9 → 53.9 | 0/0 → 1/0 | 10.8 → 54.5 (5.05) |
| nissan-patrol-y62-problems-dubai.html | 2026-05-10 | Indexed | 12 / 644 / 5.7 | 1 / 189 / 6.5 | 23.0 → 21.0 | 1/0 → 0/0 | 8.7 → 17.6 (2.02) |
| nissan-patrol-y62-transmission-problems-dubai.html | 2026-05-11 | Indexed | 7 / 265 / 6.3 | 0 / 98 / 6.4 | 9.5 → 10.9 | 1/0 → 0/0 | 9.6 → 3.3 (0.35) |
| nissan-patrol-y62-vs-y63-dubai-comparison.html | 2026-05-11 | Indexed | 7 / 912 / 7.7 | 0 / 309 / 8.6 | 32.6 → 34.3 | 1/0 → 0/0 | 12.0 → 13.7 (1.14) |
| best-oil-nissan-patrol-uae-heat.html | 2026-05-15 | Indexed | 23 / 654 / 5.5 | 6 / 203 / 5.5 | 23.4 → 22.6 | 0/0 → 0/0 | 5.4 → 15.1 (2.83) |
| nissan-patrol-transmission-rebuild-cost-dubai-aed.html | 2026-05-15 | Indexed | 2 / 188 / 5.6 | 1 / 62 / 5.7 | 6.7 → 6.9 | 1/0 → 0/0 | too few (8 in first 14 d) |
| nissan-patrol-differential-repair-cost-uae.html | 2026-05-18 | Indexed | 0 / 12 / 4.0 | 0 / 2 / 5.0 | 0.4 → 0.2 | 0/0 → 0/0 | 2.5 → 0.5 (0.19) |
| nissan-patrol-overheating-dubai-summer-fix.html | 2026-05-18 | Indexed | 1 / 122 / 5.2 | 1 / 32 / 5.8 | 4.4 → 3.6 | 0/0 → 0/0 | too few (13 in first 14 d) |
| nissan-patrol-service-every-how-many-km-dubai.html | 2026-05-23 | Indexed | 1 / 16 / 4.8 | 0 / 8 / 6.0 | 0.6 → 0.9 | 0/0 → 0/0 | 9.1 → 1.1 (0.12) |
| y63-dashcam-installation-specialist-dubai-best-price-2026.html | 2026-07-19 | Indexed | 0 / 6 / 7.3 | 0 / 3 / 4.3 | 0.2 → 0.3 | 0/0 → 0/0 | too few (17 in first 14 d) |
| nissan-patrol-y62-oxygen-sensor-replacement-cost-dubai-2026.html | 2026-07-20 | Indexed | 0 / 10 / 10.4 | 0 / 4 / 4.0 | 0.4 → 0.4 | 0/0 → 0/0 | 7.4 → 0.4 (0.05) |
| y61-super-safari-snorkel-fitting-cost-dubai-2026.html | 2026-07-21 | Indexed | 1 / 4 / 4.5 | 0 / 0 / – | 0.1 → 0.0 | 0/0 → 0/0 | too few (19 in first 14 d) |
| nissan-patrol-y62-starter-motor-replacement-cost-uae-2026.html | 2026-07-22 | Indexed | 3 / 52 / 4.0 | 1 / 16 / 3.9 | 1.9 → 1.8 | 0/0 → 0/0 | 6.1 → 1.7 (0.28) |
| y62-fuel-injector-cleaning-cost-dubai-2026.html | 2026-07-24 | Indexed | 0 / 26 / 7.0 | 0 / 5 / 9.4 | 0.9 → 0.6 | 0/0 → 0/0 | 3.4 → 0.9 (0.26) |
| nissan-patrol-y62-head-gasket-replacement-cost-uae.html | 2026-07-25 | Indexed | 1 / 19 / 5.5 | 0 / 6 / 5.7 | 0.7 → 0.7 | 0/0 → 0/0 | 2.8 → 0.6 (0.22) |
| y62-abs-sensor-replacement-cost-dubai-2026.html | 2026-07-26 | Indexed | 0 / 3 / 10.0 | 0 / 1 / 4.0 | 0.1 → 0.1 | 0/0 → 0/0 | 1.9 → 0.1 (0.04) |
| nissan-patrol-y62-driveshaft-repair-cost-dubai-2026.html | 2026-07-27 | Indexed | 1 / 5 / 11.8 | 0 / 1 / 9.0 | 0.2 → 0.1 | 0/0 → 0/0 | 2.4 → 0.2 (0.09) |
| nissan-patrol-y62-throttle-body-cleaning-cost-dubai.html | 2026-07-29 | Indexed | 0 / 6 / 13.7 | 0 / 0 / – | 0.2 → 0.0 | 0/0 → 0/0 | 5.5 → 0.2 (0.04) |
| y62-water-pump-replacement-cost-uae-2026.html | 2026-07-30 | Indexed | 2 / 37 / 4.4 | 0 / 10 / 5.9 | 1.3 → 1.1 | 0/0 → 0/0 | 1.9 → 1.0 (0.55) |
| nissan-patrol-y62-fourth-brake-light-replacement-dubai-2026.html | 2026-07-31 | Indexed | 0 / 0 / – | 0 / 0 / – | 0.0 → 0.0 | 0/0 → 0/0 | too few (6 in first 14 d) |
| y62-engine-mount-replacement-cost-dubai-2026.html | 2026-08-01 | Indexed | 1 / 15 / 3.3 | 0 / 5 / 3.0 | 0.5 → 0.6 | 1/0 → 0/0 | 2.6 → 0.4 (0.16) |
| nissan-patrol-y62-cv-joint-replacement-cost-uae-2026.html | 2026-08-02 | Indexed | 0 / 17 / 5.6 | 1 / 5 / 4.8 | 0.6 → 0.6 | 0/0 → 0/0 | 1.7 → 0.4 (0.26) |
| y62-fuel-pressure-regulator-replacement-cost-dubai-2026.html | 2026-08-03 | Indexed | 1 / 37 / 6.3 | 0 / 5 / 7.6 | 1.3 → 0.6 | 0/0 → 0/0 | 3.9 → 1.0 (0.25) |
| nissan-patrol-y62-rear-differential-rebuild-cost-uae-2026.html | 2026-08-04 | Indexed | 0 / 6 / 11.8 | 0 / 0 / – | 0.2 → 0.0 | 0/0 → 0/0 | 3.5 → 0.2 (0.05) |
| y62-vk56-valve-cover-gasket-replacement-cost-dubai-2026.html | 2026-08-05 | Indexed | 0 / 10 / 10.0 | 0 / 4 / 3.8 | 0.4 → 0.4 | 0/0 → 0/0 | 1.8 → 0.4 (0.22) |
| nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026.html | 2026-08-06 | Indexed | 0 / 10 / 8.3 | 1 / 2 / 7.0 | 0.4 → 0.2 | 0/0 → 0/0 | too few (5 in first 14 d) |
| nissan-patrol-y62-paint-protection-film-cost-dubai-2026.html | 2026-08-08 | Indexed | 1 / 26 / 5.6 | 0 / 7 / 5.9 | 0.9 → 0.8 | 0/0 → 0/0 | 1.6 → 0.9 (0.55) |
| y62-rear-air-bag-replacement-cost-uae-2026.html | 2026-08-09 | Indexed | 0 / 4 / 6.0 | 0 / 0 / – | 0.1 → 0.0 | 0/0 → 0/0 | too few (9 in first 14 d) |
| nissan-patrol-y62-tow-bar-fitting-cost-dubai-2026.html | 2026-08-10 | Indexed | 4 / 21 / 15.2 | 0 / 4 / 5.0 | 0.8 → 0.4 | 1/0 → 0/0 | too few (19 in first 14 d) |
| y62-crankshaft-position-sensor-replacement-cost-dubai-2026.html | 2026-08-11 | Indexed | 2 / 21 / 7.1 | 0 / 4 / 5.0 | 0.8 → 0.4 | 0/0 → 0/0 | 6.3 → 0.7 (0.12) |
| nissan-patrol-y62-coolant-temperature-sensor-cost-uae-2026.html | 2026-08-12 | Indexed | 0 / 8 / 4.4 | 0 / 6 / 3.5 | 0.3 → 0.7 | 0/0 → 0/0 | 2.9 → 0.4 (0.13) |
| buying-a-used-nissan-patrol.html | 2026-08-17 | Indexed | 0 / 16 / 6.1 | 0 / 5 / 5.4 | 0.6 → 0.6 | 0/0 → 0/0 | 2.7 → 0.7 (0.24) |
| nissan-patrol-high-mileage.html | 2026-08-20 | Indexed | 0 / 69 / 5.7 | 3 / 26 / 4.9 | 2.5 → 2.9 | 0/0 → 0/0 | 16.9 → 2.4 (0.14) |
| nissan-patrol-engine-problems.html | 2026-08-24 | Indexed | 0 / 54 / 6.6 | 0 / 20 / 7.3 | 1.9 → 2.2 | 0/0 → 0/0 | 49.5 → 4.4 (0.09) |
| nissan-patrol-fuel-consumption.html | 2026-08-27 | Indexed | 3 / 1911 / 7.1 | 2 / 646 / 6.6 | 68.2 → 71.8 | 0/0 → 0/0 | 69.2 → 65.0 (0.94) |
| nissan-patrol-black-smoke.html | 2026-08-31 | Indexed | 5 / 174 / 5.9 | 0 / 59 / 4.9 | 6.2 → 6.6 | 0/0 → 0/0 | 6.4 → 5.9 (0.92) |
| nissan-patrol-engine-overheating.html | 2026-09-03 | Indexed | 2 / 181 / 5.4 | 1 / 54 / 4.6 | 6.5 → 6.0 | 0/0 → 0/0 | 8.4 → 5.0 (0.59) |
| nissan-patrol-shaking-at-high-speed.html | 2026-09-07 | Indexed | 0 / 128 / 5.9 | 2 / 58 / 5.3 | 4.6 → 6.4 | 0/0 → 0/0 | 6.0 → 5.5 (0.92) |
| nissan-patrol-best-year-to-buy.html | 2026-09-10 | Indexed | 0 / 219 / 5.6 | 0 / 53 / 5.7 | 7.8 → 5.9 | 0/0 → 0/0 | 22.7 → 5.2 (0.23) |
| nissan-patrol-major-service.html | 2026-09-14 | Indexed | 3 / 111 / 6.9 | 1 / 27 / 6.4 | 4.0 → 3.0 | 0/0 → 0/0 | 23.1 → 4.1 (0.18) |
| nissan-patrol-oil-leak.html | 2026-09-17 | Indexed | 3 / 169 / 6.3 | 0 / 57 / 5.6 | 6.0 → 6.3 | 1/0 → 0/0 | 10.6 → 4.7 (0.45) |
| nissan-patrol-warning-lights-meaning.html | 2026-09-18 | Indexed | 6 / 370 / 6.0 | 1 / 149 / 5.2 | 13.2 → 16.6 | 0/0 → 0/0 | 21.1 → 14.4 (0.68) |
| nissan-patrol-diesel-vs-petrol.html | 2026-09-21 | Indexed | 3 / 598 / 8.0 | 1 / 262 / 9.8 | 21.4 → 29.1 | 0/0 → 0/0 | 21.5 → 24.0 (1.12) |
| nissan-patrol-steering-problems.html | 2026-09-24 | Indexed | 2 / 163 / 5.0 | 0 / 54 / 4.9 | 5.8 → 6.0 | 0/0 → 0/0 | 8.6 → 5.4 (0.63) |
| nissan-patrol-not-starting.html | 2026-09-28 | Indexed | 8 / 544 / 5.0 | 5 / 399 / 4.4 | 19.4 → 44.3 | 0/0 → 0/0 | 19.7 → 41.2 (2.09) |
| nissan-patrol-vibration-when-driving.html | 2026-10-01 | Indexed | 2 / 93 / 5.0 | 0 / 103 / 4.9 | 3.3 → 11.4 | 0/0 → 0/0 | day 18 of first shown, too new |
| nissan-patrol-4wd-not-engaging.html | 2026-10-05 | **Unknown to Google** | 0 / 0 / – | 0 / 0 / – | 0.0 → 0.0 | 0/0 → 0/0 | never shown |
| nissan-patrol-losing-power.html | 2026-10-08 | Indexed | 2 / 119 / 4.5 | 3 / 113 / 4.1 | 4.2 → 12.6 | 0/0 → 1/0 | day 20 of first shown, too new |
| is-the-nissan-patrol-reliable-in-abu-dhabi.html | 2026-10-15 | Indexed | 0 / 10 / 7.0 | 0 / 41 / 5.4 | 0.4 → 4.6 | 0/0 → 0/0 | day 14 of first shown, too new |
| what-affects-nissan-patrol-maintenance-cost-in-abu-dhabi.html | 2026-10-19 | Indexed | 0 / 0 / – | 1 / 12 / 5.5 | 0.0 → 1.3 | 0/0 → 0/0 | day 9 of first shown, too new |
| nissan-patrol-brake-problems.html | 2026-10-22 | Indexed | 0 / 0 / – | 1 / 77 / 4.9 | 0.0 → 8.6 | 0/0 → 0/0 | day 9 of first shown, too new |

- **Not indexed: 1 post.** nissan-patrol-4wd-not-engaging went *backwards*, from "Discovered, not indexed" on 23 Oct to **"URL is unknown to Google"** at 28 days.
- **The merged servicing guide** is gone from the inspected set. It 301s to service-cost.
- **Index status:** the other 57 posts are indexed.

### By group

| Group | Posts | Impr/day then → now | Clicks then / now | Leads then / now / lifetime |
|---|---|---|---|---|
| May guides and cost posts | 16 | 270.4 → 200.2 * | 85 / 18 | 4 / 1 / 19 |
| Generic no-city posts (Aug–Oct) | 18 | 175.7 → 240.2 | 39 / 20 | 1 / 1 / 3 |
| Per-part cost posts (19 Jul–12 Aug) | 21 | 11.9 → 9.6 | 17 / 2 | 2 / 0 / 8 |
| Abu Dhabi | 3 | 0.7 → 6.1 | 0 / 2 | 0 / 0 / 0 |

\* The May "then" figure includes the week-40 spike on the Y62 complete guide: 2,546 impressions that week, 1,589 of them from the query "nissan patrol y61 y62 y63 present". Without it the guide is flat to rising, and the group is close to flat:

| ISO week | 36 | 37 | 38 | 39 | **40** | 41 | 42 | 43 | 44 |
|---|---|---|---|---|---|---|---|---|---|
| Impressions | 487 | 371 | 327 | 251 | **2,546** | 222 | 246 | 275 | 345 |

### The two-week fade on PG

- **Strict test:**
  - 42 eligible posts: 23 fell by more than half, 9 held and 10 grew. The median is 0.31.
  - The audit had 41 posts: 24 fell, 9 held, 8 grew, median 0.27.
  - The two new growers are nissan-patrol-not-starting (19.7 → 41.2 a day, 2.09) and diesel-vs-petrol (1.12).
- **Which generic posts hold:** reference topics hold best.

  | Post | Later/launch ratio |
  |---|---|
  | fuel-consumption | 0.94 |
  | diesel-vs-petrol | 1.12 |
  | shaking-at-high-speed | 0.92 |
  | black-smoke | 0.92 |
  | warning-lights | 0.68 |

  Single-fault and service posts fade:

  | Post | Later/launch ratio |
  |---|---|
  | engine-problems | 0.09 |
  | high-mileage | 0.14 |
  | major-service | 0.18 |
  | best-year-to-buy | 0.23 |
  | oil-leak | 0.45 |

- **Per-part cost posts fade hardest.** Every one of the 21 is below 0.6. The median like-for-like ratio is about 0.1.
- **The audit's "Y62 complete guide 10.8 → 54.7" growth figure is overstated** by the week-40 spike above. It is still a grower.

### Abu Dhabi posts (PG)

| Post | First shown | Lifetime clicks / impr | 23–31 Oct impr | Leads |
|---|---|---|---|---|
| nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026 | 21 Aug | 1 / 25 | 2 | 0 |
| is-the-nissan-patrol-reliable-in-abu-dhabi | 18 Oct | 0 / 59 | 41 | 0 |
| what-affects-nissan-patrol-maintenance-cost-in-abu-dhabi | 23 Oct | 1 / 12 | 12 | 0 |

- **Reliable-in-Abu-Dhabi** is in its second week at 4.6 impressions a day, with no clicks. It reaches day 28 on 14 Nov.
- **The 11-week-old specialist post** is at 0.3 a day. On PG, the Abu Dhabi angle still shows no demand that converts.

---

## 4. The audit's claims, re-tested

| Audit claim (23 Oct) | 2 Nov |
|---|---|
| TC: the fade holds without exception | **Holds** for the 13 posts first shown before October. **Not so far** for the 8 first shown 7–10 Oct (0.83 at days 14–21). Re-test after 6 Nov. |
| TC: blog doesn't pay for its schedule | **Holds.** 0 blog leads in 10 days; 2 lifetime. |
| PG: fade holds for most posts, not the oldest | **Holds,** with more growers (10). Reference posts hold; single-fault and per-part posts fade. |
| PG: Y62 guide grew 10.8 → 54.7 a day | **Overstated** by a one-week, one-query spike. Still a grower. |
| PG: what earns leads is close to a paid job | **Unchanged.** Too few leads in the new window (2) to test it. |
| Abu Dhabi: no clicks on either site | **No longer true:** 5 clicks across both sites since 21 Oct, 4 of them 23–31 Oct. Still 0 leads. |
| PG: service complete guide de-indexed | **Done:** merged and 301'd on 23 Oct. No effect on service-cost yet. |
| TC: y62-major-service not indexed | **Still not indexed,** now "Discovered" (61 days). |
| PG: 4wd-not-engaging not indexed | **Worse:** now "unknown to Google". |

## 5. Answers

### Should TC stay on Mon/Wed/Fri?

**No. Drop to one post a week (Monday) once the pipeline publishes again.**

- **For keeping three:**
  - The blog's impressions doubled per day.
  - The October-shown posts are holding at days 14–21.
  - TC's blog clicks rose to 0.89 a day.
- **Against:**
  - Leads are the goal. The blog produced 0 of TC's 20 leads in 10 days, 1 of 43 in the audit window, and 2 lifetime.
  - Blog landings almost never reach a service page. That is the audit's finding; onward paths were not re-measured.
  - TC's non-blog pages produced all 20 leads in the new window, and 98% all-time.
- **Why one, not none:** the new evidence that some posts hold justifies keeping one slot. That slot should go to topics tied to a bookable job with its own service page (valve body, brakes, HBMC). On PG, those convert best: 16 leads per 100 clicks for cost and job posts, against 2–6 for maintenance and problem posts.
- **Revisit on 16 Nov,** when the October cohort is past day 28. If it still holds and earns clicks, a second slot is defensible.

### Should PG keep its per-part cost posts?

**Keep the ones that have earned something. Merge the dead ones. Write no new ones.**

- **The case against new ones:**
  - The 21 posts together get 9.6 impressions a day. That is 2% of the blog's impressions, with 2 clicks and 0 leads in the new window.
  - Their fade is the steepest on the site.
- **The case for keeping some:** they have 8 lifetime leads from about 48 clicks, the best rate of any group. That rate comes almost entirely from posts already live, mostly tow bar (3).
- **The queue already has none,** so stopping them needs no queue change. It means not adding any back.

### Which posts to merge, update or leave

**Merge** (301 each merged URL, and mark its keyword done so the pipeline doesn't rewrite it):

| Site | Merge these | Into | Evidence |
|---|---|---|---|
| TC | gearbox-shudder, transmission-slipping, transmission-overheating | y62-gearbox-transmission-problems-dubai | 1–3 impressions each in 9 days, 0 clicks since 24 Sep |
| TC | radiator-sand-blockage | y62-overheating-dubai-summer | 0 impressions in 9 days; the target holds at 0.75 |
| TC | engine-repair-cost | y62-engine-problems-dubai | 1 impression in 9 days |
| TC | major-service-what-is-included | y62-service-interval-dubai-heat | never indexed in 61 days |
| TC | alignment-after-desert-driving, dune-bashing-damage | y62-desert-driving-preparation-uae | 0 impressions in 9 days; refresh before the Liwa season |
| PG | nissan-patrol-y62-rear-differential-rebuild-cost-uae-2026 | nissan-patrol-differential-repair-cost-uae | same topic, 0 clicks lifetime on both |
| PG | y62-abs-sensor-replacement-cost-dubai-2026 | nissan-patrol-warning-lights-meaning | 0 clicks lifetime |
| PG | nissan-patrol-y62-fourth-brake-light-replacement-dubai-2026 | nissan-patrol-brake-problems | 0 clicks, 9 impressions lifetime |
| PG | y62-fuel-injector-cleaning-cost-dubai-2026 | nissan-patrol-losing-power | 0 clicks lifetime; the target is growing and has a lead |
| PG | nissan-patrol-y62-cv-joint-replacement-cost-uae-2026 | nissan-patrol-vibration-when-driving | 1 click lifetime |
| PG | y62-rear-air-bag-replacement-cost-uae-2026 | no parent yet (PG has no suspension post) | 0 clicks, 17 impressions lifetime |

On TC, merges have to go through the generator or its copy pins: generators overwrite hand edits.

**Owner's call on PG:** two posts conflict with the Y62-only service rule. Neither is ranked below.
- y63-dashcam-installation-specialist-dubai-best-price-2026 is a Y63 post, and its slug contains "best". It has 1 lifetime lead.
- y61-super-safari-snorkel-fitting-cost-dubai-2026 frames a Y61 job as a service.

**Update** (no new URL):

| Site | Post | Change | Evidence |
|---|---|---|---|
| PG | nissan-patrol-fuel-consumption | "fuel economy", "per litre" and tank-capacity lines (keyword research) | 646 impressions and 2 clicks in 9 days (CTR 0.3%) at 6.6: the biggest blog page with the weakest CTR |
| PG | nissan-patrol-y62-vs-y63-dubai-comparison | title and intro for "y62 vs y63" | 309 impressions, 0 clicks in 9 days (7 in the audit window) |
| TC | y62-tyre-pressure-for-sand-uae | a road-pressure answer from the door placard near the top | holding at 6.0 a day, 69 impressions and 0 clicks in 9 days; the 110/mo "nissan patrol tyre pressure" family |
| PG | service-every-how-many-km, major-service, service-cost | the audit's change 6 (one question per post), still open | major-service faded to 0.18; how-many-km to 0.12 |

**Leave:**
- TC:
  - the 8 October-shown posts
  - the 4 Abu Dhabi posts, liwa-trip, diff-lock and tyre-pressure (apart from the update above)
  - the two lead earners: ac-not-cold-at-idle and suspension-hbmc-problems
  - cooling-ac-problems, service-diagnostics, transmission-fluid-change-interval, gearbox-transmission-problems (survivor) and engine-problems (survivor)
- PG: every May post, every generic no-city post, and the per-part posts with a click or lead.
- **nissan-patrol-high-mileage:** the audit's retitle (its change 7) is no longer urgent. The post took 3 clicks from 26 impressions at 4.9 in 9 days. Add the "how many kilometers can a Y62 do?" answer only.

### Should the 40 new topics change the queue order?

**Yes on both sites.** The case differs, and the new topics themselves are untested: their evidence is measured demand, not performance.

**PG: put the reference topics first.**
- **The current queue, oldest first:**
  - long-term-ownership Abu Dhabi, which is failing
  - 9 generic symptoms
  - 4 Abu Dhabi topics
- **The evidence:**
  - On PG, reference posts hold best: fuel-consumption 0.94, diesel-vs-petrol 1.12.
  - The May model-level guides earn the most leads: 19 lifetime.
  - The 20 new PG topics are that kind: specs, buying and engine reference.
- **Proposed order:**

| # | Topic | Monthly volume |
|---|---|---|
| 1 | fuel tank capacity and range | 210 + 110 |
| 2 | Patrol vs Land Cruiser | 170 (check why the old slot was archived first) |
| 3 | horsepower and torque | 170 |
| 4 | Armada vs Patrol | 140 |
| 5 | V6 or V8 | 140 + 20 |
| 6 | dimensions | 110 × 4 terms |
| 7 | weight | 110 |
| 8 | Titanium vs Platinum | 70, PG GSC position 2 |
| 9 | tyre sizes | 70 |

- **After those:** the generic symptoms (engine hesitation, fuel smell, vibration at idle, stalling, petrol consumption fix). Petrol consumption fix overlaps the fuel-consumption post and topic 1, so check it first.
- **Take out:** the 4 PG pending topics that the keyword research puts in TC clusters: coolant loss, temperature gauge rising, cooling system problems and suspension noise.
- **Hold:** all 5 Abu Dhabi topics until reliable-in-Abu-Dhabi reaches day 28 on 14 Nov. The queue head is one of them, so it publishes next once the image step is fixed.
- **Leave out of the front:** model-year and Nismo topics. Their volume is shopping intent, or includes the new model.

**TC: put job-tied topics with measured demand first.**
- **The current queue:**
  - 7 pending: 5 Abu Dhabi, plus "y62 best tyres for desert uae" and "y62 4wd light flashing uae"
  - then 15 unqueued `PUBLISHING_ORDER` slots
- **The trouble with the pending topics:** none has measured volume, and none earned a lead on the 4 Abu Dhabi posts already live.
- **Proposed order at one post a week:**

| # | Topic | Evidence |
|---|---|---|
| 1 | Y62 P0430 and P0420 | Labs 90/mo, PAA |
| 2 | Y62 valve body failure signs | 6 PAA questions; links to `/services/y62-valve-body-repair` |
| 3 | y62 brake pads dubai | an existing slot; Labs 30; GBP topic 18 Jan |
| 4 | Y62 radiator cap | 40 + 10 |
| 5 | HBMC fluid top-up and bleeding | 20 |

- **Then:** the queued 4wd-light post. The Abu Dhabi pending posts go only if limp-mode still holds and earns clicks at day 28 (8 Nov).
- **Take out:**
  - "y62 best tyres for desert uae": "best" is a banned word
  - y62 pre purchase inspection dubai, y62 battery replacement dubai heat and y62 alternator failure dubai: these are PG clusters
  - "y62 hbmc suspension problems dubai": the same words as the live y62-suspension-hbmc-problems-dubai in another order
- **Lower:** P0051, which overlaps PG's O2-sensor cost post.

---

## Ranked actions (10)

None of these was done in this pass. Each one changes the live sites or pipelines, so each one needs the go-ahead.

| # | Site | Action | Why |
|---|---|---|---|
| 1 | Both | **Find and fix the "generate hero image" failure.** Read the Railway execution logs for 26 Oct–2 Nov now: logs are kept for about 7 days, so 26 Oct's expire around today. | Nothing has published for 10 days. TC has requeued 2 keywords, and PG's 29 Oct and 2 Nov runs left no record. Both OpenAI keys are valid; they are different keys, and both failed from the same day. |
| 2 | TC | **Change the cron from Mon/Wed/Fri to Monday only** (`0 5 * * 1`), deployed so the live manifest carries it. | 0 blog leads in 10 days, 2 lifetime (§5) |
| 3 | PG | **Reorder the queue:** the 9 reference topics first, take out the 4 TC-cluster topics, hold the 5 Abu Dhabi ones to 14 Nov. | Reference posts hold (0.94–1.12); the queue head is an Abu Dhabi topic |
| 4 | TC | **Reorder the queue:** drop best-tyres, pre-purchase, battery, alternator and the HBMC duplicate; put P0430/P0420, valve body, brake pads, radiator cap and HBMC bleeding first; hold Abu Dhabi to 8 Nov. | Banned word, PG clusters, duplicate; new topics have measured demand and a service page |
| 5 | PG | **Update nissan-patrol-fuel-consumption** for fuel economy and tank capacity. | 646 impressions and 2 clicks in 9 days |
| 6 | PG | **Merge the 6 dead per-part posts** (table above) into their parents, with 301s, and add no new per-part cost topics. | 0–1 clicks lifetime each; steepest fade on the site |
| 7 | TC | **Merge the 8 dead posts** into 5 survivors through the generator; leave the October-shown cohort. | ≤3 impressions each in 9 days; the October group holds at 0.83 |
| 8 | PG | **Request indexing for nissan-patrol-4wd-not-engaging** (GSC's quota is account-wide, about one site a day). | Now "unknown to Google" at 28 days |
| 9 | PG | **Update the Y62 vs Y63 title and intro**, and split the service-interval cluster (the audit's change 6). | 309 impressions, 0 clicks in 9 days; interval posts at 0.12–0.18 |
| 10 | Both | **Re-measure on 16 Nov:** the TC October cohort past day 28, limp-mode and reliable-in-Abu-Dhabi at day 28, service-cost after the merge, and the first posts after the image fix. | Settles actions 2–4 |

## Not covered

- **Railway run logs.** `railway logs` returned nothing, so the hero-image error text is unknown. It may be OpenAI billing or quota, model access, or the vision check in `image_gen.py`. No image was generated to test it, because that would cost money.
- **Two days of data.** GSC data for 1 Nov is not final, so it is excluded. GA4 includes 1 Nov.
- **PG internal traffic** still can't be excluded by tag.
- **Queries** are a revealed sample, as in the audit.
- **Raw data** is in the session scratchpad only, which is temporary: `gsc.json`, `ga4.json`, `an.json` and `lfl.json`.
