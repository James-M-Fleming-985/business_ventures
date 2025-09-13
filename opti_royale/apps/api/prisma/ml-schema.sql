# User Analysis History and ML Data Schema

-- Users table (already exists in main API)
-- Extended with ML-specific fields

-- Analysis History Table
CREATE TABLE analysis_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id UUID NOT NULL,
    analysis_timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    -- Video metadata
    video_filename VARCHAR(255) NOT NULL,
    video_duration_seconds INTEGER,
    video_resolution VARCHAR(20),
    video_file_size_bytes BIGINT,
    video_storage_url TEXT,
    
    -- Game context
    game_mode VARCHAR(50), -- ladder, tournament, clan_war, etc.
    player_level INTEGER,
    player_trophies INTEGER,
    opponent_trophies INTEGER,
    elixir_advantage DECIMAL(3,2),
    
    -- Analysis results
    overall_score DECIMAL(5,2), -- 0-100 optimization score
    placement_accuracy DECIMAL(5,2), -- percentage of optimal placements
    elixir_efficiency DECIMAL(5,2), -- elixir usage optimization
    timing_score DECIMAL(5,2), -- timing of card placements
    
    -- Detailed placement data (JSON)
    card_placements JSONB, -- Array of placement decisions with scores
    optimal_placements JSONB, -- AI-recommended optimal placements
    improvement_suggestions JSONB, -- Specific suggestions for improvement
    
    -- Model metadata
    model_version VARCHAR(50),
    confidence_score DECIMAL(5,4),
    processing_time_ms INTEGER,
    
    -- User feedback (for model improvement)
    user_rating INTEGER CHECK (user_rating >= 1 AND user_rating <= 5),
    user_feedback TEXT,
    feedback_timestamp TIMESTAMPTZ,
    
    -- Indexing for fast queries
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_analysis_history_user_id ON analysis_history(user_id);
CREATE INDEX idx_analysis_history_timestamp ON analysis_history(analysis_timestamp DESC);
CREATE INDEX idx_analysis_history_model_version ON analysis_history(model_version);
CREATE INDEX idx_analysis_history_score ON analysis_history(overall_score DESC);

-- Card Placement Details Table
CREATE TABLE card_placements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID NOT NULL REFERENCES analysis_history(id) ON DELETE CASCADE,
    
    -- Placement timing
    game_time_seconds DECIMAL(6,2),
    placement_order INTEGER,
    
    -- Card details
    card_name VARCHAR(100),
    card_level INTEGER,
    elixir_cost INTEGER,
    
    -- Placement coordinates (arena grid 18x32)
    x_coordinate INTEGER CHECK (x_coordinate >= 0 AND x_coordinate <= 17),
    y_coordinate INTEGER CHECK (y_coordinate >= 0 AND y_coordinate <= 31),
    
    -- Analysis scores
    placement_score DECIMAL(5,2), -- 0-100 score for this specific placement
    optimal_x INTEGER, -- AI-recommended X coordinate
    optimal_y INTEGER, -- AI-recommended Y coordinate
    distance_from_optimal DECIMAL(6,2), -- Tiles away from optimal
    
    -- Context awareness
    enemy_units_nearby JSONB, -- Enemy units in vicinity
    friendly_units_nearby JSONB, -- Friendly units in vicinity
    tower_health JSONB, -- King/Princess tower health at time of placement
    elixir_available INTEGER,
    elixir_advantage INTEGER,
    
    -- Strategic analysis
    placement_purpose VARCHAR(100), -- attack, defend, counter, support
    effectiveness_rating DECIMAL(5,2),
    alternative_suggestions JSONB,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_card_placements_analysis_id ON card_placements(analysis_id);
CREATE INDEX idx_card_placements_card_name ON card_placements(card_name);
CREATE INDEX idx_card_placements_score ON card_placements(placement_score DESC);

-- Game Pattern Recognition Table (for ML training)
CREATE TABLE game_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Pattern identification
    pattern_type VARCHAR(100), -- opening, counter_push, defense, etc.
    pattern_name VARCHAR(200),
    frequency_score INTEGER, -- How often this pattern appears
    
    -- Pattern data
    card_sequence JSONB, -- Sequence of cards played
    timing_pattern JSONB, -- Timing between placements
    position_pattern JSONB, -- Common placement positions
    
    -- Success metrics
    win_rate DECIMAL(5,4),
    average_damage_dealt INTEGER,
    average_damage_taken INTEGER,
    elixir_efficiency DECIMAL(5,2),
    
    -- Context
    trophy_range_min INTEGER,
    trophy_range_max INTEGER,
    game_mode VARCHAR(50),
    
    -- ML metadata
    pattern_confidence DECIMAL(5,4),
    training_samples_count INTEGER,
    last_updated TIMESTAMPTZ DEFAULT NOW(),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Model Training Data Table
CREATE TABLE training_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    analysis_id UUID REFERENCES analysis_history(id),
    
    -- Feature vectors (stored as compressed binary)
    input_features BYTEA, -- Preprocessed game state features
    target_labels BYTEA, -- Optimal placement labels
    
    -- Data quality metrics
    label_confidence DECIMAL(5,4),
    data_quality_score DECIMAL(5,4),
    
    -- Training metadata
    used_in_training BOOLEAN DEFAULT FALSE,
    training_run_id VARCHAR(100),
    data_split VARCHAR(20), -- train, validation, test
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Model Performance Tracking
CREATE TABLE model_performance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Model identification
    model_version VARCHAR(50) NOT NULL,
    model_type VARCHAR(50), -- cnn, transformer, ensemble
    deployment_timestamp TIMESTAMPTZ,
    
    -- Performance metrics
    accuracy DECIMAL(6,4),
    precision_score DECIMAL(6,4),
    recall_score DECIMAL(6,4),
    f1_score DECIMAL(6,4),
    
    -- Business metrics
    user_satisfaction_avg DECIMAL(3,2),
    processing_speed_ms_avg INTEGER,
    error_rate DECIMAL(6,4),
    
    -- A/B testing results
    test_group VARCHAR(20), -- champion, challenger_a, challenger_b
    traffic_percentage DECIMAL(5,2),
    conversion_rate DECIMAL(6,4),
    
    -- Sample size
    predictions_count INTEGER,
    feedback_count INTEGER,
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- User Favorites and Collections
CREATE TABLE user_analysis_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    collection_name VARCHAR(200) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE collection_analyses (
    collection_id UUID REFERENCES user_analysis_collections(id) ON DELETE CASCADE,
    analysis_id UUID REFERENCES analysis_history(id) ON DELETE CASCADE,
    added_at TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT,
    
    PRIMARY KEY (collection_id, analysis_id)
);

-- Performance optimization
CREATE INDEX idx_training_data_analysis_id ON training_data(analysis_id);
CREATE INDEX idx_model_performance_version ON model_performance(model_version);
CREATE INDEX idx_collections_user_id ON user_analysis_collections(user_id);

-- Partitioning for large datasets (partition by month)
CREATE TABLE analysis_history_y2025m01 PARTITION OF analysis_history
    FOR VALUES FROM ('2025-01-01') TO ('2025-02-01');

CREATE TABLE analysis_history_y2025m02 PARTITION OF analysis_history
    FOR VALUES FROM ('2025-02-01') TO ('2025-03-01');

-- Add more partitions as needed...
