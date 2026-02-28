from typing import Optional
from services.data_loader import get_catalog, get_promo_history, get_elasticity, get_cannibalization


def retrieve_product_and_siblings(sku_id: str) -> dict:
    """Return target product and sibling SKUs in the same category."""
    catalog = get_catalog()
    target = None
    siblings = []

    for sku in catalog["skus"]:
        if sku["sku_id"] == sku_id:
            target = sku

    if not target:
        return {"target": None, "siblings": []}

    for sku in catalog["skus"]:
        if sku["category"] == target["category"] and sku["sku_id"] != sku_id:
            siblings.append(sku)

    return {"target": target, "siblings": siblings}


def retrieve_promo_history(sku_id: str, category: str, limit: int = 5) -> dict:
    """Return recent promotions for the SKU and its category."""
    history = get_promo_history()
    promos = history["promotions"]

    sku_promos = sorted(
        [p for p in promos if p["sku_id"] == sku_id],
        key=lambda x: x["start_date"],
        reverse=True,
    )[:limit]

    category_promos = sorted(
        [p for p in promos if p["category"] == category and p["sku_id"] != sku_id],
        key=lambda x: x["start_date"],
        reverse=True,
    )[:limit]

    return {"sku_promos": sku_promos, "category_promos": category_promos}


def retrieve_elasticity(category: str) -> Optional[dict]:
    """Return elasticity data for the given category."""
    data = get_elasticity()
    for entry in data["elasticity"]:
        if entry["category"] == category:
            return entry
    return None


def retrieve_cannibalization(sku_id: str) -> Optional[dict]:
    """Return cannibalization mapping for the given SKU."""
    data = get_cannibalization()
    return data["cannibalization_map"].get(sku_id)
