#!/usr/bin/env python3
"""Regression test for copy_rules.py (and through it check_prose.py,
check_model_years.py and, for Round 6, check_claims.py).

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
    # Round 3: unverified figures
    ("HORSEPOWER", "The Y62's 5.6L VK56VD V8 produces 400hp, and all that power has to transfer."),
    ("HORSEPOWER", "Typical single-turbo Y62 upgrades produce 450-500hp compared to stock."),
    ("HORSEPOWER", "The TB48DE produces approximately 210 horsepower."),
    ("TORQUE", "The Y62 petrol V8 produces 560 Nm and has modern traction control."),
    ("TORQUE", "The VK56VD plugs go in at approximately 18 to 20 Nm."),
    ("Y63_DETAIL", "The Y63, launched in the UAE in 2024, is too new for a meaningful leak history."),
    ("Y63_DETAIL", "The Y63 only arrived in UAE showrooms in 2024, so used examples are rare."),
    ("Y63_DETAIL", "The Y63 uses a 3.5L twin-turbo V6 with a 9-speed automatic."),
    # Round 4
    # Round 5: modification offers
    ("MOD_OFFER", "We can advise on the right intercooler specification for your existing turbo kit and quote the job in full."),
    ("MOD_OFFER", "We fit lift kits and suspension lifts for serious dune work."),
    ("MOD_OFFER", "Book your ECU remap with Patrol Garage."),
    ("MOD_OFFER", "Get a quote for a stereo upgrade on your Y62."),
    ("MOD_OFFER", "Top Challenger installs performance exhausts and body kits."),
]
SITE_RULE_CASES = [
    ("OIL_GRADE", "Nissan Patrol Y62 models require full synthetic 5W-30 or 0W-20 oil."),
    ("OIL_GRADE", "Thick 20W-50 oil isn't recommended for modern Patrols."),
    ("OIL_GRADE", "Older engines can use a slightly thicker 10W-40."),
    ("OIL_GRADE", "Use a GL-5 rated 75W-140 gear oil for most Y62 applications."),
    ("INTERVAL_KM_MONTHS", "The most common service interval for a Patrol is every 10,000 km or 6 months."),
    ("INTERVAL_KM_MONTHS", "Nissan Patrol models in Dubai require service every 10,000km or 6 months under normal conditions."),
    ("INTERVAL_KM_MONTHS", "Change oil every 5,000km or 3 months in Dubai conditions."),
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
    "The Y63 uses a twin-turbo V6, replacing the Y62's 5.6L naturally aspirated V8.",
    "Ask how many Y63 services they have completed in 2025 and 2026.",
    "What does Y63 dashcam installation cost in Dubai in 2026?",
    "The VK56VD 5.6L V8 is strong, but it is thirsty and heat-sensitive.",
    "Nissan's North American owner's manual for the Armada, which uses the same VK56VD, recommends 0W-20, so the grade is not wrong for the engine.",
    "The owner's manual sets a 10,000 km or 12 month service interval.",
    "You will often see a 10,000km interval quoted as the standard for Patrol models.",
    "After a lift kit has been fitted by a third party, altered driveshaft angles accelerate CV wear.",
    "Aftermarket parts can affect the warranty.",
    "A conversion to a conventional shock setup is possible, particularly when fitting a lift kit.",
    "The Y63 uses a twin-turbo V6.",
    "We do not fit lift kits or turbo kits.",
    "Nismo variants run slightly hotter due to performance tuning.",
]


# Round 6 (2026-10-09): checked through unverified_claims() by check_claims,
# never by sentence_findings() / check_prose. First two are the live Liwa
# sentences; the rest are live copy found by the first scan of both sites.
UNVERIFIED_FIRE = [
    ("CROWD", "December is the busiest time out there because the Liwa International Festival 2027 runs from 11 December 2026 to 3 January 2027, and hundreds of Patrols make the same drive in the same week."),
    ("FIRST_HAND", "Cars at higher mileage that have had the fluid changed late are the ones we see with early wear in the valve body."),
    ("CROWD", "Today, we're proud to serve hundreds of Patrol owners across Dubai and the UAE."),
    ("CROWD", "Thousands of Y62 owners head to Liwa in December."),
    ("CROWD", "Most owners skip the transmission service entirely."),
    ("CROWD", "Many Patrols run hot on the climb."),
    ("CROWD", "Many owners forget to reinflate after a desert run."),
    ("CROWD", "Most Y62 owners think about engine oil at service intervals."),
    ("FIRST_HAND", "We often see cracked coolant tanks in August."),
    ("FIRST_HAND", "On a car with a documented history, we often find one component at fault."),
    ("FIRST_HAND", "In our experience, genuine module failure on the Y62 is uncommon."),
    ("FIRST_HAND", "We regularly see Y62 Patrols with overheated automatics."),
    ("FIRST_HAND", "Most cars we get have skipped a fluid change."),
    ("FIRST_HAND", "The Jatco JR710E transmission is the component we see fail most often."),
    ("FIRST_HAND", "We see this regularly at the workshop."),
]
UNVERIFIED_QUIET = [
    "On a higher-mileage gearbox, fluid that has been left too long between changes can contribute to early wear in the valve body.",
    "The highway leg can add thousands of kilometres over a season.",
    "This check suits most owners.",
    "Mussafah is inside Abu Dhabi, so for most owners in the city this is a local trip.",
    "The total cost for most Y62 owners depends on a few specific choices.",
    "We pull the fluid, check the colour and smell.",
    "If we see metal in the pan, we stop and tell you.",
    "What we see on the dipstick tells us how hot it has run.",
    "Many of the checks take ten minutes.",
    "Most of the load comes from soft sand.",
    "We often recommend a fluid change before a desert trip.",
    "Owners ask whether 4L is needed; it is for technical climbs.",
]


def main():
    failures = []
    for rule, sent in UNVERIFIED_FIRE:
        got = [r for r, _ in copy_rules.unverified_claims(sent)]
        if rule not in got:
            failures.append(f"MISS   {rule}: {sent[:90]}")
        elif any(r in copy_rules.UNVERIFIED_RULES for r, _ in copy_rules.sentence_findings(sent)):
            # In sentence_findings, check_prose would block it first, with no retry.
            failures.append(f"PROSE  {rule} reached sentence_findings: {sent[:70]}")
        else:
            print(f"  fires    {rule:12} {sent[:70]}")
    for sent in UNVERIFIED_QUIET:
        got = copy_rules.unverified_claims(sent)
        if got:
            failures.append(f"FALSE+ {got}: {sent[:90]}")
        else:
            print(f"  quiet    {sent[:80]}")
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

    # Per-site rules: fire where enabled, stay quiet where copy_rules_site.py
    # switches them off. Patrolgarage enables all; topchallenger disables 0W-20.
    for rule, sent in SITE_RULE_CASES:
        got = [r for r, _ in copy_rules.sentence_findings(sent)]
        if rule in copy_rules.DISABLED:
            if rule in got:
                failures.append(f"SITE   {rule} is disabled here but fired: {sent[:70]}")
            else:
                print(f"  off      {rule:12} (disabled on this site)")
        elif rule not in got:
            failures.append(f"MISS   {rule}: {sent[:90]}")
        else:
            print(f"  fires    {rule:12} {sent[:70]}")

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
        # Round 6 reaches the claims gate (and so the one regenerate), not prose.
        import check_claims
        crowd = Path(td) / "crowd.html"
        crowd.write_text("<html><head><title>Y62 desert prep</title></head><body><article>"
                         f"<p>{UNVERIFIED_FIRE[0][1]}</p><p>{UNVERIFIED_FIRE[1][1]}</p>"
                         "</article></body></html>", encoding="utf-8")
        rules = {a for _, a, _, _ in check_claims.review_items(crowd)}
        if rules != {"CROWD", "FIRST_HAND"}:
            failures.append(f"GUARD  check_claims missed CROWD/FIRST_HAND on a page: {rules}")
        if check_prose.check_file(crowd):
            failures.append("GUARD  check_prose blocked CROWD/FIRST_HAND (would skip the retry)")
        if check_claims.review_items(clean):
            failures.append("GUARD  check_claims flagged a clean page")
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
    print(f"[+] copy rules regression passed: {len(MUST_FIRE) + len(UNVERIFIED_FIRE)} must-fire, "
          f"{len(MUST_NOT_FIRE) + len(UNVERIFIED_QUIET)} must-not-fire, guard integration.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
