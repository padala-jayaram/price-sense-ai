import re
from typing import Optional
from pydantic import BaseModel, Field
from rapidfuzz import fuzz, process
from services.data_loader import get_catalog


class ProductMatch(BaseModel):
    sku_id: str
    product_name: str
    category: str
    confidence: float


class ParsedQuery(BaseModel):
    product_hint: str = ""
    discount_pct: Optional[float] = None
    timing: Optional[str] = None
    duration_days: Optional[int] = None
    intent: str = "evaluate_promotion"
    original_message: str = ""


def match_product(text: str) -> Optional[ProductMatch]:
    """Fuzzy match user text against product catalog names."""
    catalog = get_catalog()
    choices = {sku["product_name"]: sku for sku in catalog["skus"]}

    result = process.extractOne(
        text,
        choices.keys(),
        scorer=fuzz.token_sort_ratio,
        score_cutoff=40,
    )

    if not result:
        return None

    matched_name, score, _ = result
    sku = choices[matched_name]

    return ProductMatch(
        sku_id=sku["sku_id"],
        product_name=sku["product_name"],
        category=sku["category"],
        confidence=score / 100.0,
    )


def parse_chat_message(message: str) -> ParsedQuery:
    """Parse a free-text chat message into structured query fields."""
    msg_lower = message.strip().lower()

    # Extract discount percentage
    discount_match = re.search(r"(\d{1,2})\s*%\s*(?:off|discount)?", msg_lower)
    discount_pct = float(discount_match.group(1)) if discount_match else None

    # Extract timing
    timing = None
    timing_patterns = [
        r"(next\s+week)", r"(this\s+week)", r"(next\s+month)",
        r"(holiday\s+season)", r"(q[1-4])", r"(black\s+friday)",
        r"(christmas)", r"(thanksgiving)", r"(summer)",
        r"(winter)", r"(spring)", r"(fall)",
    ]
    for pattern in timing_patterns:
        m = re.search(pattern, msg_lower)
        if m:
            timing = m.group(1)
            break

    # Extract duration
    duration_days = None
    dur_match = re.search(r"(\d+)\s*(?:day|week)s?", msg_lower)
    if dur_match:
        val = int(dur_match.group(1))
        duration_days = val * 7 if "week" in dur_match.group(0) else val

    # Determine intent
    intent = "evaluate_promotion"
    if any(g in msg_lower for g in ["hi", "hello", "hey", "help"]):
        if len(msg_lower.split()) <= 3:
            intent = "greeting"
    if any(w in msg_lower for w in ["compare", "versus", "vs", "or"]):
        intent = "compare_options"

    # Extract product hint by stripping noise words
    product_hint = _extract_product_hint(message)

    return ParsedQuery(
        product_hint=product_hint,
        discount_pct=discount_pct,
        timing=timing,
        duration_days=duration_days,
        intent=intent,
        original_message=message,
    )


def _extract_product_hint(message: str) -> str:
    noise_words = {
        "should", "i", "we", "run", "do", "a", "an", "the",
        "off", "on", "for", "next", "this", "week", "month",
        "promo", "promotion", "discount", "sale", "deal",
        "what", "how", "about", "would", "could", "if",
        "think", "recommend", "suggest", "good", "idea",
        "percent", "is", "it", "to", "at", "my",
    }
    tokens = re.sub(r"[^\w\s]", "", message).split()
    tokens = [t for t in tokens if t.lower() not in noise_words and not t.isdigit()]
    return " ".join(tokens) if tokens else message
