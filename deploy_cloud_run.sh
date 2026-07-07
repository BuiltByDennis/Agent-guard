#!/bin/bash

# Ensure the script stops on the first error
set -e

echo "🚀 Preparing to deploy Agent Proxy to Google Cloud Run..."

# Replace these variables with your actual project details
PROJECT_ID="your-gcp-project-id"
REGION="us-central1"
SERVICE_NAME="agent-proxy-backend"

# Supabase and other secrets
# IMPORTANT: Supabase uses port 6543 for its PgBouncer connection pooler!
DATABASE_URL="postgresql+asyncpg://postgres:password@db.your-supabase-id.supabase.co:6543/postgres"
REDIS_URL="redis://your-redis-host:6379"
SENTRY_DSN="your-sentry-dsn"
FIREWALL_MODE="BLOCK"
OPENAI_API_KEY="your-openai-api-key"
FRONTEND_URL="https://your-dashboard.vercel.app"

echo "📦 Submitting build to Google Cloud Build..."
# This command uploads your source code and builds the Docker image on GCP
gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME ./backend --project $PROJECT_ID

echo "☁️ Deploying image to Google Cloud Run..."
# This command deploys the container, configures autoscaling, and injects environment variables
gcloud run deploy $SERVICE_NAME \
  --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --no-cpu-throttling \
  --min-instances 1 \
  --max-instances 50 \
  --port 8000 \
  --set-env-vars="DATABASE_URL=$DATABASE_URL,REDIS_URL=$REDIS_URL,SENTRY_DSN=$SENTRY_DSN,FIREWALL_MODE=$FIREWALL_MODE,OPENAI_API_KEY=$OPENAI_API_KEY,FRONTEND_URL=$FRONTEND_URL" \
  --project $PROJECT_ID

echo "✅ Deployment complete! Check the Cloud Run console for your live HTTPS URL."
