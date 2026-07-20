"""
Normalize stat karna ntah kenapa beda2 semua dibuat game8 ini
Standar stat yang digunakan:
  Crit Rate%, Crit DMG%, ATK, ATK%, HP, HP%, DEF, DEF%,
  SPD, Effect Hit Rate, Effect Res, Break Effect,
  Outgoing Healing Boost, Energy Regeneration Rate,
  {Element} DMG (Fire, Ice, Wind, Lightning, Physical, Quantum, Imaginary)
"""

import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CHAR_FILE = os.path.join(DATA_DIR, "characters.json")

# Mapping dari semua bentuk raw ke bentuk standar
# Exception per karakter untuk stat yg lain kali kek punya sampo ini (atp this site is just ahh)
CHAR_EXCEPTIONS = {
    "Sampo": {"DMG": "Wind DMG"},
}

STAT_MAP = {
    # Crit
    "CRIT Rate":        "Crit Rate%",
    "CRIT Rate%":       "Crit Rate%",
    "Crit Rate":        "Crit Rate%",
    "Crit Rate%":       "Crit Rate%",
    "CRIT DMG":         "Crit DMG%",
    "CRIT DMG%":        "Crit DMG%",
    "Crit DMG":         "Crit DMG%",
    "Crit DMG%":        "Crit DMG%",
    # Base
    "ATK":              "ATK",
    "ATK%":             "ATK%",
    "HP":               "HP",
    "HP%":              "HP%",
    "DEF":              "DEF",
    "DEF%":             "DEF%",
    "Flat ATK":         "ATK",
    "Flat HP":          "HP",
    "SPD":              "SPD",
    # Effect 
    "EHR":              "Effect Hit Rate",
    "Effect Hit Rate":  "Effect Hit Rate",
    "Effect Hit Rate%": "Effect Hit Rate",
    "Effect RES":       "Effect Res",
    "Effect RES%":      "Effect Res",
    "Effect Res":       "Effect Res",
    "Effect Res%":      "Effect Res",
    # Other
    "Break Effect":             "Break Effect",
    "Energy Regen":             "Energy Regeneration Rate",
    "Energy Regeneration Rate": "Energy Regeneration Rate",
    "Outgoing Healing":         "Outgoing Healing Boost",
    "Outgoing Healing Boost":   "Outgoing Healing Boost",
    # Element DMG 
    "Fire DMG":        "Fire DMG",
    "Fire DMG%":       "Fire DMG",
    "Ice DMG":         "Ice DMG",
    "Ice DMG%":        "Ice DMG",
    "Wind DMG":        "Wind DMG",
    "Wind DMG%":       "Wind DMG",
    "Lightning DMG":   "Lightning DMG",
    "Lightning DMG%":  "Lightning DMG",
    "Physical DMG":    "Physical DMG",
    "Physical DMG%":   "Physical DMG",
    "Phys DMG":        "Physical DMG",
    "Phys DMG%":       "Physical DMG",
    "Quantum DMG":     "Quantum DMG",
    "Quantum DMG%":    "Quantum DMG",
    "Imaginary DMG":   "Imaginary DMG",
    "Imaginary DMG%":  "Imaginary DMG",
}


def normalizeStat(raw, char_name=None):
    if char_name and char_name in CHAR_EXCEPTIONS:
        if raw in CHAR_EXCEPTIONS[char_name]:
            return CHAR_EXCEPTIONS[char_name][raw], True
    if raw in STAT_MAP:
        return STAT_MAP[raw], True
    return raw, False


def normalizeChars(chars):
    unknown = set()
    changed = 0

    for c in chars:
        build = c.get("best_build") or {}

        for slot, stat_list in (build.get("main_stats") or {}).items():
            new_list = []
            for s in stat_list:
                normalized, found = normalizeStat(s, c["name"])
                if not found:
                    unknown.add(s)
                elif normalized != s:
                    changed += 1
                new_list.append(normalized)
            build["main_stats"][slot] = new_list

        sub_stats = (c.get("recommended_stats") or {}).get("sub_stats_priority", [])
        for entry in sub_stats:
            normalized, found = normalizeStat(entry["stat"], c["name"])
            if not found:
                unknown.add(entry["stat"])
            elif normalized != entry["stat"]:
                changed += 1
            entry["stat"] = normalized

    return changed, unknown


def run():
    with open(CHAR_FILE, "r", encoding="utf-8") as f:
        chars = json.load(f)

    changed, unknown = normalizeChars(chars)

    if unknown:
        print(f"[WARN] {len(unknown)} stat tidak dikenali, dibiarkan apa adanya:")
        for u in sorted(unknown):
            print(f"  '{u}'")
    
    print(f"[INFO] {changed} nilai stat diubah ke bentuk standar")

    with open(CHAR_FILE, "w", encoding="utf-8") as f:
        json.dump(chars, f, indent=4, ensure_ascii=False)

    print(f"[SAVED] {CHAR_FILE}")