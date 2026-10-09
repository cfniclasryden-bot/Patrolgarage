#!/usr/bin/env python3
"""Copy pins: corrections to published copy that no rebuild may revert.

Added 2026-10-09, with the unverified-claims cleanup. Each entry is a raw-HTML
passage on a shipped page and its replacement. publish.publish() re-applies
every pin on every run, before journal_update and the deploy, so a refresh
(refresh_patch.py), a rebuild (build_service_pages.py) or a re-run patch script
that brings an old sentence back is corrected before it can ship.
scripts/test_copy_pins.py fails if any pinned passage is back on disk.

Semantics, per pin, per page:
  * the old passage is present  -> every occurrence is replaced (the FAQ
                                   JSON-LD copy of a sentence included)
  * it is absent and the new text is there (or the pin is a deletion)
                                -> already applied, nothing to do
  * neither is there            -> DRIFT: the copy changed under the pin.
                                   Reported loudly, never fatal to a publish;
                                   the test is what fails.

Replacements carry no double quotes (they land in JSON-LD strings unescaped)
and no em dashes. File mtimes are preserved; dates come from datePublished,
but nothing here should look like a content date change to anything else.

    python3 scripts/copy_pins.py            # apply, report
    python3 scripts/copy_pins.py --check    # report only, exit 1 on pending/drift
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Unverified-claims cleanup, 2026-10-09: every CROWD and FIRST_HAND finding of
# that day's scan (copy_rules.unverified_claims), reworded to a neutral general
# statement. This site has no premises, so no replacement may suggest a
# workshop, a bay, a team inspecting cars or a customer base.
#
# Later the same day: about.html (tenure and workshop claims), contact.html
# ("workshop only") and the homepage steps (no How It Works label, no
# drop-off or warranty wording) with the first-screen redesign. Then about.html's
# staff claim and the Abu Dhabi page's How It Works label.
PINS = {'about.html': [("Today, we're proud to serve hundreds of Patrol owners across Dubai and the UAE. ",
                 ''),
                (" We've earned our reputation as the go-to Patrol specialists not through "
                 'marketing, but through ten years of honest work.',
                 ''),
                ('From routine maintenance to complex engine work, suspension and HBMC repair to '
                 "full restorations, we've become the workshop Patrol owners trust.",
                 'Patrol Garage focuses on one car only: the Nissan Patrol Y62.'),
                ('We built Patrol Garage specifically around servicing this car—the right tools, '
                 'the right parts supply, and mechanics who can diagnose problems from the sound '
                 'the engine makes.',
                 'We built Patrol Garage specifically around this car, from the parts it needs to '
                 'the faults it is known for.')],
 'blog/best-oil-nissan-patrol-uae-heat.html': [('We regularly see Patrols with oil-related damage '
                                                'that could have been prevented with the right '
                                                'lubricant choice.',
                                                'Oil-related damage on a Patrol can often be '
                                                'prevented with the right lubricant choice.'),
                                               ('We regularly see Y62 Patrols brought in after '
                                                'highway drives where oil has literally cooked, '
                                                'turning black and losing its protective '
                                                'properties within just a few thousand kilometers.',
                                                'After hard highway driving, oil in a Y62 can '
                                                'literally cook, turning black and losing its '
                                                'protective properties within just a few thousand '
                                                'kilometers.'),
                                               ('Oil analysis services can help optimize your '
                                                'change intervals, but most UAE Patrol owners find '
                                                '6-month or 6,000km intervals provide excellent '
                                                'protection without unnecessary expense.',
                                                'Oil analysis services can help optimize your '
                                                'change intervals, and a 6-month or 6,000km '
                                                'interval is a sensible default without '
                                                'unnecessary expense.'),
                                               ('In our experience, they perform only marginally '
                                                'better than conventional oils in UAE heat while '
                                                'costing significantly more.',
                                                'In UAE heat, they tend to perform only marginally '
                                                'better than conventional oils while costing '
                                                'significantly more.'),
                                               ('<h2>Common Oil-Related Problems We See in Dubai '
                                                'Patrols</h2>',
                                                '<h2>Common Oil-Related Problems in Dubai '
                                                'Patrols</h2>')],
 'blog/buying-a-used-nissan-patrol.html': [('We see this regularly: a Y62 that looks immaculate on '
                                            'the outside but has transmission fluid that has never '
                                            'been changed.',
                                            'Watch for this: a Y62 that looks immaculate on the '
                                            'outside but has transmission fluid that has never '
                                            'been changed.'),
                                           ('We see a lot of Y62 transmissions come in for '
                                            'rebuilds that could have been avoided with a fluid '
                                            'change done at the right time.',
                                            'A Y62 transmission rebuild can often be avoided with '
                                            'a fluid change done at the right time.')],
 'blog/nissan-patrol-4wd-not-engaging.html': [('and many Patrols spend most of the year in '
                                               'stop-and-go traffic on Sheikh Zayed Road before '
                                               'they ever see an off-road track.',
                                               'and a Patrol can spend most of the year in '
                                               'stop-and-go traffic on Sheikh Zayed Road before it '
                                               'ever sees an off-road track.')],
 'blog/nissan-patrol-best-year-to-buy.html': [('and most Patrols here carry a dual life: school '
                                               'runs on Sheikh Zayed Road during the week, Big Red '
                                               'or Liwa on the weekend.',
                                               'and a Patrol here can carry a dual life: school '
                                               'runs on Sheikh Zayed Road during the week, Big Red '
                                               'or Liwa on the weekend.'),
                                              ('Many UAE owners who experience early gearbox '
                                               'problems have transmission fluid that has never '
                                               'been changed.',
                                               'If a Patrol develops early gearbox problems, check '
                                               'whether the transmission fluid has ever been '
                                               'changed.')],
 'blog/nissan-patrol-black-smoke.html': [('There are five causes we see most often, and the right '
                                          'diagnosis depends on which engine you have and when the '
                                          'smoke appears.',
                                          'There are five common causes, and the right diagnosis '
                                          'depends on which engine you have and when the smoke '
                                          'appears.')],
 'blog/nissan-patrol-engine-problems.html': [('but the reality is that the majority of engine '
                                              'problems we see at Patrol Garage come down to '
                                              'maintenance timing and oil spec, not factory '
                                              'faults.',
                                              'but in practice engine problems more often come '
                                              'down to maintenance timing and oil spec than to '
                                              'factory faults.')],
 'blog/nissan-patrol-fuel-consumption.html': [('The AC compressor is the biggest single factor, '
                                               'and it is one most owners underestimate.',
                                               'The AC compressor is the biggest single factor, '
                                               'and it is an easy one to underestimate.')],
 'blog/nissan-patrol-high-mileage.html': [('The Nissan Patrol has been on UAE roads long enough '
                                           'that plenty of Y62s launched in 2010 are now sitting '
                                           'at 200,000 km or more.',
                                           'The Nissan Patrol has been on UAE roads long enough '
                                           'that a Y62 from the 2010 launch can now be sitting at '
                                           '200,000 km or more.'),
                                          ('Many Y62s on the used market in Dubai, Al Quoz, and Al '
                                           'Aweer are commercial or family vehicles that have '
                                           'spent years in stop-and-go on Sheikh Zayed Road or '
                                           'Sheikh Mohammed Bin Zayed Road, where the evening '
                                           'average speed would embarrass a bicycle.',
                                           'A Y62 on the used market in Dubai, Al Quoz, or Al '
                                           'Aweer may be a commercial or family vehicle that has '
                                           'spent years in stop-and-go on Sheikh Zayed Road or '
                                           'Sheikh Mohammed Bin Zayed Road, where the evening '
                                           'average speed would embarrass a bicycle.'),
                                          ('The transmission, the HBMC suspension system, and the '
                                           'AC are the three areas we see most often on '
                                           'higher-mileage Y62s, roughly in that order of '
                                           'frequency.',
                                           'The transmission, the HBMC suspension system, and the '
                                           'AC are the three areas to watch most closely on '
                                           'higher-mileage Y62s.')],
 'blog/nissan-patrol-losing-power.html': [('Most owners with a power complaint have a repair that '
                                           'is far more straightforward than a new engine.',
                                           'A power complaint can have a repair that is far more '
                                           'straightforward than a new engine.')],
 'blog/nissan-patrol-major-service.html': [('most Y62 owners are better served letting a workshop '
                                            'handle the full major service and doing their own '
                                            'post-trip checks and visual inspections in between.',
                                            'if you own a Y62 you are usually better served '
                                            'leaving the full major service to a specialist and '
                                            'doing your own post-trip checks and visual '
                                            'inspections in between.')],
 'blog/nissan-patrol-overheating-dubai-summer-fix.html': [('Many Patrol owners disable temperature '
                                                           'warning systems accidentally, leaving '
                                                           'them unaware of developing problems.',
                                                           'It is easy to disable a temperature '
                                                           'warning system accidentally, leaving '
                                                           'you unaware of developing problems.')],
 'blog/nissan-patrol-service-cost-dubai.html': [('Many owners do twice-yearly AC service in '
                                                 'summer.',
                                                 'A twice-yearly AC service in summer is an option '
                                                 'worth considering.')],
 'blog/nissan-patrol-service-dubai-complete-guide.html': [('Skipping these milestones is the '
                                                           'single biggest cause of the expensive '
                                                           'failures we see.',
                                                           'Skipping these milestones is the '
                                                           'single biggest cause of expensive '
                                                           'failures.'),
                                                          ('Letting transmission fluid go beyond '
                                                           'its service life is the leading cause '
                                                           'of the Jatco gearbox failures we see '
                                                           'in Y62 Patrols — the maths strongly '
                                                           'favour the service schedule.',
                                                           'Letting transmission fluid go beyond '
                                                           'its service life is a leading cause of '
                                                           'Jatco gearbox failure in Y62 Patrols, '
                                                           'and the maths strongly favour the '
                                                           'service schedule.')],
 'blog/nissan-patrol-shaking-at-high-speed.html': [('We regularly see bent rims on Y62s that '
                                                    'owners have used off-road without reducing '
                                                    'tyre pressure, and the deformation is often '
                                                    'invisible to the naked eye until it is '
                                                    'measured on a balancing machine.',
                                                    'Rims on a Y62 used off-road without reducing '
                                                    'tyre pressure can bend, and the deformation '
                                                    'is often invisible to the naked eye until it '
                                                    'is measured on a balancing machine.')],
 'blog/nissan-patrol-transmission-rebuild-cost-dubai-aed.html': [('We regularly see Y62 Patrols '
                                                                  'with overheated 7-speed '
                                                                  'automatics where the complex '
                                                                  'valve body has warped, causing '
                                                                  'erratic shifting and eventual '
                                                                  'failure.',
                                                                  'An overheated 7-speed automatic '
                                                                  'in a Y62 Patrol can warp the '
                                                                  'complex valve body, causing '
                                                                  'erratic shifting and eventual '
                                                                  'failure.')],
 'blog/nissan-patrol-vibration-when-driving.html': [('We see this regularly at the workshop: '
                                                     'owners who have already paid for a wheel '
                                                     'balance and new tyres but still feel the '
                                                     'shake because the real cause was a worn tie '
                                                     'rod end or a warped front rotor.',
                                                     'Watch for this trap: paying for a wheel '
                                                     'balance and new tyres but still feeling the '
                                                     'shake because the real cause was a worn tie '
                                                     'rod end or a warped front rotor.'),
                                                    ('Add the fact that many UAE Patrol owners run '
                                                     'large-diameter aftermarket wheels, and you '
                                                     'have a vehicle that is more sensitive to '
                                                     'imbalance and alignment issues than the '
                                                     'factory setup.',
                                                     'If you run large-diameter aftermarket '
                                                     'wheels, you have a vehicle that is more '
                                                     'sensitive to imbalance and alignment issues '
                                                     'than the factory setup.'),
                                                    ('and many owners forget to reinflate after a '
                                                     'desert run.',
                                                     'so remember to reinflate after a desert '
                                                     'run.')],
 'blog/nissan-patrol-y61-dubai-complete-guide.html': [('Transmission cooling system inspection '
                                                       'becomes essential, with many owners adding '
                                                       'auxiliary coolers for improved reliability '
                                                       'in stop-and-go traffic.',
                                                       'Transmission cooling system inspection '
                                                       'becomes essential, and an auxiliary cooler '
                                                       'is one option for improved reliability in '
                                                       'stop-and-go traffic.')],
 'blog/nissan-patrol-y62-coolant-temperature-sensor-cost-uae-2026.html': [('We see this regularly, '
                                                                           'and the symptoms that '
                                                                           'bring owners in range '
                                                                           'from a check engine '
                                                                           'light and poor fuel '
                                                                           'economy to hard '
                                                                           'starting and fans '
                                                                           'running continuously '
                                                                           'even after shutdown.',
                                                                           'The symptoms of a '
                                                                           'failing sensor range '
                                                                           'from a check engine '
                                                                           'light and poor fuel '
                                                                           'economy to hard '
                                                                           'starting and fans '
                                                                           'running continuously '
                                                                           'even after shutdown.')],
 'blog/nissan-patrol-y62-cv-joint-replacement-cost-uae-2026.html': [('CV joints and axle shafts '
                                                                     'are among the components we '
                                                                     'see regularly.',
                                                                     'CV joints and axle shafts '
                                                                     'are among the components '
                                                                     'that need regular '
                                                                     'attention.')],
 'blog/nissan-patrol-y62-dubai-complete-guide.html': [('Most Dubai Patrols doing casual desert '
                                                       "days don't need anything beyond what "
                                                       'leaves the factory.',
                                                       'For casual desert days, a Dubai Patrol '
                                                       "doesn't need anything beyond what leaves "
                                                       'the factory.'),
                                                      ('The failures we see most often come from '
                                                       'skipped coolant changes and worn cooling '
                                                       'parts, not the engine itself.',
                                                       'The usual culprits are skipped coolant '
                                                       'changes and worn cooling parts, not the '
                                                       'engine itself.'),
                                                      ('The three we see most at the workshop are '
                                                       'transmission shudder',
                                                       'The three most common are transmission '
                                                       'shudder')],
 'blog/nissan-patrol-y62-oxygen-sensor-replacement-cost-dubai-2026.html': [('<p>Other things we '
                                                                            'commonly see in '
                                                                            'workshop:</p>',
                                                                            '<p>Other signs to '
                                                                            'watch for:</p>')],
 'blog/nissan-patrol-y62-paint-protection-film-cost-dubai-2026.html': [('We work on Y62 Patrols '
                                                                        'every day, and we see a '
                                                                        'lot of paint damage that '
                                                                        'PPF could have prevented.',
                                                                        'Paint damage that PPF '
                                                                        'could have prevented is '
                                                                        'easier to avoid than to '
                                                                        'fix.')],
 'blog/nissan-patrol-y62-problems-dubai.html': [('The most common differential failures we see '
                                                 'come from two sources:',
                                                 'The most common differential failures come from '
                                                 'two sources:'),
                                                ('All are predictable and preventable with the '
                                                 'right maintenance intervals — the problems we '
                                                 'see most are caused by following factory '
                                                 'schedules designed for temperate climates, not '
                                                 'UAE heat.',
                                                 'All are predictable and preventable with the '
                                                 'right maintenance intervals; the most common '
                                                 'cause is following factory schedules designed '
                                                 'for temperate climates, not UAE heat.')],
 'blog/nissan-patrol-y62-rear-differential-rebuild-cost-uae-2026.html': [('Most of the Y62 rear '
                                                                          'differential failures '
                                                                          'we see at Patrol Garage '
                                                                          'trace back to one root '
                                                                          'cause:',
                                                                          'Y62 rear differential '
                                                                          'failures often trace '
                                                                          'back to one root '
                                                                          'cause:')],
 'blog/nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026.html': [('The Jatco JR710E '
                                                                     'transmission is the '
                                                                     'component we see fail most '
                                                                     'often on high-mileage Y62s '
                                                                     'in UAE conditions.',
                                                                     'The Jatco JR710E '
                                                                     'transmission is one of the '
                                                                     'components most prone to '
                                                                     'failure on high-mileage Y62s '
                                                                     'in UAE conditions.'),
                                                                    ('so most owners with a Y62 '
                                                                     'that needs one or two '
                                                                     'specific jobs are better '
                                                                     'served fixing what they '
                                                                     'have,',
                                                                     'so if your Y62 needs one or '
                                                                     'two specific jobs, you are '
                                                                     'usually better served fixing '
                                                                     'what you have,'),
                                                                    ('The first sign most owners '
                                                                     'notice is a shudder or '
                                                                     'vibration on light throttle,',
                                                                     'The first sign to look for '
                                                                     'is a shudder or vibration on '
                                                                     'light throttle,')],
 'blog/nissan-patrol-y62-throttle-body-cleaning-cost-dubai.html': [('In a temperate climate, many '
                                                                    'owners go 80,000 km or more '
                                                                    'without issue.',
                                                                    'In a temperate climate, a Y62 '
                                                                    'can go 80,000 km or more '
                                                                    'without issue.')],
 'blog/nissan-patrol-y62-tow-bar-fitting-cost-dubai-2026.html': [('What surprises most owners is '
                                                                  'how affordable a proper tow bar '
                                                                  'fitting actually is compared to '
                                                                  'what the dealership charges for '
                                                                  'accessories.',
                                                                  'A proper tow bar fitting can be '
                                                                  'more affordable than you might '
                                                                  'expect compared to what the '
                                                                  'dealership charges for '
                                                                  'accessories.'),
                                                                 ('We see a lot of Y62s with '
                                                                  'aftermarket tow bars fitted at '
                                                                  'varying quality levels, and the '
                                                                  'price difference',
                                                                  'Aftermarket tow bars on a Y62 '
                                                                  'are fitted at varying quality '
                                                                  'levels, and the price '
                                                                  'difference'),
                                                                 ('Yes, and it is something most '
                                                                  'owners do not think about until '
                                                                  'corrosion sets in.',
                                                                  'Yes, and it is easy to overlook '
                                                                  'until corrosion sets in.')],
 'blog/nissan-patrol-y62-transmission-problems-dubai.html': [('We regularly see Y62 Patrols with '
                                                              'transmission issues that could have '
                                                              'been prevented with early '
                                                              'intervention.',
                                                              'Transmission issues on a Y62 Patrol '
                                                              'can often be prevented with early '
                                                              'intervention.'),
                                                             ("Let's dive into the real-world "
                                                              'transmission issues we see in Dubai '
                                                              'and what you can actually do about '
                                                              'them.',
                                                              "Let's dive into the real-world "
                                                              'transmission issues in Dubai and '
                                                              'what you can actually do about '
                                                              'them.'),
                                                             ('Many owners imported from Japan or '
                                                              'Canada find that sourcing '
                                                              'replacement transmissions requires '
                                                              'careful attention to gear ratios '
                                                              'and compatibility.',
                                                              'If your Patrol was imported from '
                                                              'Japan or Canada, sourcing a '
                                                              'replacement transmission requires '
                                                              'careful attention to gear ratios '
                                                              'and compatibility.'),
                                                             ("We've seen too many Y62 owners skip "
                                                              'fluid changes to save money, then '
                                                              'face a rebuild bill two years '
                                                              'later.',
                                                              'Skipping fluid changes to save '
                                                              'money can lead to a rebuild bill '
                                                              'two years later.')],
 'blog/y62-abs-sensor-replacement-cost-dubai-2026.html': [('On a dry motorway in normal '
                                                           'conditions, most drivers would not '
                                                           'notice any difference.',
                                                           'On a dry motorway in normal '
                                                           'conditions, you might not notice any '
                                                           'difference.'),
                                                          ('In our experience, genuine module '
                                                           'failure on the Y62 is uncommon before '
                                                           '200,000 km.',
                                                           'Genuine module failure on the Y62 is '
                                                           'uncommon before 200,000 km.')],
 'blog/y62-crankshaft-position-sensor-replacement-cost-dubai-2026.html': [('The Y62 models most '
                                                                           'commonly presenting '
                                                                           'with this fault in our '
                                                                           'experience are '
                                                                           'high-mileage examples '
                                                                           'in the 150,000 km to '
                                                                           '250,000 km range.',
                                                                           'The fault is more '
                                                                           'likely on high-mileage '
                                                                           'examples in the '
                                                                           '150,000 km to 250,000 '
                                                                           'km range.')],
 'blog/y62-engine-mount-replacement-cost-dubai-2026.html': [('The result is that we regularly see '
                                                             'Y62s come in at 90,000 km with '
                                                             'mounts that have softened and '
                                                             'cracked enough to need replacement.',
                                                             'The result is that a Y62 at 90,000 '
                                                             'km can have mounts that have '
                                                             'softened and cracked enough to need '
                                                             'replacement.')],
 'blog/y62-fuel-injector-cleaning-cost-dubai-2026.html': [('Most owners assume it is just the '
                                                           'heat.',
                                                           'It is easy to assume it is just the '
                                                           'heat.')],
 'blog/y62-fuel-pressure-regulator-replacement-cost-dubai-2026.html': [('Y62s with higher mileage '
                                                                        '(above 120,000 km) are '
                                                                        'the ones we see most '
                                                                        'often with fuel system '
                                                                        'pressure faults.',
                                                                        'Fuel system pressure '
                                                                        'faults are more likely on '
                                                                        'Y62s with higher mileage '
                                                                        '(above 120,000 km).'),
                                                                       ('most owners have the car '
                                                                        'back the same day if they '
                                                                        'bring it in before '
                                                                        'midday.',
                                                                        'the job can often be '
                                                                        'finished the same day.')],
 'blog/y62-vk56-valve-cover-gasket-replacement-cost-dubai-2026.html': [('We see this regularly at '
                                                                        'Patrol Garage, especially '
                                                                        'on Y62 models with higher '
                                                                        'mileage.',
                                                                        'The fault is more likely '
                                                                        'on Y62 models with higher '
                                                                        'mileage.')],
 'blog/y62-water-pump-replacement-cost-uae-2026.html': [('We specialise in Nissan Patrols and '
                                                         'carry common Y62 cooling parts in stock, '
                                                         'which avoids the two to four day wait '
                                                         'for dealer parts ordering that many '
                                                         'owners run into elsewhere.',
                                                         'Sourcing common Y62 cooling parts in '
                                                         'advance can avoid the two to four day '
                                                         'wait for dealer parts ordering.')],
 'contact.html': [('Most Patrol owners reach us from Deira, Mirdif, Nad Al Sheba, Al Quoz, '
                   'Business Bay and Sharjah.',
                   'Send us a message with the symptom and we will take it from there.'),
                  ('Worth repeating before you get in touch: this is a Nissan Patrol Y62 workshop '
                   'only.',
                   'Worth repeating before you get in touch: Nissan Patrol Y62 only.')],
 'index.html': [('<div class="section-num">01 — How It Works</div>',
                 '<div class="section-num">01 · Start Here</div>'),
                ('<h2>Drop it off.<br>Drive it back.</h2>',
                 '<h2>One message.<br>A clear next step.</h2>'),
                ('<p>A four-step process, no surprises. You hear from us before any work '
                 'happens.</p>',
                 '<p>Tell us what the car is doing and you get a plain reply on what it could be '
                 'and what comes next.</p>'),
                ('<h3>Send the Issue</h3>', '<h3>Describe the Fault</h3>'),
                ("<p>Message on WhatsApp or call. Describe the problem. We'll tell you what we "
                 "suspect and what it'll likely cost.</p>",
                 '<p>What the car is doing, when it started and the mileage. Text, a voice note or '
                 'a video all work.</p>'),
                ('<h3>Bring It In</h3>', '<h3>Get a Straight Answer</h3>'),
                ('<p>Message us and we confirm the drop-off point and a time. We diagnose properly '
                 '— no guessing, no parts roulette.</p>',
                 '<p>We reply with the likely causes and how urgent it looks, so you know what you '
                 'are dealing with.</p>'),
                ('<h3>Drive It Out</h3>', '<h3>Back on the Road</h3>'),
                ('<p>Repairs done with genuine parts where it matters. Warranty on every job. '
                 'Pickup and delivery on request.</p>',
                 '<p>Repairs done with genuine parts where it matters, and you hear from us as '
                 'soon as the car is ready.</p>')],
 'nissan-patrol-abu-dhabi.html': [('<div class="section-num">01 &mdash; How It Works</div>',
                                   '<div class="section-num">01 · Booking</div>')],
 'services/y62-major-service-dubai.html': [('Most Patrols in Dubai are better served on a shorter '
                                            'rhythm than the book interval, and we will tell you '
                                            'what yours actually needs based on how you drive it.',
                                            'In Dubai conditions a shorter rhythm than the book '
                                            'interval is usually the better choice, and we will '
                                            'tell you what yours actually needs based on how you '
                                            'drive it.')]}


def apply_page(rel, pins, write=True):
    """(applied, already, drift) for one page."""
    path = ROOT / rel
    if not path.exists():
        return 0, 0, [f"{rel}: page missing"]
    text = path.read_text(encoding="utf-8")
    new_text, applied, already, drift = text, 0, 0, []
    for old, new in pins:
        if old in new_text:
            new_text = new_text.replace(old, new)
            applied += 1
        elif new == "" or new in new_text:
            already += 1
        else:
            drift.append(f"{rel}: neither the pinned passage nor its replacement is on the page: {old[:80]!r}")
    if write and new_text != text:
        st = path.stat()
        path.write_text(new_text, encoding="utf-8")
        os.utime(path, (st.st_atime, st.st_mtime))
    return applied, already, drift


def apply_all(write=True):
    totals, drift = [0, 0], []
    for rel, pins in PINS.items():
        a, al, d = apply_page(rel, pins, write)
        totals[0] += a
        totals[1] += al
        drift += d
    return totals[0], totals[1], drift


def main(argv):
    check = "--check" in argv
    applied, already, drift = apply_all(write=not check)
    total = sum(len(p) for p in PINS.values())
    verb = "pending" if check else "applied"
    print(f"[copy_pins] {total} pin(s) on {len(PINS)} page(s): {applied} {verb}, {already} already in place")
    for d in drift:
        print(f"[!] copy_pins DRIFT: {d}")
    if check and (applied or drift):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
