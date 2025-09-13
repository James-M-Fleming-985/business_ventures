# Gamification and Clash Royale API Integration Schema

-- User Ranking and Progression System
CREATE TABLE user_rankings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Current Ranking
    current_rank INTEGER NOT NULL DEFAULT 0,
    rank_tier VARCHAR(20) DEFAULT 'bronze', -- bronze, silver, gold, platinum, diamond, legend
    rank_division INTEGER DEFAULT 1, -- 1-5 within each tier
    
    -- Rating System (ELO-style)
    rating DECIMAL(8,2) DEFAULT 1000.00,
    peak_rating DECIMAL(8,2) DEFAULT 1000.00,
    season_rating DECIMAL(8,2) DEFAULT 1000.00,
    
    -- XP and Level System
    total_xp BIGINT DEFAULT 0,
    current_level INTEGER DEFAULT 1,
    xp_to_next_level INTEGER DEFAULT 100,
    
    -- Performance Metrics
    total_analyses INTEGER DEFAULT 0,
    average_accuracy DECIMAL(5,2) DEFAULT 0.00,
    best_accuracy DECIMAL(5,2) DEFAULT 0.00,
    improvement_rate DECIMAL(5,4) DEFAULT 0.00, -- Rate of improvement over time
    consistency_score DECIMAL(5,2) DEFAULT 0.00, -- How consistent placements are
    
    -- Streaks and Bonuses
    current_streak INTEGER DEFAULT 0,
    longest_streak INTEGER DEFAULT 0,
    daily_analyses_count INTEGER DEFAULT 0,
    last_analysis_date DATE,
    
    -- Seasonal Data
    season_id VARCHAR(20),
    season_start_date DATE,
    season_analyses INTEGER DEFAULT 0,
    season_best_accuracy DECIMAL(5,2) DEFAULT 0.00,
    
    -- Timestamps
    last_rank_update TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for leaderboards and fast lookups
CREATE INDEX idx_user_rankings_rating ON user_rankings(rating DESC);
CREATE INDEX idx_user_rankings_tier_division ON user_rankings(rank_tier, rank_division);
CREATE INDEX idx_user_rankings_season ON user_rankings(season_id, season_rating DESC);
CREATE INDEX idx_user_rankings_level ON user_rankings(current_level DESC);

-- Achievement System
CREATE TABLE achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL, -- unique identifier for achievement
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(50), -- placement, improvement, consistency, social, special
    tier VARCHAR(20) DEFAULT 'bronze', -- bronze, silver, gold, platinum, diamond, legend
    
    -- Requirements
    requirement_type VARCHAR(50), -- total_analyses, accuracy_threshold, streak, etc.
    requirement_value DECIMAL(10,2),
    requirement_condition TEXT, -- JSON with complex conditions
    
    -- Rewards
    xp_reward INTEGER DEFAULT 0,
    badge_url VARCHAR(500),
    title VARCHAR(100),
    
    -- Metadata
    is_active BOOLEAN DEFAULT true,
    is_seasonal BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User Achievements (earned achievements)
CREATE TABLE user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES achievements(id) ON DELETE CASCADE,
    
    -- Progress tracking
    progress_current DECIMAL(10,2) DEFAULT 0,
    progress_required DECIMAL(10,2),
    is_completed BOOLEAN DEFAULT false,
    
    -- Completion details
    completed_at TIMESTAMPTZ,
    analysis_id UUID REFERENCES analysis_history(id), -- Analysis that triggered completion
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, achievement_id)
);

-- Leaderboards (materialized views for performance)
CREATE TABLE leaderboards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    leaderboard_type VARCHAR(50), -- global, weekly, monthly, seasonal, friends
    user_id UUID NOT NULL REFERENCES users(id),
    rank_position INTEGER NOT NULL,
    score DECIMAL(10,2) NOT NULL,
    display_name VARCHAR(100),
    
    -- Additional stats for context
    total_analyses INTEGER,
    average_accuracy DECIMAL(5,2),
    rating DECIMAL(8,2),
    
    -- Time period
    period_start DATE,
    period_end DATE,
    
    -- Metadata
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(leaderboard_type, user_id, period_start, period_end)
);

-- Indexes for leaderboard queries
CREATE INDEX idx_leaderboards_type_rank ON leaderboards(leaderboard_type, rank_position);
CREATE INDEX idx_leaderboards_period ON leaderboards(period_start, period_end);

-- Clash Royale Card Data Integration
CREATE TABLE card_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id INTEGER UNIQUE NOT NULL, -- Clash Royale API card ID
    name VARCHAR(100) NOT NULL,
    
    -- Card Properties (from Clash Royale API)
    elixir_cost INTEGER,
    type VARCHAR(50), -- spell, troop, building
    rarity VARCHAR(20), -- common, rare, epic, legendary
    arena INTEGER, -- unlock arena
    
    -- Combat Stats
    hitpoints INTEGER,
    damage INTEGER,
    damage_per_second DECIMAL(6,2),
    hit_speed DECIMAL(4,2),
    targets VARCHAR(50), -- ground, air, ground_air
    range DECIMAL(4,2),
    deploy_time DECIMAL(4,2),
    
    -- Movement and Mechanics
    speed VARCHAR(20), -- slow, medium, fast, very_fast
    count INTEGER, -- for cards that spawn multiple units
    lifetime DECIMAL(4,2), -- for temporary units/buildings
    radius DECIMAL(4,2), -- area of effect
    
    -- Strategic Properties
    description TEXT,
    strategy_tips TEXT,
    counters TEXT[], -- Array of counter card names
    synergies TEXT[], -- Array of synergy card names
    
    -- Balance History
    balance_changes JSONB, -- Historical balance changes
    current_meta_rating DECIMAL(3,2), -- Current meta strength (0-10)
    usage_rate DECIMAL(5,4), -- Usage rate in top ladder
    win_rate DECIMAL(5,4), -- Win rate when used
    
    -- API Sync
    last_api_sync TIMESTAMPTZ DEFAULT NOW(),
    api_version VARCHAR(20),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Card Balance Changes Log
