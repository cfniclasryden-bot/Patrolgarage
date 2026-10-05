# patrolgarage.ae claims and premises cleanup, 2026-10-05

**Pages changed:** 72 HTML pages (of 72 shipped), plus `llms.txt` and 9 scripts. **Edits:** 205 text edits (591 replacements, counting every copy: visible text, FAQ schema, meta tags) and 56 hero alts.

**Result:** all five guards (`check_prose`, `check_schema`, `check_model_years`, `check_claims`, `check_alt`) pass on all 72 shipped pages. File mtimes were preserved. No `datePublished` changed, so post dates and blog order are unchanged.

**Rules applied:** delete the sentence, or rewrite it so it no longer makes the claim. No new sources, figures, model years, facelift claims, horsepower, fluid specs, prices or dealer service names. Where a sentence also appeared in the page's FAQ JSON-LD or meta tags, every copy was changed the same way.


## 1. `[NEEDS_SOURCE]` markers (11 markers in 10 pages)

| Page | Before | After |
|---|---|---|
| `blog/nissan-patrol-engine-problems.html` | “Major service at a Nissan dealer: documented around AED 3,065 for a 40,000 km service [NEEDS_SOURCE for current dealer pricing]” | *(deleted)* |
| `blog/nissan-patrol-high-mileage.html` | “Nissan dealer major service is documented at around AED 3,065 for the 40,000 km service. [NEEDS_SOURCE for current dealer pricing beyond documented DriveArabia long-term test figure.]” | *(deleted)* |
| `blog/nissan-patrol-major-service.html` | “At the Nissan dealer, a documented 40,000 km service on a Y62 has come out at around AED 3,065, while a basic dealer service using synthetic oil runs closer to AED 827. [NEEDS_SOURCE for current dealer menu pricing]” | *(deleted)* |
| `blog/nissan-patrol-y62-head-gasket-replacement-cost-uae.html` | “The standard Nissan factory warranty covers defects in materials and workmanship. Head gasket failure caused by overheating due to owner neglect, low coolant, or a missed service is generally not covered. If the vehicle is still within the warranty period and there is no overheating history, it is worth raising with a Nissan dealer before paying for an independent repair. Extended service contracts may have different terms. [NEEDS_SOURCE for specific Nissan UAE warranty terms]” | “If the vehicle is still within the warranty period, check the warranty terms with a Nissan dealer before paying for an independent repair.” |
| `blog/nissan-patrol-y62-oxygen-sensor-replacement-cost-dubai-2026.html` | “Oxygen sensors are rated for around 100,000 to 160,000 km under normal operating conditions [NEEDS_SOURCE for exact OEM interval]. In Dubai, we see them degrading earlier than that for a few reasons.” | “In Dubai, we see oxygen sensors degrading earlier than they would in a cooler climate, for a few reasons.” |
| `blog/nissan-patrol-y62-starter-motor-replacement-cost-uae-2026.html` | “At an authorised dealer with OEM parts: AED 1,800 to AED 3,000 or more [NEEDS_SOURCE for specific dealer quote].” | *(deleted)* |
| `blog/nissan-patrol-y62-throttle-body-cleaning-cost-dubai.html` | “Nissan dealer pricing [NEEDS_SOURCE for exact current dealer labour rate] tends to run higher, typically in the AED 400 to AED 600 range once you add the dealer surcharge on labour and consumables.” | *(deleted)* |
| `blog/nissan-patrol-y62-throttle-body-cleaning-cost-dubai.html` | “Nissan does not publish a fixed throttle body cleaning interval in the standard service schedule [NEEDS_SOURCE for exact published interval].” | *(deleted)* |
| `blog/y61-super-safari-snorkel-fitting-cost-dubai-2026.html` | “For the Y61, Safari Snorkels' part reference is SS780HF (TB48DE engines) [NEEDS_SOURCE for exact current part number verification from Safari]. ARB makes a direct equivalent.” | “For the Y61, both Safari Snorkels and ARB make a snorkel kit.” |
| `blog/y62-spark-plug-replacement-cost-al-futtaim-vs-independent.html` | “Al-Futtaim's flat-rate labour time for a Y62 spark plug replacement is typically billed at 2.0 to 2.5 hours at dealer labour rates [NEEDS_SOURCE for exact current rate], which puts the labour portion alone at roughly AED 600 to AED 900 before parts.” | “The dealer bills this job on a flat-rate labour time at dealer labour rates, so ask the service advisor for the current figure before you book.” |
| `blog/y62-vk56-valve-cover-gasket-replacement-cost-dubai-2026.html` | “Expect AED 3,000 to AED 4,500 at dealer labour rates, including a marked-up Nissan-branded gasket kit. [NEEDS_SOURCE: named dealer quote]” | *(deleted)* |

## 2a. `check_claims` findings (45 findings in 26 pages)

