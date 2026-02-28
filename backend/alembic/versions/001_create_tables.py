"""create tables

Revision ID: 001
Revises:
Create Date: 2026-02-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column("sku_id", sa.Text, primary_key=True),
        sa.Column("product_name", sa.Text, nullable=False),
        sa.Column("category", sa.Text),
        sa.Column("subcategory", sa.Text),
        sa.Column("unit_size", sa.Text),
        sa.Column("base_price", sa.Numeric(10, 2)),
        sa.Column("unit_cost", sa.Numeric(10, 2)),
        sa.Column("avg_weekly_units", sa.Integer),
        sa.Column("margin_pct", sa.Numeric(6, 2)),
        sa.Column("tags", JSONB),
    )

    op.create_table(
        "promo_history",
        sa.Column("promo_id", sa.Text, primary_key=True),
        sa.Column("sku_id", sa.Text),
        sa.Column("product_name", sa.Text),
        sa.Column("category", sa.Text),
        sa.Column("discount_pct", sa.Integer),
        sa.Column("promo_price", sa.Numeric(10, 2)),
        sa.Column("start_date", sa.Date),
        sa.Column("duration_days", sa.Integer),
        sa.Column("units_sold", sa.Integer),
        sa.Column("baseline_units", sa.Integer),
        sa.Column("lift_pct", sa.Numeric(6, 2)),
        sa.Column("revenue", sa.Numeric(10, 2)),
        sa.Column("margin", sa.Numeric(10, 2)),
        sa.Column("roi", sa.Numeric(6, 2)),
        sa.Column("cannibalization_notes", sa.Text),
        sa.Column("post_promo_dip_pct", sa.Integer),
        sa.Column("outcome", sa.Text),
    )

    op.create_table(
        "elasticity",
        sa.Column("category", sa.Text, primary_key=True),
        sa.Column("price_elasticity", sa.Numeric(5, 2)),
        sa.Column("cross_elasticity_within_category", sa.Numeric(5, 2)),
        sa.Column("cross_elasticity_adjacent_categories", sa.Numeric(5, 2)),
        sa.Column("seasonality_index", JSONB),
        sa.Column("optimal_discount_min_pct", sa.Integer),
        sa.Column("optimal_discount_max_pct", sa.Integer),
        sa.Column("notes", sa.Text),
    )

    op.create_table(
        "cannibalization",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_sku_id", sa.Text),
        sa.Column("affected_sku_id", sa.Text),
        sa.Column("impact_pct", sa.Integer),
        sa.Column("relationship", sa.Text),
        sa.Column("impact_type", sa.Text),
    )


def downgrade() -> None:
    op.drop_table("cannibalization")
    op.drop_table("elasticity")
    op.drop_table("promo_history")
    op.drop_table("products")
