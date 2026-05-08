#!/usr/bin/env bash
set -e

echo "Setting up local development environment..."

if [ ! -f .env ]; then
  echo "Copying .env.example to .env..."
  cp .env.example .env
fi

if ! command -v pnpm &> /dev/null; then
  echo "Installing pnpm..."
  npm install -g pnpm
fi

if ! command -v uv &> /dev/null; then
  echo "Installing uv..."
  pip install uv
fi

echo "Installing workspace dependencies..."
pnpm install

echo "Starting infrastructure containers..."
docker-compose up -d postgres redis nats minio emqx chirpstack mailhog

echo "Waiting for PostgreSQL..."
./scripts/wait-for-it.sh localhost:5432 -t 60

echo "Setup complete! Run 'make migrate' and 'make seed' next."
