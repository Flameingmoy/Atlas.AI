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

@router.get("/points", response_model=List[dict])
def get_points(category: Optional[str] = None):
    """
    Get points of interest from delhi_points table
    """
    conn = get_db_connection()
    
    query = "SELECT id, name, category, ST_Y(geom) as lat, ST_X(geom) as lon FROM delhi_points"
    params = []
    
    if category:
        query += " WHERE category = ?"
        params.append(category)
        
    results = conn.execute(query, params).fetchall()
    conn.close()
    
    # Format response
    points = []
    for r in results:
        points.append({
            "id": r[0],
            "name": r[1],
            "category": r[2],
            "lat": r[3],
            "lon": r[4]
        })
        
    return points

@router.get("/areas", response_model=List[dict])
def get_areas():
    """
    Get all areas/districts from delhi_area table
    """
    conn = get_db_connection()
    
    query = "SELECT id, name FROM delhi_area"
    results = conn.execute(query).fetchall()
    conn.close()
    
    areas = []
    for r in results:
        areas.append({
            "id": r[0],
            "name": r[1]
        })
        
    return areas

@router.get("/pincodes", response_model=List[dict])
def get_pincodes():
    """
    Get all pincodes from delhi_pincode table
    """
    conn = get_db_connection()
    
    query = "SELECT id, name FROM delhi_pincode"
    results = conn.execute(query).fetchall()
    conn.close()
    
    pincodes = []
    for r in results:
        pincodes.append({
            "id": r[0],
            "pincode": r[1]
        })
        
    return pincodes

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