CREATE TABLE balance_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id INTEGER NOT NULL REFERENCES card_metadata(card_id),
    
    -- Change Details
    change_date DATE NOT NULL,
    change_type VARCHAR(50), -- buff, nerf, rework, bug_fix
    affected_stats TEXT[], -- Array of changed stats
    
    -- Before/After Values
    changes_data JSONB, -- Detailed before/after values
    patch_notes TEXT,
    
    -- Impact Analysis
    usage_rate_before DECIMAL(5,4),
    usage_rate_after DECIMAL(5,4),
    win_rate_before DECIMAL(5,4),
    win_rate_after DECIMAL(5,4),
    meta_impact_score DECIMAL(3,2), -- How much this changed the meta
    
    -- Our Response
    model_retrain_triggered BOOLEAN DEFAULT false,
    retrain_completed_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User Preferences and Social Features
CREATE TABLE user_social_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    
    -- Privacy Settings
    show_on_leaderboards BOOLEAN DEFAULT true,
    allow_friend_requests BOOLEAN DEFAULT true,
    public_profile BOOLEAN DEFAULT false,
    
    -- Display Settings
    display_name VARCHAR(100),
    show_real_name BOOLEAN DEFAULT false,
    profile_avatar_url VARCHAR(500),
    
    -- Clash Royale Integration
    clash_royale_tag VARCHAR(20), -- Player tag from CR
    clash_royale_verified BOOLEAN DEFAULT false,
    auto_sync_cr_data BOOLEAN DEFAULT true,
    
    -- Notification Preferences
    notify_rank_changes BOOLEAN DEFAULT true,
    notify_achievements BOOLEAN DEFAULT true,
    notify_friend_activity BOOLEAN DEFAULT true,
    notify_weekly_summary BOOLEAN DEFAULT true,
    notify_balance_changes BOOLEAN DEFAULT true,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Friend System
CREATE TABLE user_friends (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    requester_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    addressee_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'pending', -- pending, accepted, blocked
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(requester_id, addressee_id),
    CHECK(requester_id != addressee_id)
);

-- Challenges and Events
CREATE TABLE challenges (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    challenge_type VARCHAR(50), -- daily, weekly, monthly, seasonal, special
    
    -- Requirements
    requirements JSONB, -- JSON with challenge requirements
    target_value DECIMAL(10,2),
    
    -- Rewards
    xp_reward INTEGER DEFAULT 0,
    special_rewards JSONB, -- Badges, titles, etc.
    
    -- Time Period
    start_date TIMESTAMPTZ NOT NULL,
    end_date TIMESTAMPTZ NOT NULL,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    max_participants INTEGER,
    current_participants INTEGER DEFAULT 0,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User Challenge Progress
CREATE TABLE user_challenge_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    challenge_id UUID NOT NULL REFERENCES challenges(id) ON DELETE CASCADE,
    
    -- Progress
    current_progress DECIMAL(10,2) DEFAULT 0,
    is_completed BOOLEAN DEFAULT false,
    completion_rank INTEGER, -- Rank among all participants
    
    -- Timestamps
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    
    UNIQUE(user_id, challenge_id)
);

-- Performance optimization
CREATE INDEX idx_user_rankings_user_id ON user_rankings(user_id);
CREATE INDEX idx_user_achievements_user_id ON user_achievements(user_id);
CREATE INDEX idx_user_achievements_progress ON user_achievements(user_id, is_completed);
CREATE INDEX idx_card_metadata_name ON card_metadata(name);
CREATE INDEX idx_balance_changes_date ON balance_changes(change_date DESC);
CREATE INDEX idx_user_friends_status ON user_friends(addressee_id, status);

-- Materialized view for global leaderboard (refreshed every 5 minutes)
CREATE MATERIALIZED VIEW global_leaderboard AS
SELECT 
    ROW_NUMBER() OVER (ORDER BY rating DESC) as rank,
    user_id,
    rating,
    rank_tier,
    rank_division,
    total_analyses,
    average_accuracy,
    improvement_rate,
    current_streak
FROM user_rankings 
WHERE rating > 0
ORDER BY rating DESC
LIMIT 1000;

-- Refresh index
CREATE UNIQUE INDEX ON global_leaderboard (rank);

-- Function to update user ranking after each analysis
CREATE OR REPLACE FUNCTION update_user_ranking()
RETURNS TRIGGER AS $$
BEGIN
    -- Update user ranking stats based on new analysis
    UPDATE user_rankings 
    SET 
        total_analyses = total_analyses + 1,
        average_accuracy = (
            SELECT AVG(overall_score) 
            FROM analysis_history 
            WHERE user_id = NEW.user_id
        ),
        best_accuracy = GREATEST(best_accuracy, NEW.overall_score),
        last_analysis_date = CURRENT_DATE,
        updated_at = NOW()
    WHERE user_id = NEW.user_id;
    
    -- Calculate new rating (simplified ELO-style)
    -- This would be more sophisticated in practice
    UPDATE user_rankings
    SET rating = rating + (NEW.overall_score - 70) * 0.5
    WHERE user_id = NEW.user_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update rankings
CREATE TRIGGER trigger_update_user_ranking
    AFTER INSERT ON analysis_history
    FOR EACH ROW
    EXECUTE FUNCTION update_user_ranking();
