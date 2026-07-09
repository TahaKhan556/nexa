#!/bin/bash
set -e

echo "=== Nexa Setup ==="

# Create data directories
mkdir -p data/sessions logs

# Setup Python virtual environment
echo "[1/5] Setting up Python backend..."
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt -q
python -m playwright install chromium
deactivate
cd ..

# Setup Next.js frontend
echo "[2/5] Setting up Next.js frontend..."
cd frontend
npm install --silent
cd ..

echo "[3/5] Building frontend..."
cd frontend
npm run build
cd ..

echo "[4/5] Starting services with PM2..."
pm2 delete nexa-frontend nexa-backend 2>/dev/null || true
cd /home/projects/nexa
pm2 start ecosystem.config.js
pm2 save

echo "[5/5] Done!"
echo ""
echo "Frontend: http://localhost:3500"
echo "Backend:  http://localhost:8200"
echo ""
echo "To login to NotebookLM: cd backend && source venv/bin/activate && python login.py"
echo "To check status: pm2 list"
