# Installation Guide

## Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **Docker & Docker Compose** (optional, for containerized deployment)
- **Groq API Key** (for text-to-SQL functionality)

## Quick Start with Docker

The easiest way to run Atlas.AI is using Docker Compose:

```bash
# Clone the repository
git clone https://github.com/Flameingmoy/Atlas.AI.git
cd Atlas.AI

# Create environment file
cp .env.example .env
# Edit .env and add your GROQ_API_KEY

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
```

## Manual Installation

### 1. Backend Setup

```bash
# Navigate to project root
cd Atlas.AI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r backend/requirements.txt

# Set environment variables
export GROQ_API_KEY=your_groq_api_key_here
export DATABASE_PATH=data/atlas.duckdb

# Initialize and seed database
python scripts/seed_db.py

# Run the backend
cd backend
python -m app.main
```

Backend will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
# In a new terminal
cd Atlas.AI/frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will be available at `http://localhost:5173`

## Environment Variables

Create a `.env` file in the project root:

```env
# Required
GROQ_API_KEY=your_groq_api_key_here

# Optional
DATABASE_PATH=data/atlas.duckdb
```

### Getting a Groq API Key

1. Sign up at [console.groq.com](https://console.groq.com)
2. Navigate to API Keys section
3. Create a new API key
4. Copy and add to your `.env` file

## Database Seeding

The seed script populates the database with sample Delhi data:

```bash
python scripts/seed_db.py
```

This creates:
- 1 city boundary (Delhi)
- 11 administrative areas
- 30 pincode boundaries
- 200+ points of interest

## Verify Installation

### Test Backend

```bash
# Health check
curl http://localhost:8000/api/v1/points

# Test chat
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How many restaurants are there?"}'
```

### Test Text-to-SQL

```bash
cd backend
python test_text_to_sql.py
```

## Troubleshooting

### Backend won't start

1. Check Python version: `python --version` (need 3.10+)
2. Verify all dependencies: `pip install -r backend/requirements.txt`
3. Check GROQ_API_KEY is set: `echo $GROQ_API_KEY`

### Frontend won't start

1. Check Node version: `node --version` (need 18+)
2. Clear node_modules: `rm -rf node_modules && npm install`

### Database errors

1. Ensure DuckDB spatial extension loads:
   ```python
   import duckdb
   conn = duckdb.connect()
   conn.execute("INSTALL spatial; LOAD spatial;")
   ```

2. Re-run seed script:
   ```bash
   python scripts/seed_db.py
   ```

### CORS errors

Ensure backend is running before frontend, or check that CORS middleware is configured in `backend/app/main.py`.
