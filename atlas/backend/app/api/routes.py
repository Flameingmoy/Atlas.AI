from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.services.analysis import AnalysisService
from app.services.ai_agent import AIAgentService
from app.core.db import get_db_connection
import json

agent = AIAgentService()
router = APIRouter()

@router.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0", "db": "duckdb"}

@router.get("/pois", response_model=List[dict])
def get_pois(category: Optional[str] = None):
    conn = get_db_connection()
    
    query = "SELECT id, name, category, ST_Y(location) as lat, ST_X(location) as lon FROM pois"
    params = []
    
    if category:
        query += " WHERE category = ?"
        params.append(category)
        
    results = conn.execute(query, params).fetchall()
    conn.close()
    
    # Format response
    pois = []
    for r in results:
        pois.append({
            "id": str(r[0]),
            "name": r[1],
            "category": r[2],
            "lat": r[3],
            "lon": r[4]
        })
        
    return pois

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
