import json
import os
from pathlib import Path
from typing import Optional

_catalog: Optional[dict] = None
_promo_history: Optional[dict] = None
_elasticity: Optional[dict] = None
_cannibalization: Optional[dict] = None
_initialized: bool = False

DATA_DIR = Path(__file__).parent.parent / "data"


def _load_from_db():
    """Load all data from PostgreSQL via SQLAlchemy ORM."""
    from services.database import get_session
    from models import Product, PromoHistory, Elasticity, Cannibalization

    session = get_session()
    try:
        # products → {"skus": [...]}
        products = session.query(Product).all()
        skus = [
            {
                "sku_id": p.sku_id,
                "product_name": p.product_name,
                "category": p.category,
                "subcategory": p.subcategory,
                "unit_size": p.unit_size,
                "base_price": float(p.base_price) if p.base_price is not None else None,
                "unit_cost": float(p.unit_cost) if p.unit_cost is not None else None,
                "avg_weekly_units": p.avg_weekly_units,
                "margin_pct": float(p.margin_pct) if p.margin_pct is not None else None,
                "tags": p.tags or [],
            }
            for p in products
        ]

        # promo_history → {"promotions": [...]}
        promos = session.query(PromoHistory).all()
        promotions = [
            {
                "promo_id": p.promo_id,
                "sku_id": p.sku_id,
                "product_name": p.product_name,
                "category": p.category,
                "discount_pct": p.discount_pct,
                "promo_price": float(p.promo_price) if p.promo_price is not None else None,
                "start_date": p.start_date.isoformat() if p.start_date else None,
                "duration_days": p.duration_days,
                "units_sold": p.units_sold,
                "baseline_units": p.baseline_units,
                "lift_pct": float(p.lift_pct) if p.lift_pct is not None else None,
                "revenue": float(p.revenue) if p.revenue is not None else None,
                "margin": float(p.margin) if p.margin is not None else None,
                "roi": float(p.roi) if p.roi is not None else None,
                "cannibalization_notes": p.cannibalization_notes,
                "post_promo_dip_pct": p.post_promo_dip_pct,
                "outcome": p.outcome,
            }
            for p in promos
        ]

        # elasticity → {"elasticity": [...]}
        elasticity_rows = session.query(Elasticity).all()
        elasticity_list = [
            {
                "category": e.category,
                "price_elasticity": float(e.price_elasticity) if e.price_elasticity is not None else None,
                "cross_elasticity_within_category": float(e.cross_elasticity_within_category) if e.cross_elasticity_within_category is not None else None,
                "cross_elasticity_adjacent_categories": float(e.cross_elasticity_adjacent_categories) if e.cross_elasticity_adjacent_categories is not None else None,
                "seasonality_index": e.seasonality_index or {},
                "optimal_discount_range_pct": [e.optimal_discount_min_pct, e.optimal_discount_max_pct],
                "notes": e.notes,
            }
            for e in elasticity_rows
        ]

        # cannibalization → {"cannibalization_map": {"SKU": {"primary_siblings": [...], "secondary_affected": [...]}}}
        cann_rows = session.query(Cannibalization).all()
        cann_map: dict = {}
        for row in cann_rows:
            if row.source_sku_id not in cann_map:
                cann_map[row.source_sku_id] = {"primary_siblings": [], "secondary_affected": []}
            entry = {"sku_id": row.affected_sku_id, "impact_pct": row.impact_pct, "relationship": row.relationship}
            if row.impact_type == "primary":
                cann_map[row.source_sku_id]["primary_siblings"].append(entry)
            else:
                cann_map[row.source_sku_id]["secondary_affected"].append(entry)

        return (
            {"skus": skus},
            {"promotions": promotions},
            {"elasticity": elasticity_list},
            {"cannibalization_map": cann_map},
        )
    finally:
        session.close()


def _load_from_json():
    """Load all data from local JSON files (fallback for local dev)."""
    with open(DATA_DIR / "products.json", "r") as f:
        catalog = json.load(f)
    with open(DATA_DIR / "promo_history.json", "r") as f:
        promo_history = json.load(f)
    with open(DATA_DIR / "elasticity.json", "r") as f:
        elasticity = json.load(f)
    with open(DATA_DIR / "cannibalization.json", "r") as f:
        cannibalization = json.load(f)
    return catalog, promo_history, elasticity, cannibalization


def init():
    global _catalog, _promo_history, _elasticity, _cannibalization, _initialized
    if _initialized:
        return

    if os.getenv("DATABASE_URL"):
        _catalog, _promo_history, _elasticity, _cannibalization = _load_from_db()
    else:
        _catalog, _promo_history, _elasticity, _cannibalization = _load_from_json()

    _initialized = True


def get_catalog() -> dict:
    if not _initialized:
        init()
    return _catalog


def get_promo_history() -> dict:
    if not _initialized:
        init()
    return _promo_history


def get_elasticity() -> dict:
    if not _initialized:
        init()
    return _elasticity


def get_cannibalization() -> dict:
    if not _initialized:
        init()
    return _cannibalization


_general_summary: Optional[str] = None


def get_general_catalog_summary() -> str:
    """Build a general summary of all products, categories, and promo history for chat without analysis."""
    global _general_summary
    if _general_summary:
        return _general_summary

    if not _initialized:
        init()

    lines = ["== PRODUCT CATALOG ==\n"]
    categories = {}
    for sku in _catalog["skus"]:
        cat = sku["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(sku)

    for cat, skus in categories.items():
        lines.append(f"Category: {cat.replace('_', ' ').title()} ({len(skus)} products)")
        for s in skus:
            lines.append(f"  - {s['product_name']} ({s['unit_size']}) | ${s['base_price']} | margin {s['margin_pct']}% | ~{s['avg_weekly_units']} units/week")
        lines.append("")

    lines.append("== ELASTICITY DATA ==\n")
    for e in _elasticity.get("elasticity", []):
        discount_range = e.get("optimal_discount_range_pct", [])
        min_d = discount_range[0] if len(discount_range) > 0 else "?"
        max_d = discount_range[1] if len(discount_range) > 1 else "?"
        lines.append(f"{e['category'].replace('_', ' ').title()}: elasticity {e['price_elasticity']}, optimal discount {min_d}%-{max_d}%")
    lines.append("")

    lines.append("== RECENT PROMO HISTORY ==\n")
    for promo in _promo_history.get("promotions", []):
        lines.append(f"  - {promo['product_name']}: {promo['discount_pct']}% off, lift {promo.get('lift_pct', promo.get('actual_lift_pct', '?'))}%, ROI {promo['roi']}, outcome: {promo['outcome']}")

    _general_summary = "\n".join(lines)
    return _general_summary
