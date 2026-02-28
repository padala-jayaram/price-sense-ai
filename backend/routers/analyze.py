from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from services.query_parser import match_product, parse_chat_message
from services.context_retriever import (
    retrieve_product_and_siblings,
    retrieve_promo_history,
    retrieve_elasticity,
    retrieve_cannibalization,
)
from services.context_assembler import assemble_context
from services.ai_engine import get_recommendation, get_chat_response, get_greeting_response
from services.data_loader import get_catalog, get_general_catalog_summary

router = APIRouter(prefix="/api", tags=["analysis"])


class AnalyzeRequest(BaseModel):
    product: str
    discount_pct: float
    duration_days: int = 7
    timing: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[dict] = []
    last_context: Optional[str] = None


class ProductListResponse(BaseModel):
    products: list[dict]


@router.get("/products", response_model=ProductListResponse)
async def list_products():
    """Return all products for the dropdown."""
    catalog = get_catalog()
    products = [
        {
            "sku_id": sku["sku_id"],
            "product_name": sku["product_name"],
            "category": sku["category"],
            "base_price": sku["base_price"],
        }
        for sku in catalog["skus"]
    ]
    return {"products": products}


@router.post("/analyze")
async def analyze_promotion(request: AnalyzeRequest):
    """Full promotion analysis from form input."""
    if request.discount_pct <= 0 or request.discount_pct > 50:
        raise HTTPException(status_code=400, detail="Discount must be between 1% and 50%")

    # Match product
    product_match = match_product(request.product)
    if not product_match:
        raise HTTPException(status_code=404, detail=f"Could not find product matching '{request.product}'")

    # Retrieve context
    product_data = retrieve_product_and_siblings(product_match.sku_id)
    promo_history = retrieve_promo_history(product_match.sku_id, product_match.category)
    elasticity = retrieve_elasticity(product_match.category)
    cannibalization = retrieve_cannibalization(product_match.sku_id)

    # Assemble context
    context = assemble_context(
        product_data=product_data,
        promo_history=promo_history,
        elasticity=elasticity,
        cannibalization=cannibalization,
        discount_pct=request.discount_pct,
        timing=request.timing,
    )

    # Build user message for Gemini
    user_msg = (
        f"Analyze this promotion: {request.discount_pct}% off {product_match.product_name} "
        f"for {request.duration_days} days"
    )
    if request.timing:
        user_msg += f", timing: {request.timing}"

    # Get recommendation
    recommendation = await get_recommendation(context, user_msg)

    return {
        "recommendation": recommendation,
        "matched_product": product_match.model_dump(),
        "context": context,
        "context_tokens_estimate": len(context) // 4,
    }


@router.post("/chat")
async def chat(request: ChatRequest):
    """Follow-up chat with conversation history."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Parse message to detect intent
    parsed = parse_chat_message(request.message)

    # Handle greetings
    if parsed.intent == "greeting":
        reply = await get_greeting_response(request.message)
        return {"reply": reply, "parsed": parsed.model_dump()}

    # Use last analysis context if available, otherwise build new context
    context = request.last_context or ""

    if not context and parsed.product_hint:
        product_match = match_product(parsed.product_hint)
        if product_match:
            product_data = retrieve_product_and_siblings(product_match.sku_id)
            promo_history = retrieve_promo_history(product_match.sku_id, product_match.category)
            elasticity = retrieve_elasticity(product_match.category)
            cannibalization = retrieve_cannibalization(product_match.sku_id)
            context = assemble_context(
                product_data=product_data,
                promo_history=promo_history,
                elasticity=elasticity,
                cannibalization=cannibalization,
                discount_pct=parsed.discount_pct,
                timing=parsed.timing,
            )

    # Fallback: provide general catalog summary so the LLM can answer
    # questions about products, categories, and promo history
    if not context:
        context = get_general_catalog_summary()

    reply = await get_chat_response(
        context=context,
        user_message=request.message,
        conversation_history=request.conversation_history or None,
    )

    return {"reply": reply, "parsed": parsed.model_dump()}
