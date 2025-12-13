#!/bin/bash
set -e

# Configuration
SECRET_NAME="supabase-anon-key"
PROJECT_ID=$(gcloud config get-value project)

echo "=== Update Supabase Anon Key Secret ==="
echo "Project: $PROJECT_ID"
echo "Secret: $SECRET_NAME"
echo ""
echo "Paste your Supabase Anon Key below and press ENTER:"
read -r RAW_KEY

# Trim whitespace/newlines
CLEAN_KEY=$(echo -n "$RAW_KEY" | tr -d '\n' | tr -d ' ')

if [ -z "$CLEAN_KEY" ]; then
  echo "Error: Key is empty."
  exit 1
fi

echo ""
echo "Updating secret (creating new version)..."

# Pipe the clean key strictly without newlines into gcloud
echo -n "$CLEAN_KEY" | gcloud secrets versions add "$SECRET_NAME" --data-file=-

echo ""
echo "✅ Secret updated successfully!"
echo "Now run ./deploy.sh to deploy the changes."