| Page | Before | After |
|---|---|---|
| `blog/nissan-patrol-4wd-not-engaging.html` | “Nissan's published interval is a starting point, but for a Y62 used in UAE conditions, including regular off-road use and summer temperatures above 45 degrees Celsius, most Patrol specialists recommend checking the fluid every 40,000 to 60,000 km and changing it if it is dark, smells burnt, or contains metallic particles.” | “For a Y62 used in UAE conditions, including regular off-road use and summer temperatures above 45 degrees Celsius, check the fluid regularly and change it if it is dark, smells burnt, or contains metallic particles.” |
| `blog/nissan-patrol-best-year-to-buy.html` | “At a Nissan dealer, documented cost for the 40,000km service on a Patrol was around AED 3,065 based on published long-term test data.” | *(deleted)* |
| `blog/nissan-patrol-diesel-vs-petrol.html` | “The diesel's torque advantage at low revs (the ZD30 produces around 380 Nm, the TD42T more depending on specification) means” | “The diesel's torque advantage at low revs means” |
| `blog/nissan-patrol-engine-overheating.html` | “A general interval is every 50,000 km or every two years, whichever comes first, but the owner's manual for the specific model and engine should be the reference point.” | “Have the coolant condition checked at every service.” |
| `blog/nissan-patrol-engine-problems.html` | “Every 5,000 to 7,500 km in UAE conditions is a practical interval for the VK56VD, even if the owner's manual states 10,000 km.” | “In Dubai, the practical engine oil change interval for a Y62 is 5,000 to 7,500 km, rather than the 10,000 km in the owner's manual.” |
| `blog/nissan-patrol-fuel-consumption.html` | “Published combined figures sit around 14.4 to 14.5 L/100km, but that number comes from test cycles that bear little resemblance to Dubai.” | “Laboratory test-cycle figures bear little resemblance to driving in Dubai.” |
| `blog/nissan-patrol-fuel-consumption.html` | “Published combined figures around 14.4 L/100km are recorded under test conditions that do not reflect Dubai summer traffic.” | “Laboratory test-cycle figures do not reflect Dubai summer traffic.” |
| `blog/nissan-patrol-fuel-consumption.html` | “Nissan dealer major service pricing has been documented at around AED 3,065 for the 40,000 km service.” | *(deleted)* |
| `blog/nissan-patrol-high-mileage.html` | “At 150,000 km and above, the standard manufacturer interval is a starting point, not a ceiling.” | “At 150,000 km and above, treat the standard service interval as a starting point, not a ceiling.” |
| `blog/nissan-patrol-major-service.html` | “, while a Nissan dealer 40,000 km service has been documented at around AED 3,065.” | “.” |
| `blog/nissan-patrol-major-service.html` | “Nissan's factory interval is 10,000 km for oil changes and 40,000 km for major service items, but those intervals were not designed with 48°C summers and sand ingress in mind.” | “Standard service intervals were not designed with 48°C summers and sand ingress in mind.” |
| `blog/nissan-patrol-major-service.html` | “Nissan's standard interval is every 40,000 km or two years, whichever comes first.” | “A major service typically falls every 40,000 km or two years.” |
| `blog/nissan-patrol-major-service.html` | “A Nissan dealer 40,000 km service has been documented at around AED 3,065.” | *(deleted)* |
| `blog/nissan-patrol-service-dubai-complete-guide.html` | “accelerate wear at rates manufacturers don't anticipate.” | “accelerate wear far faster than a temperate climate would.” |
| `blog/nissan-patrol-service-dubai-complete-guide.html` | “The factory service interval of 10,000 km is calibrated for temperate climates.” | “Standard service intervals are calibrated for temperate climates.” |
| `blog/nissan-patrol-service-dubai-complete-guide.html` | “degrades well before that mark.” | “degrades well before the standard interval.” |
| `blog/nissan-patrol-service-dubai-complete-guide.html` | “For the Y62's VK56VD V8, full synthetic 5W-30 is the correct specification.” | *(deleted)* |
| `blog/nissan-patrol-service-dubai-complete-guide.html` | “Follow the severe-service schedule: oil changes” | “Treat Dubai driving as severe service: oil changes” |
| `blog/nissan-patrol-service-every-how-many-km-dubai.html` | “The standard 10,000km service interval recommended by Nissan assumes moderate temperatures” | “Standard service intervals assume moderate temperatures” |
| `blog/nissan-patrol-service-every-how-many-km-dubai.html` | “Nissan officially recommends 10,000km or 6-month service intervals for all Patrol models under normal operating conditions.” | “You will often see 10,000km or 6 months quoted as the standard service interval for Patrol models under normal operating conditions.” |
| `blog/nissan-patrol-service-every-how-many-km-dubai.html` | “The Y62's 7-speed Jatco transmission (JR710E/RE7R01A) has its own service schedule, requiring fluid changes every 60,000km under normal conditions. But we've seen” | “We've seen” |
| `blog/nissan-patrol-service-every-how-many-km-dubai.html` | “AED 4,000-12,000 depending on specification level.” | “AED 4,000-12,000 depending on trim level.” |
| `blog/nissan-patrol-y61-dubai-complete-guide.html` | “Oil change intervals should be reduced from manufacturer recommendations—every 5,000km” | “Oil change intervals should be shortened—every 5,000km” |
| `blog/nissan-patrol-y62-dubai-complete-guide.html` | “and a transmission fluid change earlier than the factory interval.” | “and a transmission fluid change sooner than you would in a cooler climate.” |
| `blog/nissan-patrol-y62-head-gasket-replacement-cost-uae.html` | “The VK56VD 5.6L V8 has two cylinder heads” | “The VK56VD V8 has two cylinder heads” |
| `blog/nissan-patrol-y62-head-gasket-replacement-cost-uae.html` | “For the Y62's VK56VD 5.6L V8, the cost runs” | “For the Y62's VK56VD V8, the cost runs” |
| `blog/nissan-patrol-y62-paint-protection-film-cost-dubai-2026.html` | “should offer a minimum two to three years on workmanship and pass through” | “should offer a written warranty on workmanship and pass through” |
| `blog/nissan-patrol-y62-rear-differential-rebuild-cost-uae-2026.html` | “The standard Nissan service interval for differential oil is every 40,000 km for normal use. In UAE conditions, with high ambient temperatures and any off-road use at all, 20,000 km is the correct interval.” | “In UAE conditions, with high ambient temperatures and any off-road use at all, 20,000 km is the correct interval for differential oil.” |
| `blog/nissan-patrol-y62-starter-motor-replacement-cost-uae-2026.html` | “Do that repeatedly over five or six years and the brushes and solenoid contacts degrade faster than the manufacturer's projected service life.” | “Do that repeatedly for years and the brushes and solenoid contacts degrade faster than they would in a cooler climate.” |
| `blog/nissan-patrol-y62-transmission-problems-dubai.html` | “in Dubai conditions — more frequently than Nissan's global service intervals.” | “in Dubai conditions.” |
| `blog/nissan-patrol-y62-transmission-problems-dubai.html` | “While Nissan's global recommendation might suggest 100,000 kilometers between changes, we see optimal results” | “We see optimal results” |
| `blog/nissan-patrol-y62-vs-y63-dubai-comparison.html` | “Meanwhile, the Y63 represents Nissan's latest thinking on luxury SUVs, but it's still an unknown quantity” | “Meanwhile, the Y63 is still an unknown quantity” |
| `blog/y62-abs-sensor-replacement-cost-dubai-2026.html` | “For a 2012 or 2016 Y62 with 150,000 km on it, a Delphi” | “For a high-mileage Y62, a Delphi” |
| `blog/y62-engine-mount-replacement-cost-dubai-2026.html` | “degrades rubber mounts faster than manufacturer schedules suggest, so” | “degrades rubber mounts faster than a cooler climate would, so” |
| `blog/y62-engine-mount-replacement-cost-dubai-2026.html` | “Dubai's sustained summer heat above 45°C degrades rubber faster than manufacturer schedules account for.” | “Dubai's sustained summer heat above 45°C is what wears the rubber out sooner.” |
| `blog/y62-fuel-injector-cleaning-cost-dubai-2026.html` | “There is no fixed factory interval for injector cleaning published for the Y62, but our experience with UAE-operated Patrols points to 40,000 to 60,000 km as a sensible range.” | “Our experience with UAE-operated Patrols points to 40,000 to 60,000 km as a sensible range for injector cleaning.” |
| `blog/y62-fuel-injector-cleaning-cost-dubai-2026.html` | “the spray pattern on ten-year-old injectors in Dubai conditions will not be the same as it was from the factory.” | “the spray pattern on old injectors in Dubai conditions will not be what it was when they were new.” |
| `blog/y62-intercooler-upgrade-cost-dubai-al-futtaim-vs-independent.html` | “The VK56VD 5.6L V8 in the Y62 makes 400hp from the factory without forced induction.” | “The VK56VD V8 in the Y62 is naturally aspirated.” |
| `blog/y62-intercooler-upgrade-cost-dubai-al-futtaim-vs-independent.html` | “In temperate climates with ambient temperatures of 15 to 20°C, factory intercoolers handle this reasonably well.” | “In temperate climates, intercoolers handle this reasonably well.” |
| `blog/y62-rear-air-bag-replacement-cost-uae-2026.html` | “OEM Nissan bags typically last” | “Genuine bags typically last” |
| `blog/y62-spark-plug-replacement-cost-al-futtaim-vs-independent.html` | “Nissan's factory interval for the VK56VD iridium plugs is 60,000 km, but UAE driving conditions push that recommendation earlier for many owners.” | “UAE driving conditions push iridium plug replacement earlier than a temperate climate would.” |
| `blog/y62-spark-plug-replacement-cost-al-futtaim-vs-independent.html` | “Nissan specifies 60,000 km for iridium plugs on the VK56VD.” | *(deleted)* |
| `blog/y63-independent-service-centre-abu-dhabi-vs-dubai-2026.html` | “Per the UAE government's official information portal, summer ambient temperatures in the UAE regularly reach” | “Summer ambient temperatures in the UAE regularly reach” |

