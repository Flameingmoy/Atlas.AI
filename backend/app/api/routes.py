from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from app.services.analysis import AnalysisService
from app.services.ai_agent import AIAgentService
from app.services.latlong_client import LatLongClient
from app.services.business_location_agent import get_business_location_agent
from app.core.db import get_db_cursor, execute_query
from cachetools import TTLCache
from functools import wraps
import hashlib
import json

agent = AIAgentService()
latlong_client = LatLongClient()
router = APIRouter()

# Request models
class LocationRecommendRequest(BaseModel):
    query: str
    radius_km: float = 1.0

# ============================================
# Backend Caching Layer
# ============================================

# Cache instances with different TTLs
viewport_cache = TTLCache(maxsize=200, ttl=30)        # 30 sec for viewport queries
search_cache = TTLCache(maxsize=500, ttl=300)         # 5 min for searches
static_cache = TTLCache(maxsize=100, ttl=3600)        # 1 hour for static data
external_cache = TTLCache(maxsize=300, ttl=600)       # 10 min for external API calls

def make_cache_key(*args, **kwargs):
    """Generate a hash key from function arguments"""
    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
    return hashlib.md5(key_data.encode()).hexdigest()

def cached(cache_instance):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = make_cache_key(func.__name__, *args, **kwargs)
            if key in cache_instance:
                return cache_instance[key]
            result = func(*args, **kwargs)
            cache_instance[key] = result
            return result
        return wrapper
    return decorator

@router.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1.0", "db": "postgis"}

@router.get("/cache/stats")
def cache_stats():
    """Get cache statistics for monitoring"""
    return {
        "viewport": {"size": len(viewport_cache), "maxsize": viewport_cache.maxsize},
        "search": {"size": len(search_cache), "maxsize": search_cache.maxsize},
        "static": {"size": len(static_cache), "maxsize": static_cache.maxsize},
        "external": {"size": len(external_cache), "maxsize": external_cache.maxsize}
    }

@router.get("/points", response_model=List[dict])
def get_points(category: Optional[str] = None, limit: int = 2000):
    """
    Get points of interest from delhi_points table.
    Only returns points within Delhi bounds and limited to prevent memory issues.
    """
    return _get_points_cached(category, limit)

@cached(search_cache)
def _get_points_cached(category: Optional[str], limit: int):
    # Delhi bounding box (approximate)
    min_lat, max_lat = 28.4, 28.9
    min_lon, max_lon = 76.8, 77.4
    
    if category:
        query = """
            SELECT id, name, category, ST_Y(geom) as lat, ST_X(geom) as lon 
            FROM delhi_points
            WHERE ST_Y(geom) BETWEEN %s AND %s
            AND ST_X(geom) BETWEEN %s AND %s
            AND category = %s
            LIMIT %s
        """
        params = (min_lat, max_lat, min_lon, max_lon, category, limit)
    else:
        query = """
            SELECT id, name, category, ST_Y(geom) as lat, ST_X(geom) as lon 
            FROM delhi_points
            WHERE ST_Y(geom) BETWEEN %s AND %s
            AND ST_X(geom) BETWEEN %s AND %s
            LIMIT %s
        """
        params = (min_lat, max_lat, min_lon, max_lon, limit)
    
    results = execute_query(query, params)
    
    return [
        {"id": r[0], "name": r[1], "category": r[2], "lat": r[3], "lon": r[4]}
        for r in results
    ]


@router.get("/points/viewport", response_model=List[dict])
def get_points_viewport(
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    limit: int = 100,
    buffer_frac: float = 0.05
):
    """
    Return POIs within the given viewport bounding box (cached).
    """
    # Round coordinates for better cache hit rate (~100m precision)
    r_min_lat = round(min_lat, 3)
    r_min_lon = round(min_lon, 3)
    r_max_lat = round(max_lat, 3)
    r_max_lon = round(max_lon, 3)
    
    return _get_viewport_cached(r_min_lat, r_min_lon, r_max_lat, r_max_lon, limit, buffer_frac)

