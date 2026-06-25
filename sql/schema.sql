-- Soccer Scouting Platform — core schema (SQLite)

CREATE TABLE IF NOT EXISTS competitions (
    competition_id INTEGER NOT NULL,
    season_id INTEGER NOT NULL,
    competition_name TEXT NOT NULL,
    country_name TEXT,
    season_name TEXT NOT NULL,
    competition_gender TEXT,
    PRIMARY KEY (competition_id, season_id)
);

CREATE TABLE IF NOT EXISTS matches (
    match_id INTEGER PRIMARY KEY,
    competition_id INTEGER NOT NULL,
    season_id INTEGER NOT NULL,
    match_date TEXT,
    kick_off TEXT,
    home_team_id INTEGER,
    home_team_name TEXT NOT NULL,
    away_team_id INTEGER,
    away_team_name TEXT NOT NULL,
    home_score INTEGER,
    away_score INTEGER,
    FOREIGN KEY (competition_id, season_id)
        REFERENCES competitions (competition_id, season_id)
);

CREATE TABLE IF NOT EXISTS events (
    event_id TEXT PRIMARY KEY,
    match_id INTEGER NOT NULL,
    team_id INTEGER,
    team_name TEXT,
    player_id INTEGER,
    player_name TEXT,
    event_type TEXT NOT NULL,
    event_type_id INTEGER,
    possession INTEGER,
    period INTEGER,
    minute INTEGER,
    second INTEGER,
    location_x REAL,
    location_y REAL,
    end_location_x REAL,
    end_location_y REAL,
    is_goal INTEGER DEFAULT 0,
    is_shot INTEGER DEFAULT 0,
    shot_xg REAL,
    shot_body_part TEXT,
    shot_type TEXT,
    shot_outcome TEXT,
    pass_type TEXT,
    pass_outcome TEXT,
    pass_length REAL,
    pass_angle REAL,
    under_pressure INTEGER DEFAULT 0,
    play_pattern TEXT,
    FOREIGN KEY (match_id) REFERENCES matches (match_id)
);

CREATE INDEX IF NOT EXISTS idx_events_match_id ON events (match_id);
CREATE INDEX IF NOT EXISTS idx_events_team_name ON events (team_name);
CREATE INDEX IF NOT EXISTS idx_events_event_type ON events (event_type);
CREATE INDEX IF NOT EXISTS idx_matches_home_team ON matches (home_team_name);
CREATE INDEX IF NOT EXISTS idx_matches_away_team ON matches (away_team_name);