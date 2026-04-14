# MJ-ITAD Setup

## Database Setup

1. Start PostgreSQL with Docker:
   ```bash
   docker run --name mj-itad-db -e POSTGRES_PASSWORD=password -e POSTGRES_DB=mj_itad -p 5432:5432 -d postgres:15
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
   docker run --name mj-itad-backend --link mj-itad-db:db -p 8000:8000 -d mj-itad-backend
   ```

3. Initialize database tables:
   ```bash
   docker exec mj-itad-backend python init_db.py
   ```

4. Test API:
   ```bash
   curl http://localhost:8000/
   curl "http://localhost:8000/dispensaries?lat=37.7749&lng=-122.4194&radius=5000"
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

3. Run development server:
   ```bash
   npm run dev
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

3. Set up environment variables in `.env.local`

4. Run the development server:
   ```bash
   npm run dev
   ```