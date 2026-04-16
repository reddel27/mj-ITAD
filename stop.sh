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