## 2b. `check_model_years` findings (24 findings in 15 pages)

| Page | Before | After |
|---|---|---|
| `blog/nissan-patrol-best-year-to-buy.html` | “The pre-2016 cars also lack some of the interior and tech upgrades that the first refresh introduced, but they are significantly cheaper on the used market,” | “Higher-mileage examples are significantly cheaper on the used market,” |
| `blog/nissan-patrol-best-year-to-buy.html` | “The post-2020 refresh added more features but also added complexity, and used prices for 2020 to 2023 cars are still relatively high.” | “Used prices for the most recent Y62s are still relatively high.” |
| `blog/nissan-patrol-diesel-vs-petrol.html` | “since the model launched here in 2010, through the 2016 facelift, the 2020 update, and right up to when the Y63 replaced it as the top-of-range model in 2024.” | “since the model launched here in 2010.” |
| `blog/nissan-patrol-oil-leak.html` | “Valve cover gaskets on both banks are the most frequent complaint, particularly on Y62s from 2010 to 2015.” | “Valve cover gaskets on both banks are the most frequent complaint.” |
| `blog/nissan-patrol-service-every-how-many-km-dubai.html` | “Y62 models from 2010-2024 demand more sophisticated maintenance.” | “Y62 models demand more sophisticated maintenance.” |
| `blog/nissan-patrol-y62-coolant-temperature-sensor-cost-uae-2026.html` | “which is accessible but requires partial underbonnet disassembly on post-2016 refresh models, adding” | “which is accessible but can require partial underbonnet disassembly, adding” |
| `blog/nissan-patrol-y62-coolant-temperature-sensor-cost-uae-2026.html` | “since 2010, through two refresh cycles in 2016 and 2020, and older examples” | “since 2010, and older examples” |
| `blog/nissan-patrol-y62-coolant-temperature-sensor-cost-uae-2026.html` | “On the post-2016 Y62, some intake ducting needs to be moved” | “On some Y62s, intake ducting needs to be moved” |
| `blog/nissan-patrol-y62-dubai-complete-guide.html` | “The Y63 (from 2024) is a significant step forward” | “The Y63 is a significant step forward” |
| `blog/nissan-patrol-y62-fourth-brake-light-replacement-dubai-2026.html` | “and on the 2010 to 2015 build years in particular the original lamp housings are now old enough that a replacement is overdue on many cars.” | “and on many of the oldest cars the original lamp housing is now overdue for replacement.” |
| `blog/nissan-patrol-y62-fourth-brake-light-replacement-dubai-2026.html` | “Whether your Y62 is a pre-facelift, the 2016 refresh, or the 2020 model, the process and costs are close to identical.” | “Whatever the age of your Y62, the process and costs are close to identical.” |
| `blog/nissan-patrol-y62-fourth-brake-light-replacement-dubai-2026.html` | “On the 2010 to 2015 pre-facelift Y62, the housing is a narrower strip. The 2016 facelift and 2020 update use a slightly wider design that is not directly interchangeable with the older housing without checking fitment carefully.” | *(deleted)* |
| `blog/nissan-patrol-y62-fourth-brake-light-replacement-dubai-2026.html` | “The part numbers for the Y62 HMSL vary by year, so when you order, confirm your model year: 2010 to 2015 pre-facelift, 2016 to 2019 mid-cycle, or 2020 onwards.” | “When you order, confirm the part number for your exact car.” |
| `blog/nissan-patrol-y62-fourth-brake-light-replacement-dubai-2026.html` | “If your Y62 is a 2016 facelift or 2020 model and the lamp failure also triggered” | “If the lamp failure also triggered” |
| `blog/nissan-patrol-y62-fourth-brake-light-replacement-dubai-2026.html` | “Pre-facelift 2010 to 2015 Y62s use a different housing to the 2016 to 2019 facelift and the 2020 refresh.” | *(deleted)* |
| `blog/nissan-patrol-y62-head-gasket-replacement-cost-uae.html` | “On lower-mileage Y62s, particularly post-2016 refresh models, a head gasket” | “On lower-mileage Y62s, a head gasket” |
| `blog/nissan-patrol-y62-paint-protection-film-cost-dubai-2026.html` | “That is over a decade of facelifts, trim upgrades, and roughly 400 horsepower worth of desert driving.” | “That is over a decade of trim upgrades and desert driving.” |
| `blog/nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026.html` | “on a high-mileage SE trim from 2012, that is” | “on a high-mileage SE trim, that is” |
| `blog/nissan-patrol-y62-starter-motor-replacement-cost-uae-2026.html` | “The Y62 ran from 2010 to 2023 in the UAE before the Y63 replaced it in 2024.” | *(deleted)* |
| `blog/y62-fuel-injector-cleaning-cost-dubai-2026.html` | “(or has never had one), or is a pre-2016 model with original injectors still in place, book it in.” | “(or has never had one), book it in.” |
| `blog/y62-spark-plug-replacement-cost-al-futtaim-vs-independent.html` | “If your Y62 is a 2016 or earlier model and has not had plugs replaced since purchase, do it now regardless of the odometer. Pre-2016 trucks on UAE roads often have unknown service histories from previous owners.” | “If your Y62 has not had plugs replaced since you bought it, do it now regardless of the odometer. Used trucks on UAE roads often have unknown service histories from previous owners.” |
| `blog/y63-dashcam-installation-specialist-dubai-best-price-2026.html` | “Beyond the ADAS risk: the Y63 warranty from Nissan UAE is still active on vehicles bought from 2024 onwards. Electrical alterations that cause faults can complicate warranty claims.” | “Beyond the ADAS risk: if your Y63 is still under warranty, electrical alterations that cause faults can complicate a claim.” |
| `services/nissan-patrol-v8-engine.html` | “it is the engine in every Y62 sold in the UAE from 2010 until the Y63 arrived in 2024 with a twin-turbo 3.5-litre V6.” | “it is the engine in every Y62 sold in the UAE since the model launched here in 2010.” |

## 3a. Premises claims in page copy, meta tags and schema

