#!/bin/bash

set -e

echo "Applying building..."
echo " "

docker compose \
  --env-file .env.dev \
  -f docker-compose.dev.yml \
  build

echo " "
echo "Applying up..."

docker compose \
  --env-file .env.dev \
  -f docker-compose.dev.yml \
  up -d

echo " "
