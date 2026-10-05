#!/usr/bin/env python3
"""Regression test for copy_rules.py (and through it check_prose.py and
check_model_years.py).

    python3 scripts/test_copy_rules.py

Exit 0 = every case behaves. Identical in topchallenger-site and Patrolgarage.

MUST_FIRE sentences are real copy that was live on patrolgarage.ae until
2026-10-05. MUST_NOT_FIRE are the true statements each rule has to leave
alone: the vehicle's own history, Y61 comparison copy, a negated service
claim, an ordinary cost explanation with no figure, calendar years.
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import copy_rules            # noqa: E402
import check_model_years     # noqa: E402
import check_prose           # noqa: E402

MUST_FIRE = [
    # PRICE
    ("PRICE", "Replacing the coolant temperature sensor costs between AED 150 and AED 350 all-in."),
    ("PRICE", "Labour at a specialist workshop typically runs AED 300 to AED 600 for the Y62."),
    ("PRICE", "The total lands between AED 1,320 and AED 1,780 depending on the service advisor."),
    ("PRICE", "Expect to pay 4,500 AED at the dealer."),
    ("PRICE", "Understanding what to look for can save you thousands of dirhams."),
    # Y61_SERVICE
    ("Y61_SERVICE", "We fit snorkels regularly, we know the Y61 airbox routing well, and we stock Safari Snorkels and ARB kits for common GCC-spec Y61 configurations."),
    ("Y61_SERVICE", "Patrol Garage works on Y61 and Y62 Patrols."),
    ("Y61_SERVICE", "We diagnose Y61, Y62, and Y63 — same-day quotes via WhatsApp."),
    ("Y61_SERVICE", "We work on Patrol models from Y61 through to the current Y63."),
    ("Y61_SERVICE", "Patrol Garage specializes in all Patrol models from Y61 to the latest Y63."),
    # TENURE
    ("TENURE", "10+ Years in Business"),
    ("TENURE", "500+ Patrols Serviced"),
    ("TENURE", "We've serviced thousands of Patrols, and the pattern is clear."),
    ("TENURE", "We've been rebuilding Patrol transmissions for over a decade."),
    ("TENURE", "We've been working on Y62 Patrols since the model launched in the UAE in 2010."),
    ("TENURE", "At Patrol Garage, we've serviced hundreds of Y62s since they launched in the UAE in 2010."),
    ("TENURE", "Learn about our team of Nissan Patrol specialists with 10+ years of experience."),
    # REFRESH
    ("REFRESH", "The Y62, launched in the UAE in 2010 and refreshed in 2016 and again in 2020, is a different animal."),
    ("REFRESH", "If the Y62 is a 2010 to 2015 pre-refresh model with original injectors, book it in."),
    ("REFRESH", "On newer Y62 models (the 2020 refresh onward), the rear bumper has integrated sensors."),
    ("REFRESH", "Refreshed 2020-onwards Y62 Platinums have fewer kilometres on them."),
    ("REFRESH", "Confirm your model year: 2010 to 2015, 2016 to 2019 mid-cycle, or 2020 onwards."),
]

MUST_NOT_FIRE = [
    "The Y62 has been on UAE roads since 2010, and every summer the pattern repeats.",
    "A 2012 model is now over a decade old and may have 180,000 kilometres on the clock.",
    "The Y61 uses the TB48 petrol V8, a simpler engine than the Y62's VK56VD.",
    "The Y61 is no longer serviced at Patrol Garage, but this guide is for owners researching it.",
    "As with the TB48, the Y61 falls outside what Patrol Garage services.",
    "We work on the Y62 only, not the Y61.",
    "What the job costs depends on whether the injectors can be cleaned or need replacing.",
    "Ask for an itemised quote before any work starts.",
    "Ask how many Y63 services they have completed in 2025 and 2026.",
    "Message us on WhatsApp for a quote on your car.",
    "We see this pattern regularly.",
    "The fan runs at 2,000 rpm.",
]


def main():
    failures = []
    for rule, sent in MUST_FIRE:
        got = [r for r, _ in copy_rules.sentence_findings(sent)]
        if rule not in got:
            failures.append(f"MISS   {rule}: {sent[:90]}")
        else:
            print(f"  fires    {rule:12} {sent[:70]}")
    for sent in MUST_NOT_FIRE:
        got = copy_rules.sentence_findings(sent)
        if got:
            failures.append(f"FALSE+ {got}: {sent[:90]}")
        else:
            print(f"  quiet    {sent[:80]}")

    # Through the guards themselves, on a real file, in body AND head scopes.
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / "case.html"
        f.write_text(
            '<html><head><title>Y62 Service</title>'
            '<meta name="description" content="Y62 service in Dubai costs AED 800 to 2,500.">'
            '<script type="application/ld+json">{"@type":"FAQPage","mainEntity":[{"@type":'
            '"Question","name":"How much?","acceptedAnswer":{"@type":"Answer","text":'
            '"It costs AED 900."}}]}</script></head><body>'
            '<p>It was refreshed in 2016 and again in 2020.</p></body></html>', encoding="utf-8")
        prose = check_prose.check_file(f)
        if not any("PRICE [meta]" in x for x in prose):
            failures.append("GUARD  check_prose missed a price in the meta description")
        if not any("PRICE [json-ld]" in x for x in prose):
            failures.append("GUARD  check_prose missed a price in FAQ JSON-LD")
        if not check_model_years.review_items(f):
            failures.append("GUARD  check_model_years missed 'refreshed in 2016'")
        clean = Path(td) / "clean.html"
        clean.write_text("<html><head><title>Y62</title></head><body><p>The Y62 has been "
                         "on UAE roads since 2010.</p></body></html>", encoding="utf-8")
        # Chrome is not copy: a Y61 nav link next to "Patrol Garage" and a
        # "Services" menu item once read as a Y61 service claim (2026-10-05).
        chrome = Path(td) / "chrome.html"
        chrome.write_text("<html><head><title>Y61 vs Y62 | Patrol Garage</title></head><body>"
                          "<header><nav><a>Services</a><a>Patrol Garage</a><a>Y61 guide</a></nav>"
                          "</header><h1>Which Patrol?</h1><p>The Y61 uses a TB48.</p>"
                          "<footer>Patrol Garage services</footer></body></html>", encoding="utf-8")
        if check_prose.check_file(chrome):
            failures.append("GUARD  header/nav/footer chrome was read as copy")
        if check_prose.check_file(clean) or check_model_years.review_items(clean):
            failures.append("GUARD  a clean page was flagged")
        else:
            print("  ok       guards fire on head + body scopes, stay quiet on a clean page")

    print()
    if failures:
        print(f"[!] copy rules regression FAILED — {len(failures)} problem(s):")
        for x in failures:
            print("    " + x)
        return 1
    print(f"[+] copy rules regression passed: {len(MUST_FIRE)} must-fire, "
          f"{len(MUST_NOT_FIRE)} must-not-fire, guard integration.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
