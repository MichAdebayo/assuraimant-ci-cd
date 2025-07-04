#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Ensure all required variables are set early
if [[ -z "$GITHUB_TOKEN" || -z "$GITHUB_ACTOR" || -z "$REPO_LC" || -z "$IMAGE_TAG" || -z "$RENDER_API_TOKEN" ]]; then
  echo "❌ One or more required environment variables (GITHUB_TOKEN, GITHUB_ACTOR, REPO_LC, IMAGE_TAG, RENDER_API_TOKEN) are not set."
  exit 1
fi

# Log in to GitHub Container Registry
echo "🔐 Logging into GitHub Container Registry..."
echo "$GITHUB_TOKEN" | docker login ghcr.io -u "$GITHUB_ACTOR" --password-stdin

# Debug Render API Token (partial only for security)
echo "🔑 RENDER_API_TOKEN starts with: ${RENDER_API_TOKEN:0:4}***"

# Pull the Docker image from GHCR
IMAGE="ghcr.io/${REPO_LC}/assuraimant-web-app:${IMAGE_TAG}"
echo "📥 Pulling Docker image: $IMAGE"
docker pull "$IMAGE"

# Deploy to Render
echo "🚀 Deploying Docker image to Render..."
echo "Deploying image: $IMAGE"
docker inspect "$IMAGE" --format='Image ID: {{.Id}}'

# Replace with your actual Render service ID
SERVICE_ID="srv-d0k6j0d6ubrc73b0uh0g"

if [[ -z "$SERVICE_ID" ]]; then
  echo "❌ SERVICE_ID is not set."
  exit 1
fi

# Prepare JSON payload with explicit version
DEPLOY_PAYLOAD=$(jq -n \
  --arg image "ghcr.io/${REPO_LC}/assuraimant-web-app:${IMAGE_TAG}" \
  '{
    dockerCommand: null,
    imageUrl: $image,
    isDockerCompose: false
  }')

echo "🧾 Generated JSON Payload:"
echo "$DEPLOY_PAYLOAD" | jq .

# Send deploy request to Render
RESPONSE=$(curl -s -w "\n%{http_code}" "https://api.render.com/v1/services/${SERVICE_ID}/deploys" \
  -H "Authorization: Bearer $RENDER_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data "$DEPLOY_PAYLOAD" 2>&1)

# Parse response and HTTP status
HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RESPONSE" | sed '$d')

if [[ "$HTTP_STATUS" != "200" && "$HTTP_STATUS" != "201" && "$HTTP_STATUS" != "202" ]]; then
  echo "❌ Deployment failed with status code $HTTP_STATUS"
  echo "📦 Response: $RESPONSE_BODY"
  exit 1
fi

  echo "✅ Deployment to Render completed successfully!"
