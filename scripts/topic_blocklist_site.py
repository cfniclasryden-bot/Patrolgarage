"""Per-site topic bans for topic_blocklist.py (that module is identical in both repos).

patrolgarage.ae, 2026-11-20 (BLOG-AUDIT-2026-11-20 §6.3): no cost or price posts.
PG publishes no prices, so a cost post cannot answer its own query, and the
per-part cost posts were the ones that read like a quote and drew calls for work
the partner workshop does not do (tow bar: 4 taps from 9 clicks). The 21 per-part
cost posts faded fastest of any group (BLOG-REMEASURE-2026-11-02).
"""
EXTRA_TOPICS = {
    "cost / price posts (PG)": r"\b(?:cost|costs|price|prices|pricing|priced|how\s+much|aed)\b",
}
