import os
import json
import re
import time
import logging
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("price_sense_ai")

# --- Provider config ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()  # "google", "bedrock", or "groq"

# --- Initialize the correct client ---
if LLM_PROVIDER == "bedrock":
    from anthropic import AnthropicBedrock

    _aws_profile = os.getenv("AWS_PROFILE", "berrygpt_dev_profile")
    _aws_region = os.getenv("AWS_REGION", "us-west-2")
    _bedrock_client = AnthropicBedrock(aws_profile=_aws_profile, aws_region=_aws_region)
    BEDROCK_MODEL = "us.anthropic.claude-sonnet-4-20250514-v1:0"
    logger.info(f"Provider=bedrock | model={BEDROCK_MODEL} | profile={_aws_profile} | region={_aws_region}")
elif LLM_PROVIDER == "groq":
    from groq import Groq

    _groq_key = os.getenv("GROQ_API_KEY", "")
    _groq_client = Groq(api_key=_groq_key)
    GROQ_MODEL = "llama-3.3-70b-versatile"
    logger.info(f"Provider=groq | model={GROQ_MODEL} | key={'***' + _groq_key[-4:] if len(_groq_key) > 4 else 'MISSING'}")
else:
    from google import genai
    from google.genai import types as genai_types

    _gemini_key = os.getenv("GEMINI_API_KEY", "")
    _gemini_client = genai.Client(api_key=_gemini_key)
    GEMINI_MODEL = "gemini-2.0-flash"
    logger.info(f"Provider=google | model={GEMINI_MODEL} | key={'***' + _gemini_key[-4:] if len(_gemini_key) > 4 else 'MISSING'}")


class PromoRecommendation(BaseModel):
    verdict: str  # GO, CAUTION, DECLINE
    verdict_summary: str
    projected_lift_pct: float
    projected_units: int
    baseline_units: int
    projected_revenue: float
    margin_per_unit: float
    gross_profit: float
    cannibalization_risk: str  # LOW, MEDIUM, HIGH
    cannibalization_details: str
    cannibalization_cost: float
    post_promo_dip_pct: float
    post_promo_dip_cost: float
    net_incremental_profit: float
    roi: float
    risk_factors: list[str]
    timing_assessment: str
    alternative_suggestion: str
    reasoning: str


RECOMMENDATION_SCHEMA = """\
You MUST respond with a JSON object with exactly these fields:
{
  "verdict": "GO" or "CAUTION" or "DECLINE",
  "verdict_summary": "one-line summary",
  "projected_lift_pct": number,
  "projected_units": integer,
  "baseline_units": integer,
  "projected_revenue": number,
  "margin_per_unit": number,
  "gross_profit": number,
  "cannibalization_risk": "LOW" or "MEDIUM" or "HIGH",
  "cannibalization_details": "string",
  "cannibalization_cost": number,
  "post_promo_dip_pct": number,
  "post_promo_dip_cost": number,
  "net_incremental_profit": number,
  "roi": number,
  "risk_factors": ["string", ...],
  "timing_assessment": "string",
  "alternative_suggestion": "string",
  "reasoning": "string"
}"""


SYSTEM_PROMPT = """You are Price Sense AI, an expert retail promotion analyst. You help mid-market retailers make data-driven promotion decisions.

You have access to the following data about the retailer's products and promotion history:

{context}

---

INSTRUCTIONS:
1. Analyze the proposed promotion using the data above.
2. Show your math. Reference specific historical promotions when making projections.
3. Be direct and actionable. Retailers need clear guidance, not hedging.
4. Use the elasticity coefficients and historical lift data to project volume impact.
5. Calculate cannibalization cost using the cross-elasticity and sibling product data.
6. Factor in post-promo dip cost when computing net incremental profit.
7. When the discount is outside the optimal range, flag this in risk_factors.
8. For timing_assessment, use the seasonality index to evaluate if the timing is favorable.
9. If a better discount level exists based on historical ROI data, suggest it in alternative_suggestion.
10. Round all dollar amounts to 2 decimal places and percentages to 1 decimal place.

IMPORTANT: Your response must be valid JSON matching the required schema exactly.
"""


def _build_system_prompt(context: str) -> str:
    return SYSTEM_PROMPT.format(context=context) + "\n\n" + RECOMMENDATION_SCHEMA


CHAT_SYSTEM_PROMPT = """You are Price Sense AI, a friendly and knowledgeable retail promotion analyst.

You have access to the following data about the retailer's products, categories, pricing, and promotion history:

{context}

You are having a conversation about promotion strategy. The user may ask:
- Questions about products, categories, pricing, and margins
- Questions about past promotions and their performance
- What-if questions ("What about 15% instead?")
- Clarifications about a previous analysis
- Comparisons between products or categories
- General promotion strategy and best practices

Be conversational but data-driven. Reference specific numbers from the data above.
Keep responses concise (2-4 paragraphs max). Use markdown formatting for readability."""


