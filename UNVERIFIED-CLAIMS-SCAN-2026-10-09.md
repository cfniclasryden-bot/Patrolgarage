# Unverified-claims scan, 2026-10-09

> **Resolved 2026-10-09 (same day).** Every finding below was reworded to a neutral general statement and saved as a copy pin (topchallenger: `site_config.COPY_PINS`, plus `build_pages.py` for the homepage; patrolgarage: `scripts/copy_pins.py`, re-applied by `publish()` on every run, plus `build_service_pages.py`). One finding is kept on purpose: the owner's pinned festival sentence on topchallenger `y62-desert-driving-preparation-uae`, now the only baseline entry. The tables below are the pre-cleanup record.

First scan of every shipped page on both sites with the Round 6 rules in `scripts/copy_rules.py`
(`CROWD`: a crowd or volume count followed by a claim about behaviour; `FIRST_HAND`: a first-hand
workshop observation). Checked through `check_claims.py`. **Report only: nothing below was edited.**
Every finding is frozen in `scripts/unverified_claims_baseline.json`; `test_check_claims.py` tolerates
exactly those and fails on any new one. Remove an entry when its page is fixed.

Not counted as findings: scoping phrases ("for most owners in the city this is a local trip",
"applies to most Y62 Patrols"), units ("thousands of kilometres"), and "most owners" with no claim after it.

## topchallenger.ae

48 shipped pages scanned (26 blog posts, every post file on disk). **14 findings on 11 pages**: 8 CROWD, 6 FIRST_HAND.

Note: the `a lot of Patrols` finding on y62-desert-driving-preparation-uae is inside the owner's own
COPY_PINS festival sentence (site_config.py, 2026-09-18). Changing it is the owner's call.

| Page | Rule | Matched | Sentence |
|---|---|---|---|
| `blog/y62-alignment-after-desert-driving-dubai.html` | FIRST_HAND | we typically see | After a hard run, we typically see a combination of toe drift and camber shift rather than one or the other in isolation. |
| `blog/y62-coolant-leak-dubai.html` | FIRST_HAND | failures we see | On higher-mileage Y62s, this is one of the more quietly damaging failures we see. |
| `blog/y62-coolant-leak-dubai.html` | CROWD | most people | Bearing noise is the tell most people know to listen for, but an eroded impeller can have perfect bearings. |
| `blog/y62-desert-driving-preparation-uae.html` | CROWD | most drivers | For general dune driving in UAE conditions, dropping to around 14 to 18 PSI is where most drivers find the car works well. |
| `blog/y62-desert-driving-preparation-uae.html` | CROWD | a lot of Patrols | It sits in the Liwa area, where the Liwa International Festival 2027 runs from 11 December 2026 to 3 January 2027, which is the reason a lot of Patrols get driven hard in December. |
| `blog/y62-engine-problems-dubai.html` | CROWD | many Y62 owners | Because of the sustained heat, dust, and stop-start driving that UAE conditions impose, many Y62 owners shorten their oil change intervals relative to what the manufacturer's base schedule specifies for temperate climates. |
| `blog/y62-engine-repair-cost-dubai.html` | FIRST_HAND | we tend to find | Where the service history is documented and the oil has been changed consistently, we tend to find that the job stays at the timing chain and guide level. |
| `blog/y62-major-service-what-is-included-dubai.html` | CROWD | most owners | The JR710E gearbox is a sealed unit with no dipstick, so most owners have no visibility on fluid condition between services. |
| `blog/y62-overheating-dubai-summer.html` | FIRST_HAND | we often find | On a car with a documented service history where coolant has been changed regularly and the system has been inspected, we often find one component at fault and the rest of the system in good condition. |
| `blog/y62-overheating-dubai-summer.html` | FIRST_HAND | we typically find | On a car at high mileage where service records are sparse or missing, we typically find multiple things running below where they should be. |
| `blog/y62-radiator-sand-blockage-dubai.html` | CROWD | most owners | The blockage is slow, which is why most owners do not notice it until the temperature gauge starts climbing in heavy Sheikh Zayed Road traffic, then drops again on the motorway. |
| `blog/y62-suspension-sagging-dubai.html` | FIRST_HAND | we usually find | Where the service history is documented and the owner acts on symptoms early, we usually find one primary cause and everything else still within tolerance. |
| `blog/y62-transmission-fluid-change-interval-dubai.html` | CROWD | many Y62 owners | For UAE driving conditions, a 40,000 km interval is a sensible upper limit, and many Y62 owners in this market are better served by going shorter. |
| `index.html` | CROWD | most people | The gearbox runs closer to its thermal limit here than it was designed to, the HBMC suspension has its own failure pattern, and the VK56VD hides a timing chain job behind a noise most people ignore. |

