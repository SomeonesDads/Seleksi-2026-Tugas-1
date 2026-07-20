CREATE TABLE path (
    path_id SERIAL PRIMARY KEY,
    name    VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE element (
    element_id SERIAL PRIMARY KEY,
    name       VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE stat (
    stat_id SERIAL PRIMARY KEY,
    name    VARCHAR(60) UNIQUE NOT NULL
);

CREATE TABLE material (
    material_id SERIAL PRIMARY KEY,
    name        VARCHAR(100) UNIQUE NOT NULL,
    rarity      SMALLINT    NOT NULL CHECK (rarity BETWEEN 2 AND 5),
    type        VARCHAR(20) NOT NULL CHECK (type IN ('ascension_mat', 'trace_mat', 'currency'))
);

CREATE TABLE light_cone (
    light_cone_id       SERIAL PRIMARY KEY,
    archive_id          VARCHAR(20)  UNIQUE NOT NULL,
    name                VARCHAR(100) NOT NULL,
    rarity              SMALLINT     NOT NULL CHECK (rarity BETWEEN 3 AND 5),
    path_id             INT          NOT NULL REFERENCES path(path_id),
    hp_lv1              INT,
    atk_lv1             INT,
    def_lv1             INT,
    hp_lv80             INT,
    atk_lv80            INT,
    def_lv80            INT,
    passive_name        VARCHAR(100),
    passive_description TEXT
);

CREATE TABLE relic_set (
    relic_set_id SERIAL PRIMARY KEY,
    archive_id   VARCHAR(20)  UNIQUE NOT NULL,
    name         VARCHAR(100) NOT NULL,
    type         VARCHAR(10)  NOT NULL CHECK (type IN ('relic', 'planar')),
    effect_2pc   TEXT,
    effect_4pc   TEXT
);

CREATE TABLE character (
    character_id SERIAL PRIMARY KEY,
    archive_id   VARCHAR(20)  UNIQUE NOT NULL,
    name         VARCHAR(100) NOT NULL,
    rarity       SMALLINT     NOT NULL CHECK (rarity IN (4, 5)),
    path_id      INT          NOT NULL REFERENCES path(path_id),
    element_id   INT          NOT NULL REFERENCES element(element_id),
    hp_lv1       INT,
    atk_lv1      INT,
    def_lv1      INT,
    spd_lv1      INT,
    hp_lv80      INT,
    atk_lv80     INT,
    def_lv80     INT,
    spd_lv80     INT
);

CREATE TABLE character_ascension_material (
    character_id INT NOT NULL REFERENCES character(character_id) ON DELETE CASCADE,
    material_id  INT NOT NULL REFERENCES material(material_id),
    amount       INT NOT NULL CHECK (amount > 0),
    PRIMARY KEY (character_id, material_id)
);

CREATE TABLE character_trace_material (
    character_id INT NOT NULL REFERENCES character(character_id) ON DELETE CASCADE,
    material_id  INT NOT NULL REFERENCES material(material_id),
    amount       INT NOT NULL CHECK (amount > 0),
    PRIMARY KEY (character_id, material_id)
);

CREATE TABLE character_recommended_lc (
    character_id  INT      NOT NULL REFERENCES character(character_id) ON DELETE CASCADE,
    light_cone_id INT      NOT NULL REFERENCES light_cone(light_cone_id),
    priority_rank SMALLINT NOT NULL CHECK (priority_rank > 0),
    PRIMARY KEY (character_id, light_cone_id)
);

CREATE TABLE character_recommended_relic (
    character_id  INT      NOT NULL REFERENCES character(character_id) ON DELETE CASCADE,
    relic_set_id  INT      NOT NULL REFERENCES relic_set(relic_set_id),
    priority_rank SMALLINT NOT NULL CHECK (priority_rank > 0),
    PRIMARY KEY (character_id, relic_set_id)
);

CREATE TABLE character_main_stat (
    character_id  INT          NOT NULL REFERENCES character(character_id) ON DELETE CASCADE,
    slot          VARCHAR(20)  NOT NULL CHECK (slot IN ('body', 'feet', 'planar_sphere', 'link_rope')),
    stat_id       INT          NOT NULL REFERENCES stat(stat_id),
    priority_rank SMALLINT     NOT NULL CHECK (priority_rank > 0),
    PRIMARY KEY (character_id, slot, stat_id)
);

CREATE TABLE character_sub_stat_priority (
    character_id  INT      NOT NULL REFERENCES character(character_id) ON DELETE CASCADE,
    stat_id       INT      NOT NULL REFERENCES stat(stat_id),
    priority_rank SMALLINT NOT NULL CHECK (priority_rank > 0),
    PRIMARY KEY (character_id, stat_id)
);

CREATE TABLE light_cone_ascension_material (
    light_cone_id INT NOT NULL REFERENCES light_cone(light_cone_id) ON DELETE CASCADE,
    material_id   INT NOT NULL REFERENCES material(material_id),
    amount        INT NOT NULL CHECK (amount > 0),
    PRIMARY KEY (light_cone_id, material_id)
);

CREATE TABLE team (
    team_id     SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE active_character (
    active_char_id    SERIAL PRIMARY KEY,
    team_id           INT      NOT NULL REFERENCES team(team_id) ON DELETE CASCADE,
    character_id      INT      NOT NULL REFERENCES character(character_id),
    slot_number       SMALLINT NOT NULL CHECK (slot_number BETWEEN 1 AND 3),
    level             SMALLINT NOT NULL DEFAULT 1  CHECK (level BETWEEN 1 AND 80),
    eidolon           SMALLINT NOT NULL DEFAULT 0  CHECK (eidolon BETWEEN 0 AND 6),
    trace_level       SMALLINT NOT NULL DEFAULT 1  CHECK (trace_level BETWEEN 1 AND 10),
    equipped_lc_id    INT      REFERENCES light_cone(light_cone_id),
    lc_superimposition SMALLINT CHECK (lc_superimposition BETWEEN 1 AND 5),
    UNIQUE (team_id, slot_number),
    UNIQUE (team_id, character_id)
);

--Triggers + helpers

-- Fungsi validasi konsistensi tipe relic set terhadap efek yang tersedia
CREATE OR REPLACE FUNCTION fn_check_relic_type()
RETURNS TRIGGER AS $$
BEGIN
    -- Planar cuma 2pc
    IF NEW.type = 'planar' AND NEW.effect_4pc IS NOT NULL THEN
        RAISE EXCEPTION
            'Relic set bertipe planar tidak boleh memiliki effect_4pc (id: %).', NEW.relic_set_id;
    END IF;

    --  Relic wajib ad efek 4pc
    IF NEW.type = 'relic' AND NEW.effect_4pc IS NULL THEN
        RAISE EXCEPTION
            'Relic set bertipe relic harus memiliki effect_4pc (id: %).', NEW.relic_set_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger validasi tipe relic set sebelum insert atau update
CREATE TRIGGER trg_check_relic_type
    BEFORE INSERT OR UPDATE ON relic_set
    FOR EACH ROW
    EXECUTE FUNCTION fn_check_relic_type();

-- Fungsi validasi superimposistion, harus ad klo ad activelc, dan gk boleh ad klo gk ad activelc
CREATE OR REPLACE FUNCTION fn_check_lc_superimposition()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.equipped_lc_id IS NOT NULL AND NEW.lc_superimposition IS NULL THEN
        RAISE EXCEPTION
            'Light cone terpasang harus memiliki nilai lc_superimposition (active_char_id: %).', NEW.active_char_id;
    END IF;
    IF NEW.equipped_lc_id IS NULL AND NEW.lc_superimposition IS NOT NULL THEN
        RAISE EXCEPTION
            'lc_superimposition tidak boleh diisi jika tidak ada light cone terpasang (active_char_id: %).', NEW.active_char_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger validasi superimposition light cone sebelum insert atau update
CREATE TRIGGER trg_check_lc_superimposition
    BEFORE INSERT OR UPDATE ON active_character
    FOR EACH ROW
    EXECUTE FUNCTION fn_check_lc_superimposition();

