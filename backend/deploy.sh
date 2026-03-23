#!/bin/bash
set -e

echo "========================================="
echo "  RentPe Auto-Deploy (triggered by push)"
echo "========================================="

cd /home/ubuntu/RentPe

# Pull latest code
echo "[1/4] Pulling latest code..."
git pull origin main

# Install any new dependencies
echo "[2/4] Installing dependencies..."
cd backend
source venv/bin/activate
pip install -r requirements.txt --quiet

# Run database migrations
echo "[3/4] Running database migrations..."
alembic upgrade heads

# Restart the service
echo "[4/4] Restarting RentPe service..."
sudo systemctl restart rentpe

echo "========================================="
echo "  Deploy complete! Checking service..."
echo "========================================="
sleep 2
sudo systemctl status rentpe --no-pager