| Page | Before | After |
|---|---|---|
| `blog/best-oil-nissan-patrol-uae-heat.html` | “Patrols arrive at our Ras Al Khor workshop with oil-related damage” | “Patrols with oil-related damage” |
| `blog/best-oil-nissan-patrol-uae-heat.html` | “our Ras Al Khor workshop specializes in all Patrol models” | “Patrol Garage specializes in all Patrol models” |
| `blog/buying-a-used-nissan-patrol.html` | “After years working on these trucks in Ras Al Khor, we have” | “After years working on these trucks, we have” |
| `blog/buying-a-used-nissan-patrol.html` | “bring it to us in Ras Al Khor.” | “bring it to us.” |
| `blog/nissan-patrol-4wd-not-engaging.html` | “bring it to us at Patrol Garage in Ras Al Khor.” | “bring it to us at Patrol Garage.” |
| `blog/nissan-patrol-best-year-to-buy.html` | “the workshop at Ras Al Khor can diagnose and repair it.” | “Patrol Garage can diagnose and repair it.” |
| `blog/nissan-patrol-black-smoke.html` | “That is what we do at Patrol Garage in Ras Al Khor.” | “That is what we do at Patrol Garage.” |
| `blog/nissan-patrol-diesel-vs-petrol.html` | “Patrol Garage in Ras Al Khor works on Y62 Patrols.” | “Patrol Garage works on Y62 Patrols.” |
| `blog/nissan-patrol-differential-repair-cost-uae.html` | “We see Patrol owners daily at our Ras Al Khor workshop, often” | “We see Patrol owners daily, often” |
| `blog/nissan-patrol-differential-repair-cost-uae.html` | “Ras Al Khor industrial area, where we're located, typically offers” | “Ras Al Khor industrial area typically offers” |
| `blog/nissan-patrol-differential-repair-cost-uae.html` | “When to Bring Your Patrol to Our Ras Al Khor Workshop” | “When to Bring Your Patrol to Patrol Garage” |
| `blog/nissan-patrol-differential-repair-cost-uae.html` | “Our Ras Al Khor location provides easy access from both Dubai and Sharjah, with transparent pricing and genuine parts sourcing.” | *(deleted)* |
| `blog/nissan-patrol-engine-problems.html` | “Patrol Garage in Ras Al Khor handles engine diagnostics” | “Patrol Garage handles engine diagnostics” |
| `blog/nissan-patrol-fuel-consumption.html` | “Patrol Garage is in Ras Al Khor, Dubai. We work on the Y62” | “We work on the Y62” |
| `blog/nissan-patrol-high-mileage.html` | “Patrol Garage is based in Ras Al Khor, Dubai, and the workshop works on Y62 Patrols.” | “Patrol Garage works on Y62 Patrols.” |
| `blog/nissan-patrol-overheating-dubai-summer-fix.html` | “overheated Patrols roll into our Ras Al Khor workshop every summer” | “overheated Patrols every summer” |
| `blog/nissan-patrol-overheating-dubai-summer-fix.html` | “Our Ras Al Khor location stocks Dubai-specific cooling components and offers same-day service for most overheating problems.” | *(deleted)* |
| `blog/nissan-patrol-pre-purchase-inspection.html` | “JR710E gearbox checks and cooling work at our Ras Al Khor workshop.” | “JR710E gearbox checks and cooling work.” |
| `blog/nissan-patrol-service-dubai-complete-guide.html` | “Patrol Garage specialists, Ras Al Khor.” | “Patrol Garage specialists.” |
| `blog/nissan-patrol-service-dubai-complete-guide.html` | “the expensive failures we see come through our workshop.” | “the expensive failures we see.” |
| `blog/nissan-patrol-service-dubai-complete-guide.html` | “We're Nissan Patrol specialists in Ras Al Khor” | “We're Nissan Patrol specialists” |
| `blog/nissan-patrol-service-every-how-many-km-dubai.html` | “We've serviced thousands of Patrols at our Ras Al Khor workshop, from” | “We've serviced thousands of Patrols, from” |
| `blog/nissan-patrol-service-every-how-many-km-dubai.html` | “another critical factor we see daily in our workshop.” | “another critical factor we see daily.” |
| `blog/nissan-patrol-service-every-how-many-km-dubai.html` | “Our Ras Al Khor workshop specializes in Dubai-specific” | “Patrol Garage specializes in Dubai-specific” |
| `blog/nissan-patrol-shaking-at-high-speed.html` | “At Patrol Garage in Ras Al Khor, we work” | “At Patrol Garage, we work” |
| `blog/nissan-patrol-steering-problems.html` | “Patrol Garage is based in Ras Al Khor, Dubai, and works on” | “Patrol Garage works on” |
| `blog/nissan-patrol-transmission-rebuild-cost-dubai-aed.html` | “rebuilding Patrol transmissions at our Ras Al Khor workshop for over a decade” | “rebuilding Patrol transmissions for over a decade” |
| `blog/nissan-patrol-transmission-rebuild-cost-dubai-aed.html` | “these vehicles often arrive at our workshop with” | “these vehicles often arrive with” |
| `blog/nissan-patrol-transmission-rebuild-cost-dubai-aed.html` | “Our Ras Al Khor workshop specializes exclusively” | “Patrol Garage specializes exclusively” |
| `blog/nissan-patrol-transmission-rebuild-cost-dubai-aed.html` | “Expert service in Ras Al Khor.” | “Expert Patrol service.” |
| `blog/nissan-patrol-transmission-rebuild-cost-dubai-aed.html` | “, ras al khor transmission” | *(deleted)* |
| `blog/nissan-patrol-vibration-when-driving.html` | “We work on Y62 Patrols in Ras Al Khor and are” | “We work on Y62 Patrols and are” |
| `blog/nissan-patrol-warning-lights-meaning.html` | “Patrol Garage works on Y62 Patrols at Ras Al Khor.” | “Patrol Garage works on Y62 Patrols.” |
| `blog/nissan-patrol-y62-coolant-temperature-sensor-cost-uae-2026.html` | “We see this regularly at our workshop in Ras Al Khor, and” | “We see this regularly, and” |
| `blog/nissan-patrol-y62-coolant-temperature-sensor-cost-uae-2026.html` | “We are based in Ras Al Khor, a straightforward drive from most of Dubai.” | *(deleted)* |
| `blog/nissan-patrol-y62-cv-joint-replacement-cost-uae-2026.html` | “we see come through our Ras Al Khor workshop regularly.” | “we see regularly.” |
| `blog/nissan-patrol-y62-cv-joint-replacement-cost-uae-2026.html` | “We are based in Ras Al Khor and work on the Y62 platform” | “We work on the Y62 platform” |
| `blog/nissan-patrol-y62-driveshaft-repair-cost-dubai-2026.html` | “We are based in Ras Al Khor, which is central to most of Dubai and close to Al Qudra Road for owners coming back from weekend desert trips.” | *(deleted)* |
| `blog/nissan-patrol-y62-fourth-brake-light-replacement-dubai-2026.html` | “We are based in Ras Al Khor, central to most of Dubai and a short run from Deira, Al Quoz, and the Sheikh Zayed Road corridor.” | *(deleted)* |
| `blog/nissan-patrol-y62-head-gasket-replacement-cost-uae.html` | “what we see going wrong on Y62s that come through our workshop in Ras Al Khor.” | “what we see going wrong on Y62s.” |
| `blog/nissan-patrol-y62-head-gasket-replacement-cost-uae.html` | “We are based in Ras Al Khor and work exclusively on Patrol models” | “We work exclusively on Patrol models” |
| `blog/nissan-patrol-y62-oxygen-sensor-replacement-cost-dubai-2026.html` | “owners come through our Ras Al Khor workshop with a check engine light” | “owners with a check engine light” |
| `blog/nissan-patrol-y62-paint-protection-film-cost-dubai-2026.html` | “We work on Y62 Patrols every day at our Ras Al Khor workshop, and” | “We work on Y62 Patrols every day, and” |
| `blog/nissan-patrol-y62-problems-dubai.html` | “We diagnose and rebuild all of these at our Ras Al Khor workshop —” | “We diagnose and rebuild all of these —” |
| `blog/nissan-patrol-y62-problems-dubai.html` | “(AED 1,200–1,800 at our workshop)” | “(AED 1,200–1,800)” |
| `blog/nissan-patrol-y62-problems-dubai.html` | “We diagnose Y61, Y62, and Y63 at our Ras Al Khor workshop —” | “We diagnose Y61, Y62, and Y63 —” |
| `blog/nissan-patrol-y62-problems-dubai.html` | “Bring it to our workshop for a scan-tool diagnostic” | “Bring it to us for a scan-tool diagnostic” |
| `blog/nissan-patrol-y62-rear-differential-rebuild-cost-uae-2026.html` | “Patrol Garage Ras Al Khor quotes after full stripdown.” | “Patrol Garage quotes after full stripdown.” |
| `blog/nissan-patrol-y62-rear-differential-rebuild-cost-uae-2026.html` | “Full stripdown quote at Patrol Garage Ras Al Khor.” | “Full stripdown quote at Patrol Garage.” |
| `blog/nissan-patrol-y62-rear-differential-rebuild-cost-uae-2026.html` | “, patrol garage Ras Al Khor” | *(deleted)* |
| `blog/nissan-patrol-y62-rear-differential-rebuild-cost-uae-2026.html` | “At Patrol Garage in Ras Al Khor, we quote” | “At Patrol Garage, we quote” |
| `blog/nissan-patrol-y62-rear-differential-rebuild-cost-uae-2026.html` | “We are based in Ras Al Khor, which puts us a short drive from Deira, Al Qudra, and the main highway corridors most Patrol owners use daily.” | *(deleted)* |
| `blog/nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026.html` | “We see Abu Dhabi-registered Y62s in our workshop regularly” | “We see Abu Dhabi-registered Y62s regularly” |
| `blog/nissan-patrol-y62-specialist-abu-dhabi-vs-dubai-2026.html` | “Patrol Garage is based in Ras Al Khor, Dubai. We work on Y62 Patrols” | “We work on Y62 Patrols” |
| `blog/nissan-patrol-y62-starter-motor-replacement-cost-uae-2026.html` | “We are based in Ras Al Khor, which puts us close to Deira, Al Qudra, and the industrial areas of Al Aweer, so getting to us from most parts of Dubai is straightforward.” | *(deleted)* |
| `blog/nissan-patrol-y62-throttle-body-cleaning-cost-dubai.html` | “We are based in Ras Al Khor, which puts us a short drive from most of Dubai and easy to reach from the Al Qudra and Liwa side if you are coming in after a weekend run.” | *(deleted)* |
| `blog/nissan-patrol-y62-tow-bar-fitting-cost-dubai-2026.html` | “Y62s come through Patrol Garage in Ras Al Khor with aftermarket tow bars” | “Y62s with aftermarket tow bars” |
| `blog/nissan-patrol-y62-tow-bar-fitting-cost-dubai-2026.html` | “bring it to us at Patrol Garage in Ras Al Khor.” | “bring it to us at Patrol Garage.” |
| `blog/nissan-patrol-y62-transmission-problems-dubai.html` | “Call our Ras Al Khor workshop today.” | “Call Patrol Garage today.” |
| `blog/nissan-patrol-y62-transmission-problems-dubai.html` | “Y62 Patrols roll into our Ras Al Khor workshop with transmission issues” | “Y62 Patrols with transmission issues” |
| `blog/nissan-patrol-y62-transmission-problems-dubai.html` | “servicing hundreds of Y62 Patrols in our Ras Al Khor facility:” | “servicing hundreds of Y62 Patrols:” |
| `blog/nissan-patrol-y62-transmission-problems-dubai.html` | “Our Ras Al Khor facility specializes in Y62 transmissions” | “Patrol Garage specializes in Y62 transmissions” |
| `blog/nissan-patrol-y62-turbo-upgrade-dubai-cost.html` | “working on Y62 Patrols in our Ras Al Khor workshop since” | “working on Y62 Patrols since” |
| `blog/nissan-patrol-y62-vs-y63-dubai-comparison.html` | “At Patrol Garage in Ras Al Khor, we've serviced” | “At Patrol Garage, we've serviced” |
| `blog/nissan-patrol-y62-vs-y63-dubai-comparison.html` | “the first Y63s rolling into our workshop.” | “the first Y63s.” |
| `blog/nissan-patrol-y62-vs-y63-dubai-comparison.html` | “Our Ras Al Khor location serves Dubai” | “Patrol Garage serves Dubai” |
| `blog/y61-super-safari-snorkel-fitting-cost-dubai-2026.html` | “We fit snorkels at our Ras Al Khor workshop regularly” | “We fit snorkels regularly” |
| `blog/y62-abs-sensor-replacement-cost-dubai-2026.html` | “We are based in Ras Al Khor, which puts us close to Al Aweer and the main routes used by Patrol owners heading in from Deira, Mirdif, and the rest of the east side of Dubai.” | *(deleted)* |
| `blog/y62-crankshaft-position-sensor-replacement-cost-dubai-2026.html` | “We are a Nissan Patrol specialist workshop based in Ras Al Khor, Dubai.” | “We are Nissan Patrol specialists serving Dubai.” |
| `blog/y62-engine-mount-replacement-cost-dubai-2026.html` | “We work exclusively on Nissan Patrols at our Ras Al Khor workshop, so” | “We work exclusively on Nissan Patrols, so” |
| `blog/y62-fuel-injector-cleaning-cost-dubai-2026.html` | “Book same-day at Al Quoz or Ras Al Khor.” | “Same-day bookings available.” |
| `blog/y62-fuel-pressure-regulator-replacement-cost-dubai-2026.html` | “We see these jobs regularly at our Ras Al Khor workshop, and” | “We see these jobs regularly, and” |
| `blog/y62-intercooler-upgrade-cost-dubai-al-futtaim-vs-independent.html` | “We work on Y62 Patrols every day at our Ras Al Khor workshop.” | “We work on Y62 Patrols every day.” |
| `blog/y62-rear-air-bag-replacement-cost-uae-2026.html` | “fairly regularly at our Ras Al Khor workshop, and” | “fairly regularly, and” |
| `blog/y62-rear-air-bag-replacement-cost-uae-2026.html` | “We are a Y62 specialist workshop in Ras Al Khor.” | “We are Y62 specialists.” |
| `blog/y62-spark-plug-replacement-cost-al-futtaim-vs-independent.html` | “We work on Y62s daily at our Ras Al Khor workshop, we stock” | “We work on Y62s daily, we stock” |
| `blog/y62-vk56-valve-cover-gasket-replacement-cost-dubai-2026.html` | “At Patrol Garage in Ras Al Khor, we stock” | “At Patrol Garage, we stock” |
| `blog/y62-water-pump-replacement-cost-uae-2026.html` | “We see this pattern regularly at our workshop in Ras Al Khor.” | “We see this pattern regularly.” |
| `blog/y62-water-pump-replacement-cost-uae-2026.html` | “We specialise in Nissan Patrols at our Ras Al Khor workshop and carry” | “We specialise in Nissan Patrols and carry” |
| `blog/y63-dashcam-installation-specialist-dubai-best-price-2026.html` | “relay at Patrol Garage Ras Al Khor.” | “relay at Patrol Garage.” |
| `blog/y63-dashcam-installation-specialist-dubai-best-price-2026.html` | “Book at Patrol Garage Ras Al Khor.” | “Book at Patrol Garage.” |
| `blog/y63-dashcam-installation-specialist-dubai-best-price-2026.html` | “Patrol Garage in Ras Al Khor installs dashcams” | “Patrol Garage installs dashcams” |
| `blog/y63-dashcam-installation-specialist-dubai-best-price-2026.html` | “We are in Ras Al Khor, which is also a reasonable stop if you are coming from Al Qudra or heading back from an off-road trip through the eastern side of Dubai.” | *(deleted)* |
| `blog/y63-independent-service-centre-abu-dhabi-vs-dubai-2026.html` | “We see this gap directly at Patrol Garage in Ras Al Khor.” | “We see this gap directly at Patrol Garage.” |
| `blog/y63-independent-service-centre-abu-dhabi-vs-dubai-2026.html` | “through to the current Y63 at our Ras Al Khor workshop in Dubai.” | “through to the current Y63.” |
| `blog/y63-independent-service-centre-abu-dhabi-vs-dubai-2026.html` | “Abu Dhabi owners: we are roughly 90 minutes from Mussafah, and we can arrange” | “Abu Dhabi owners: we can arrange” |
| `about.html` | “About Patrol Garage Dubai | Nissan Patrol Specialists Ras Al Khor” | “About Patrol Garage Dubai | Nissan Patrol Specialists” |
| `about.html` | “Nissan Patrol Y62 service and repair in Ras Al Khor.” | “Nissan Patrol Y62 service and repair in Dubai.” |
| `about.html` | “, Ras Al Khor garage"” | “"” |
| `about.html` | “Nissan Patrol specialists with 10+ years in Dubai and Ras Al Khor” | “Nissan Patrol specialists with 10+ years in Dubai” |
| `about.html` | “We built our workshop in Ras Al Khor specifically around servicing this car” | “We built Patrol Garage specifically around servicing this car” |
| `index.html` | “One workshop in Ras Al Khor, one car: the Nissan Patrol.” | “One car: the Nissan Patrol.” |
| `index.html` | “Ras Al Khor Workshop” | “Serving Dubai” |
| `index.html` | “Ras Al Khor, Dubai. Patrol owners reach us from” | “Dubai. Patrol owners reach us from” |
| `index.html` | “Drop off at our Ras Al Khor workshop. We diagnose properly” | “Message us and we confirm the drop-off point and a time. We diagnose properly” |
| `index.html` | “We've built our workshop in Ras Al Khor specifically around servicing this car” | “We've built Patrol Garage specifically around servicing this car” |
| `index.html` | “A garage inRas Al Khor.” | “Where thework happens.” |
| `index.html` | “If you are looking for a car garage in Ras Al Khor, one thing is worth knowing before you call: we only take Nissan Patrols.” | “One thing is worth knowing before you call: we only take Nissan Patrols.” |
| `contact.html` | “Patrol Garage, Ras Al Khor | Nissan Patrol Workshop Dubai” | “Contact Patrol Garage | Nissan Patrol Service Dubai” |
| `contact.html` | “Patrol Garage contact, Ras Al Khor garage, Dubai Patrol repair” | “Patrol Garage contact, Dubai Patrol repair” |
| `contact.html` | “"description": "Nissan Patrol specialist workshop in Ras Al Khor, Dubai."” | “"description": "Nissan Patrol specialists serving Dubai."” |
| `contact.html` | “Based in Ras Al Khor Industrial Area” | *(deleted)* |
| `contact.html` | “Business Hours” | “When You Can Reach Us” |
| `contact.html` | “Available during business hours” | “Available during the hours below” |
| `contact.html` | “We are not a general car garage in Ras Al Khor and we will not pretend” | “We are not a general car garage and we will not pretend” |
| `y62-garage-dubai.html` | “A Y62-only garage in Ras Al Khor, Dubai.” | “Y62-only Nissan Patrol service in Dubai.” |
| `y62-garage-dubai.html` | “, Patrol Y62 mechanic Ras Al Khor” | *(deleted)* |
| `y62-garage-dubai.html` | “"description": "Nissan Patrol Y62 specialist workshop in Ras Al Khor, Dubai."” | “"description": "Nissan Patrol Y62 specialists serving Dubai."” |
| `y62-garage-dubai.html` | “Ras Al Khor” | “Dubai” |
| `y62-garage-dubai.html` | “02 — Where We Are” | “02 — Coverage” |
| `y62-garage-dubai.html` | “Ras Al Khor,Dubai.” | “AcrossDubai.” |
| `y62-garage-dubai.html` | “We are an independent workshop in Ras Al Khor, working on Nissan Patrols across Dubai, Sharjah and the Northern Emirates.” | “We work on Nissan Patrols for owners across Dubai, Sharjah and the Northern Emirates.” |
| `services/nissan-patrol-v8-engine.html` | “We are a Nissan Patrol workshop in Ras Al Khor, so if you do end up needing someone to look at a VK56VD, we are here.” | “We work on Nissan Patrols only, so if you do end up needing someone to look at a VK56VD, message us.” |
| `services/y62-major-service-dubai.html` | “We are in Ras Al Khor and we work on Nissan Patrols only, so” | “We work on Nissan Patrols only, so” |
| `llms.txt` | “- **Service area:** Ras Al Khor, Dubai. Owners travel” | “- **Service area:** Dubai. Owners travel” |
| `blog/nissan-patrol-not-starting.html` | “The workshop is in Ras Al Khor, accessible from Al Qudra Road and a straightforward tow from anywhere on the Dubai side of the E611.” | *(deleted)* |
| `blog/nissan-patrol-y62-coolant-temperature-sensor-cost-uae-2026.html` | “Ten dull minutes of cross-referencing beats a second drive out to Ras Al Khor.” | “Ten dull minutes of cross-referencing beats a second trip.” |
| `blog/y62-fuel-injector-cleaning-cost-dubai-2026.html` | “individual injector flow testing on site in Ras Al Khor.” | “individual injector flow testing.” |
| `blog/nissan-patrol-y62-tow-bar-fitting-cost-dubai-2026.html` | “wiring harness prices explained by Ras Al Khor workshop.” | “wiring harness prices explained.” |
| `blog/y63-dashcam-installation-specialist-dubai-best-price-2026.html` | “battery relay. Ras Al Khor Dubai.” | “battery relay. Dubai.” |
| `services/y62-major-service-dubai.html` | “Ras Al Khor” | “Dubai” |

