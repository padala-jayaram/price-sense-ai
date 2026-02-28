import json
from pathlib import Path
from typing import Optional

_catalog: Optional[dict] = None
_promo_history: Optional[dict] = None
_elasticity: Optional[dict] = None
_cannibalization: Optional[dict] = None
_initialized: bool = False

DATA_DIR = Path(__file__).parent.parent / "data"


def init():
    global _catalog, _promo_history, _elasticity, _cannibalization, _initialized
    if _initialized:
        return

    with open(DATA_DIR / "products.json", "r") as f:
        _catalog = json.load(f)
    with open(DATA_DIR / "promo_history.json", "r") as f:
        _promo_history = json.load(f)
    with open(DATA_DIR / "elasticity.json", "r") as f:
        _elasticity = json.load(f)
    with open(DATA_DIR / "cannibalization.json", "r") as f:
        _cannibalization = json.load(f)

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
    for cat, data in _elasticity.items():
        lines.append(f"{cat.replace('_', ' ').title()}: elasticity {data['price_elasticity']}, optimal discount {data['optimal_discount_range']['min']}%-{data['optimal_discount_range']['max']}%")
    lines.append("")

    lines.append("== RECENT PROMO HISTORY ==\n")
    for promo in _promo_history.get("promotions", []):
        lines.append(f"  - {promo['product_name']}: {promo['discount_pct']}% off, lift {promo['actual_lift_pct']}%, ROI {promo['roi']}, outcome: {promo['outcome']}")

    _general_summary = "\n".join(lines)
    return _general_summary
