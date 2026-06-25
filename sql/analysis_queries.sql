-- Soccer Scouting Platform — SQL analysis examples
-- Open database/scouting.db in DB Browser for SQLite, DBeaver, or Azure Data Studio
-- Replace 'Chelsea' with any team name from the dataset

-- =============================================================================
-- STEP 1: EXPLORATION
-- =============================================================================

-- Chelsea fixtures and results
SELECT
    match_date,
    home_team_name,
    away_team_name,
    home_score,
    away_score
FROM matches
WHERE home_team_name = 'Chelsea' OR away_team_name = 'Chelsea'
ORDER BY match_date;

-- Event counts by type for Chelsea
SELECT
    event_type,
    COUNT(*) AS event_count
FROM events
WHERE team_name = 'Chelsea'
GROUP BY event_type
ORDER BY event_count DESC;


-- =============================================================================
-- STEP 2: TACTICAL METRICS
-- =============================================================================

-- Season xG summary
SELECT
    team_name,
    COUNT(*) AS shots,
    SUM(is_goal) AS goals,
    ROUND(SUM(shot_xg), 2) AS total_xg,
    ROUND(SUM(is_goal) - SUM(shot_xg), 2) AS xg_difference,
    ROUND(AVG(shot_xg), 3) AS avg_xg_per_shot
FROM events
WHERE team_name = 'Chelsea'
  AND is_shot = 1
GROUP BY team_name;

-- xG breakdown by shot context (open play, free kick, penalty)
SELECT
    shot_type AS shot_context,
    COUNT(*) AS shots,
    SUM(is_goal) AS goals,
    ROUND(SUM(shot_xg), 2) AS total_xg
FROM events
WHERE team_name = 'Chelsea'
  AND is_shot = 1
GROUP BY shot_type
ORDER BY shots DESC;

-- Shot zone analysis (left / central / right)
SELECT
    CASE
        WHEN location_y < 80.0 / 3 THEN 'Left'
        WHEN location_y > (80.0 / 3) * 2 THEN 'Right'
        ELSE 'Central'
    END AS zone,
    COUNT(*) AS shots,
    SUM(is_goal) AS goals,
    ROUND(SUM(shot_xg), 2) AS total_xg
FROM events
WHERE team_name = 'Chelsea'
  AND is_shot = 1
  AND location_y IS NOT NULL
GROUP BY zone
ORDER BY shots DESC;

-- Top 10 shooters by xG
SELECT
    player_name,
    COUNT(*) AS shots,
    SUM(is_goal) AS goals,
    ROUND(SUM(shot_xg), 2) AS total_xg
FROM events
WHERE team_name = 'Chelsea'
  AND is_shot = 1
GROUP BY player_name
ORDER BY total_xg DESC
LIMIT 10;

-- PPDA per team (simplified: opponent passes / defensive actions)
-- Lower PPDA = more aggressive press
WITH defensive_actions AS (
    SELECT
        team_name,
        match_id,
        COUNT(*) AS def_actions
    FROM events
    WHERE event_type IN ('Pressure', 'Foul Committed', 'Tackle', 'Interception', 'Block')
    GROUP BY team_name, match_id
),
opponent_passes AS (
    SELECT
        m.match_id,
        e.team_name AS opponent,
        COUNT(*) AS opp_passes
    FROM events e
    JOIN matches m ON e.match_id = m.match_id
    WHERE e.event_type = 'Pass'
      AND e.team_name != 'Chelsea'  -- change team here for full league query
      AND (m.home_team_name = 'Chelsea' OR m.away_team_name = 'Chelsea')
    GROUP BY m.match_id, e.team_name
)
SELECT
    da.team_name,
    ROUND(SUM(op.opp_passes) * 1.0 / SUM(da.def_actions), 2) AS ppda
FROM defensive_actions da
JOIN matches m ON da.match_id = m.match_id
JOIN opponent_passes op ON da.match_id = op.match_id
WHERE da.team_name = 'Chelsea'
  AND op.opponent != da.team_name
GROUP BY da.team_name;


-- =============================================================================
-- STEP 3: SET-PIECE ANALYSIS
-- =============================================================================

-- Corners taken and delivery count by player
SELECT
    player_name,
    COUNT(*) AS corners_taken
FROM events
WHERE team_name = 'Chelsea'
  AND event_type = 'Pass'
  AND pass_type = 'Corner'
GROUP BY player_name
ORDER BY corners_taken DESC;

-- Shots from corners
SELECT
    COUNT(*) AS corner_shots,
    SUM(is_goal) AS goals,
    ROUND(SUM(shot_xg), 2) AS total_xg
FROM events
WHERE team_name = 'Chelsea'
  AND is_shot = 1
  AND play_pattern = 'From Corner';

-- Set-piece shots conceded (defensive vulnerability)
SELECT
    play_pattern,
    COUNT(*) AS shots_conceded,
    SUM(is_goal) AS goals_conceded,
    ROUND(SUM(shot_xg), 2) AS xg_conceded
FROM events e
JOIN matches m ON e.match_id = m.match_id
WHERE e.team_name != 'Chelsea'
  AND (m.home_team_name = 'Chelsea' OR m.away_team_name = 'Chelsea')
  AND e.is_shot = 1
  AND e.play_pattern IN ('From Corner', 'From Free Kick')
GROUP BY play_pattern;

-- Corner delivery target zones
SELECT
    CASE
        WHEN end_location_y < 80.0 / 3 THEN 'Near Post'
        WHEN end_location_y > (80.0 / 3) * 2 THEN 'Far Post'
        ELSE 'Penalty Spot'
    END AS target_zone,
    COUNT(*) AS deliveries
FROM events
WHERE team_name = 'Chelsea'
  AND pass_type = 'Corner'
  AND end_location_y IS NOT NULL
GROUP BY target_zone
ORDER BY deliveries DESC;