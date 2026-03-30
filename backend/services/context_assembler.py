from typing import Optional


def assemble_context(
    product_data: dict,
    promo_history: Optional[dict],
    elasticity: Optional[dict],
    cannibalization: Optional[dict],
    discount_pct: Optional[float] = None,
    timing: Optional[str] = None,
) -> str:
    """Build a focused ~400 token context string from retrieved data."""
    target = product_data.get("target")
    if not target:
        return (
            "== NO PRODUCT MATCH ==\n"
            "Could not identify the target product from the user's message. "
            "Ask the user to clarify which product they are asking about."
        )

    sections = []

    # Section 1: Target Product
    promo_price = None
    margin_at_promo = None
    if discount_pct:
        promo_price = round(target["base_price"] * (1 - discount_pct / 100), 2)
        margin_at_promo = round(promo_price - target["unit_cost"], 2)

    target_section = f"""== TARGET PRODUCT ==
Name: {target['product_name']}
SKU: {target['sku_id']}
Category: {target['category']}
Base Price: ${target['base_price']:.2f}
Unit Cost: ${target['unit_cost']:.2f}
Current Margin: {target['margin_pct']:.1f}% (${target['base_price'] - target['unit_cost']:.2f}/unit)
Avg Weekly Units: {target['avg_weekly_units']}"""

    if discount_pct:
        target_section += f"\nProposed Discount: {discount_pct}%"
        target_section += f"\nPromo Price: ${promo_price:.2f}"
        target_section += f"\nMargin at Promo Price: ${margin_at_promo:.2f}/unit ({margin_at_promo / promo_price * 100:.1f}%)"
    else:
        target_section += "\nProposed Discount: Not specified"

    if timing:
        target_section += f"\nTiming: {timing}"

    sections.append(target_section)

    # Section 2: Sibling SKUs
    siblings = product_data.get("siblings", [])
    if siblings:
        lines = [
            f"  - {s['product_name']} | ${s['base_price']:.2f} | {s['avg_weekly_units']} units/wk"
            for s in siblings
        ]
        sections.append(f"== SAME-CATEGORY PRODUCTS (cannibalization risk) ==\n" + "\n".join(lines))

    # Section 3: Cannibalization Map
    if cannibalization:
        canib_lines = []
        for s in cannibalization.get("primary_siblings", []):
            canib_lines.append(f"  - {s['sku_id']}: ~{s['impact_pct']}% drop ({s['relationship']})")
        for s in cannibalization.get("secondary_affected", []):
            canib_lines.append(f"  - {s['sku_id']}: ~{s['impact_pct']}% drop ({s['relationship']})")
        if canib_lines:
            sections.append("== EXPECTED CANNIBALIZATION ==\n" + "\n".join(canib_lines))

    # Section 4: Promo History for this SKU
    if promo_history and promo_history.get("sku_promos"):
        lines = []
        for p in promo_history["sku_promos"]:
            lines.append(
                f"  - {p['discount_pct']}% off ({p['start_date']}, {p['duration_days']}d): "
                f"lift={p['lift_pct']:.0f}%, ROI={p['roi']:.2f}, "
                f"outcome={p['outcome']}, post-dip={p['post_promo_dip_pct']}%"
            )
        sections.append("== PROMO HISTORY (this product) ==\n" + "\n".join(lines))

    # Section 5: Category Promo History
    if promo_history and promo_history.get("category_promos"):
        lines = []
        for p in promo_history["category_promos"]:
            lines.append(
                f"  - {p['product_name']} {p['discount_pct']}% off ({p['start_date']}): "
                f"lift={p['lift_pct']:.0f}%, cannib: {p['cannibalization_notes']}"
            )
        sections.append("== CATEGORY PROMO HISTORY ==\n" + "\n".join(lines))

    # Section 6: Elasticity
    if elasticity:
        seasonality = elasticity.get("seasonality_index", {}) or {}
    
        q1 = seasonality.get("Q1", "N/A")
        q2 = seasonality.get("Q2", "N/A")
        q3 = seasonality.get("Q3", "N/A")
        q4 = seasonality.get("Q4", "N/A")
    
        min_disc = elasticity.get("optimal_discount_min_pct", "N/A")
        max_disc = elasticity.get("optimal_discount_max_pct", "N/A")
    
        sections.append(
            f"== PRICE ELASTICITY ({elasticity.get('category', 'N/A')}) ==\n"
            f"Price Elasticity: {elasticity.get('price_elasticity', 'N/A')}\n"
            f"Within-Category Cross-Elasticity: {elasticity.get('cross_elasticity_within_category', 'N/A')}\n"
            f"Adjacent-Category Cross-Elasticity: {elasticity.get('cross_elasticity_adjacent_categories', 'N/A')}\n"
            f"Seasonality: Q1={q1}, Q2={q2}, Q3={q3}, Q4={q4}\n"
            f"Optimal Discount Range: {min_disc}-{max_disc}%\n"
            f"Notes: {elasticity.get('notes', 'N/A')}"
        )

    return "\n\n".join(sections)
