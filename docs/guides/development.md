# Development Guide

## Project Structure

```
Atlas.AI/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── api/routes.py        # REST endpoints
│   │   ├── core/db.py           # Database init
│   │   ├── models/schema.py     # Data models
│   │   └── services/
│   │       ├── ai_agent.py      # LangChain agent
│   │       ├── text_to_sql_service.py
│   │       ├── analysis.py
│   │       └── latlong_client.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/
│   │   │   ├── Map.jsx
│   │   │   └── LayerControl.jsx
│   │   └── services/api.js
│   ├── package.json
│   └── Dockerfile
├── scripts/
│   ├── seed_db.py
│   └── test_api.py
├── data/
│   └── Delhi_Areas_All_11_Criteria_Real_Data.csv
├── docs/
└── docker-compose.yml
```

## Development Workflow

### Running Locally

**Terminal 1 - Backend:**
```bash
cd backend
python -m app.main
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Hot Reloading

- Backend: Uvicorn automatically reloads on file changes
- Frontend: Vite provides instant HMR

## Adding New Features

### Adding a New API Endpoint

1. Edit `backend/app/api/routes.py`:

```python
@router.get("/your-endpoint")
async def your_endpoint():
    # Your logic here
    return {"data": result}
```

2. Access at `http://localhost:8000/api/v1/your-endpoint`

### Adding a New AI Tool

1. Edit `backend/app/services/ai_agent.py`:

```python
@tool
def your_new_tool(param: str) -> str:
    """Description of what this tool does."""
    # Your logic here
    return result
```

2. Add to agent's tools list

### Adding a New POI Category

1. Update seed script with new category
2. Add color mapping in `frontend/src/components/Map.jsx`:

```javascript
const colorMap = {
  // ... existing
  'YourCategory': '#HexCode',
};
```

### Adding a New Frontend Component

1. Create component in `frontend/src/components/`
2. Import and use in `App.jsx` or `Map.jsx`

## Testing

### Backend Tests

```bash
cd backend
python test_text_to_sql.py
```

### API Testing

```bash
python scripts/test_api.py
```

### Manual Testing

```bash
# Test points endpoint
curl http://localhost:8000/api/v1/points

# Test chat
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "List all restaurants"}'
```

## Debugging

### Backend Logging

FastAPI logs requests to console. For verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Frontend Debugging

1. Open browser DevTools (F12)
2. Check Console for errors
3. Network tab for API calls

### Database Debugging

```python
import duckdb
conn = duckdb.connect('data/atlas.duckdb')

# Check tables
print(conn.execute("SHOW TABLES").fetchall())

# Check data
print(conn.execute("SELECT * FROM delhi_points LIMIT 5").fetchdf())
```

## Code Style

### Python
- Use type hints
- Follow PEP 8
- Use meaningful variable names

### JavaScript/React
- Use functional components with hooks
- Use Tailwind CSS for styling
- Keep components small and focused

## Dependencies

### Adding Backend Dependencies

```bash
pip install new-package
pip freeze > backend/requirements.txt
```

### Adding Frontend Dependencies

```bash
cd frontend
npm install new-package
```

## Docker Development

### Build Images

```bash
docker-compose build
```

### Run with Logs

```bash
docker-compose up
```

### Rebuild Single Service

```bash
docker-compose up --build backend
```
