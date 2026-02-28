from sqlalchemy import Column, Text, Numeric, Integer, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    sku_id = Column(Text, primary_key=True)
    product_name = Column(Text, nullable=False)
    category = Column(Text)
    subcategory = Column(Text)
    unit_size = Column(Text)
    base_price = Column(Numeric(10, 2))
    unit_cost = Column(Numeric(10, 2))
    avg_weekly_units = Column(Integer)
    margin_pct = Column(Numeric(6, 2))
    tags = Column(JSONB)


class PromoHistory(Base):
    __tablename__ = "promo_history"

    promo_id = Column(Text, primary_key=True)
    sku_id = Column(Text)
    product_name = Column(Text)
    category = Column(Text)
    discount_pct = Column(Integer)
    promo_price = Column(Numeric(10, 2))
    start_date = Column(Date)
    duration_days = Column(Integer)
    units_sold = Column(Integer)
    baseline_units = Column(Integer)
    lift_pct = Column(Numeric(6, 2))
    revenue = Column(Numeric(10, 2))
    margin = Column(Numeric(10, 2))
    roi = Column(Numeric(6, 2))
    cannibalization_notes = Column(Text)
    post_promo_dip_pct = Column(Integer)
    outcome = Column(Text)


class Elasticity(Base):
    __tablename__ = "elasticity"

    category = Column(Text, primary_key=True)
    price_elasticity = Column(Numeric(5, 2))
    cross_elasticity_within_category = Column(Numeric(5, 2))
    cross_elasticity_adjacent_categories = Column(Numeric(5, 2))
    seasonality_index = Column(JSONB)
    optimal_discount_min_pct = Column(Integer)
    optimal_discount_max_pct = Column(Integer)
    notes = Column(Text)


class Cannibalization(Base):
    __tablename__ = "cannibalization"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_sku_id = Column(Text)
    affected_sku_id = Column(Text)
    impact_pct = Column(Integer)
    relationship = Column(Text)
    impact_type = Column(Text)  # 'primary' or 'secondary'
