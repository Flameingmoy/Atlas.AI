# Technical Design Document: Project Atlas

## 1. System Architecture

### High-Level Stack
* **Frontend:** React (Vite) + Tailwind CSS
    * *Map Engine:* Mapbox GL JS (preferred for vector tile performance) or Deck.gl (for heavy data visualization).
    * *State Management:* TanStack Query (React Query) + Zustand.
* **Backend:** Python (FastAPI)
    * *Reasoning:* Python is the native language of geospatial data science (GeoPandas, PySAL, Scikit-learn).
* **Database:** PostgreSQL + PostGIS Extension
    * *Reasoning:* The gold standard for spatial indexing and complex geometric queries.
* **AI/LLM Layer:** OpenAI API (GPT-4o) or Anthropic (Claude 3.5 Sonnet)
    * *Integration:* LangChain for orchestration + Function Calling for map control.

### Architecture Diagram
[Client: React App] <--> [API Gateway: FastAPI] <--> [Orchestrator: LangChain]
                                      |
                                      +--> [DB: PostGIS]
                                      |
                                      +--> [Worker: Celery/Redis] (For heavy clustering tasks)

## 2. Database Schema (Key Entities)

### `pois` (Points of Interest)
* `id`: UUID
* `name`: String
* `category`: String (Hierarchical)
* `location`: GEOMETRY(POINT, 4326)
* `metadata`: JSONB (Opening hours, rating, price_tier)

### `demographics` (Grid/Polygon Data)
* `id`: UUID
* `boundary`: GEOMETRY(POLYGON, 4326)
* `population_density`: Float
* `median_income`: Integer
* `traffic_score`: Float

### `analyses` (User Saved Sessions)
* `id`: UUID
* `user_id`: UUID
* `search_criteria`: JSONB (The query parameters)
* `result_clusters`: JSONB (Cached results)
* `ai_narrative`: Text (The generated report)

## 3. The Analysis Pipeline

### Step A: Data Fetching & Filtering
1.  User request converts to Bounding Box (BBOX) coordinates.
2.  **PostGIS Query:** `ST_DWithin` (Distance) and `ST_Contains` (Polygon lookups).

### Step B: Clustering Logic (Scikit-Learn)
1.  **Input:** Lat/Lon array of relevant competitors.
2.  **Algorithm:** `DBSCAN(eps=0.5km, min_samples=3)` to find high-density clusters.
3.  **Output:** Cluster centroids and noise points (potential white spaces).

### Step C: Scoring (Pandas/NumPy)
1.  Normalize all metrics (0-1 scale).
2.  Apply weights defined in User Preferences.
3.  Assign score to specific grid cells or candidate properties.

## 4. AI Agent Workflow (Function Calling)

The LLM is not just a chatbot; it has tools.
* **`get_demographics(lat, lon, radius)`**: Returns census data.
* **`find_competitors(category, bounds)`**: Returns competitor count/locations.
* **`calculate_isochrone(lat, lon, minutes, mode)`**: Returns accessible polygon.

**Flow:**
1.  User: "Find a coffee spot in Austin."
2.  LLM: Calls `geocode("Austin")`.
3.  LLM: Calls `find_competitors("coffee", austin_bounds)`.
4.  LLM: Calls `analyze_gaps(competitor_data)`.
5.  LLM: Returns response + triggers UI to render specific Map Layers.

## 5. UI/UX Philosophy
* **Map-First Design:** The map is the canvas. The chat is the overlay.
* **Progressive Disclosure:** Start with simple heatmaps. Allow users to click for deep-dive metrics.
* **Latency Handling:** Heavy clustering takes time (1-3s). Use "Skeleton Loaders" on the map or have the AI say "I'm crunching the numbers on density now..." to fill the silence.