## 3b. Premises and opening-hours claims in site-wide chrome

| Page | Before | After |
|---|---|---|
| `site-wide (72 files)` | “RAS AL KHOR · DUBAI” | “DUBAI · UAE” |
| `site-wide (72 files)` | “BUILT IN DUBAI · RAS AL KHOR” | “BUILT IN DUBAI” |
| `site-wide (72 files)` | “Nissan Patrol specialists in Ras Al Khor, Dubai. Engine, gearbox, servicing and diagnostics.” | “Nissan Patrol specialists serving Dubai. Engine, gearbox, servicing and diagnostics.” |
| `site-wide (72 files)` | “Hours” | “Reach Us” |
| `site-wide (72 files)` | “FRI CLOSED” | “FRI OFF” |
| `site-wide (14 files)` | “>our Y62 workshop in Ras Al Khor” | “>Patrol Garage” |
| `site-wide (5 files)` | “is a Nissan Patrol specialist workshop in Ras Al Khor, Dubai.” | “is a Nissan Patrol specialist serving Dubai.” |

## 3c. Hero alt text (56 posts)

Every generated hero used its headline as the alt (e.g. “Patrol 4WD Not Engaging”), which names a model the AI-generated picture does not show. All were set to the shared neutral alt: “Illustration for this article: a large SUV in a workshop or desert setting. Not a photograph of a customer's vehicle.”

