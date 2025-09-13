from feast import Entity, FeatureService, FeatureView, Field, FileSource, PushSource, RequestSource
from feast.types import Float32, Int64, String, UnixTimestamp
from feast.value_type import ValueType
from datetime import timedelta

# Entities
user = Entity(
    name="user_id",
    description="User identifier",
    value_type=ValueType.STRING,
)

game_match = Entity(
    name="match_id", 
    description="Game match identifier",
    value_type=ValueType.STRING,
)

# Data Sources
game_data_source = FileSource(
    name="game_data_source",
    path="data/game_events.parquet",
    timestamp_field="event_timestamp",
)

user_stats_source = FileSource(
    name="user_stats_source", 
    path="data/user_stats.parquet",
    timestamp_field="event_timestamp",
)

# Real-time features from Redis
realtime_source = PushSource(
    name="realtime_game_features",
    batch_source=game_data_source,
)

# Feature Views
game_context_features = FeatureView(
    name="game_context_features",
    entities=[game_match],
    ttl=timedelta(hours=24),
    schema=[
        Field(name="game_mode", dtype=String),
        Field(name="player_trophies", dtype=Int64),
        Field(name="opponent_trophies", dtype=Int64),
        Field(name="elixir_advantage", dtype=Float32),
        Field(name="king_tower_hp", dtype=Int64),
        Field(name="princess_tower_left_hp", dtype=Int64),
        Field(name="princess_tower_right_hp", dtype=Int64),
        Field(name="current_elixir", dtype=Int64),
        Field(name="time_remaining", dtype=Float32),
    ],
    source=game_data_source,
)

user_performance_features = FeatureView(
    name="user_performance_features",
    entities=[user],
    ttl=timedelta(days=30),
    schema=[
        Field(name="avg_placement_score", dtype=Float32),
        Field(name="total_analyses", dtype=Int64),
        Field(name="favorite_cards", dtype=String),
        Field(name="skill_level", dtype=String),
        Field(name="preferred_placements", dtype=String),
        Field(name="win_rate", dtype=Float32),
        Field(name="avg_elixir_efficiency", dtype=Float32),
        Field(name="last_30_day_improvement", dtype=Float32),
    ],
    source=user_stats_source,
)

card_effectiveness_features = FeatureView(
    name="card_effectiveness_features",
    entities=[game_match],
    ttl=timedelta(hours=12),
    schema=[
        Field(name="card_synergy_score", dtype=Float32),
        Field(name="counter_card_present", dtype=Int64),
        Field(name="placement_density", dtype=Float32),
        Field(name="expected_damage", dtype=Float32),
        Field(name="survival_probability", dtype=Float32),
        Field(name="meta_strength", dtype=Float32),
    ],
    source=game_data_source,
)

# Real-time features
realtime_game_features = FeatureView(
    name="realtime_game_features",
    entities=[game_match],
    ttl=timedelta(minutes=30),
    schema=[
        Field(name="current_board_state", dtype=String),
        Field(name="enemy_cards_on_field", dtype=String),
        Field(name="friendly_cards_on_field", dtype=String),
        Field(name="immediate_threats", dtype=String),
        Field(name="optimal_response_cards", dtype=String),
    ],
    source=realtime_source,
)

# Feature Services (for model serving)
clash_royale_prediction_service = FeatureService(
    name="clash_royale_prediction_v1",
    features=[
        game_context_features,
        user_performance_features,
        card_effectiveness_features,
        realtime_game_features,
    ],
)

# Historical analysis features for training
historical_analysis_service = FeatureService(
    name="historical_analysis_v1",
    features=[
        game_context_features,
        user_performance_features,
        card_effectiveness_features,
    ],
)
