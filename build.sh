#!/usr/bin/env bash
# Build script for Render.com deployment

set -o errexit

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Running database migrations..."
# Convert DATABASE_URL from postgres:// to postgresql+asyncpg:// for SQLAlchemy
if [[ $DATABASE_URL == postgres://* ]]; then
    export DATABASE_URL="${DATABASE_URL/postgres:\/\//postgresql+asyncpg:\/\/}"
fi

alembic upgrade head

echo "Build completed successfully!"

