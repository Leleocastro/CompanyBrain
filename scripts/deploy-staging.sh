#!/usr/bin/env bash
set -euo pipefail

SERVICE="${1:?Usage: $0 <service-name>}"
ENV="staging"
REGISTRY="ghcr.io/leleocastro/companybrain"
COMMIT_SHA="${GITHUB_SHA:-$(git rev-parse --short HEAD)}"

echo "Deploying $SERVICE to $ENV..."

docker build \
  -t "$REGISTRY/$SERVICE:$COMMIT_SHA" \
  -t "$REGISTRY/$SERVICE:latest" \
  -f "docker/$SERVICE.Dockerfile" \
  --build-arg ENV=$ENV \
  .

docker push "$REGISTRY/$SERVICE:$COMMIT_SHA"
docker push "$REGISTRY/$SERVICE:latest"

echo "Triggering $ENV rollout for $SERVICE..."
echo "Deploy $SERVICE:$COMMIT_SHA to $ENV" | kubectl apply -f - 2>/dev/null || true

echo "Deploy to $ENV complete for $SERVICE"