@cached(viewport_cache)
def _get_viewport_cached(min_lat, min_lon, max_lat, max_lon, limit, buffer_frac):
    # expand bbox slightly to preload nearby POIs
    lat_span = max_lat - min_lat
    lon_span = max_lon - min_lon
    pad_lat = lat_span * buffer_frac
    pad_lon = lon_span * buffer_frac

    q_min_lat = min_lat - pad_lat
    q_max_lat = max_lat + pad_lat
    q_min_lon = min_lon - pad_lon
    q_max_lon = max_lon + pad_lon

    # Use points_area joined to area_scores to compute importance
    query = """
        SELECT p.id, p.name, p.category, ST_Y(p.geom) as lat, ST_X(p.geom) as lon,
               COALESCE(a.score_footfall, 0) as footfall,
               COALESCE(a.score_poi_synergy, 0) as poi_synergy,
               COALESCE(a.score_transit, 0) as transit,
               (COALESCE(a.score_footfall, 0)*0.5 + COALESCE(a.score_poi_synergy, 0)*0.3 + COALESCE(a.score_transit, 0)*0.2) as importance
        FROM points_area p
        LEFT JOIN area_scores a ON p.area = a.name
        WHERE ST_Y(p.geom) BETWEEN %s AND %s
          AND ST_X(p.geom) BETWEEN %s AND %s
        ORDER BY importance DESC
        LIMIT %s
    """
    params = (q_min_lat, q_max_lat, q_min_lon, q_max_lon, limit)

    try:
        results = execute_query(query, params)
    except Exception:
        # Fallback: if points_area/area_scores not available, query delhi_points directly
        fallback_q = """
            SELECT id, name, category, ST_Y(geom) as lat, ST_X(geom) as lon
            FROM delhi_points
            WHERE ST_Y(geom) BETWEEN %s AND %s
              AND ST_X(geom) BETWEEN %s AND %s
            LIMIT %s
        """
        results = execute_query(fallback_q, (q_min_lat, q_max_lat, q_min_lon, q_max_lon, limit))

    return [
        {"id": r[0], "name": r[1], "category": r[2], "lat": r[3], "lon": r[4]}
        for r in results
    ]

@router.get("/areas", response_model=List[dict])
def get_areas():
    """Get all areas/districts (cached for 1 hour)"""
    return _get_areas_cached()

@cached(static_cache)
def _get_areas_cached():
    query = """
        SELECT id, name, longitude, latitude 
        FROM area_with_centroid 
        ORDER BY name
    """
    results = execute_query(query)
    
    return [
        {"id": r[0], "name": r[1], "lon": r[2], "lat": r[3]}
        for r in results
    ]

@router.get("/areas/search")
def search_areas(q: str, limit: int = 10):
    """Search areas by name (cached)"""
    return _search_areas_cached(q.lower(), limit)

@cached(search_cache)
def _search_areas_cached(q: str, limit: int):
    query = """
        SELECT id, name, longitude, latitude 
        FROM area_with_centroid 
        WHERE name ILIKE %s
        ORDER BY 
            CASE WHEN LOWER(name) = LOWER(%s) THEN 0
                 WHEN name ILIKE %s THEN 1
                 ELSE 2 END,
            name
        LIMIT %s
    """
    search_term = f"%{q}%"
    starts_with = f"{q}%"
    results = execute_query(query, (search_term, q, starts_with, limit))
    
    return [{
        "id": r[0],
        "name": r[1],
        "lon": r[2],
        "lat": r[3],
        "type": "area"
    } for r in results]


@router.get("/pois/search")
def search_pois(q: str, limit: int = 10):
    """Search POIs by name (cached)"""
    return _search_pois_cached(q.lower(), limit)

