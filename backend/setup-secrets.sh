#!/bin/bash
# Set up secrets in Google Cloud Secret Manager
#
# Run this once to create secrets, then use deploy.sh for deployments
#
# Usage: ./setup-secrets.sh

set -e

PROJECT_ID=$(gcloud config get-value project)

echo "Setting up secrets for project: $PROJECT_ID"
echo ""
echo "You'll be prompted to enter each secret value."
echo "Values are NOT echoed to the terminal for security."
echo ""

# Function to create or update a secret
create_secret() {
    local secret_name=$1
    local description=$2

    echo "---"
    echo "Secret: $secret_name"
    echo "Description: $description"

    # Check if secret exists
    if gcloud secrets describe $secret_name --project=$PROJECT_ID &>/dev/null; then
        echo "Secret exists. Enter new value to update (or press Enter to skip):"
        read -s secret_value
        if [ -n "$secret_value" ]; then
            echo -n "$secret_value" | gcloud secrets versions add $secret_name --data-file=-
            echo "✓ Updated"
        else
            echo "⏭ Skipped"
        fi
    else
        echo "Creating new secret. Enter value:"
        read -s secret_value
        if [ -n "$secret_value" ]; then
            echo -n "$secret_value" | gcloud secrets create $secret_name --data-file=- --replication-policy="automatic"
            echo "✓ Created"
        else
            echo "✗ Skipped (no value provided)"
        fi
    fi
    echo ""
}

# Create each secret
create_secret "openai-api-key" "OpenAI API key (sk-...)"
create_secret "redis-host" "Redis Cloud host"
create_secret "redis-port" "Redis Cloud port"
create_secret "redis-password" "Redis Cloud password"
create_secret "supabase-url" "Supabase project URL (https://xxx.supabase.co)"
create_secret "frontend-url" "Frontend URL for CORS (https://xxx.vercel.app)"

echo ""
echo "Done! Secrets configured:"
gcloud secrets list --project=$PROJECT_ID

echo ""
echo "Next step: Run ./deploy.sh to deploy to Cloud Run"
