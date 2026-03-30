import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import analyze
from services import data_loader
from models import Base   # your Base is here
from services.database import engine  # your engine is here
import models  # VERY IMPORTANT (loads all tables)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("price_sense_ai")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ Create tables in NEW DB
    if engine:
        Base.metadata.create_all(bind=engine)
    data_loader.init()
    logger.info("Data loaded: products, promo_history, elasticity, cannibalization")
    yield


app = FastAPI(
    title="Price Sense AI",
    description="AI-powered promotion recommendation engine",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=False,
    )