| Page | Alt before |
|---|---|
| `blog/best-oil-nissan-patrol-uae-heat.html` | Nissan Patrol Y62 |
| `blog/buying-a-used-nissan-patrol.html` | Used Patrol Buyer's Guide |
| `blog/nissan-patrol-4wd-not-engaging.html` | Patrol 4WD Not Engaging |
| `blog/nissan-patrol-ac-problems-dubai.html` | Nissan Patrol |
| `blog/nissan-patrol-best-year-to-buy.html` | Which Patrol Year Wins |
| `blog/nissan-patrol-black-smoke.html` | Patrol Black Smoke Fixes |
| `blog/nissan-patrol-diesel-vs-petrol.html` | Diesel or Petrol Patrol |
| `blog/nissan-patrol-differential-repair-cost-uae.html` | Patrol Differential Repair Costs |
| `blog/nissan-patrol-engine-overheating.html` | Patrol Engine Overheating |
| `blog/nissan-patrol-engine-problems.html` | Patrol Engine Problems Fixed |
| `blog/nissan-patrol-fuel-consumption.html` | Patrol Fuel Costs Explained |
| `blog/nissan-patrol-high-mileage.html` | Patrol High Mileage Facts |
| `blog/nissan-patrol-major-service.html` | Patrol Major Service Costs |
| `blog/nissan-patrol-mechanic-al-quoz.html` | Nissan Patrol |
| `blog/nissan-patrol-not-starting.html` | Patrol Not Starting |
| `blog/nissan-patrol-off-road-uae.html` | Nissan Patrol |
| `blog/nissan-patrol-oil-leak.html` | Patrol Oil Leak Fixes |
| `blog/nissan-patrol-overheating-dubai-summer-fix.html` | Patrol Overheating Dubai Fix |
| `blog/nissan-patrol-pre-purchase-inspection.html` | Nissan Patrol |
| `blog/nissan-patrol-service-cost-dubai.html` | Nissan Patrol |
| `blog/nissan-patrol-service-dubai-complete-guide.html` | nissan patrol service dubai complete guide |
| `blog/nissan-patrol-service-every-how-many-km-dubai.html` | Patrol Service Intervals Dubai |
| `blog/nissan-patrol-shaking-at-high-speed.html` | Patrol Shaking at Speed |
| `blog/nissan-patrol-steering-problems.html` | Patrol Steering Problems Fixed |
| `blog/nissan-patrol-suspension-dubai.html` | Nissan Patrol |
| `blog/nissan-patrol-transmission-rebuild-cost-dubai-aed.html` | Nissan Patrol Y62 |
| `blog/nissan-patrol-vibration-when-driving.html` | Patrol Vibration Fixed |
| `blog/nissan-patrol-warning-lights-meaning.html` | Patrol Warning Lights Explained |
| `blog/nissan-patrol-y61-dubai-complete-guide.html` | nissan patrol y61 dubai complete guide |
| `blog/nissan-patrol-y61-vs-y62-dubai.html` | Nissan Patrol |
| `blog/nissan-patrol-y62-coolant-temperature-sensor-cost-uae-2026.html` | Y62 Coolant Sensor Cost |
| `blog/nissan-patrol-y62-cv-joint-replacement-cost-uae-2026.html` | Y62 CV Joint Costs |
| `blog/nissan-patrol-y62-driveshaft-repair-cost-dubai-2026.html` | Y62 Driveshaft Repair Costs |
| `blog/nissan-patrol-y62-dubai-complete-guide.html` | Nissan Patrol Y62 |
| `blog/nissan-patrol-y62-fourth-brake-light-replacement-dubai-2026.html` | Y62 Brake Light Fixed |
| `blog/nissan-patrol-y62-head-gasket-replacement-cost-uae.html` | Y62 Head Gasket Cost |
| `blog/nissan-patrol-y62-oxygen-sensor-replacement-cost-dubai-2026.html` | Y62 Oxygen Sensor Cost |
| `blog/nissan-patrol-y62-paint-protection-film-cost-dubai-2026.html` | Y62 PPF Cost Dubai |
| `blog/nissan-patrol-y62-problems-dubai.html` | Nissan Patrol Y62 |
| `blog/nissan-patrol-y62-rear-differential-rebuild-cost-uae-2026.html` | Y62 Rear Diff Rebuild Cost |
| `blog/nissan-patrol-y62-starter-motor-replacement-cost-uae-2026.html` | Y62 Starter Motor Cost |
| `blog/nissan-patrol-y62-throttle-body-cleaning-cost-dubai.html` | Y62 Throttle Body Cleaning Cost |
| `blog/nissan-patrol-y62-tow-bar-fitting-cost-dubai-2026.html` | Y62 Tow Bar Cost |
| `blog/nissan-patrol-y62-transmission-problems-dubai.html` | Nissan Patrol Y62 |
| `blog/nissan-patrol-y62-turbo-upgrade-dubai-cost.html` | Y62 Turbo Upgrade Costs |
| `blog/nissan-patrol-y62-vs-y63-dubai-comparison.html` | nissan patrol y62 vs y63 dubai comparison |
| `blog/y61-super-safari-snorkel-fitting-cost-dubai-2026.html` | Y61 Snorkel Fitting Cost |
| `blog/y62-abs-sensor-replacement-cost-dubai-2026.html` | Y62 ABS Sensor Cost |
| `blog/y62-crankshaft-position-sensor-replacement-cost-dubai-2026.html` | Y62 CKP Sensor Cost |
| `blog/y62-engine-mount-replacement-cost-dubai-2026.html` | Y62 Mount Replacement Cost |
| `blog/y62-fuel-injector-cleaning-cost-dubai-2026.html` | Y62 Injector Cleaning Dubai |
| `blog/y62-fuel-pressure-regulator-replacement-cost-dubai-2026.html` | Y62 Regulator Replacement Cost |
| `blog/y62-intercooler-upgrade-cost-dubai-al-futtaim-vs-independent.html` | Y62 Intercooler Upgrade Cost |
| `blog/y62-rear-air-bag-replacement-cost-uae-2026.html` | Y62 Air Bag Cost |
| `blog/y62-spark-plug-replacement-cost-al-futtaim-vs-independent.html` | Y62 Spark Plug Cost |
| `blog/y62-water-pump-replacement-cost-uae-2026.html` | Y62 Water Pump Cost |

