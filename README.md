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
| Frontend | React 19, Vite, Tailwind CSS, Leaflet |
| Backend | FastAPI, Python 3.10+ |
| AI/LLM | LangChain, Groq (llama-3.3-70b) |
| Database | DuckDB with spatial extensions |
| Deployment | Docker, Docker Compose |

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/Flameingmoy/Atlas.AI.git
cd Atlas.AI

# Create environment file
echo "GROQ_API_KEY=your_api_key_here" > .env

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
```

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

1. Open `http://localhost:5173` in your browser
2. The map displays Delhi, India with POI markers
3. Use the **chat bar** at the bottom to ask questions:
   - "How many restaurants are there?"
   - "Show me all categories of POIs"
   - "List cafes with their coordinates"
4. Toggle map layers using the **layer control** (top-left)

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
| `DATABASE_PATH` | DuckDB database path | No (default: `data/atlas.duckdb`) |

Get a Groq API key at [console.groq.com](https://console.groq.com)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
