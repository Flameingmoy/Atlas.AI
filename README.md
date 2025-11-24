# Atlas.AI 🌍

**Atlas.AI** is an intelligent location intelligence platform designed to de-risk physical business expansion. It combines geospatial data analysis with a conversational AI interface, allowing users to find optimal real estate locations through natural language.

![Atlas Interface](assets/atlas_screenshot.png)

## 🚀 Features

*   **Chat-with-Map Interface:** Ask questions like "Show me high foot traffic areas in Bangalore" and watch the map update instantly.
*   **AI Orchestrator:** Powered by **Ollama (qwen3:32b)** and **LangChain**, converting natural language into spatial actions.
*   **Dynamic Scoring:** Proprietary algorithm scoring locations based on Traffic, Competition, Demand, Access, and Synergy.
*   **H3 Hexagonal Indexing:** Uses Uber's H3 system for superior spatial analysis and data visualization.
*   **Interactive Map:** Built with **React Leaflet** and **CartoDB Dark Matter** tiles for a premium, responsive experience.

## 🛠️ Tech Stack

*   **Frontend:** React (Vite), Tailwind CSS, React Leaflet
*   **Backend:** FastAPI (Python), PostGIS (PostgreSQL), SQLAlchemy/SQLModel
*   **AI/ML:** LangChain, Ollama, Scikit-Learn (DBSCAN Clustering)
*   **Data:** OpenStreetMap (via Overpass/Geofabrik), H3 Indexing

## 📦 Installation

### Prerequisites
*   Python 3.10+
*   Node.js 18+
*   PostgreSQL with PostGIS extension enabled
*   [Ollama](https://ollama.com/) installed and running (`ollama pull qwen3:32b`)

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/Flameingmoy/Atlas.AI.git
cd Atlas.AI

# Create Conda Environment
conda create -n atlas python=3.12 -y
conda activate atlas

# Install Dependencies
pip install -r atlas/backend/requirements.txt
pip install langchain langchain-ollama

# Set up Database (Ensure Postgres is running)
# Update connection string in atlas/scripts/seed_db.py if needed
export PYTHONPATH=$(pwd)/atlas/backend
python atlas/scripts/seed_db.py
```

### 2. Frontend Setup

```bash
cd atlas/frontend

# Install Dependencies
npm install

# Run Development Server
npm run dev
```

### 3. Running the AI Backend

```bash
# From the root directory
conda activate atlas
export PYTHONPATH=$(pwd)/atlas/backend
python atlas/backend/app/main.py
```

## 🎮 Usage

1.  Open the frontend at `http://localhost:5173` (or the port shown in terminal).
2.  The map defaults to **Bangalore, India**.
3.  Use the **Layer Control** (top-left) to toggle Competitors or Heatmaps manually.
4.  Use the **Chat Bar** (bottom) to ask Atlas:
    *   *"Show me the demand heatmap"*
    *   *"Where are the competitors?"*
    *   *"What are the demographics of Bangalore?"*

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
