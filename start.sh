#!/bin/bash

# MJ-ITAD Full Stack Setup Script
# Starts PostgreSQL (Docker), Backend (Docker), and Frontend (npm)

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "=========================================="
echo "MJ-ITAD Full Stack Startup"
echo "=========================================="
echo

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
  echo -e "${BLUE}ℹ ${1}${NC}"
}

log_success() {
  echo -e "${GREEN}✓ ${1}${NC}"
}

log_warning() {
  echo -e "${YELLOW}⚠ ${1}${NC}"
}

BACKEND_DATABASE_URL="postgresql://postgres:password@mj-itad-db:5432/mj_itad"
BACKEND_ALLOWED_ORIGINS="http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001"

stop_frontend_ports() {
  local frontend_pids
  frontend_pids=$( (lsof -tiTCP:3000 -sTCP:LISTEN 2>/dev/null || true; lsof -tiTCP:3001 -sTCP:LISTEN 2>/dev/null || true) | cat )
  if [ -n "$frontend_pids" ]; then
    log_warning "Stopping existing frontend listeners on ports 3000/3001..."
    echo "$frontend_pids" | sort -u | xargs kill >/dev/null 2>&1 || true
    sleep 1
  fi
}

backend_container_needs_recreate() {
  if ! docker ps -a --format '{{.Names}}' | grep -qx 'mj-itad-backend'; then
    return 0
  fi

  local current_env
  current_env=$(docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' mj-itad-backend 2>/dev/null || true)
  if ! printf '%s\n' "$current_env" | grep -qx "DATABASE_URL=$BACKEND_DATABASE_URL"; then
    return 0
  fi

  if ! printf '%s\n' "$current_env" | grep -qx "ALLOWED_ORIGINS=$BACKEND_ALLOWED_ORIGINS"; then
    return 0
  fi

  if ! docker inspect -f '{{json .NetworkSettings.Networks}}' mj-itad-backend 2>/dev/null | grep -q 'mj-itad-net'; then
    return 0
  fi

  return 1
}

# Check Docker is available
if ! command -v docker &> /dev/null; then
  echo "Docker is not installed or not in PATH. Please install Docker."
  exit 1
fi

# ====================
# 1. Setup Docker Network
# ====================
log_info "Setting up Docker network..."
if ! docker network inspect mj-itad-net &> /dev/null; then
  docker network create mj-itad-net
  log_success "Created Docker network: mj-itad-net"
else
  log_success "Docker network already exists: mj-itad-net"
fi
echo

# ====================
# 2. Start PostgreSQL
# ====================
log_info "Starting PostgreSQL database..."
if docker ps -a --format '{{.Names}}' | grep -qx 'mj-itad-db'; then
  if docker ps --format '{{.Names}}' | grep -qx 'mj-itad-db'; then
    log_success "PostgreSQL is already running"
  else
    log_info "Restarting PostgreSQL..."
    docker start mj-itad-db
    sleep 2
    log_success "PostgreSQL started"
  fi
else
  log_info "Creating and starting PostgreSQL container..."
  docker run \
    --name mj-itad-db \
    --network mj-itad-net \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=mj_itad \
    -p 5432:5432 \
    -d postgres:15 > /dev/null
  sleep 3
  log_success "PostgreSQL started"
fi
echo

# ====================
# 3. Build and Start Backend
# ====================
log_info "Building backend Docker image..."
cd "$PROJECT_ROOT/backend"
docker build -t mj-itad-backend . > /dev/null 2>&1
log_success "Backend image built"

log_info "Starting backend container..."
if backend_container_needs_recreate; then
  if docker ps -a --format '{{.Names}}' | grep -qx 'mj-itad-backend'; then
    log_warning "Recreating backend container to apply current config..."
    docker rm -f mj-itad-backend > /dev/null
  fi
  docker run \
    --name mj-itad-backend \
    --network mj-itad-net \
    -e DATABASE_URL=$BACKEND_DATABASE_URL \
    -e ALLOWED_ORIGINS=$BACKEND_ALLOWED_ORIGINS \
    -p 8000:8000 \
    -d mj-itad-backend > /dev/null
  sleep 2
  log_success "Backend started"
elif docker ps --format '{{.Names}}' | grep -qx 'mj-itad-backend'; then
  log_success "Backend is already running with current config"
else
  log_info "Starting existing backend container..."
  docker start mj-itad-backend > /dev/null
  sleep 2
  log_success "Backend started"
fi

log_info "Initializing database schema..."
docker exec mj-itad-backend python init_db.py > /dev/null 2>&1
log_success "Database initialized"

log_info "Applying database migrations..."
docker exec mj-itad-backend python migrate_db.py > /dev/null 2>&1
log_success "Migrations applied"
echo

# ====================
# 4. Start Frontend
# ====================
log_info "Starting frontend development server..."
cd "$PROJECT_ROOT/frontend"

stop_frontend_ports

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
  log_info "Installing frontend dependencies..."
  npm install > /dev/null 2>&1
  log_success "Dependencies installed"
fi

# Start the dev server in background
npm run dev &
FRONTEND_PID=$!
sleep 5

# Check if terminal is interactive
if [ -t 0 ]; then
  log_success "Frontend started (PID: $FRONTEND_PID)"
else
  log_success "Frontend started"
fi
echo

# ====================
# 5. Health Checks
# ====================
echo "=========================================="
echo "Verifying services..."
echo "=========================================="
echo

# Check PostgreSQL
if docker ps --format '{{.Names}}' | grep -qx 'mj-itad-db'; then
  log_success "PostgreSQL is running on localhost:5432"
else
  log_warning "PostgreSQL may not be healthy"
fi

# Check Backend
if curl -s http://localhost:8000/ > /dev/null 2>&1; then
  log_success "Backend is running on http://localhost:8000"
else
  log_warning "Backend may not be ready yet (it can take a few seconds)"
fi

# Check Frontend
if curl -s http://localhost:3000/ > /dev/null 2>&1; then
  log_success "Frontend is running on http://localhost:3000"
else
  log_warning "Frontend may not be ready yet (it can take a few seconds)"
fi

echo
echo "=========================================="
echo "MJ-ITAD is ready!"
echo "=========================================="
echo
echo "Open your browser to:"
echo "  ${GREEN}http://localhost:3000${NC}"
echo
echo "Available endpoints:"
echo "  Frontend:  http://localhost:3000"
echo "  Backend:   http://localhost:8000"
echo "  Database:  localhost:5432"
echo
echo "To stop all services, run: docker stop mj-itad-backend mj-itad-db && fg"
echo "To view backend logs: docker logs -f mj-itad-backend"
echo "To view database logs: docker logs -f mj-itad-db"
echo
echo "Frontend is running in foreground. Press Ctrl+C to stop it."
echo "Database and backend will continue running in Docker."
echo "=========================================="

# Wait for frontend to finish
wait $FRONTEND_PID
