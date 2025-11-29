from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.routes import router
from app.core.db import init_postgis_schema, init_pool, close_pool

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize PostGIS connection pool and schema on startup, cleanup on shutdown."""
    # Startup
    init_pool()
    init_postgis_schema()
    print("PostGIS connection pool initialized and schema ready")
    yield
    # Shutdown
    close_pool()
    print("PostGIS connection pool closed")

app = FastAPI(title="Atlas API", version="0.1.0", lifespan=lifespan)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for prototype
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
