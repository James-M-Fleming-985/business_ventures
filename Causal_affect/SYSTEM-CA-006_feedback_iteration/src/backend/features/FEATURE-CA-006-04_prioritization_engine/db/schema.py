"""Database schema for prioritization engine."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

import enum

Base = declarative_base()


class SegmentType(str, enum.Enum):
    DEMOGRAPHIC = "demographic"
    BEHAVIORAL = "behavioral"
    VALUE_BASED = "value_based"
    LIFECYCLE = "lifecycle"
    CUSTOM = "custom"


class RuleType(str, enum.Enum):
    SCORING = "scoring"
    FILTERING = "filtering"
    BOOSTING = "boosting"
    EXCLUSION = "exclusion"


class ConditionOperator(str, enum.Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"


class ProductStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"
    COMING_SOON = "coming_soon"


class InteractionType(str, enum.Enum):
    VIEW = "view"
    CLICK = "click"
    PURCHASE = "purchase"
    ADD_TO_CART = "add_to_cart"
    WISHLIST = "wishlist"
    REVIEW = "review"
    INQUIRY = "inquiry"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    external_id = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(255), index=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Customer attributes for segmentation
    age = Column(Integer)
    gender = Column(String(20))
    location_country = Column(String(100))
    location_city = Column(String(100))
    lifetime_value = Column(Numeric(12, 2), default=0)
    total_purchases = Column(Integer, default=0)
    average_order_value = Column(Numeric(12, 2), default=0)
    last_purchase_date = Column(DateTime)
    registration_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    custom_attributes = Column(JSON, default=dict)
    
    # Relationships
    segments = relationship("SegmentAssignment", back_populates="customer", cascade="all, delete-orphan")
    interactions = relationship("CustomerProductInteraction", back_populates="customer", cascade="all, delete-orphan")
    histories = relationship("PrioritizationHistory", back_populates="customer", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_customer_activity', 'is_active', 'updated_at'),
        Index('idx_customer_location', 'location_country', 'location_city'),
    )


class CustomerSegment(Base):
    __tablename__ = "customer_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    segment_type = Column(Enum(SegmentType), nullable=False)
    criteria = Column(JSON, nullable=False)  # Stores segment definition criteria
    priority_weight = Column(Float, default=1.0)  # Weight for prioritization
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Statistics
    member_count = Column(Integer, default=0)
    last_calculated = Column(DateTime)
    
    # Relationships
    assignments = relationship("SegmentAssignment", back_populates="segment", cascade="all, delete-orphan")
    rules = relationship("PrioritizationRule", back_populates="segment")


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    external_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), index=True)
    subcategory = Column(String(100))
    brand = Column(String(100), index=True)
    price = Column(Numeric(12, 2), nullable=False)
    status = Column(Enum(ProductStatus), default=ProductStatus.ACTIVE, nullable=False)
    
    # Product attributes for scoring
    popularity_score = Column(Float, default=0.0)
    margin_percentage = Column(Float)
    inventory_level = Column(Integer)
    launch_date = Column(DateTime)
    is_featured = Column(Boolean, default=False)
    is_promotional = Column(Boolean, default=False)
    custom_attributes = Column(JSON, default=dict)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    scores = relationship("ProductScore", back_populates="product", cascade="all, delete-orphan")
    interactions = relationship("CustomerProductInteraction", back_populates="product", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_product_category', 'category', 'subcategory'),
        Index('idx_product_status', 'status', 'is_featured'),
    )


class ProductScore(Base):
    __tablename__ = "product_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("customer_segments.id"), nullable=False)
    
    # Scoring components
    base_score = Column(Float, nullable=False, default=0.0)
    popularity_component = Column(Float, default=0.0)
    margin_component = Column(Float, default=0.0)
    inventory_component = Column(Float, default=0.0)
    personalization_component = Column(Float, default=0.0)
    rule_adjustments = Column(JSON, default=list)  # List of rule-based adjustments
    
    # Final calculated score
    final_score = Column(Float, nullable=False, index=True)
    
    calculated_at = Column(DateTime, default=func.now(), nullable=False)
    expires_at = Column(DateTime)  # When this score should be recalculated
    
    # Relationships
    product = relationship("Product", back_populates="scores")
    segment = relationship("CustomerSegment")
    
    __table_args__ = (
        UniqueConstraint('product_id', 'segment_id', name='uq_product_segment_score'),
        Index('idx_score_segment_final', 'segment_id', 'final_score'),
        Index('idx_score_expiry', 'expires_at'),
    )


class PrioritizationRule(Base):
    __tablename__ = "prioritization_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    rule_type = Column(Enum(RuleType), nullable=False)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("customer_segments.id"))
    
    # Rule configuration
    priority = Column(Integer, default=0)  # Higher priority rules execute first
    weight = Column(Float, default=1.0)  # Impact factor
    conditions = Column(JSON, nullable=False)  # Rule conditions
    actions = Column(JSON, nullable=False)  # What the rule does
    
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    segment = relationship("CustomerSegment", back_populates="rules")
    conditions_rel = relationship("RuleCondition", back_populates="rule", cascade="all, delete-orphan")
    executions = relationship("RuleExecution", back_populates="rule", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_rule_active_priority', 'is_active', 'priority'),
        Index('idx_rule_validity', 'valid_from', 'valid_until'),
    )


class RuleCondition(Base):
    __tablename__ = "rule_conditions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("prioritization_rules.id"), nullable=False)
    
    field_name = Column(String(100), nullable=False)  # e.g., 'product.category', 'customer.age'
    operator = Column(Enum(ConditionOperator), nullable=False)
    value = Column(JSON, nullable=False)  # Flexible value storage
    
    # Logic grouping
    group_id = Column(String(50))  # For grouping AND/OR conditions
    is_negated = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    # Relationships
    rule = relationship("PrioritizationRule", back_populates="conditions_rel")


class PrioritizationHistory(Base):
    __tablename__ = "prioritization_histories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    session_id = Column(String(100), index=True)
    
    request_context = Column(JSON)  # Store request parameters
    segment_ids = Column(JSON)  # Segments customer belonged to
    rules_applied = Column(JSON)  # Rules that were applied
    
    execution_time_ms = Column(Integer)  # Performance tracking
    item_count = Column(Integer)
    
    created_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="histories")
    items = relationship("HistoryItem", back_populates="history", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index('idx_history_customer_date', 'customer_id', 'created_at'),
    )


class HistoryItem(Base):
    __tablename__ = "history_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    history_id = Column(UUID(as_uuid=True), ForeignKey("prioritization_histories.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    position = Column(Integer, nullable=False)  # Final position in list
    score = Column(Float, nullable=False)  # Final score
    score_components = Column(JSON)  # Breakdown of score calculation
    
    # Relationships
    history = relationship("PrioritizationHistory", back_populates="items")
    product = relationship("Product")
    
    __table_args__ = (
        Index('idx_history_item_position', 'history_id', 'position'),
    )


class CustomerProductInteraction(Base):
    __tablename__ = "customer_product_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    
    interaction_type = Column(Enum(InteractionType), nullable=False)
    interaction_value = Column(Float)  # e.g., rating, quantity
    interaction_metadata = Column(JSON)  # Additional context
    
    occurred_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relationships
    customer = relationship("Customer", back_populates="interactions")
    product = relationship("Product", back_populates="interactions")
    
    __table_args__ = (
        Index('idx_interaction_customer_product', 'customer_id', 'product_id'),
        Index('idx_interaction_type_date', 'interaction_type', 'occurred_at'),
    )


class SegmentAssignment(Base):
    __tablename__ = "segment_assignments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id"), nullable=False)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("customer_segments.id"), nullable=False)
    
    assigned_at = Column(DateTime, default=func.now(), nullable=False)
    confidence_score = Column(Float, default=1.0)  # How well customer fits segment
    expires_at = Column(DateTime)  # When to re-evaluate
    
    # Relationships
    customer = relationship("Customer", back_populates="segments")
    segment = relationship("CustomerSegment", back_populates="assignments")
    
    __table_args__ = (
        UniqueConstraint('customer_id', 'segment_id', name='uq_customer_segment_assignment'),
        Index('idx_assignment_segment', 'segment_id'),
        Index('idx_assignment_expiry', 'expires_at'),
    )


class RuleExecution(Base):
    __tablename__ = "rule_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("prioritization_rules.id"), nullable=False)
    
    execution_context = Column(JSON)  # Context when rule was executed
    affected_products = Column(Integer)  # Number of products affected
    execution_time_ms = Column(Integer)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text)
    
    executed_at = Column(DateTime, default=func.now(), nullable=False, index=True)
    
    # Relationships
    rule = relationship("PrioritizationRule", back_populates="executions")


class AnalyticsSnapshot(Base):
    __tablename__ = "analytics_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    snapshot_type = Column(String(50), nullable=False)  # e.g., 'daily', 'hourly'
    
    # Aggregate metrics
    total_prioritizations = Column(Integer, default=0)
    unique_customers = Column(Integer, default=0)
    average_execution_time_ms = Column(Float)
    
    # Performance metrics
    cache_hit_rate = Column(Float)
    rule_execution_count = Column(Integer, default=0)
    failed_requests = Column(Integer, default=0)
    
    # Business metrics
    top_segments = Column(JSON)  # Segment usage statistics
    top_products = Column(JSON)  # Most prioritized products
    rule_effectiveness = Column(JSON)  # Rule impact analysis
    
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('idx_snapshot_period', 'snapshot_type', 'period_start', 'period_end'),
    )