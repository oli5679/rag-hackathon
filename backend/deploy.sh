#!/bin/bash
# Cloud Run deployment script with Secret Manager
#
# Prerequisites:
# 1. gcloud CLI installed and authenticated
# 2. Secrets created in Secret Manager (run setup-secrets.sh first)

set -e

PROJECT_ID=$(gcloud config get-value project)
REGION="europe-west2"
SERVICE_NAME="spareroom-api"

echo "Deploying to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"

# Clear any existing plain-text env vars and use secrets instead
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --allow-unauthenticated \
  --clear-env-vars \
  --set-secrets="OPENAI_API_KEY=openai-api-key:latest,REDIS_HOST=redis-host:latest,REDIS_PORT=redis-port:latest,REDIS_PASSWORD=redis-password:latest,SUPABASE_URL=supabase-url:latest,FRONTEND_URL=frontend-url:latest" \
  --min-instances=0 \
  --max-instances=10 \
  --memory=512Mi \
  --cpu=1 \
  --timeout=300

echo ""
echo "Deployment complete!"
echo "Service URL:"
gcloud run services describe $SERVICE_NAME --region $REGION --format="value(status.url)"
