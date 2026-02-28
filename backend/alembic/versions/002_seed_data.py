"""seed data from JSON files

Revision ID: 002
Revises: 001
Create Date: 2026-02-28
"""
from typing import Sequence, Union
from pathlib import Path
import json

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def _load(filename: str) -> dict:
    with open(DATA_DIR / filename) as f:
        return json.load(f)


def upgrade() -> None:
    raw_products = _load("products.json")
    raw_promos = _load("promo_history.json")
    raw_elasticity = _load("elasticity.json")
    raw_cannibalization = _load("cannibalization.json")

    # ── products ──────────────────────────────────────────────────────────────
    products_table = sa.table(
        "products",
        sa.column("sku_id", sa.Text),
        sa.column("product_name", sa.Text),
        sa.column("category", sa.Text),
        sa.column("subcategory", sa.Text),
        sa.column("unit_size", sa.Text),
        sa.column("base_price", sa.Numeric),
        sa.column("unit_cost", sa.Numeric),
        sa.column("avg_weekly_units", sa.Integer),
        sa.column("margin_pct", sa.Numeric),
        sa.column("tags", JSONB),
    )
    op.bulk_insert(
        products_table,
        [
            {
                "sku_id": s["sku_id"],
                "product_name": s["product_name"],
                "category": s["category"],
                "subcategory": s.get("subcategory"),
                "unit_size": s.get("unit_size"),
                "base_price": s["base_price"],
                "unit_cost": s["unit_cost"],
                "avg_weekly_units": s["avg_weekly_units"],
                "margin_pct": s["margin_pct"],
                "tags": s.get("tags", []),
            }
            for s in raw_products["skus"]
        ],
    )

    # ── promo_history ─────────────────────────────────────────────────────────
    promo_table = sa.table(
        "promo_history",
        sa.column("promo_id", sa.Text),
        sa.column("sku_id", sa.Text),
        sa.column("product_name", sa.Text),
        sa.column("category", sa.Text),
        sa.column("discount_pct", sa.Integer),
        sa.column("promo_price", sa.Numeric),
        sa.column("start_date", sa.Date),
        sa.column("duration_days", sa.Integer),
        sa.column("units_sold", sa.Integer),
        sa.column("baseline_units", sa.Integer),
        sa.column("lift_pct", sa.Numeric),
        sa.column("revenue", sa.Numeric),
        sa.column("margin", sa.Numeric),
        sa.column("roi", sa.Numeric),
        sa.column("cannibalization_notes", sa.Text),
        sa.column("post_promo_dip_pct", sa.Integer),
        sa.column("outcome", sa.Text),
    )
    op.bulk_insert(
        promo_table,
        [
            {
                "promo_id": p["promo_id"],
                "sku_id": p["sku_id"],
                "product_name": p["product_name"],
                "category": p["category"],
                "discount_pct": p["discount_pct"],
                "promo_price": p["promo_price"],
                "start_date": p["start_date"],
                "duration_days": p["duration_days"],
                "units_sold": p["units_sold"],
                "baseline_units": p["baseline_units"],
                "lift_pct": p["lift_pct"],
                "revenue": p["revenue"],
                "margin": p["margin"],
                "roi": p["roi"],
                "cannibalization_notes": p.get("cannibalization_notes"),
                "post_promo_dip_pct": p.get("post_promo_dip_pct"),
                "outcome": p.get("outcome"),
            }
            for p in raw_promos["promotions"]
        ],
    )

    # ── elasticity ────────────────────────────────────────────────────────────
    elasticity_table = sa.table(
        "elasticity",
        sa.column("category", sa.Text),
        sa.column("price_elasticity", sa.Numeric),
        sa.column("cross_elasticity_within_category", sa.Numeric),
        sa.column("cross_elasticity_adjacent_categories", sa.Numeric),
        sa.column("seasonality_index", JSONB),
        sa.column("optimal_discount_min_pct", sa.Integer),
        sa.column("optimal_discount_max_pct", sa.Integer),
        sa.column("notes", sa.Text),
    )
    op.bulk_insert(
        elasticity_table,
        [
            {
                "category": e["category"],
                "price_elasticity": e["price_elasticity"],
                "cross_elasticity_within_category": e["cross_elasticity_within_category"],
                "cross_elasticity_adjacent_categories": e["cross_elasticity_adjacent_categories"],
                "seasonality_index": e["seasonality_index"],
                "optimal_discount_min_pct": e["optimal_discount_range_pct"][0],
                "optimal_discount_max_pct": e["optimal_discount_range_pct"][1],
                "notes": e.get("notes"),
            }
            for e in raw_elasticity["elasticity"]
        ],
    )

    # ── cannibalization ───────────────────────────────────────────────────────
    cann_table = sa.table(
        "cannibalization",
        sa.column("source_sku_id", sa.Text),
        sa.column("affected_sku_id", sa.Text),
        sa.column("impact_pct", sa.Integer),
        sa.column("relationship", sa.Text),
        sa.column("impact_type", sa.Text),
    )
    rows = []
    for source_sku, data in raw_cannibalization["cannibalization_map"].items():
        for sibling in data.get("primary_siblings", []):
            rows.append({
                "source_sku_id": source_sku,
                "affected_sku_id": sibling["sku_id"],
                "impact_pct": sibling["impact_pct"],
                "relationship": sibling["relationship"],
                "impact_type": "primary",
            })
        for sibling in data.get("secondary_affected", []):
            rows.append({
                "source_sku_id": source_sku,
                "affected_sku_id": sibling["sku_id"],
                "impact_pct": sibling["impact_pct"],
                "relationship": sibling["relationship"],
                "impact_type": "secondary",
            })
    op.bulk_insert(cann_table, rows)


def downgrade() -> None:
    op.execute("DELETE FROM cannibalization")
    op.execute("DELETE FROM elasticity")
    op.execute("DELETE FROM promo_history")
    op.execute("DELETE FROM products")
