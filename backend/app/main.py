"""Choose My Lawyer — FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.tasks.review_sync import start_scheduler, stop_scheduler

# API routers
from app.api.public import sessions, search, appointments, reviews as public_reviews
from app.api.firm import auth, profile, pricing, dashboard, reviews as firm_reviews
from app.api.admin import organisations

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Choose My Lawyer API")
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("Shutting down Choose My Lawyer API")


app = FastAPI(
    title="Choose My Lawyer API",
    description="UK legal comparison platform — Probate MVP",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Health check
@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok", "environment": settings.environment}


# Mount public API
app.include_router(sessions.router, prefix="/api/public")
app.include_router(search.router, prefix="/api/public")
app.include_router(appointments.router, prefix="/api/public")
app.include_router(public_reviews.router, prefix="/api/public")

# Mount firm API
app.include_router(auth.router, prefix="/api/firm")
app.include_router(profile.router, prefix="/api/firm")
app.include_router(pricing.router, prefix="/api/firm")
app.include_router(dashboard.router, prefix="/api/firm")
app.include_router(firm_reviews.router, prefix="/api/firm")

# Mount admin API
app.include_router(organisations.router, prefix="/api/admin")
