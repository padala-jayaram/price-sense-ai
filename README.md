# Price Sense AI

> AI-powered promotion recommendation engine for mid-market retailers — delivering GO, CAUTION, or DECLINE verdicts backed by data.

## Overview

Price Sense AI analyzes proposed retail promotions and returns structured, data-driven recommendations. Given a product, discount percentage, duration, and timing, the system evaluates:

- **Sales lift** — projected volume increase and revenue impact
- **Cannibalization** — how the promotion affects sibling SKUs in the same category
- **Profit impact** — net incremental margin after accounting for all costs
- **Post-promotion dip** — demand hangover cost after the promo ends
- **ROI** — return on investment for the promotion spend
- **Risk factors** — timing, margin, competitive, and cannibalization risks

The verdict is always one of **GO**, **CAUTION**, or **DECLINE**, with explicit reasoning and alternative suggestions where applicable.

---

## Features

- Structured promotion analysis with numeric metric breakdown
- Conversational follow-up chat for what-if scenarios and comparisons
- Fuzzy product name matching (handles typos, word reordering)
- Multi-provider LLM support — switch between Groq, Google Gemini, and AWS Bedrock via a single env var
- 24-SKU product catalog across 5 categories with price elasticity and cannibalization data
- Dark mode UI with conversation history sidebar

---

## Tech Stack

### Backend
| Component | Technology |
|---|---|
| Framework | FastAPI 0.115.0 + Uvicorn |
| Language | Python 3.13 |
| Validation | Pydantic 2.9 |
| Product matching | RapidFuzz 3.13 (fuzzy string matching) |
| LLM providers | Groq (llama-3.3-70b), Google Gemini 2.0 Flash, AWS Bedrock (Claude) |
| ORM | SQLAlchemy 2.0 |
| Migrations | Alembic |
| Database driver | psycopg2-binary |

### Frontend
| Component | Technology |
|---|---|
| Framework | React 19.2 + Vite 7.3 |
| Markdown rendering | React Markdown 10.1 |
| API proxy | Vite dev server → localhost:8000 |

### Database (PostgreSQL)
| Table | Contents |
|---|---|
| `products` | 24 SKUs — name, price, margin, weekly volume, category |
| `promo_history` | Historical promotions with lift, ROI, and outcomes |
| `elasticity` | Price elasticity by category, seasonality, optimal discount ranges |
| `cannibalization` | Cross-product impact rows (52 sibling relationships) |

---

## Project Structure

```
price-sense-ai/
├── backend/
│   ├── main.py                   # FastAPI app, CORS setup
│   ├── models.py                 # SQLAlchemy ORM models (4 tables)
│   ├── requirements.txt
│   ├── alembic.ini               # Alembic config
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 001_create_tables.py
│   │       └── 002_seed_data.py
│   ├── routers/
│   │   └── analyze.py            # /api/analyze, /api/chat, /api/products
│   └── services/
│       ├── ai_engine.py          # Multi-provider LLM abstraction
│       ├── context_assembler.py  # Builds ~400-token focused context
│       ├── context_retriever.py  # Fetches product, promo, elasticity data
│       ├── database.py           # SQLAlchemy engine + session factory
│       ├── data_loader.py        # Loads data from PostgreSQL (or JSON fallback)
│       └── query_parser.py       # RapidFuzz matching, message parsing
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── App.jsx               # Root component, conversation state
        ├── api.js                # Fetch wrappers
        ├── components/
        │   ├── AnalysisCard.jsx  # Verdict + metrics dashboard
        │   ├── ChatArea.jsx      # Message display
        │   ├── ChatInput.jsx     # Free-text input
        │   ├── ChatMessage.jsx   # Individual message rendering
        │   ├── CustomSelect.jsx  # Product dropdown
        │   ├── Header.jsx        # Dark mode toggle, branding
        │   ├── InputControls.jsx # Product + discount form
        │   ├── Sidebar.jsx       # Conversation history
        │   └── WelcomeScreen.jsx # Empty state
        └── hooks/
            └── useConversations.js
```

