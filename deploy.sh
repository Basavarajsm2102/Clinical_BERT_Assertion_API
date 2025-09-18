#!/bin/bash

# Clinical BERT API - Production Deployment Script

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="clinical-bert-api"
REPOSITORY="clinical-bert-repo"

echo "🚀 Deploying Clinical BERT API..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Validate project ID
if [[ -z "$PROJECT_ID" ]]; then
    echo "❌ Error: GCP_PROJECT_ID environment variable required"
    exit 1
fi

# Set project
gcloud config set project "$PROJECT_ID"

# Enable APIs
echo "📡 Enabling APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create repository
echo "📦 Setting up Artifact Registry..."
gcloud artifacts repositories create "$REPOSITORY" \
    --repository-format=docker \
    --location="$REGION" \
    --description="Clinical BERT API repository" || true

# Configure Docker
gcloud auth configure-docker "${REGION}-docker.pkg.dev" --quiet

# Build image
echo "🔨 Building Docker image..."
docker build -t "$SERVICE_NAME:latest" .

# Tag for registry
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPOSITORY}/${SERVICE_NAME}:latest"
docker tag "$SERVICE_NAME:latest" "$IMAGE_NAME"

# Push image
echo "📤 Pushing to Artifact Registry..."
docker push "$IMAGE_NAME"

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --image="$IMAGE_NAME" \
    --region="$REGION" \
    --platform=managed \
    --allow-unauthenticated \
    --memory=2Gi \
    --cpu=1 \
    --timeout=900 \
    --concurrency=10 \
    --min-instances=0 \
    --max-instances=5 \
    --port=8000 \
    --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=INFO"

# Get service URL
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" \
    --region="$REGION" \
    --format="value(status.url)")

echo "✅ Deployment completed!"
echo "🌐 Service URL: $SERVICE_URL"

# Test deployment
echo "🧪 Testing deployment..."
sleep 30
curl -f "$SERVICE_URL/health" || echo "⚠️ Health check failed"

echo "🎉 Clinical BERT API deployed successfully!"
