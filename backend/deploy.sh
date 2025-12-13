#!/bin/bash
set -e

# Deployment script for Backend
# Usage: ./deploy.sh
# Make sure to have a .env file with production values

# 1. Load Secrets
  echo "Loading .env file..."
  set -a
  source .env
  set +a

# 2. Sync Dependencies
echo "Syncing dependencies..."
uv sync --frozen

# 4. Validation
echo "Validating configuration..."
: "${SUPABASE_URL:?Error: SUPABASE_URL is not set}"
: "${SUPABASE_ANON_KEY:?Error: SUPABASE_ANON_KEY is not set}"

# 5. Deploy to Cloud Run
echo "Deploying to Cloud Run..."
PROJECT_ID=$(gcloud config get-value project)
REGION="europe-west2"
SERVICE_NAME="spareroom-api"

# Deploy using source (uses Dockerfile we updated)
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --set-secrets="OPENAI_API_KEY=openai-api-key:latest,REDIS_HOST=redis-host:latest,REDIS_PORT=redis-port:latest,REDIS_PASSWORD=redis-password:latest,SUPABASE_URL=supabase-url:latest,SUPABASE_ANON_KEY=supabase-anon-key:latest,FRONTEND_URL=frontend-url:latest" \
  --timeout=300 \
  --startup-cpu-boost

echo "Deployment triggered!"