@cached(search_cache)
def _search_pois_cached(q: str, limit: int):
    query = """
        SELECT id, name, category, ST_Y(geom) as lat, ST_X(geom) as lon
        FROM delhi_points
        WHERE name ILIKE %s
        ORDER BY 
            CASE WHEN LOWER(name) = LOWER(%s) THEN 0
                 WHEN name ILIKE %s THEN 1
                 ELSE 2 END,
            name
        LIMIT %s
    """
    search_term = f"%{q}%"
    starts_with = f"{q}%"
    results = execute_query(query, (search_term, q, starts_with, limit))
    
    return [{
        "id": r[0],
        "name": r[1],
        "category": r[2],
        "lat": r[3],
        "lon": r[4],
        "type": "poi"
    } for r in results]


@router.get("/categories")
def get_categories():
    """Get all unique POI categories (cached 1 hour)"""
    return _get_categories_cached()

@cached(static_cache)
def _get_categories_cached():
    query = """
        SELECT DISTINCT category 
        FROM delhi_points 
        WHERE category IS NOT NULL
        ORDER BY category
    """
    results = execute_query(query)
    return [r[0] for r in results]


@router.get("/categories/search")
def search_categories(q: str, limit: int = 10):
    """Search POI categories (cached)"""
    return _search_categories_cached(q.lower(), limit)

@cached(search_cache)
def _search_categories_cached(q: str, limit: int):
    query = """
        SELECT category, COUNT(*) as count
        FROM delhi_points
        WHERE category ILIKE %s
        GROUP BY category
        ORDER BY 
            CASE WHEN LOWER(category) = LOWER(%s) THEN 0
                 WHEN category ILIKE %s THEN 1
                 ELSE 2 END,
            count DESC
        LIMIT %s
    """
    search_term = f"%{q}%"
    starts_with = f"{q}%"
    results = execute_query(query, (search_term, q, starts_with, limit))
    
    return [{
        "category": r[0],
        "count": r[1],
        "type": "category"
    } for r in results]


@router.get("/super-categories")
def get_super_categories():
    """Get all unique super categories (cached 1 hour)"""
    return _get_super_categories_cached()

@cached(static_cache)
def _get_super_categories_cached():
    query = """
        SELECT DISTINCT super_category 
        FROM points_super 
        WHERE super_category IS NOT NULL
        ORDER BY super_category
    """
    results = execute_query(query)
    return [r[0] for r in results]


@router.get("/super-categories/search")
def search_super_categories(q: str, limit: int = 10):
    """Search super categories (cached)"""
    return _search_super_categories_cached(q.lower(), limit)

@cached(search_cache)
def _search_super_categories_cached(q: str, limit: int):
    query = """
        SELECT super_category, COUNT(*) as count
        FROM points_super
        WHERE super_category ILIKE %s
        GROUP BY super_category
        ORDER BY 
            CASE WHEN LOWER(super_category) = LOWER(%s) THEN 0
                 WHEN super_category ILIKE %s THEN 1
                 ELSE 2 END,
            count DESC
        LIMIT %s
    """
    search_term = f"%{q}%"
    starts_with = f"{q}%"
    results = execute_query(query, (search_term, q, starts_with, limit))
    
    return [{
        "super_category": r[0],
        "count": r[1],
        "type": "super_category"
    } for r in results]


@router.get("/pois/by-category")
def get_pois_by_category(category: str, limit: int = 500):
    """Get POIs filtered by category (cached 2 min)"""
    return _get_pois_by_category_cached(category, limit)

@cached(search_cache)
def _get_pois_by_category_cached(category: str, limit: int):
    query = """
        SELECT id, name, category, ST_Y(geom) as lat, ST_X(geom) as lon
        FROM delhi_points
        WHERE category = %s
        LIMIT %s
    """
    results = execute_query(query, (category, limit))
    
    return [{
        "id": r[0],
        "name": r[1],
        "category": r[2],
        "lat": r[3],
        "lon": r[4]
    } for r in results]


@router.get("/pois/by-super-category")
def get_pois_by_super_category(super_category: str, limit: int = 500):
    """Get POIs filtered by super category (cached 2 min)"""
    return _get_pois_by_super_category_cached(super_category, limit)

