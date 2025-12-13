#!/bin/bash
set -e

# Deployment script for Backend
# Usage: ./deploy.sh
# Make sure to have a .env file with production values

# 1. Update Secrets (if needed) across environments
# Note: Ensure you have the `supabase` CLI installed and authenticated if pushing config
# 1. Load Secrets
if [ -f .env ]; then
    echo "Loading .env file..."
    set -a
    source .env
    set +a
fi

# 2. Sync Dependencies
echo "Syncing dependencies..."
uv sync --frozen

# 4. Validation
echo "Validating configuration..."
: "${SUPABASE_URL:?Error: SUPABASE_URL is not set}"
: "${SUPABASE_ANON_KEY:?Error: SUPABASE_ANON_KEY is not set}"

# 5. Run
echo "Starting application with uv run..."
# uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
