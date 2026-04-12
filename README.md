# Nepse Trader Web App

This is a minimal web application using Python FastAPI for the backend and Angular for the frontend.

## Backend

1. Install dependencies:
   ```bash
   python -m pip install -r requirements.txt
   ```
2. Run backend:
   ```bash
   uvicorn app:app --reload
   ```
3. Backend API endpoint:
   - `http://localhost:8000/api/message`

## Frontend

### Option 1: Run locally with Node.js

1. Change to frontend folder:
   ```bash
   cd frontend
   ```
2. Install Node dependencies:
   ```bash
   npm install
   ```
3. Run Angular app:
   ```bash
   npm start
   ```
4. Open the browser at `http://localhost:4200`

### Option 2: Run with Docker Compose (no local npm required)

1. Build and start both services:
   ```bash
   docker compose up --build
   ```
2. Open the browser at `http://localhost:4200`

## Notes

- The frontend fetches a message from the Python backend using a REST API.
- Each button click increments a counter stored in PostgreSQL.
- CORS is enabled for `http://localhost:4200`.
- Docker Compose now includes a `db` PostgreSQL service for persistence.