## patrolgarage.ae

68 shipped pages scanned (56 blog posts, every post file on disk). **62 findings on 38 pages**: 30 CROWD, 32 FIRST_HAND.

Includes nissan-patrol-losing-power, published by the cron at 05:00 UTC the same day.
Patrol Garage has no premises, so every FIRST_HAND finding there also implies a workshop it does not have.

| Page | Rule | Matched | Sentence |
|---|---|---|---|
| `about.html` | CROWD | hundreds of Patrol owners | Today, we're proud to serve hundreds of Patrol owners across Dubai and the UAE. |
| `blog/best-oil-nissan-patrol-uae-heat.html` | FIRST_HAND | We regularly see | We regularly see Patrols with oil-related damage that could have been prevented with the right lubricant choice. |
| `blog/best-oil-nissan-patrol-uae-heat.html` | FIRST_HAND | We regularly see | We regularly see Y62 Patrols brought in after highway drives where oil has literally cooked, turning black and losing its protective properties within just a few thousand kilometers. |
| `blog/best-oil-nissan-patrol-uae-heat.html` | CROWD | most UAE Patrol owners | Oil analysis services can help optimize your change intervals, but most UAE Patrol owners find 6-month or 6,000km intervals provide excellent protection without unnecessary expense. |
| `blog/best-oil-nissan-patrol-uae-heat.html` | FIRST_HAND | In our experience | In our experience, they perform only marginally better than conventional oils in UAE heat while costing significantly more. |
| `blog/best-oil-nissan-patrol-uae-heat.html` | FIRST_HAND | Problems We See | Common Oil-Related Problems We See in Dubai Patrols The most frequent issues include accelerated oil consumption, timing chain stretch from inadequate lubrication, and VVT system problems caused by oil breakdown in extreme heat. |
| `blog/buying-a-used-nissan-patrol.html` | FIRST_HAND | We see this regularly | We see this regularly: a Y62 that looks immaculate on the outside but has transmission fluid that has never been changed. |
| `blog/buying-a-used-nissan-patrol.html` | FIRST_HAND | We see a lot | We see a lot of Y62 transmissions come in for rebuilds that could have been avoided with a fluid change done at the right time. |
| `blog/nissan-patrol-4wd-not-engaging.html` | CROWD | many Patrols | Ambient temperatures regularly hit 45 to 50 degrees Celsius in summer, sand and fine dust work their way into electrical connectors and actuator mechanisms, and many Patrols spend most of the year in stop-and-go traffic on Sheikh Zayed Road before they ever see an off-road track. |
| `blog/nissan-patrol-best-year-to-buy.html` | CROWD | most Patrols | Ambient temperatures in Dubai hit 45 to 50°C in summer, tarmac can exceed 70°C, and most Patrols here carry a dual life: school runs on Sheikh Zayed Road during the week, Big Red or Liwa on the weekend. |
| `blog/nissan-patrol-best-year-to-buy.html` | CROWD | Many UAE owners | Many UAE owners who experience early gearbox problems have transmission fluid that has never been changed. |
| `blog/nissan-patrol-black-smoke.html` | FIRST_HAND | we see most | There are five causes we see most often, and the right diagnosis depends on which engine you have and when the smoke appears. |
| `blog/nissan-patrol-engine-problems.html` | FIRST_HAND | problems we see | Per UAE consumer protection guidelines , vehicle owners have rights when manufacturer defects appear within warranty, but the reality is that the majority of engine problems we see at Patrol Garage come down to maintenance timing and oil spec, not factory faults. |
| `blog/nissan-patrol-fuel-consumption.html` | CROWD | most owners | The AC compressor is the biggest single factor, and it is one most owners underestimate. |
| `blog/nissan-patrol-high-mileage.html` | CROWD | plenty of Y62s | Ask about your Patrol → The Nissan Patrol has been on UAE roads long enough that plenty of Y62s launched in 2010 are now sitting at 200,000 km or more. |
| `blog/nissan-patrol-high-mileage.html` | CROWD | Many Y62s | Many Y62s on the used market in Dubai, Al Quoz, and Al Aweer are commercial or family vehicles that have spent years in stop-and-go on Sheikh Zayed Road or Sheikh Mohammed Bin Zayed Road, where the evening average speed would embarrass a bicycle. |
| `blog/nissan-patrol-high-mileage.html` | FIRST_HAND | we see most | The transmission, the HBMC suspension system, and the AC are the three areas we see most often on higher-mileage Y62s, roughly in that order of frequency. |
| `blog/nissan-patrol-losing-power.html` | CROWD | Most owners | Most owners with a power complaint have a repair that is far more straightforward than a new engine. |
| `blog/nissan-patrol-major-service.html` | CROWD | most Y62 owners | In practice, and we accept we are hardly a neutral party here, most Y62 owners are better served letting a workshop handle the full major service and doing their own post-trip checks and visual inspections in between. |
| `blog/nissan-patrol-overheating-dubai-summer-fix.html` | CROWD | Many Patrol owners | Many Patrol owners disable temperature warning systems accidentally, leaving them unaware of developing problems. |
| `blog/nissan-patrol-service-cost-dubai.html` | CROWD | Many owners | Many owners do twice-yearly AC service in summer. |
| `blog/nissan-patrol-service-dubai-complete-guide.html` | FIRST_HAND | failures we see | Skipping these milestones is the single biggest cause of the expensive failures we see. |
| `blog/nissan-patrol-service-dubai-complete-guide.html` | FIRST_HAND | failures we see | Letting transmission fluid go beyond its service life is the leading cause of the Jatco gearbox failures we see in Y62 Patrols — the maths strongly favour the service schedule. |
| `blog/nissan-patrol-shaking-at-high-speed.html` | FIRST_HAND | We regularly see | We regularly see bent rims on Y62s that owners have used off-road without reducing tyre pressure, and the deformation is often invisible to the naked eye until it is measured on a balancing machine. |
| `blog/nissan-patrol-transmission-rebuild-cost-dubai-aed.html` | FIRST_HAND | We regularly see | We regularly see Y62 Patrols with overheated 7-speed automatics where the complex valve body has warped, causing erratic shifting and eventual failure. |
| `blog/nissan-patrol-vibration-when-driving.html` | FIRST_HAND | We see this regularly | We see this regularly at the workshop: owners who have already paid for a wheel balance and new tyres but still feel the shake because the real cause was a worn tie rod end or a warped front rotor. |
| `blog/nissan-patrol-vibration-when-driving.html` | CROWD | many UAE Patrol owners | Add the fact that many UAE Patrol owners run large-diameter aftermarket wheels, and you have a vehicle that is more sensitive to imbalance and alignment issues than the factory setup. |
| `blog/nissan-patrol-vibration-when-driving.html` | CROWD | many owners | On Y62 models, the recommended pressures differ between on-road and off-road use, and many owners forget to reinflate after a desert run. |
| `blog/nissan-patrol-y61-dubai-complete-guide.html` | CROWD | many owners | Transmission cooling system inspection becomes essential, with many owners adding auxiliary coolers for improved reliability in stop-and-go traffic. |
| `blog/nissan-patrol-y62-coolant-temperature-sensor-cost-uae-2026.html` | FIRST_HAND | We see this regularly | We see this regularly, and the symptoms that bring owners in range from a check engine light and poor fuel economy to hard starting and fans running continuously even after shutdown. |
| `blog/nissan-patrol-y62-cv-joint-replacement-cost-uae-2026.html` | FIRST_HAND | components we see | CV joints and axle shafts are among the components we see regularly. |
| `blog/nissan-patrol-y62-dubai-complete-guide.html` | CROWD | Most Dubai Patrols | Most Dubai Patrols doing casual desert days don't need anything beyond what leaves the factory. |
| `blog/nissan-patrol-y62-dubai-complete-guide.html` | FIRST_HAND | failures we see | The failures we see most often come from skipped coolant changes and worn cooling parts, not the engine itself. |
| `blog/nissan-patrol-y62-dubai-complete-guide.html` | FIRST_HAND | we see most | The three we see most at the workshop are transmission shudder (usually the torque converter or old transmission fluid), cooling system faults (radiators and hoses that harden in the heat), and AC problems during summer. |
| `blog/nissan-patrol-y62-oxygen-sensor-replacement-cost-dubai-2026.html` | FIRST_HAND | we commonly see | Other things we commonly see in workshop: Fuel consumption noticeably higher than usual. |
| `blog/nissan-patrol-y62-paint-protection-film-cost-dubai-2026.html` | FIRST_HAND | we see a lot | When to bring it to Patrol Garage We work on Y62 Patrols every day, and we see a lot of paint damage that PPF could have prevented. |
| `blog/nissan-patrol-y62-problems-dubai.html` | FIRST_HAND | failures we see | The most common differential failures we see come from two sources: oil seal leaks that go unnoticed until the differential runs dry (catastrophic and expensive), and aggressive off-road use without appropriate diff lock operation. |
| `blog/nissan-patrol-y62-problems-dubai.html` | FIRST_HAND | problems we see | All are predictable and preventable with the right maintenance intervals — the problems we see most are caused by following factory schedules designed for temperate climates, not UAE heat. |
| `blog/nissan-patrol-y62-rear-differential-rebuild-cost-uae-2026.html` | FIRST_HAND | failures we see | Most of the Y62 rear differential failures we see at Patrol Garage trace back to one root cause: the differential oil was not changed at the right interval for the way the vehicle was actually used. |
| `blog/nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026.html` | FIRST_HAND | component we see | The Jatco JR710E transmission is the component we see fail most often on high-mileage Y62s in UAE conditions. |
| `blog/nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026.html` | CROWD | most owners | A new Y63 is a significant step up from even the cost of a comprehensive Y62 repair, so most owners with a Y62 that needs one or two specific jobs are better served fixing what they have, provided the work is done by someone who knows the platform. |
| `blog/nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026.html` | CROWD | most owners | The first sign most owners notice is a shudder or vibration on light throttle, usually between 2nd and 3rd gear at 40 to 60 km/h. |
| `blog/nissan-patrol-y62-throttle-body-cleaning-cost-dubai.html` | CROWD | many owners | In a temperate climate, many owners go 80,000 km or more without issue. |
| `blog/nissan-patrol-y62-tow-bar-fitting-cost-dubai-2026.html` | CROWD | most owners | What surprises most owners is how affordable a proper tow bar fitting actually is compared to what the dealership charges for accessories. |
| `blog/nissan-patrol-y62-tow-bar-fitting-cost-dubai-2026.html` | CROWD | a lot of Y62s | We see a lot of Y62s with aftermarket tow bars fitted at varying quality levels, and the price difference between a safe installation and a botched one is not always obvious until you are already on Sheikh Zayed Road with something heavy in tow. |
| `blog/nissan-patrol-y62-tow-bar-fitting-cost-dubai-2026.html` | FIRST_HAND | We see a lot | We see a lot of Y62s with aftermarket tow bars fitted at varying quality levels, and the price difference between a safe installation and a botched one is not always obvious until you are already on Sheikh Zayed Road with something heavy in tow. |
| `blog/nissan-patrol-y62-tow-bar-fitting-cost-dubai-2026.html` | CROWD | most owners | Yes, and it is something most owners do not think about until corrosion sets in. |
| `blog/nissan-patrol-y62-transmission-problems-dubai.html` | FIRST_HAND | We regularly see | We regularly see Y62 Patrols with transmission issues that could have been prevented with early intervention. |
| `blog/nissan-patrol-y62-transmission-problems-dubai.html` | FIRST_HAND | issues we see | Let's dive into the real-world transmission issues we see in Dubai and what you can actually do about them. |
| `blog/nissan-patrol-y62-transmission-problems-dubai.html` | CROWD | Many owners | Many owners imported from Japan or Canada find that sourcing replacement transmissions requires careful attention to gear ratios and compatibility. |
| `blog/nissan-patrol-y62-transmission-problems-dubai.html` | CROWD | many Y62 owners | We've seen too many Y62 owners skip fluid changes to save money, then face a rebuild bill two years later. |
| `blog/y62-abs-sensor-replacement-cost-dubai-2026.html` | CROWD | most drivers | On a dry motorway in normal conditions, most drivers would not notice any difference. |
| `blog/y62-abs-sensor-replacement-cost-dubai-2026.html` | FIRST_HAND | In our experience | In our experience, genuine module failure on the Y62 is uncommon before 200,000 km. |
| `blog/y62-crankshaft-position-sensor-replacement-cost-dubai-2026.html` | FIRST_HAND | in our experience | The Y62 models most commonly presenting with this fault in our experience are high-mileage examples in the 150,000 km to 250,000 km range. |
| `blog/y62-engine-mount-replacement-cost-dubai-2026.html` | FIRST_HAND | we regularly see | The result is that we regularly see Y62s come in at 90,000 km with mounts that have softened and cracked enough to need replacement. |
| `blog/y62-fuel-injector-cleaning-cost-dubai-2026.html` | CROWD | Most owners | Most owners assume it is just the heat. |
| `blog/y62-fuel-pressure-regulator-replacement-cost-dubai-2026.html` | FIRST_HAND | the ones we see | Y62s with higher mileage (above 120,000 km) are the ones we see most often with fuel system pressure faults. |
| `blog/y62-fuel-pressure-regulator-replacement-cost-dubai-2026.html` | CROWD | most owners | Including the diagnostic pressure test at the start and a post-repair pressure hold test at the end, most owners have the car back the same day if they bring it in before midday. |
| `blog/y62-vk56-valve-cover-gasket-replacement-cost-dubai-2026.html` | FIRST_HAND | We see this regularly | We see this regularly at Patrol Garage, especially on Y62 models with higher mileage. |
| `blog/y62-water-pump-replacement-cost-uae-2026.html` | CROWD | many owners | We specialise in Nissan Patrols and carry common Y62 cooling parts in stock, which avoids the two to four day wait for dealer parts ordering that many owners run into elsewhere. |
| `contact.html` | CROWD | Most Patrol owners | Most Patrol owners reach us from Deira, Mirdif, Nad Al Sheba, Al Quoz, Business Bay and Sharjah. |
| `services/y62-major-service-dubai.html` | CROWD | Most Patrols | Most Patrols in Dubai are better served on a shorter rhythm than the book interval, and we will tell you what yours actually needs based on how you drive it. |