@cached(search_cache)
def _get_pois_by_super_category_cached(super_category: str, limit: int):
    query = """
        SELECT id, name, category, ST_Y(geom) as lat, ST_X(geom) as lon, super_category
        FROM points_super
        WHERE super_category = %s
        LIMIT %s
    """
    results = execute_query(query, (super_category, limit))
    
    return [{
        "id": r[0],
        "name": r[1],
        "category": r[2],
        "lat": r[3],
        "lon": r[4],
        "super_category": r[5]
    } for r in results]


@router.get("/search/unified")
def unified_search(q: str, limit: int = 15):
    """Unified search across areas, POIs, categories, super categories (cached)"""
    return _unified_search_cached(q.lower(), limit)

@cached(search_cache)
def _unified_search_cached(q: str, limit: int):
    results = []
    per_type_limit = max(3, limit // 4)
    
    # 1. Search areas (highest priority for location searches)
    area_query = """
        SELECT id, name, longitude, latitude 
        FROM area_with_centroid 
        WHERE name ILIKE %s
        ORDER BY 
            CASE WHEN LOWER(name) = LOWER(%s) THEN 0
                 WHEN name ILIKE %s THEN 1
                 ELSE 2 END,
            name
        LIMIT %s
    """
    search_term = f"%{q}%"
    starts_with = f"{q}%"
    areas = execute_query(area_query, (search_term, q, starts_with, per_type_limit))
    for r in areas:
        results.append({
            "id": r[0],
            "name": r[1],
            "lon": r[2],
            "lat": r[3],
            "type": "area",
            "icon": "building"
        })
    
    # 2. Search categories
    cat_query = """
        SELECT category, COUNT(*) as count
        FROM delhi_points
        WHERE category ILIKE %s
        GROUP BY category
        ORDER BY 
            CASE WHEN LOWER(category) = LOWER(%s) THEN 0
                 WHEN category ILIKE %s THEN 1
                 ELSE 2 END,
            count DESC
        LIMIT %s
    """
    categories = execute_query(cat_query, (search_term, q, starts_with, per_type_limit))
    for r in categories:
        results.append({
            "name": r[0],
            "count": r[1],
            "type": "category",
            "icon": "tag"
        })
    
    # 3. Search super categories
    super_query = """
        SELECT super_category, COUNT(*) as count
        FROM points_super
        WHERE super_category ILIKE %s
        GROUP BY super_category
        ORDER BY 
            CASE WHEN LOWER(super_category) = LOWER(%s) THEN 0
                 WHEN super_category ILIKE %s THEN 1
                 ELSE 2 END,
            count DESC
        LIMIT %s
    """
    super_cats = execute_query(super_query, (search_term, q, starts_with, per_type_limit))
    for r in super_cats:
        results.append({
            "name": r[0],
            "count": r[1],
            "type": "super_category",
            "icon": "layers"
        })
    
    # 4. Search POI names (lower priority, only if we have room)
    remaining = limit - len(results)
    if remaining > 0:
        poi_query = """
            SELECT id, name, category, ST_Y(geom) as lat, ST_X(geom) as lon
            FROM delhi_points
            WHERE name ILIKE %s
            ORDER BY 
                CASE WHEN LOWER(name) = LOWER(%s) THEN 0
                     WHEN name ILIKE %s THEN 1
                     ELSE 2 END,
                name
            LIMIT %s
        """
        pois = execute_query(poi_query, (search_term, q, starts_with, min(remaining, per_type_limit)))
        for r in pois:
            results.append({
                "id": r[0],
                "name": r[1],
                "category": r[2],
                "lat": r[3],
                "lon": r[4],
                "type": "poi",
                "icon": "map-pin"
            })
    
    return results[:limit]

@router.get("/delhi/bounds")
def get_delhi_bounds():
    """
    Get Delhi city boundary bounding box from the database.
    Used for validating if coordinates are within Delhi.
    """
    query = """
        SELECT 
            ST_XMin(geom) as min_lon,
            ST_XMax(geom) as max_lon,
            ST_YMin(geom) as min_lat,
            ST_YMax(geom) as max_lat
        FROM delhi_city
        LIMIT 1
    """
    result = execute_query(query, fetch="one")
    
    if result:
        return {
            "min_lon": result[0],
            "max_lon": result[1],
            "min_lat": result[2],
            "max_lat": result[3]
        }
    return None

@router.get("/delhi/contains")
def check_point_in_delhi(lat: float, lon: float):
    """
    Check if a point is within the Delhi city boundary polygon.
    Uses actual geometry for precise validation.
    """
    query = """
        SELECT ST_Contains(geom, ST_SetSRID(ST_Point(%s, %s), 4326)) as is_inside
        FROM delhi_city
        LIMIT 1
    """
    result = execute_query(query, (lon, lat), fetch="one")
    
    return {"is_inside": bool(result[0]) if result else False}

@router.get("/pincodes", response_model=List[dict])
def get_pincodes():
    """Get all pincodes (cached 1 hour)"""
    return _get_pincodes_cached()

@cached(static_cache)
def _get_pincodes_cached():
    query = "SELECT id, name FROM delhi_pincode"
    results = execute_query(query)
    return [{"id": r[0], "pincode": r[1]} for r in results]

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

@router.get("/delhi_boundary")
def get_delhi_boundary():
    """Get Delhi city boundary as GeoJSON (cached 1 hour)."""
    return _get_delhi_boundary_cached()

@cached(static_cache)
def _get_delhi_boundary_cached():
    try:
        query = "SELECT ST_AsGeoJSON(geom) as geometry, name FROM delhi_city LIMIT 1"
        results = execute_query(query)
        
        features = []
        for r in results:
            features.append({
                "type": "Feature",
                "geometry": json.loads(r[0]),
                "properties": {"name": r[1]}
            })
        
        return {
            "type": "FeatureCollection",
            "features": features
        }
    except Exception as e:
        print(f"Error fetching boundary: {e}")
        return {"type": "FeatureCollection", "features": []}


# ============================================
# External API Routes (with caching)
# ============================================

@router.get("/external/poi")
def get_external_poi(lat: float, lon: float, category: Optional[str] = None):
    """Get points of interest near a location (cached 10 min)."""
    r_lat = round(lat, 4)
    r_lon = round(lon, 4)
    return _external_poi_cached(r_lat, r_lon, category)

@cached(external_cache)
def _external_poi_cached(lat: float, lon: float, category: Optional[str]):
    return latlong_client.get_pois(lat, lon, category=category)

@router.get("/external/reverse")
def get_external_reverse(lat: float, lon: float):
    """Get address for coordinates (cached 10 min)."""
    r_lat = round(lat, 4)
    r_lon = round(lon, 4)
    return _external_reverse_cached(r_lat, r_lon)

@cached(external_cache)
def _external_reverse_cached(lat: float, lon: float):
    return latlong_client.reverse_geocode(lat, lon)

@router.get("/external/isochrone")
def get_external_isochrone(lat: float, lon: float, distance: float = 1.0):
    """Get isochrone polygon (cached 10 min)."""
    r_lat = round(lat, 4)
    r_lon = round(lon, 4)
    return _external_isochrone_cached(r_lat, r_lon, distance)

@cached(external_cache)
def _external_isochrone_cached(lat: float, lon: float, distance: float):
    return latlong_client.get_isochrone(lat, lon, distance_km=distance)

@router.get("/external/distance")
def get_external_distance(lat1: float, lon1: float, lat2: float, lon2: float):
    """Get distance between two points."""
    return latlong_client.get_distance(lat1, lon1, lat2, lon2)

@router.get("/external/autocomplete")
def get_external_autocomplete(query: str, lat: Optional[float] = None, lon: Optional[float] = None, limit: int = 10):
    """Get autocomplete suggestions (cached 1 min)."""
    r_lat = round(lat, 4) if lat else None
    r_lon = round(lon, 4) if lon else None
    return _external_autocomplete_cached(query.lower(), r_lat, r_lon, limit)

@cached(search_cache)
def _external_autocomplete_cached(query: str, lat: Optional[float], lon: Optional[float], limit: int):
    return latlong_client.autocomplete(query, lat=lat, lon=lon, limit=limit)

@router.get("/external/geocode")
def get_external_geocode(address: str):
    """Convert address to coordinates (cached 10 min)."""
    return _external_geocode_cached(address.lower())

@cached(external_cache)
def _external_geocode_cached(address: str):
    return latlong_client.geocode(address)

@router.get("/external/validate")
def get_external_validate(address: str, lat: float, lon: float):
    """Validate address/coordinates match (cached 10 min)."""
    r_lat = round(lat, 4)
    r_lon = round(lon, 4)
    return _external_validate_cached(address.lower(), r_lat, r_lon)

@cached(external_cache)
def _external_validate_cached(address: str, lat: float, lon: float):
    return latlong_client.validate_address(address, lat, lon)

@router.get("/external/landmarks")
def get_external_landmarks(lat: float, lon: float):
    """Get nearby landmarks (cached 10 min)."""
    r_lat = round(lat, 4)
    r_lon = round(lon, 4)
    return _external_landmarks_cached(r_lat, r_lon)

@cached(external_cache)
def _external_landmarks_cached(lat: float, lon: float):
    return latlong_client.get_landmarks(lat, lon)


# ============================================
# Business Location Recommendation
# ============================================

@router.post("/recommend/location")
def recommend_business_location(request: LocationRecommendRequest):
    """
    Recommend top 3 areas for a business based on user query.
    
    Uses AI to understand the business type, then analyzes:
    - Area base scores (60%)
    - Competition (opportunity) score (20%)
    - Complementary businesses (ecosystem) score (20%)
    
    Returns top 3 areas with their centroids for map highlighting.
    """
    try:
        location_agent = get_business_location_agent()
        result = location_agent.recommend_locations(request.query, request.radius_km)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Failed to get recommendations"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing recommendation: {str(e)}")


