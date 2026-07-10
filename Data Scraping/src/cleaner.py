"""
Intinya di cleaner ini mau ngilangin yg gk jelas (e. g. Divergent universe masuk jadi relic) + char char yang belum rilis
Entah kenapa dimasukin game8 ke sitenya, hasil akhirnya ada yg null gitu.
Cuma ada beberapa inconsistency kayak boothill gk ad archive id, LC gak ada effectnya ditulis, jadi kita buat exclusion list
"""

EXCLUSION_LIST = [
    "boothill",
    "earthly escapade",
    "patience Is all you need",
    "carve the moon, weave the clouds"
]

import json
import os

DATA_DIR = "../data"


def contains_null(obj):
    if isinstance(obj, dict):
        return any(
            value is None or contains_null(value)
            for value in obj.values()
        )
    elif isinstance(obj, list):
        return any(contains_null(item) for item in obj)

    return False


def phase3():
    total_scanned = 0
    total_deleted = 0
    for filename in os.listdir(DATA_DIR):
        if not filename.endswith(".json"):
            continue

        if "link" in filename.lower():
            continue

        filepath = os.path.join(DATA_DIR, filename)
        print(f"\n[CLEANER] Opening {filepath}...")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        deleted_in_file = 0

        if isinstance(data, list):
            cleaned_data = []

            for entry in data:
                total_scanned += 1
                if(entry['name'].lower() in EXCLUSION_LIST): continue

                if contains_null(entry):
                    print(f"    [DELETED] Entry: {entry['name']}")
                    total_deleted += 1
                    deleted_in_file += 1
                    continue

                cleaned_data.append(entry)

        elif isinstance(data, dict):
            cleaned_data = {}

            for key, value in data.items():
                total_scanned += 1

                if contains_null(value):
                    print(f"[DELETED] Entry: {value['name']}")
                    total_deleted += 1
                    deleted_in_file += 1
                    continue

                cleaned_data[key] = value

        else:
            continue

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                cleaned_data,
                f,
                indent=4,
                ensure_ascii=False
            )

        print(f"[CLEANED] {filename} | Deleted: {deleted_in_file}")


    print(f"\n[CLEANER] Total entries scanned : {total_scanned}")
    print(f"[CLEANER] Total entries deleted: {total_deleted}")