---

## Architecture

### Current Architecture (Prototype)

```
┌─────────────────────────────────────────────────────────┐
│                    REACT FRONTEND                         │
│  Form Input (product, discount, timing, duration)        │
│  Dashboard (verdict, metrics, profit breakdown, risks)   │
│  Chat (follow-up questions with conversation history)    │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP
┌────────────────────────▼────────────────────────────────┐
│                    FASTAPI BACKEND                        │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │ Query Parser  │→│   Context     │→│   Context      │  │
│  │ (RapidFuzz)   │  │   Retriever   │  │   Assembler    │  │
│  └──────────────┘  └──────────────┘  └───────┬───────┘  │
│                                               │          │
│  ┌────────────────────────────────────────────▼───────┐  │
│  │              AI ENGINE (Gemini / Groq / Claude)    │  │
│  │  System Prompt + ~400 tokens of focused context    │  │
│  │  → Structured JSON recommendation                  │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │            POSTGRESQL (Render)                     │  │
│  │  products | promo_history                          │  │
│  │  elasticity | cannibalization                      │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

#### Why Smart Context Assembly (Not RAG)

The core data is **structured** — SKU records, price elasticity coefficients, promo history with numeric fields. This is a **database lookup problem**, not a semantic search problem.

- 24 SKUs, promo history, 5 elasticity categories = ~3,000 tokens total
- The retrieval layer filters this down to **~400 tokens of relevant context** per query
- RapidFuzz fuzzy matching handles product name ambiguity (typos, word reordering)
- No embeddings or vector similarity needed for structured numeric data

Implementing RAG for this data size would add complexity without benefit. RAG belongs where meaning matters — unstructured text where semantic similarity is needed (see Production Architecture below).

---

### Production Architecture (At Scale)

```
┌─────────────────────────────────────────────────────────────┐
│                     REACT FRONTEND                           │
│  Multi-tenant dashboard | Role-based access | Real-time      │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS (API Gateway)
┌────────────────────────▼────────────────────────────────────┐
│                    API LAYER (FastAPI)                        │
│  Auth middleware | Rate limiting | Request validation         │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                RETRIEVAL & ANALYSIS LAYER                     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  STRUCTURED DATA RETRIEVAL (SQL)                     │     │
│  │  PostgreSQL + pgvector                               │     │
│  │  - Product catalog (100K+ SKUs)                      │     │
│  │  - Promo history (millions of records)               │     │
│  │  - Elasticity models (per SKU, not just category)    │     │
│  │  - Cannibalization matrices                          │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  UNSTRUCTURED DATA RETRIEVAL (RAG) ← RAG goes HERE  │     │
│  │  Pinecone / pgvector embeddings                      │     │
│  │  - Promo post-mortems & analyst notes                │     │
│  │  - Competitor pricing intelligence                    │     │
│  │  - Market research reports                            │     │
│  │  - Category management playbooks                      │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  ML MODELS                                           │     │
│  │  - Price elasticity estimation (per-SKU from POS)    │     │
│  │  - Demand forecasting (Prophet / LightGBM)           │     │
│  │  - Cannibalization prediction (cross-elasticity ML)  │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  CONTEXT ASSEMBLER (same pattern as prototype)       │     │
│  │  Pulls from SQL + RAG + ML → builds focused context  │     │
│  │  The assembler interface is identical — only data     │     │
│  │  sources change underneath                            │     │
│  └─────────────────────────────────────────────────────┘     │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐     │
│  │  LLM LAYER (Claude / Gemini / GPT-4)                 │     │
│  │  Multi-model routing based on query complexity        │     │
│  │  Structured output → validated → stored               │     │
│  └─────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   FEEDBACK LOOP                              │
│  Track actual promo outcomes vs. predictions                 │
│  Fine-tune elasticity models with real results               │
│  Capture analyst corrections to improve LLM prompts          │
└──────────────────────────────────────────────────────────────┘
```

#### Key Scaling Decisions

| Component | Current | Production |
|---|---|---|
| Product data | PostgreSQL (24 SKUs) | PostgreSQL (100K+ SKUs) |
| Promo history | PostgreSQL records | PostgreSQL (millions) + time-series indexing |
| Elasticity | Static per-category | ML model per-SKU, retrained weekly |
| Product matching | RapidFuzz string matching | SQL full-text search + vector similarity |
| Unstructured data | None | RAG with Pinecone/pgvector for analyst notes, market research |
| Cannibalization | Static mapping | ML cross-elasticity model trained on POS data |
| LLM | Single provider | Multi-model routing by query complexity |
| Context assembly | Same pattern | Same pattern (retriever interfaces unchanged) |
| Auth | None | SSO + RBAC (multi-tenant) |
| Feedback | None | Outcome tracking → model retraining loop |

#### Where RAG Belongs in Production

RAG is the correct tool for **unstructured data retrieval** — when you need semantic similarity rather than exact lookup:

1. **Promo post-mortems** — "Find past promotions with similar market conditions"
2. **Competitor intelligence** — "What did competitors price this category at last Q4?"
3. **Market research** — "What consumer trends affect pistachio demand?"
4. **Category playbooks** — "What are best practices for holiday nut promotions?"

These are text documents where meaning matters. In contrast, looking up `SKU PST-16 base price` is a database query, not a search problem.

---

## API Endpoints

### `GET /api/products`
Returns all SKUs with prices, margins, and weekly volumes.

### `POST /api/analyze`
Runs a full promotion analysis.

**Request:**
```json
{
  "product": "Olive Oil",
  "discount_pct": 20,
  "duration_days": 7,
  "timing": "weekend"
}
```

**Response:**
```json
{
  "verdict": "CAUTION",
  "metrics": {
    "projected_lift_pct": 35,
    "incremental_units": 148,
    "cannibalization_pct": 12
  },
  "profit_analysis": {
    "gross_revenue_impact": 890,
    "net_incremental_profit": 142,
    "roi": 0.18
  },
  "risk_factors": ["margin squeeze at 20% discount", "cannibalization of Pasta SKU"],
  "reasoning": "..."
}
```

### `POST /api/chat`
Conversational follow-up on an existing analysis.

**Request:**
```json
{
  "message": "What if we dropped the discount to 15%?",
  "conversation_history": [],
  "last_context": "..."
}
```

---

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 20+
- PostgreSQL database (or use the Render-hosted instance)
- A `.env` file at the repo root (see [Configuration](#configuration))

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run database migrations (creates tables + seeds data — first time only)
alembic upgrade head

uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev   # Starts on http://localhost:5173
```

The Vite dev server proxies `/api/*` requests to `http://localhost:8000`.

---

## Configuration

Create a `.env` file at the repo root with the following keys:

| Key | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql://user:pass@host/db`) |
| `LLM_PROVIDER` | Which LLM to use: `groq`, `google`, or `bedrock` |
| `GROQ_API_KEY` | API key from [console.groq.com](https://console.groq.com) |
| `GEMINI_API_KEY` | API key from [aistudio.google.com](https://aistudio.google.com) |
| `AWS_PROFILE` | AWS profile name (for Bedrock) |
| `AWS_REGION` | AWS region (for Bedrock, e.g. `us-east-1`) |

If `DATABASE_URL` is not set, the app falls back to local JSON files in `backend/data/` (useful for quick local dev without a database).

### LLM Providers

| Provider | Model | Notes |
|---|---|---|
| `groq` | llama-3.3-70b-versatile | Fast, free tier available — **default** |
| `google` | gemini-2.0-flash | Free tier available |
| `bedrock` | Claude Sonnet 4 | Requires AWS account + Bedrock access |

Switch providers by setting `LLM_PROVIDER` in your `.env` — no code changes needed.

---

## License

MIT
