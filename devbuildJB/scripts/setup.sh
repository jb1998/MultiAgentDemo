#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== GodSimple Setup ==="

# Backend
echo "Setting up backend..."
cd "$ROOT/backend"
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# Frontend
echo "Setting up frontend..."
cd "$ROOT/frontend"
npm install
cp -n .env.example .env 2>/dev/null || true

echo ""
echo "Setup complete!"
echo ""
echo "Start backend:  cd backend && source venv/bin/activate && python -m app.main"
echo "Start frontend: cd frontend && npm run dev"
echo ""
echo "Demo login: demo / demo1234"
echo "Backend API: http://localhost:8000/api/docs"
echo "Frontend UI: http://localhost:5173"