## 4. Generators fixed so the next run does not put the claims back

| Script | Change |
|---|---|
| `scripts/generate.py` | Opening line no longer says "a Nissan Patrol specialist workshop in Dubai (Ras Al Khor)". It now reads "a Nissan Patrol specialist service for owners in Dubai", followed by a NO PREMISES hard rule. The "WORKSHOP AREAS" list is relabelled as market context, not where Patrol Garage is. |
| `scripts/refresh_patch.py`, `scripts/humour_pass.py` | Same opening-line fix. Both prompts described the site as a Ras Al Khor workshop. |
| `scripts/money_links.py` | The two in-body money-link templates no longer say "our Y62 workshop in Ras Al Khor" or "specialist workshop in Ras Al Khor, Dubai". |
| `scripts/gen_llms_txt.py` | Service area is now "Dubai". `publish.py` regenerates `llms.txt` on every deploy, so this is the fix that holds. |
| `scripts/build_y62_garage_page.py`, `scripts/build_service_pages.py`, `scripts/site_update.py` | Same strings as the pages they build, so a re-run cannot restore "Where We Are", "We are an independent workshop in Ras Al Khor" or the "RAS AL KHOR" strip. |
| `scripts/test_check_claims.py` | The live-pages check fails again on any finding. It had been report-only while the 26 pages were dirty. |

