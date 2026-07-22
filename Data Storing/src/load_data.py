import json
import os
import sys
import psycopg2
from psycopg2.extras import execute_values

DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "hsr_db",
    "user":     "postgres",
    "password": "Undertale",
}

DATA_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "Data Scraping", "data"
)

WARN_COUNT = 0

def header(title):
    print("=======================================================")
    print(f" {title}")
    print("=======================================================\n")


def log(msg):
    print(f"  {msg}")

def warn(msg):
    global WARN_COUNT
    WARN_COUNT += 1
    print(f"  [WARN] {msg}", file=sys.stderr)

def loadJSON(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalizePath(raw):
    return raw.removeprefix("The ").strip() if raw else ""

def insertPaths(cur, chars, lcs):
    paths = set()
    for c in chars:
        p = c["basic_info"].get("path")
        if p: paths.add(normalizePath(p))
    for lc in lcs:
        p = lc["basic_info"].get("path")
        if p: paths.add(normalizePath(p))

    execute_values(
        cur,
        "INSERT INTO path (name) VALUES %s ON CONFLICT DO NOTHING",
        [(p,) for p in sorted(paths)]
    )
    cur.execute("SELECT name, path_id FROM path")
    path_map = {r[0]: r[1] for r in cur.fetchall()}
    log(f"[SAVED] {len(path_map)} entries -> path")
    return path_map

def insertElements(cur, chars):
    elements = {
        c["basic_info"]["element"]
        for c in chars
        if c["basic_info"].get("element")
    }
    execute_values(
        cur,
        "INSERT INTO element (name) VALUES %s ON CONFLICT DO NOTHING",
        [(e,) for e in sorted(elements)]
    )
    cur.execute("SELECT name, element_id FROM element")
    element_map = {r[0]: r[1] for r in cur.fetchall()}
    log(f"[SAVED] {len(element_map)} entries -> element")
    return element_map

def insertStats(cur, chars):
    stats = set()
    for c in chars:
        build = c.get("best_build") or {}
        for stat_list in (build.get("main_stats") or {}).values():
            stats.update(stat_list)
        for entry in (c.get("recommended_stats") or {}).get("sub_stats_priority", []):
            stats.add(entry["stat"])

    execute_values(
        cur,
        "INSERT INTO stat (name) VALUES %s ON CONFLICT DO NOTHING",
        [(s,) for s in sorted(stats)]
    )
    cur.execute("SELECT name, stat_id FROM stat")
    stat_map = {r[0]: r[1] for r in cur.fetchall()}
    log(f"[SAVED] {len(stat_map)} entries -> stat")
    return stat_map

def insertMaterials(cur, mats):
    rows = []
    for m in mats:
        try:
            rows.append((m["name"], int(m["rarity"]), m["type"]))
        except (KeyError, ValueError):
            warn(f"Material rarity tidak valid, diskip: {m.get('name')}")

    execute_values(
        cur,
        "INSERT INTO material (name, rarity, type) VALUES %s ON CONFLICT DO NOTHING",
        rows
    )
    cur.execute("SELECT name, material_id FROM material")
    mat_map = {r[0]: r[1] for r in cur.fetchall()}
    log(f"[SAVED] {len(mat_map)} entries -> material")
    return mat_map

def insertRelicSets(cur, relics):
    rows = []
    for r in relics:
        effects = r.get("set_effects") or {}
        rows.append((
            r["archive_id"], r["name"], r["type"],
            effects.get("2pc_effect"),
            effects.get("4pc_effect"),
        ))
    execute_values(
        cur,
        """INSERT INTO relic_set (archive_id, name, type, effect_2pc, effect_4pc)
           VALUES %s ON CONFLICT DO NOTHING""",
        rows
    )
    cur.execute("SELECT name, relic_set_id FROM relic_set")
    relic_map = {r[0]: r[1] for r in cur.fetchall()}
    log(f"[SAVED] {len(relic_map)} entries -> relic_set")
    return relic_map


def insertLightCones(cur, lcs, path_map, mat_map):
    lc_rows = []
    for lc in lcs:
        path_name = normalizePath(lc["basic_info"].get("path") or "")
        path_id   = path_map.get(path_name)
        if not path_id:
            warn(f"Path tidak ditemukan untuk LC: {lc['name']} ({path_name})")
            continue

        lv1 = lc["base_stats"].get("level_1") or {}
        lv80 = lc["base_stats"].get("level_80") or {}
        passive = lc.get("passive_skill") or {}

        lc_rows.append((
            lc["archive_id"], lc["name"], lc["basic_info"]["rarity"], path_id,
            lv1.get("hp"),  lv1.get("atk"),  lv1.get("def"),
            lv80.get("hp"), lv80.get("atk"), lv80.get("def"),
            passive.get("name"), passive.get("description"),
        ))

    execute_values(cur, """
        INSERT INTO light_cone
            (archive_id, name, rarity, path_id,
             hp_lv1, atk_lv1, def_lv1,
             hp_lv80, atk_lv80, def_lv80,
             passive_name, passive_description)
        VALUES %s ON CONFLICT DO NOTHING
    """, lc_rows)

    cur.execute("SELECT name, light_cone_id FROM light_cone")
    lc_map = {r[0]: r[1] for r in cur.fetchall()}
    log(f"[SAVED] {len(lc_map)} entries -> light_cone")

    lc_mat_rows = []
    for lc in lcs:
        lc_id = lc_map.get(lc["name"])
        if not lc_id: continue
        for mat in (lc.get("total_materials") or {}).get("ascension", []):
            mat_id = mat_map.get(mat["name"])
            if mat_id:
                lc_mat_rows.append((lc_id, mat_id, mat["amount"]))
            else:
                warn(f"Material '{mat['name']}' tidak ada di materials.json (LC: {lc['name']})")

    if lc_mat_rows:
        execute_values(cur, """
            INSERT INTO light_cone_ascension_material (light_cone_id, material_id, amount)
            VALUES %s ON CONFLICT DO NOTHING
        """, lc_mat_rows)
    log(f"[SAVED] {len(lc_mat_rows)} entries -> light_cone_ascension_material")

    return lc_map


def insertCharacters(cur, chars, path_map, element_map, stat_map, mat_map, lc_map, relic_map):
    char_rows = []
    for c in chars:
        path_id    = path_map.get(normalizePath(c["basic_info"].get("path") or ""))
        element_id = element_map.get(c["basic_info"].get("element") or "")
        if not path_id or not element_id:
            warn(f"Path/Element tidak ditemukan: {c['name']}")
            continue

        lv1  = (c.get("base_stats") or {}).get("level_1") or {}
        lv80 = (c.get("base_stats") or {}).get("level_80") or {}

        char_rows.append((
            c["archive_id"], c["name"], c["basic_info"]["rarity"], path_id, element_id,
            lv1.get("hp"),  lv1.get("atk"),  lv1.get("def"),  lv1.get("spd"),
            lv80.get("hp"), lv80.get("atk"), lv80.get("def"), lv80.get("spd"),
        ))

    execute_values(cur, """
        INSERT INTO character
            (archive_id, name, rarity, path_id, element_id,
             hp_lv1, atk_lv1, def_lv1, spd_lv1,
             hp_lv80, atk_lv80, def_lv80, spd_lv80)
        VALUES %s ON CONFLICT DO NOTHING
    """, char_rows)

    cur.execute("SELECT name, character_id FROM character")
    char_map = {r[0]: r[1] for r in cur.fetchall()}
    log(f"[SAVED] {len(char_map)} entries -> character")

    asc_mat_rows   = []
    trace_mat_rows = []
    rec_lc_rows    = []
    rec_relic_rows = []
    main_stat_rows = []
    sub_stat_rows  = []

    for c in chars:
        char_id = char_map.get(c["name"])
        if not char_id: continue

        mats = c.get("total_materials") or {}

        for mat in mats.get("ascension", []):
            mat_id = mat_map.get(mat["name"])
            if mat_id:
                asc_mat_rows.append((char_id, mat_id, mat["amount"]))
            else:
                warn(f"Ascension mat '{mat['name']}' tidak ada (char: {c['name']})")

        for mat in mats.get("traces", []):
            mat_id = mat_map.get(mat["name"])
            if mat_id:
                trace_mat_rows.append((char_id, mat_id, mat["amount"]))
            else:
                warn(f"Trace mat '{mat['name']}' tidak ada (char: {c['name']})")

        build = c.get("best_build") or {}

        for rank, lc_name in enumerate(build.get("recommended_light_cones", []), start=1):
            lc_id = lc_map.get(lc_name)
            if lc_id:
                rec_lc_rows.append((char_id, lc_id, rank))
            else:
                warn(f"LC '{lc_name}' tidak ditemukan (char: {c['name']})")

        for rank, relic_name in enumerate(build.get("recommended_relics", []), start=1):
            relic_id = relic_map.get(relic_name)
            if relic_id:
                rec_relic_rows.append((char_id, relic_id, rank))
            else:
                warn(f"Relic '{relic_name}' tidak ditemukan (char: {c['name']})")

        for slot, stat_list in (build.get("main_stats") or {}).items():
            for rank, stat_name in enumerate(stat_list, start=1):
                stat_id = stat_map.get(stat_name)
                if stat_id:
                    main_stat_rows.append((char_id, slot, stat_id, rank))
                else:
                    warn(f"Stat '{stat_name}' tidak ada di stat table (char: {c['name']})")

        for entry in (c.get("recommended_stats") or {}).get("sub_stats_priority", []):
            stat_id = stat_map.get(entry["stat"])
            if stat_id:
                sub_stat_rows.append((char_id, stat_id, entry["priority_rank"]))
            else:
                warn(f"Stat '{entry['stat']}' tidak ada di stat table (char: {c['name']})")

    def bulk(sql, rows, label):
        if rows:
            execute_values(cur, sql, rows)
        log(f"[SAVED] {len(rows)} entries -> {label}")

    bulk("INSERT INTO character_ascension_material (character_id, material_id, amount) VALUES %s ON CONFLICT DO NOTHING", asc_mat_rows, "character_ascension_material")
    bulk("INSERT INTO character_trace_material (character_id, material_id, amount) VALUES %s ON CONFLICT DO NOTHING", trace_mat_rows, "character_trace_material")
    bulk("INSERT INTO character_recommended_lc (character_id, light_cone_id, priority_rank) VALUES %s ON CONFLICT DO NOTHING", rec_lc_rows, "character_recommended_lc")
    bulk("INSERT INTO character_recommended_relic (character_id, relic_set_id, priority_rank) VALUES %s ON CONFLICT DO NOTHING", rec_relic_rows, "character_recommended_relic")
    bulk("INSERT INTO character_main_stat (character_id, slot, stat_id, priority_rank) VALUES %s ON CONFLICT DO NOTHING", main_stat_rows, "character_main_stat")
    bulk("INSERT INTO character_sub_stat_priority (character_id, stat_id, priority_rank) VALUES %s ON CONFLICT DO NOTHING", sub_stat_rows, "character_sub_stat_priority")

    return char_map


def load():
    print("Mulai Data Loading...")
    header("Phase 1: Loading scraped JSON files")
    print("[LOAD 1/4] Loading characters.json...")
    chars = loadJSON("characters.json")
    print("[LOAD 2/4] Loading light_cone.json...")
    lcs = loadJSON("light_cone.json")
    print("[LOAD 3/4] Loading relic.json...")
    relics = loadJSON("relic.json")
    print("[LOAD 4/4] Loading materials.json...")
    mats = loadJSON("materials.json")
    print(f"\n[DONE] All JSON files loaded from data/ folder.")

    header("Phase 2: Connecting to PostgreSQL")
    print(f"[CONNECT] Connecting to {DB_CONFIG['dbname']} at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    print("[CONNECTED] Connection established.")
    try:
        header("Phase 3: Inserting reference tables")
        print("[STEP 1/3] Inserting paths...")
        path_map = insertPaths(cur, chars, lcs)
        print("[STEP 2/3] Inserting elements...")
        element_map = insertElements(cur, chars)
        print("[STEP 3/3] Inserting stats...")
        stat_map = insertStats(cur, chars)

        header("Phase 4: Inserting materials")
        print("[STEP 1/1] Inserting materials...")
        mat_map = insertMaterials(cur, mats)

        header("Phase 5: Inserting relic sets")
        print("[STEP 1/1] Inserting relic sets...")
        relic_map = insertRelicSets(cur, relics)

        header("Phase 6: Inserting light cones")
        print("[STEP 1/2] Inserting light cone base data...")
        lc_map = insertLightCones(cur, lcs, path_map, mat_map)

        header("Phase 7: Inserting characters")
        print("[STEP 1/2] Inserting character base data and relation tables...")
        char_map = insertCharacters(cur, chars, path_map, element_map, stat_map, mat_map, lc_map, relic_map)

        conn.commit()

        print("\n=======================================================")
        print(f"[SUMMARY] Warnings raised: {WARN_COUNT}")
        print("[DONE] All data inserted into hsr_db.")
        print("=======================================================")

    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] {e}")
        raise
    finally:
        cur.close()
        conn.close()

# load()