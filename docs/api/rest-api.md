# REST API Reference

## Base URL

```
http://localhost:8000/api/v1
```

## Endpoints

### Points of Interest

#### GET /points

Retrieve points of interest, optionally filtered by category.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| category | string | No | Filter by POI category |

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/points?category=Restaurant"
```

**Example Response:**
```json
[
  {
    "id": 1,
    "name": "Karim's",
    "category": "Restaurant",
    "lat": 28.6506,
    "lon": 77.2334
  },
  {
    "id": 2,
    "name": "Bukhara",
    "category": "Restaurant", 
    "lat": 28.5988,
    "lon": 77.1731
  }
]
```

---

### Areas

#### GET /areas

Retrieve all Delhi administrative areas/districts.

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/areas"
```

**Example Response:**
```json
[
  {
    "id": 1,
    "name": "Central Delhi",
    "geometry": {...}
  },
  {
    "id": 2,
    "name": "North Delhi",
    "geometry": {...}
  }
]
```

---

### Pincodes

#### GET /pincodes

Retrieve all Delhi pincode boundaries.

**Example Request:**
```bash
curl "http://localhost:8000/api/v1/pincodes"
```

**Example Response:**
```json
[
  {
    "id": 1,
    "name": "110001",
    "geometry": {...}
  }
]
```

---

### Chat

#### POST /chat

Send a message to the AI agent and receive a response.

**Request Body:**
```json
{
  "message": "How many restaurants are in the database?"
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "How many restaurants are in the database?"}'
```

**Example Response:**
```json
{
  "response": "There are 28 restaurants in the database.",
  "type": "data",
  "sql": "SELECT COUNT(*) FROM delhi_points WHERE category = 'Restaurant'",
  "results": [{"count": 28}],
  "row_count": 1
}
```

---

## Response Types

### Data Response
When the query returns database results:
```json
{
  "type": "data",
  "response": "Natural language summary",
  "sql": "SELECT ...",
  "results": [...],
  "row_count": 10
}
```

### Message Response
When no database query is needed:
```json
{
  "type": "message",
  "response": "Delhi is the capital of India..."
}
```

### Error Response
When an error occurs:
```json
{
  "type": "error",
  "response": "Error description"
}
```

---

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 500 | Internal Server Error |

---

## Example Queries

### Natural Language Queries

The `/chat` endpoint accepts questions like:

**Data Exploration:**
- "How many POIs are in the database?"
- "Show me all categories of POIs"
- "List the first 10 restaurants"

**Aggregations:**
- "Count POIs by category"
- "What's the most common POI type?"

**Filtering:**
- "Show me all cafes"
- "Find POIs with 'coffee' in the name"

**Spatial Queries:**
- "Show me POIs with their coordinates"
- "List all metro stations"
