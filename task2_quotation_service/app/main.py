"""
AL ROUF Quotation Microservice
FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import quotes, health
from app.core.config import settings

app = FastAPI(
    title="AL ROUF Quotation Microservice",
    description=(
        "Generates structured LED lighting product quotations. "
        "Supports multi-line RFQ inputs, currency conversion, and bilingual output."
    ),
    version="1.0.0",
    contact={"name": "Labeeb K M", "email": "labeeb@example.com"},
    license_info={"name": "Proprietary"},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(quotes.router, prefix="/quotes", tags=["Quotations"])


@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "AL ROUF Quotation Microservice",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }
