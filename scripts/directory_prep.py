#!/usr/bin/env python3
"""Prep submission data for UAE directories - copy-paste ready."""
from pathlib import Path

DIRECTORIES = [
    {
        "name": "Connect.ae",
        "url": "https://www.connect.ae/add-business",
        "notes": "UAE's largest business directory. Free tier exists.",
    },
    {
        "name": "DubaiBizz",
        "url": "https://www.dubaibizz.com/add-listing",
        "notes": "Dubai-focused, free basic listing.",
    },
    {
        "name": "Yalla Dubai",
        "url": "https://www.yalladubai.com/business",
        "notes": "Expat-focused, decent traffic.",
    },
    {
        "name": "YellowPages.ae",
        "url": "https://www.yellowpages.ae/add-your-company",
        "notes": "UAE Yellow Pages, established directory.",
    },
    {
        "name": "Dubai.com",
        "url": "https://www.dubai.com/business-directory",
        "notes": "Tourism-focused, useful for local relevance.",
    },
]

BUSINESS_DATA = {
    "name": "Patrol Garage Dubai",
    "category": "Auto Repair / Automotive Services",
    "subcategory": "Nissan Patrol Specialists",
    "description_short": "Nissan Patrol specialists in Dubai. Y61, Y62, Y63 service, repair, and modifications.",
    "description_long": (
        "Patrol Garage Dubai connects Nissan Patrol owners with specialist workshops in Dubai. "
        "We focus exclusively on the Nissan Patrol — Y61 Super Safari, Y62, and the new Y63. "
        "Our content covers common Patrol problems in UAE conditions, service costs, "
        "workshop recommendations, and maintenance guides written for Dubai's extreme climate. "
        "Whether you need a transmission rebuild, AC repair, suspension work, or pre-purchase "
        "inspection, we help you find the right specialist for your Patrol."
    ),
    "phone": "+971 58 514 3634",
    "whatsapp": "+971 58 514 3634",
    "email": "info@patrolgarage.ae",
    "website": "https://patrolgarage.ae",
    "area": "Ras Al Khor, Dubai",
    "city": "Dubai",
    "country": "United Arab Emirates",
    "hours": "Mon-Sat 9:00 AM - 7:00 PM, Friday Closed",
    "tags": "Nissan Patrol, Y62, Y61, Y63, Auto Repair, Dubai, Ras Al Khor, 4x4, SUV Service",
    "founded": "2026",
}

print("="*70)
print("UAE DIRECTORY SUBMISSION CHEAT SHEET")
print("="*70)
print()
print("BUSINESS INFO (copy this section for each directory):")
print("-"*70)
for k, v in BUSINESS_DATA.items():
    print(f"{k.upper().ljust(20)}: {v}")
print()
print("="*70)
print("DIRECTORIES TO SUBMIT (in order):")
print("="*70)
for i, d in enumerate(DIRECTORIES, 1):
    print(f"\n{i}. {d['name']}")
    print(f"   URL: {d['url']}")
    print(f"   Notes: {d['notes']}")

print()
print("="*70)
print("SUBMISSION TIPS:")
print("="*70)
print("- Use the same NAP (Name, Address, Phone) on every directory — consistency matters for local SEO")
print("- Always include the full website URL https://patrolgarage.ae")
print("- Pick 'Auto Repair' or closest category — if 'Lead Generation' is an option, avoid it (lower trust)")
print("- Skip paid upgrades on first submission — free tier is enough")
print("- Track which you've submitted in keywords.csv style file (add later)")
