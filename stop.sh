#!/bin/bash

# MJ-ITAD Full Stack Stop Script
# Stops the frontend (Ctrl+C), backend, and PostgreSQL

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
  echo -e "${BLUE}ℹ ${1}${NC}"
}

log_success() {
  echo -e "${GREEN}✓ ${1}${NC}"
}

echo "=========================================="
echo "Stopping MJ-ITAD services..."
echo "=========================================="
echo

# Stop Frontend
frontend_pids=$( (lsof -tiTCP:3000 -sTCP:LISTEN 2>/dev/null || true; lsof -tiTCP:3001 -sTCP:LISTEN 2>/dev/null || true) | cat )
if [ -n "$frontend_pids" ]; then
  log_info "Stopping frontend dev server on ports 3000/3001..."
  echo "$frontend_pids" | sort -u | xargs kill >/dev/null 2>&1 || true
  log_success "Frontend stopped"
else
  echo "Frontend already stopped"
fi

# Stop Backend
if docker ps --format '{{.Names}}' | grep -qx 'mj-itad-backend'; then
  log_info "Stopping backend..."
  docker stop mj-itad-backend > /dev/null
  log_success "Backend stopped"
else
  echo "Backend already stopped"
fi

# Stop Database
if docker ps --format '{{.Names}}' | grep -qx 'mj-itad-db'; then
  log_info "Stopping database..."
  docker stop mj-itad-db > /dev/null
  log_success "Database stopped"
else
  echo "Database already stopped"
fi

echo
log_success "All services stopped"
echo
echo "To restart all services, run: ./start.sh"