@router.get("/recommend/categories")
def get_super_categories():
    """Get list of valid super categories for business recommendations."""
    from app.services.location_recommender import VALID_SUPER_CATEGORIES
    return {"categories": VALID_SUPER_CATEGORIES}


@router.get("/areas/geometry")
def get_area_geometry(names: str):
    """
    Get GeoJSON polygons for given area names.
    names: comma-separated list of area names
    Returns GeoJSON FeatureCollection with area polygons.
    """
    area_list = [n.strip() for n in names.split(',') if n.strip()]
    if not area_list:
        return {"type": "FeatureCollection", "features": []}
    
    placeholders = ','.join(['%s'] * len(area_list))
    query = f"""
        SELECT name, ST_AsGeoJSON(geom) as geojson
        FROM delhi_area
        WHERE name IN ({placeholders})
    """
    results = execute_query(query, tuple(area_list))
    
    features = []
    if results:
        for row in results:
            features.append({
                "type": "Feature",
                "properties": {"name": row[0]},
                "geometry": json.loads(row[1])
            })
    
    return {"type": "FeatureCollection", "features": features}


# ============================================
# Area Business Analysis (What to open in X area)
# ============================================

class AreaAnalysisRequest(BaseModel):
    area: str

@router.post("/analyze/area")
def analyze_area_opportunities(request: AreaAnalysisRequest):
    """
    Analyze what businesses would be good to open in a specific area.
    
    Looks at:
    - Gap analysis (underserved business categories vs Delhi average)
    - Complementary opportunities (businesses that complement existing ones)
    
    Returns top 5 recommended business categories with examples.
    """
    try:
        from app.services.area_business_analyzer import get_area_analyzer
        analyzer = get_area_analyzer()
        result = analyzer.analyze_area(request.area)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Analysis failed"))
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing area: {str(e)}")



