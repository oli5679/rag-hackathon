import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SUPABASE_URL = os.getenv("SUPABASE_URL", "http://127.0.0.1:54321")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
    FRONTEND_URL = os.getenv("FRONTEND_URL")
    REDIS_HOST = os.getenv("REDIS_HOST")
    
    # CORS settings
    ALLOWED_ORIGINS = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]
    if FRONTEND_URL:
        ALLOWED_ORIGINS.append(FRONTEND_URL)

settings = Settings()