The template for new posts is a real published post (`blog/nissan-patrol-y62-problems-dubai.html`), so the chrome fixed above reaches every future post too.

## 5. Kept on purpose (judgement calls, easy to reverse)

- **Contact-availability hours are kept, relabelled.** The footer "Hours … FRI CLOSED" block is now "Reach Us … FRI OFF", and contact.html's "Business Hours" is now "When You Can Reach Us". The times themselves stay, as do the homepage's "When you can reach us", `llms.txt`'s "Contactable" line and the `ContactPoint.hoursAvailable` schema. These are phone and WhatsApp hours, which `patch_entity_schema.py` deliberately kept as real. If you want every published hour gone, that is about five strings.
- **"The work is done in Ras Al Khor, Dubai's workshop district"** (contact.html) and **"The work happens in Ras Al Khor"** (index.html) are kept. Both are true of the partner workshop, claim no premises, and are the construction `build_abu_dhabi_page.py` documents as correct. The homepage heading above the second one changed from "A garage in Ras Al Khor." to "Where the work happens."
- **Third-party market references are kept**, e.g. "independent workshops in Ras Al Khor or Al Quoz typically charge…". They describe the market, not this business.
- **`areaServed` places in the homepage schema are kept** (Dubai, Ras Al Khor, Al Quoz…). A service area is not a premises claim.
- **"You will often see 10,000km or 6 months quoted"** (`nissan-patrol-service-every-how-many-km-dubai.html`). The rest of that section builds on the figure, so the Nissan attribution was dropped and the figure kept. Note that the owner's manual figure topchallenger verified is 10,000 km or **12** months, for the Y62 only. Correcting it here would apply a Y62 fact to the Y61 and Y63 the paragraph also covers.

## 6. What could not be fixed without inventing a fact

Each of these was deleted or reduced to a no-figure sentence. Restoring the detail needs a real source:

- **Dealer prices and labour times.** The documented "AED 3,065 for the 40,000 km service" (5 pages), the starter-motor dealer range, the throttle-body dealer range, the valve-cover dealer quote and Al-Futtaim's 2.0–2.5 hour spark-plug labour time were all removed.
- **The Al-Futtaim spark-plug section still has a problem.** The next paragraph's "total lands between AED 1,320 and AED 1,780" was not flagged, so it stayed, but it rests on the labour figure that was deleted. It needs a real dealer quote or removal.
- **Y62 fourth brake light fitment.** The claim that housings differ between "2010–2015 pre-facelift", "2016 facelift" and "2020" builds was deleted. Real fitment information needs a parts catalogue. The unflagged "Fitting a wrong-year housing to a Y62 is a common mistake" remains.
- **Nissan UAE warranty terms for head-gasket failure.** The paragraph now only says to check the terms with a dealer.
- **Oxygen sensor rated life** (100,000–160,000 km) and **Y61 snorkel part number** (SS780HF) were removed.
- **Official Y62 combined fuel figure** (14.4–14.5 L/100km) was removed, pending a Nissan spec sheet.

## 7. Found but not changed (outside "only the flagged sentences")

None of these trips a guard, but each is wrong or unsupported:

- **The phantom 2016 refresh is still in two sentences:** `nissan-patrol-service-every-how-many-km-dubai.html` ("Models refreshed in 2016 and 2020 have improved heat management…") and `nissan-patrol-y62-starter-motor-replacement-cost-uae-2026.html` ("including the 2016 and 2020 refreshes"). The guard misses them because "refreshed" is not "facelift".
- **Other unverified year boundaries:** `nissan-patrol-best-year-to-buy.html` ("The early 2010 to 2013 cars… By 2014…", "the 2016 to 2019 range"), `y62-fuel-injector-cleaning-cost-dubai-2026.html` ("a 2010 to 2015 pre-refresh model") and `y62-rear-air-bag-replacement-cost-uae-2026.html` ("If your Y62 is a 2010 to 2013 build").
- **A contradiction:** `nissan-patrol-diesel-vs-petrol.html` says "The Y63 … also runs a petrol V8", while other pages say the Y63 has a twin-turbo V6.
- **Y61 framed as serviced work,** against the Y62-only rule: "We're Nissan Patrol specialists — Y61, Y62, and Y63" (service complete guide), "Patrol Garage works on Y61 and Y62 Patrols" (steering), "We diagnose Y61, Y62, and Y63" (Y62 problems), "We fit snorkels regularly… for … Y61" (snorkel post).
- **Invented first-hand claims:** "serviced thousands of Patrols", "rebuilding Patrol transmissions for over a decade", "working on Y62 Patrols since the model launched in the UAE in 2010", "10+ years" (about.html), "Warranty Guaranteed" (homepage trust bar). Possible stock claims too ("we stock the correct NGK iridium plugs", "carry common Y62 cooling parts in stock").
- **Supabase copies:** `articles.content_html` still holds the old text of these posts. It is not served anywhere.