GREETING_SYSTEM = (
    "You are Price Sense AI, a friendly retail promotion analyst. "
    "The user has greeted you or asked a general question. "
    "Respond briefly, introduce yourself, and suggest they ask about "
    "a specific promotion scenario. Mention you can analyze: "
    "projected lift, cannibalization, profit impact, and timing. "
    "Keep it to 2-3 sentences."
)


FALLBACK_RECOMMENDATION = {
    "verdict": "CAUTION",
    "verdict_summary": "Analysis could not be fully structured. See reasoning.",
    "projected_lift_pct": 0,
    "projected_units": 0,
    "baseline_units": 0,
    "projected_revenue": 0,
    "margin_per_unit": 0,
    "gross_profit": 0,
    "cannibalization_risk": "UNKNOWN",
    "cannibalization_details": "Unable to parse structured response.",
    "cannibalization_cost": 0,
    "post_promo_dip_pct": 0,
    "post_promo_dip_cost": 0,
    "net_incremental_profit": 0,
    "roi": 0,
    "risk_factors": ["Analysis response could not be parsed"],
    "timing_assessment": "N/A",
    "alternative_suggestion": "Please try again.",
    "reasoning": "",
}


def _extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown code fences."""
    # Try direct parse first
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass
    # Try extracting from ```json ... ``` blocks
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    # Try finding first { ... } block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass
    return None


# ===================== GOOGLE GEMINI =====================

async def _gemini_recommendation(system: str, user_message: str) -> dict:
    logger.info(f"[google] recommendation request | model={GEMINI_MODEL}")
    t0 = time.time()
    response = _gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_message,
        config=genai_types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.3,
            max_output_tokens=2000,
            response_mime_type="application/json",
            response_schema=PromoRecommendation,
        ),
    )
    parsed = _extract_json(response.text)
    elapsed = time.time() - t0
    if parsed:
        logger.info(f"[google] recommendation complete | {elapsed:.2f}s | verdict={parsed.get('verdict')}")
        return parsed
    logger.warning(f"[google] recommendation parse failed | {elapsed:.2f}s | falling back")
    fallback = dict(FALLBACK_RECOMMENDATION)
    fallback["reasoning"] = response.text or "No response received."
    return fallback


async def _gemini_chat(system: str, user_message: str, history: Optional[list[dict]]) -> str:
    logger.info(f"[google] chat request | model={GEMINI_MODEL} | history={len(history) if history else 0} msgs")
    t0 = time.time()
    contents = []
    if history:
        for msg in history:
            role = "user" if msg["role"] == "user" else "model"
            contents.append(genai_types.Content(role=role, parts=[genai_types.Part(text=msg["content"])]))
    contents.append(genai_types.Content(role="user", parts=[genai_types.Part(text=user_message)]))

    response = _gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=contents,
        config=genai_types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.5,
            max_output_tokens=1000,
        ),
    )
    logger.info(f"[google] chat complete | {time.time() - t0:.2f}s")
    return response.text or "I wasn't able to generate a response. Please try again."


async def _gemini_greeting(user_message: str) -> str:
    logger.info(f"[google] greeting request | model={GEMINI_MODEL}")
    t0 = time.time()
    response = _gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        contents=user_message,
        config=genai_types.GenerateContentConfig(
            system_instruction=GREETING_SYSTEM,
            temperature=0.7,
            max_output_tokens=300,
        ),
    )
    logger.info(f"[google] greeting complete | {time.time() - t0:.2f}s")
    return response.text or "Hello! I'm Price Sense AI. Ask me about any promotion scenario!"


# ===================== AWS BEDROCK (CLAUDE) =====================

async def _bedrock_recommendation(system: str, user_message: str) -> dict:
    logger.info(f"[bedrock] recommendation request | model={BEDROCK_MODEL} | profile={_aws_profile}")
    t0 = time.time()
    response = _bedrock_client.messages.create(
        model=BEDROCK_MODEL,
        max_tokens=2000,
        temperature=0.3,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    )
    text = response.content[0].text
    parsed = _extract_json(text)
    elapsed = time.time() - t0
    if parsed:
        logger.info(f"[bedrock] recommendation complete | {elapsed:.2f}s | verdict={parsed.get('verdict')}")
        return parsed
    logger.warning(f"[bedrock] recommendation parse failed | {elapsed:.2f}s | falling back")
    fallback = dict(FALLBACK_RECOMMENDATION)
    fallback["reasoning"] = text or "No response received."
    return fallback


async def _bedrock_chat(system: str, user_message: str, history: Optional[list[dict]]) -> str:
    logger.info(f"[bedrock] chat request | model={BEDROCK_MODEL} | history={len(history) if history else 0} msgs")
    t0 = time.time()
    messages = []
    if history:
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    response = _bedrock_client.messages.create(
        model=BEDROCK_MODEL,
        max_tokens=1000,
        temperature=0.5,
        system=system,
        messages=messages,
    )
    logger.info(f"[bedrock] chat complete | {time.time() - t0:.2f}s")
    return response.content[0].text or "I wasn't able to generate a response. Please try again."


async def _bedrock_greeting(user_message: str) -> str:
    logger.info(f"[bedrock] greeting request | model={BEDROCK_MODEL}")
    t0 = time.time()
    response = _bedrock_client.messages.create(
        model=BEDROCK_MODEL,
        max_tokens=300,
        temperature=0.7,
        system=GREETING_SYSTEM,
        messages=[{"role": "user", "content": user_message}],
    )
    logger.info(f"[bedrock] greeting complete | {time.time() - t0:.2f}s")
    return response.content[0].text or "Hello! I'm Price Sense AI. Ask me about any promotion scenario!"


# ===================== GROQ (LLAMA 3.3 70B) =====================

async def _groq_recommendation(system: str, user_message: str) -> dict:
    logger.info(f"[groq] recommendation request | model={GROQ_MODEL}")
    t0 = time.time()
    response = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_message},
        ],
        temperature=0.3,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )
    text = response.choices[0].message.content
    parsed = _extract_json(text)
    elapsed = time.time() - t0
    if parsed:
        logger.info(f"[groq] recommendation complete | {elapsed:.2f}s | verdict={parsed.get('verdict')}")
        return parsed
    logger.warning(f"[groq] recommendation parse failed | {elapsed:.2f}s | falling back")
    fallback = dict(FALLBACK_RECOMMENDATION)
    fallback["reasoning"] = text or "No response received."
    return fallback


async def _groq_chat(system: str, user_message: str, history: Optional[list[dict]]) -> str:
    logger.info(f"[groq] chat request | model={GROQ_MODEL} | history={len(history) if history else 0} msgs")
    t0 = time.time()
    messages = [{"role": "system", "content": system}]
    if history:
        for msg in history:
            role = "user" if msg["role"] == "user" else "assistant"
            messages.append({"role": role, "content": msg["content"]})
    messages.append({"role": "user", "content": user_message})

    response = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.5,
        max_tokens=1000,
    )
    logger.info(f"[groq] chat complete | {time.time() - t0:.2f}s")
    return response.choices[0].message.content or "I wasn't able to generate a response. Please try again."


async def _groq_greeting(user_message: str) -> str:
    logger.info(f"[groq] greeting request | model={GROQ_MODEL}")
    t0 = time.time()
    response = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": GREETING_SYSTEM},
            {"role": "user", "content": user_message},
        ],
        temperature=0.7,
        max_tokens=300,
    )
    logger.info(f"[groq] greeting complete | {time.time() - t0:.2f}s")
    return response.choices[0].message.content or "Hello! I'm Price Sense AI. Ask me about any promotion scenario!"


# ===================== PUBLIC API (provider-agnostic) =====================

async def get_recommendation(context: str, user_message: str) -> dict:
    """Get a structured promotion recommendation."""
    system = _build_system_prompt(context)
    if LLM_PROVIDER == "bedrock":
        return await _bedrock_recommendation(system, user_message)
    if LLM_PROVIDER == "groq":
        return await _groq_recommendation(system, user_message)
    return await _gemini_recommendation(system, user_message)


async def get_chat_response(
    context: str,
    user_message: str,
    conversation_history: Optional[list[dict]] = None,
) -> str:
    """Get a conversational follow-up response."""
    system = CHAT_SYSTEM_PROMPT.format(context=context)
    if LLM_PROVIDER == "bedrock":
        return await _bedrock_chat(system, user_message, conversation_history)
    if LLM_PROVIDER == "groq":
        return await _groq_chat(system, user_message, conversation_history)
    return await _gemini_chat(system, user_message, conversation_history)


async def get_greeting_response(user_message: str) -> str:
    """Handle greetings without full context assembly."""
    if LLM_PROVIDER == "bedrock":
        return await _bedrock_greeting(user_message)
    if LLM_PROVIDER == "groq":
        return await _groq_greeting(user_message)
    return await _gemini_greeting(user_message)
