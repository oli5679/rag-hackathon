import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.routers import chat

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(title="SpareRoom Assistant API")

# CORS configuration
logger.info(f"CORS allowed origins: {settings.ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler to ensure CORS headers are present on errors."""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        },
    )

@app.on_event("startup")
async def startup_event():
    """Log configuration on startup."""
    logger.info("=== SpareRoom API Starting ===")
    logger.info(f"SUPABASE_URL: {settings.SUPABASE_URL}")
    logger.info(f"FRONTEND_URL: {settings.FRONTEND_URL or 'Not set'}")
    logger.info(f"Allowed CORS origins: {settings.ALLOWED_ORIGINS}")
    logger.info("=== Configuration logged ===")

@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/debug/config")
async def debug_config() -> dict[str, str]:
    """Debug endpoint to show current configuration."""
    return {
        "allowed_origins": str(settings.ALLOWED_ORIGINS),
        "supabase_url": settings.SUPABASE_URL,
        "frontend_url": settings.FRONTEND_URL or "Not set",
        "redis_host": (settings.REDIS_HOST[:20] + "...") if settings.REDIS_HOST else "Not set",
    }

# Include routers
app.include_router(chat.router, prefix="/api")
