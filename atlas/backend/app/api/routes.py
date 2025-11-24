from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List, Optional
from app.models.schema import POI, Demographic
from app.services.analysis import AnalysisService
from app.services.ai_agent import AIAgentService
from geoalchemy2.shape import to_shape

agent = AIAgentService()

# Placeholder for DB session dependency
# In a real app, this would be in app.core.db
def get_session():
    # This is a stub. In production, use a real session generator.
    # from app.core.db import engine
    # with Session(engine) as session:
    #     yield session
    pass

router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0"}

@router.get("/pois", response_model=List[dict])
def get_pois(category: Optional[str] = None):
    # Mock response for prototype if DB isn't connected in this context
    # In real implementation:
    # query = select(POI)
    # if category:
    #     query = query.where(POI.category == category)
    # results = session.exec(query).all()
    # return results
    return [{"id": "mock-id", "name": "Mock POI", "lat": 30.26, "lon": -97.74}]

@router.post("/analyze/score")
def calculate_score(
    traffic: float,
    competition: float,
    demand: float,
    access: float,
    synergy: float
):
    score = AnalysisService.calculate_score(traffic, competition, demand, access, synergy)
    return {"score": score, "grade": "A" if score > 8 else "B" if score > 6 else "C"}

@router.post("/analyze/clusters")
def analyze_clusters(locations: List[List[float]]):
    """
    Input: List of [lat, lon]
    """
    result = AnalysisService.cluster_competitors(locations)
    return result

@router.post("/chat")
def chat(message: dict):
    """
    Input: {"message": "Show me competitors"}
    Output: {"text": "...", "actions": [...]}
    """
    user_text = message.get("message", "")
    response = agent.process_message(user_text)
    return response
