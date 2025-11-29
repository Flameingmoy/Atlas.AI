# Atlas.AI 🌍

**Atlas.AI** is an AI-powered location intelligence platform for exploring and analyzing geographic data. It combines interactive maps with a conversational AI interface, allowing users to query data using natural language.

## ✨ Features

- **Chat-with-Map Interface** - Ask questions like "How many restaurants are in the database?" and get instant results
- **Text-to-SQL** - Natural language queries automatically converted to SQL using Groq's LLM
- **Interactive Map** - Explore Delhi's geographic data with color-coded POI markers
- **Real-time Visualization** - Dynamic rendering of areas, pincodes, and points of interest

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, Vite, Tailwind CSS, MapLibre GL |
| Backend | FastAPI, Python 3.11+ |
| AI/LLM | LangChain, Groq (llama-3.3-70b) |
| Database | PostgreSQL + PostGIS (with connection pooling) |
| External APIs | LatLong.ai (geocoding, isochrones, POI) |
| Deployment | Docker, Docker Compose |

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/Flameingmoy/Atlas.AI.git
cd Atlas.AI

# Create environment file with your API keys
cp .env.example .env
# Edit .env and add your GROQ_API_KEY and LATLONG_TOKEN

# Start all services (PostGIS, Backend, Frontend)
docker compose up -d

# Migrate data from DuckDB to PostGIS (first time only)
./scripts/migrate.sh

# Access the application
# Frontend: http://localhost:8080
# Backend:  http://localhost:8000
# PostGIS:  localhost:5433
```

### Database Migration (For Teammates)

If your PostGIS database is empty, run the migration script to populate it from DuckDB:

```bash
# Make sure PostGIS is running
docker compose up -d db

# Run migration (reads from data/delhi.db, writes to PostGIS)
./scripts/migrate.sh

# Or start PostGIS and migrate in one command
./scripts/migrate.sh --start-db
```

The migration script will:
- Create all required tables with PostGIS geometry columns
- Migrate 314,000+ POIs from DuckDB
- Create spatial indexes for fast queries

### Manual Installation

```bash
# Backend
pip install -r backend/requirements.txt
python scripts/seed_db.py
cd backend && python -m app.main

# Frontend (in another terminal)
cd frontend && npm install && npm run dev
```

## 📖 Usage

1. Open `http://localhost:8080` in your browser
2. The map displays Delhi, India with color-coded POI markers
3. **Search** for locations using the search bar (top center)
4. **Click** anywhere on the map to get address info and nearby landmarks
5. **Isochrone Analysis** - Select a distance to see reachable areas
6. Use the **chat bar** at the bottom to ask questions:
   - "How many restaurants are there?"
   - "Show me all categories of POIs"
   - "List cafes with their coordinates"
7. Toggle map layers using the **layer control** (top-left)

## 🗂️ Project Structure

```
Atlas.AI/
├── backend/           # FastAPI backend
│   └── app/
│       ├── api/       # REST endpoints
│       ├── core/      # Database setup
│       ├── models/    # Data models
│       └── services/  # AI agent, text-to-sql
├── frontend/          # React frontend
│   └── src/
│       ├── components/  # Map, LayerControl
│       └── services/    # API client
├── scripts/           # Database seeding
├── data/              # Sample data files
└── docs/              # Documentation
```

## 📚 Documentation

### Architecture
- [Overview](docs/architecture/overview.md) - System architecture, tech stack, and core concepts
- [Technical Design](docs/architecture/design.md) - Detailed design document with diagrams

### Setup
- [Installation Guide](docs/setup/installation.md) - Get started with Docker or manual installation
- [Database Seeding](docs/setup/database-seeding.md) - Populate the database with sample data
- [Map Configuration](docs/setup/map-configuration.md) - Configure map tiles and POI colors

### API Reference
- [Database Schema](docs/api/database-schema.md) - Table definitions and spatial queries
- [REST API](docs/api/rest-api.md) - Endpoint documentation with examples
- [Text-to-SQL](docs/api/text-to-sql.md) - Natural language query implementation

### Guides
- [Development Guide](docs/guides/development.md) - Contributing and extending the platform
- [Migration Notes](docs/guides/migration-notes.md) - Schema changes and version history

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GROQ_API_KEY` | Groq API key for LLM | Yes |
| `LATLONG_TOKEN` | LatLong.ai API token | Yes |
| `DB_HOST` | PostGIS host | No (default: `localhost`) |
| `DB_PORT` | PostGIS port | No (default: `5433`) |
| `DB_USER` | PostGIS user | No (default: `atlas`) |
| `DB_PASSWORD` | PostGIS password | No (default: `atlas_secret`) |
| `DB_NAME` | PostGIS database | No (default: `atlas_db`) |
| `DUCKDB_PATH` | DuckDB source file for migration | No (default: `./data/delhi.db`) |

Get API keys at:
- Groq: [console.groq.com](https://console.groq.com)
- LatLong.ai: [latlong.ai](https://latlong.ai)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
