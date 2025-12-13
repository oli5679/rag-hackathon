#!/bin/bash
set -e

# Deployment script for Backend
# Usage: ./deploy.sh
# Make sure to have a .env file with production values

# 1. Update Secrets (if needed) across environments
# Note: Ensure you have the `supabase` CLI installed and authenticated if pushing config
# supabase secrets set --env-file .env

# 2. Build/Prepare Backend
# No build step for Python, but we can verify requirements
echo "Installing/Verifying dependencies..."
pip install -r requirements.txt

# 3. Validation
echo "Validating configuration..."
# Check for key env vars
if [ -z "$SUPABASE_URL" ]; then
    echo "Error: SUPABASE_URL is not set"
    exit 1
fi

if [ -z "$SUPABASE_ANON_KEY" ]; then
    echo "Error: SUPABASE_ANON_KEY is not set"
    exit 1
fi

# 4. Run (for local dev or similar start command, in production this might be a service)
# Using uvicorn with the new app location
echo "Starting application..."
# exec uvicorn app.main:app --host 0.0.0.0 --port 8000
