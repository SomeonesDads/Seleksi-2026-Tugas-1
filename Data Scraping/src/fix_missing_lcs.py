"""
- Patience Is All You Need
- Earthly Escapade
- Carve the Moon, Weave the Clouds

Game8 ini jelek kali, ntah kenapa formatny beda untuk tig
"""
import json
import lc_scraper

links = [
    {"name": "Patience Is All You Need", "archive_id": "417670", "url": "https://game8.co/games/Honkai-Star-Rail/archives/417670"},
    {"name": "Earthly Escapade", "archive_id": "441041", "url": "https://game8.co/games/Honkai-Star-Rail/archives/441041"},
    {"name": "Carve the Moon, Weave the Clouds", "archive_id": "408545", "url": "https://game8.co/games/Honkai-Star-Rail/archives/408545"}
]

passives = {
    "Patience Is All You Need": {
        "name": "Spider Web",
        "description": "Increases DMG dealt by the wearer by 24%. After every attack unleashed by the wearer, the wearer's SPD increases by 4.8%, stacking up to 3 times. If the wearer hits an enemy target that is not afflicted by Erode, there is a 100% base chance to inflict Erode on the target. Enemies afflicted with Erode are also considered to be Shocked and will receive Lightning DoT at the start of each turn equal to 60% of the wearer's ATK, lasting for 1 turn."
    },
    "Earthly Escapade": {
        "name": "Capriciousness",
        "description": "Increases the wearer's CRIT DMG by 32%. At the start of the battle, the wearer gains Mask, lasting for 3 turns. While the wearer has Mask, the wearer's allies have their CRIT Rate increased by 10% and their CRIT DMG increased by 28%. For every 1 Skill Point the wearer recovers (including Skill Points that exceed the limit), they gain 1 stack of Radiant Flame. And when the wearer has 4 stacks of Radiant Flame, all the stacks are removed, and they gain Mask, lasting for 4 turns."
    },
    "Carve the Moon, Weave the Clouds": {
        "name": "Secret",
        "description": "At the start of the battle and whenever the wearer's turn begins, one of the following effects is applied randomly: All allies' ATK increases by 10%, all allies' CRIT DMG increases by 12%, or all allies' Energy Regeneration Rate increases by 6%. The applied effect cannot be identical to the last effect applied, and will replace the previous effect. The applied effect will be removed when the wearer has been knocked down. Effects of the similar type cannot be stacked."
    }
}

def fix():
    with open('data/light_cone.json', 'r', encoding='utf-8') as f:
        lcs = json.load(f)

    for l in links:
        print(f"Scraping {l['name']}")
        soup = lc_scraper.fetch(l['url'])
        if not soup:
            print("Fetch failed")
            continue

        basic_info = lc_scraper.parseBasicInfo(soup)
        base_stats = lc_scraper.parseBaseStats(soup)
        materials = lc_scraper.parseMaterials(soup)
        passive = passives[l['name']]
        
        lc_dict = {
            "name": l["name"],
            "archive_id": l["archive_id"],
            "url": l["url"],
            "basic_info": basic_info,
            "base_stats": base_stats,
            "passive_skill": passive,
            "total_materials": materials,
        }
        exists = False
        for i, existing_lc in enumerate(lcs):
            if existing_lc['name'] == l['name']:
                lcs[i] = lc_dict
                exists = True
                break
                
        if not exists:
            lcs.append(lc_dict)

    with open('data/light_cone.json', 'w', encoding='utf-8') as f:
        json.dump(lcs, f, indent=4, ensure_ascii=False)