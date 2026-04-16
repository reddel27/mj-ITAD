# MJ-ITAD Setup

## Quick Start

Start all services with a single command:

```bash
cd /workspaces/mj-ITAD-1
./start.sh
```

This will:
- Create the Docker network (if needed)
- Start PostgreSQL
- Build and start the backend API
- Initialize the database schema
- Start the frontend dev server

Once running:
- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:8000
- **Database:** localhost:5432

To stop all services:
```bash
./stop.sh
```

Then press Ctrl+C to stop the frontend (which runs in foreground).

---

## Manual Setup

If you prefer to set up services manually, follow the steps below.

## Database Setup

1. Start PostgreSQL with Docker:
   ```bash
   docker network create mj-itad-net
   docker run --name mj-itad-db --network mj-itad-net -e POSTGRES_PASSWORD=password -e POSTGRES_DB=mj_itad -p 5432:5432 -d postgres:15
   ```

2. Verify container is running:
   ```bash
   docker ps
   ```

## Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Build and run backend with Docker:
   ```bash
   docker build -t mj-itad-backend .
   docker run --name mj-itad-backend --network mj-itad-net -e DATABASE_URL=postgresql://postgres:password@mj-itad-db:5432/mj_itad -e ALLOWED_ORIGINS=http://localhost:3000 -p 8000:8000 -d mj-itad-backend
   ```

3. Optional backend environment variables:
   - `GOOGLE_MAPS_API_KEY`: Required for live Google Places results
   - `ENABLE_MOCK_DISPENSARIES=true`: Enables mock dispensary fallback for local dev only
   - `ALLOWED_ORIGINS`: Comma-separated CORS origins

4. Initialize database tables:
   ```bash
   docker exec mj-itad-backend python init_db.py
   ```

5. Test API:
   ```bash
   curl http://localhost:8000/
   curl "http://localhost:8000/dispensaries?lat=37.7749&lng=-122.4194&radius=5000"
   ```

6. Run backend tests:
   ```bash
   cd backend
   pytest -q
   ```

## Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables in `.env.local`:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_GOOGLE_MAPS_API_KEY=<your-browser-maps-key>
   ```

4. Run development server:
   ```bash
   npm run dev
   ```