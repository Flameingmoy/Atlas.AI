# Technical Design Document

## 1. System Architecture

### Frontend Architecture

```
src/
├── App.jsx              # Main app with chat interface
├── components/
│   ├── Map.jsx          # Leaflet map with POI rendering
│   └── LayerControl.jsx # Toggle layers visibility
├── services/
│   └── api.js           # Backend API client
└── mapboxSetup.js       # Map tile configuration
```

### Backend Architecture

```
app/
├── main.py              # FastAPI application entry
├── api/
│   └── routes.py        # REST API endpoints
├── core/
│   └── db.py            # Database initialization
├── models/
│   └── schema.py        # Data models
└── services/
    ├── ai_agent.py          # LangChain agent with tools
    ├── analysis.py          # Data analysis utilities
    ├── text_to_sql_service.py # NL to SQL conversion
    └── latlong_client.py    # Map tile client
```

## 2. Database Design

### Schema Overview

All tables use DuckDB with spatial extensions for geometry support.

#### delhi_city
```sql
CREATE TABLE delhi_city (
    id INTEGER,
    name VARCHAR,
    geom GEOMETRY
);
```

#### delhi_area
```sql
CREATE TABLE delhi_area (
    id INTEGER,
    name VARCHAR,
    geom GEOMETRY
);
```

#### delhi_pincode
```sql
CREATE TABLE delhi_pincode (
    id INTEGER,
    name VARCHAR,
    geom GEOMETRY
);
```

#### delhi_points
```sql
CREATE TABLE delhi_points (
    id INTEGER,
    name VARCHAR,
    category VARCHAR,
    geom GEOMETRY
);
```

### Spatial Operations

- `ST_Y(geom)` - Extract latitude
- `ST_X(geom)` - Extract longitude
- `ST_Point(lon, lat)` - Create point geometry
- `ST_SetSRID(geom, 4326)` - Set coordinate reference system

## 3. AI Agent Design

### Agent Architecture

The AI agent uses LangChain with function calling to provide intelligent responses.

```python
@tool
def query_database(question: str):
    """Query the database using natural language."""
    # Converts NL to SQL using Groq
    # Executes query on DuckDB
    # Returns summarized results

@tool  
def get_delhi_info():
    """Get general information about Delhi."""
    # Returns static Delhi information
```

### Text-to-SQL Pipeline

```
┌─────────────────┐
│ User Question   │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Schema Context  │ ← Extract from DuckDB
└────────┬────────┘
         ▼
┌─────────────────┐
│ LLM (Groq)      │ ← JSON mode for structured output
└────────┬────────┘
         ▼
┌─────────────────┐
│ SQL Query       │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Execute Query   │ ← Auto-fix on error
└────────┬────────┘
         ▼
┌─────────────────┐
│ NL Summary      │
└─────────────────┘
```

## 4. API Design

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/points` | Get points of interest |
| GET | `/api/v1/areas` | Get Delhi areas/districts |
| GET | `/api/v1/pincodes` | Get pincode boundaries |
| POST | `/api/v1/chat` | Send chat message to AI agent |

### Response Format

```json
{
  "type": "data|message|error",
  "content": "...",
  "sql": "SELECT ...",
  "results": [...],
  "row_count": 10
}
```

## 5. Frontend Design

### Map Configuration

- **Center**: Delhi (28.6139, 77.2090)
- **Default Zoom**: 13 (city-level)
- **Tile Source**: Latlong vector tiles

### POI Color Scheme

| Category | Color | Hex |
|----------|-------|-----|
| Restaurant | Red | #EF4444 |
| Cafe | Amber | #F59E0B |
| Mall | Purple | #8B5CF6 |
| Monument | Green | #10B981 |
| Market | Pink | #EC4899 |
| Hospital | Blue | #3B82F6 |
| Metro Station | Orange | #F97316 |

### UI Components

1. **Map Canvas** - Full-screen interactive map
2. **Chat Bar** - Bottom overlay for queries
3. **Layer Control** - Top-left toggle panel
4. **Legend** - Bottom-right category colors

## 6. Data Flow

### Query Flow

```
1. User types question in chat bar
2. Frontend sends POST to /api/v1/chat
3. AI Agent receives message
4. Agent calls query_database tool if needed
5. TextToSQLService generates SQL via Groq
6. SQL executed on DuckDB
7. Results summarized by LLM
8. Response returned to frontend
9. Chat UI displays answer + data table
```

### Map Update Flow

```
1. User toggles layer or receives chat response
2. Frontend fetches data from API endpoints
3. POIs rendered as CircleMarkers
4. Colors applied based on category
5. Popups attached for interaction
```
