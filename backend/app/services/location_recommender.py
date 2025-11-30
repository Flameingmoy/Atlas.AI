"""
Business Location Recommender Service
Finds top 3 best locations for any business type in Delhi using:
1. Area scores (11 criteria from CSV)
2. Isochrone-based opportunity score (fewer competitors)
3. Isochrone-based ecosystem score (more complementary businesses)
"""
import os
import pandas as pd
from typing import Dict, List, Tuple, Optional
from app.core.db import execute_query
from app.services.latlong_client import LatLongClient
from shapely.geometry import shape, Point
from shapely import wkt
import json

# Path to area scores CSV - /app/data inside Docker container
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
AREA_SCORES_CSV = os.path.join(DATA_DIR, 'Delhi_Areas_All_11_Criteria_Real_Data.csv')

# ============================================================================
# HARDCODED WEIGHTS FOR 13 SUPER CATEGORIES
# ============================================================================
WEIGHTS = {
    'Accommodation & Lodging': {
        'Score_Population_Density': 15.0, 'Score_Footfall': 20.0, 'Score_Transit': 12.0,
        'Score_Traffic': 5.0, 'Score_Rent_Value': 8.0, 'Score_Parking': 8.0,
        'Score_Night_Activity': 5.0, 'Score_Walkability': 8.0, 'Score_POI_Synergy': 8.0,
        'Score_Safety': 6.0
    },
    'Education & Training': {
        'Score_Population_Density': 28.0, 'Score_Footfall': 10.0, 'Score_Transit': 12.0,
        'Score_Traffic': 8.0, 'Score_Rent_Value': 8.0, 'Score_Parking': 15.0,
        'Score_Night_Activity': 0.0, 'Score_Walkability': 5.0, 'Score_POI_Synergy': 5.0,
        'Score_Safety': 5.0
    },
    'Entertainment & Leisure': {
        'Score_Population_Density': 20.0, 'Score_Footfall': 25.0, 'Score_Transit': 10.0,
        'Score_Traffic': 5.0, 'Score_Rent_Value': 3.0, 'Score_Parking': 8.0,
        'Score_Night_Activity': 15.0, 'Score_Walkability': 8.0, 'Score_POI_Synergy': 2.0,
        'Score_Safety': 1.0
    },
    'Financial & Legal Services': {
        'Score_Population_Density': 20.0, 'Score_Footfall': 5.0, 'Score_Transit': 12.0,
        'Score_Traffic': 8.0, 'Score_Rent_Value': 15.0, 'Score_Parking': 8.0,
        'Score_Night_Activity': 0.0, 'Score_Walkability': 8.0, 'Score_POI_Synergy': 12.0,
        'Score_Safety': 4.0
    },
    'Fitness & Wellness': {
        'Score_Population_Density': 25.0, 'Score_Footfall': 20.0, 'Score_Transit': 8.0,
        'Score_Traffic': 3.0, 'Score_Rent_Value': 5.0, 'Score_Parking': 10.0,
        'Score_Night_Activity': 8.0, 'Score_Walkability': 10.0, 'Score_POI_Synergy': 5.0,
        'Score_Safety': 3.0
    },
    'Food & Beverages': {
        'Score_Population_Density': 20.0, 'Score_Footfall': 30.0, 'Score_Transit': 5.0,
        'Score_Traffic': 3.0, 'Score_Rent_Value': 3.0, 'Score_Parking': 5.0,
        'Score_Night_Activity': 15.0, 'Score_Walkability': 12.0, 'Score_POI_Synergy': 3.0,
        'Score_Safety': 2.0
    },
    'Government & Public Services': {
        'Score_Population_Density': 25.0, 'Score_Footfall': 10.0, 'Score_Transit': 15.0,
        'Score_Traffic': 8.0, 'Score_Rent_Value': 3.0, 'Score_Parking': 12.0,
        'Score_Night_Activity': 0.0, 'Score_Walkability': 5.0, 'Score_POI_Synergy': 8.0,
        'Score_Safety': 2.0
    },
    'Health & Medical': {
        'Score_Population_Density': 30.0, 'Score_Footfall': 15.0, 'Score_Transit': 10.0,
        'Score_Traffic': 3.0, 'Score_Rent_Value': 5.0, 'Score_Parking': 12.0,
        'Score_Night_Activity': 0.0, 'Score_Walkability': 8.0, 'Score_POI_Synergy': 7.0,
        'Score_Safety': 5.0
    },
    'Other / Misc': {
        'Score_Population_Density': 9.09, 'Score_Footfall': 9.09, 'Score_Transit': 9.09,
        'Score_Traffic': 9.09, 'Score_Rent_Value': 9.09, 'Score_Parking': 9.09,
        'Score_Night_Activity': 9.09, 'Score_Walkability': 9.09, 'Score_POI_Synergy': 9.09,
        'Score_Safety': 9.09
    },
    'Parks & Outdoor Recreation': {
        'Score_Population_Density': 25.0, 'Score_Footfall': 20.0, 'Score_Transit': 12.0,
        'Score_Traffic': 3.0, 'Score_Rent_Value': 5.0, 'Score_Parking': 10.0,
        'Score_Night_Activity': 2.0, 'Score_Walkability': 12.0, 'Score_POI_Synergy': 5.0,
        'Score_Safety': 6.0
    },
    'Religious & Spiritual Places': {
        'Score_Population_Density': 28.0, 'Score_Footfall': 15.0, 'Score_Transit': 10.0,
        'Score_Traffic': 3.0, 'Score_Rent_Value': 3.0, 'Score_Parking': 8.0,
        'Score_Night_Activity': 5.0, 'Score_Walkability': 8.0, 'Score_POI_Synergy': 5.0,
        'Score_Safety': 5.0
    },
    'Shopping & Retail': {
        'Score_Population_Density': 25.0, 'Score_Footfall': 25.0, 'Score_Transit': 8.0,
        'Score_Traffic': 5.0, 'Score_Rent_Value': 5.0, 'Score_Parking': 10.0,
        'Score_Night_Activity': 5.0, 'Score_Walkability': 10.0, 'Score_POI_Synergy': 2.0,
        'Score_Safety': 2.0
    },
    'Transport & Auto Services': {
        'Score_Population_Density': 15.0, 'Score_Footfall': 10.0, 'Score_Transit': 15.0,
        'Score_Traffic': 25.0, 'Score_Rent_Value': 5.0, 'Score_Parking': 10.0,
        'Score_Night_Activity': 3.0, 'Score_Walkability': 5.0, 'Score_POI_Synergy': 5.0,
        'Score_Safety': 2.0
    }
}

# ============================================================================
# COMPLEMENTARY CATEGORIES
# ============================================================================
COMPLEMENTARY_CATEGORIES = {
    'Food & Beverages': ['Shopping & Retail', 'Entertainment & Leisure', 'Parks & Outdoor Recreation', 'Transport & Auto Services', 'Fitness & Wellness'],
    'Fitness & Wellness': ['Food & Beverages', 'Health & Medical', 'Parks & Outdoor Recreation', 'Shopping & Retail', 'Accommodation & Lodging'],
    'Health & Medical': ['Fitness & Wellness', 'Food & Beverages', 'Shopping & Retail', 'Transport & Auto Services', 'Accommodation & Lodging'],
    'Shopping & Retail': ['Food & Beverages', 'Entertainment & Leisure', 'Transport & Auto Services', 'Fitness & Wellness', 'Accommodation & Lodging'],
    'Entertainment & Leisure': ['Food & Beverages', 'Shopping & Retail', 'Transport & Auto Services', 'Accommodation & Lodging', 'Parks & Outdoor Recreation'],
    'Education & Training': ['Food & Beverages', 'Shopping & Retail', 'Transport & Auto Services', 'Accommodation & Lodging', 'Parks & Outdoor Recreation'],
    'Accommodation & Lodging': ['Food & Beverages', 'Entertainment & Leisure', 'Shopping & Retail', 'Transport & Auto Services', 'Parks & Outdoor Recreation'],
    'Transport & Auto Services': ['Food & Beverages', 'Shopping & Retail', 'Accommodation & Lodging', 'Entertainment & Leisure', 'Financial & Legal Services'],
    'Financial & Legal Services': ['Shopping & Retail', 'Food & Beverages', 'Government & Public Services', 'Transport & Auto Services', 'Accommodation & Lodging'],
    'Government & Public Services': ['Financial & Legal Services', 'Food & Beverages', 'Transport & Auto Services', 'Shopping & Retail', 'Parks & Outdoor Recreation'],
    'Parks & Outdoor Recreation': ['Food & Beverages', 'Fitness & Wellness', 'Entertainment & Leisure', 'Shopping & Retail', 'Accommodation & Lodging'],
    'Religious & Spiritual Places': ['Food & Beverages', 'Shopping & Retail', 'Parks & Outdoor Recreation', 'Transport & Auto Services', 'Accommodation & Lodging'],
    'Other / Misc': ['Food & Beverages', 'Shopping & Retail', 'Transport & Auto Services']
}

# Valid super categories
VALID_SUPER_CATEGORIES = list(WEIGHTS.keys())


class LocationRecommender:
    """Service to find best business locations using area scores and isochrone analysis"""
    
    def __init__(self):
        self.latlong_client = LatLongClient()
        self._load_area_scores()
    
    def _load_area_scores(self):
        """Load area scores from CSV"""
        try:
            self.areas_df = pd.read_csv(AREA_SCORES_CSV)
            print(f"[LocationRecommender] Loaded {len(self.areas_df)} areas from CSV")
        except FileNotFoundError:
            print(f"[LocationRecommender] Warning: {AREA_SCORES_CSV} not found, using database")
            self.areas_df = None
    
    def get_area_centroids(self, area_names: List[str]) -> List[Dict]:
        """Get centroids for given areas from PostGIS"""
        if not area_names:
            return []
        
        placeholders = ','.join(['%s'] * len(area_names))
        query = f"""
            SELECT name, longitude, latitude 
            FROM area_with_centroid 
            WHERE name IN ({placeholders})
        """
        results = execute_query(query, tuple(area_names))
        if results is None:
            return []
        return [{"name": r[0], "lon": r[1], "lat": r[2]} for r in results]
    
    def calculate_area_scores(self, super_category: str) -> pd.DataFrame:
        """Calculate area scores based on super category weights, return top 10"""
        if self.areas_df is None:
            return pd.DataFrame()
        
        weights = WEIGHTS.get(super_category, WEIGHTS['Other / Misc'])
        
        scores = []
        for _, row in self.areas_df.iterrows():
            score = 0.0
            for feature, weight in weights.items():
                if feature in row:
                    score += (row[feature] * weight / 100)
            
            scores.append({
                'area': row['name'],
                'area_score': round(score, 2)
            })
        
        result_df = pd.DataFrame(scores)
        result_df = result_df.sort_values('area_score', ascending=False).head(10).reset_index(drop=True)
        return result_df
    
    def get_isochrone_polygon(self, lat: float, lon: float, distance_km: float = 1.0) -> Optional[object]:
        """Get isochrone polygon from LatLong API and return Shapely geometry"""
        try:
            result = self.latlong_client.get_isochrone(lat, lon, distance_km)
            if result.get('status') == 'success' and 'data' in result:
                geojson = result['data']
                if 'geometry' in geojson:
                    return shape(geojson['geometry'])
            return None
        except Exception as e:
            print(f"[LocationRecommender] Isochrone error: {e}")
            return None
    
    def count_pois_in_polygon(self, polygon, super_category: Optional[str] = None, 
                              complementary_categories: Optional[List[str]] = None) -> Tuple[int, int]:
        """
        Count competitors and complementary businesses within a polygon.
        Uses PostGIS ST_Contains for efficient spatial query.
        
        Returns: (competitor_count, complementary_count)
        """
        if polygon is None:
            return (0, 0)
        
        # Convert Shapely polygon to WKT for PostGIS
        polygon_wkt = polygon.wkt
        
        # Count competitors (same super category)
        competitor_count = 0
        if super_category:
            query = """
                SELECT COUNT(*) FROM points_super
                WHERE super_category = %s
                AND ST_Contains(ST_GeomFromText(%s, 4326), geom)
            """
            try:
                result = execute_query(query, (super_category, polygon_wkt))
                competitor_count = result[0][0] if result else 0
            except Exception as e:
                print(f"[LocationRecommender] Competitor count error: {e}")
                # Fallback: use bounding box query
                competitor_count = self._count_pois_bbox_fallback(polygon, super_category, is_competitor=True)
        
        # Count complementary businesses
        complementary_count = 0
        if complementary_categories:
            placeholders = ','.join(['%s'] * len(complementary_categories))
            query = f"""
                SELECT COUNT(*) FROM points_super
                WHERE super_category IN ({placeholders})
                AND ST_Contains(ST_GeomFromText(%s, 4326), geom)
            """
            try:
                params = tuple(complementary_categories) + (polygon_wkt,)
                result = execute_query(query, params)
                complementary_count = result[0][0] if result else 0
            except Exception as e:
                print(f"[LocationRecommender] Complementary count error: {e}")
                complementary_count = self._count_pois_bbox_fallback(polygon, complementary_categories, is_competitor=False)
        
        return (competitor_count, complementary_count)
    
    def _count_pois_bbox_fallback(self, polygon, categories, is_competitor: bool) -> int:
        """Fallback using bounding box if ST_Contains fails"""
        bounds = polygon.bounds  # (minx, miny, maxx, maxy)
        
        if is_competitor:
            query = """
                SELECT COUNT(*) FROM points_super
                WHERE super_category = %s
                AND ST_X(geom) BETWEEN %s AND %s
                AND ST_Y(geom) BETWEEN %s AND %s
            """
            result = execute_query(query, (categories, bounds[0], bounds[2], bounds[1], bounds[3]))
        else:
            placeholders = ','.join(['%s'] * len(categories))
            query = f"""
                SELECT COUNT(*) FROM points_super
                WHERE super_category IN ({placeholders})
                AND ST_X(geom) BETWEEN %s AND %s
                AND ST_Y(geom) BETWEEN %s AND %s
            """
            params = tuple(categories) + (bounds[0], bounds[2], bounds[1], bounds[3])
            result = execute_query(query, params)
        
        return result[0][0] if result else 0
    
    def normalize_score(self, value: float, all_values: List[float], inverse: bool = False) -> float:
        """Normalize a value to 0-100 scale. If inverse=True, lower is better."""
        if not all_values:
            return 50.0
        
        min_val = min(all_values)
        max_val = max(all_values)
        
        if max_val == min_val:
            return 50.0
        
        if inverse:
            # Lower value = higher score (for competitors)
            return ((max_val - value) / (max_val - min_val)) * 100
        else:
            # Higher value = higher score (for complementary)
            return ((value - min_val) / (max_val - min_val)) * 100
    
    def find_best_locations(self, super_category: str, isochrone_distance_km: float = 1.0) -> Dict:
        """
        Find top 3 best locations for a business super category.
        
        Args:
            super_category: One of the 13 valid super categories
            isochrone_distance_km: Radius for isochrone (default 1km)
        
        Returns:
            Dict with top 3 areas and their scores
        """
        if super_category not in VALID_SUPER_CATEGORIES:
            return {
                "error": f"Invalid super category. Must be one of: {VALID_SUPER_CATEGORIES}",
                "recommendations": []
            }
        
        # Step 1: Get top 10 areas by area score
        top_10_df = self.calculate_area_scores(super_category)
        if top_10_df.empty:
            return {"error": "Could not calculate area scores", "recommendations": []}
        
        top_10_areas = top_10_df['area'].tolist()
        
        # Step 2: Get centroids for top 10 areas
        centroids = self.get_area_centroids(top_10_areas)
        centroid_map = {c['name']: c for c in centroids}
        
        # Step 3: Get complementary categories
        complementary_cats = COMPLEMENTARY_CATEGORIES.get(super_category, [])
        
        # Step 4: For each area, get isochrone and count POIs
        results = []
        for _, row in top_10_df.iterrows():
            area_name = row['area']
            area_score = row['area_score']
            
            centroid = centroid_map.get(area_name)
            if not centroid:
                continue
            
            # Get isochrone polygon
            polygon = self.get_isochrone_polygon(centroid['lat'], centroid['lon'], isochrone_distance_km)
            
            # Count POIs in isochrone
            if polygon:
                competitor_count, complementary_count = self.count_pois_in_polygon(
                    polygon, super_category, complementary_cats
                )
            else:
                # Fallback: use simple radius query
                competitor_count, complementary_count = self._simple_radius_count(
                    centroid['lat'], centroid['lon'], isochrone_distance_km,
                    super_category, complementary_cats
                )
            
            results.append({
                'area': area_name,
                'area_score': area_score,
                'centroid': {
                    'lat': centroid['lat'],
                    'lon': centroid['lon']
                },
                'competitors': competitor_count,
                'complementary': complementary_count
            })
        
        if not results:
            return {"error": "No areas found", "recommendations": []}
        
        # Step 5: Normalize opportunity and ecosystem scores
        all_competitors = [r['competitors'] for r in results]
        all_complementary = [r['complementary'] for r in results]
        
        for r in results:
            r['opportunity_score'] = round(self.normalize_score(r['competitors'], all_competitors, inverse=True), 2)
            r['ecosystem_score'] = round(self.normalize_score(r['complementary'], all_complementary, inverse=False), 2)
            
            # Step 6: Calculate composite score
            r['composite_score'] = round(
                (r['area_score'] * 0.60) +
                (r['opportunity_score'] * 0.20) +
                (r['ecosystem_score'] * 0.20),
                2
            )
        
        # Sort by composite score and get top 3
        results.sort(key=lambda x: x['composite_score'], reverse=True)
        top_3 = results[:3]
        
        return {
            "super_category": super_category,
            "complementary_categories": complementary_cats,
            "isochrone_radius_km": isochrone_distance_km,
            "recommendations": top_3,
            "all_top_10": results
        }
    
    def recommend_with_research(self, super_category: str, business_type: str,
                                isochrone_distance_km: float = 1.0) -> Dict:
        """
        Enhanced recommendation that includes deep research insights for top 3 areas.
        
        Args:
            super_category: The business super category
            business_type: Specific business type (e.g., "cafe", "gym")
            isochrone_distance_km: Distance for isochrone analysis
            
        Returns:
            Standard recommendation with added 'research' field for each area
        """
        # Get base recommendations
        base_result = self.find_best_locations(super_category, isochrone_distance_km)
        
        if "error" in base_result:
            return base_result
        
        # Import research agent
        from app.services.deep_research_agent import get_research_agent
        research_agent = get_research_agent()
        
        if not research_agent.is_available():
            # Return base results with empty research
            for rec in base_result.get("recommendations", []):
                rec["research"] = {
                    "pros": [],
                    "cons": [],
                    "market_insights": "Deep research not available. Set TAVILY_API_KEY to enable.",
                    "sources": []
                }
            base_result["research_enabled"] = False
            return base_result
        
        # Research top 3 areas
        top_areas = [rec['area'] for rec in base_result.get("recommendations", [])]
        research_results = research_agent.research_multiple_areas(top_areas, business_type)
        
        # Merge research into recommendations
        research_map = {r['area']: r for r in research_results}
        for rec in base_result.get("recommendations", []):
            area_research = research_map.get(rec['area'], {})
            rec["research"] = {
                "pros": area_research.get("pros", []),
                "cons": area_research.get("cons", []),
                "market_insights": area_research.get("market_insights", ""),
                "sources": area_research.get("sources", [])
            }
        
        base_result["research_enabled"] = True
        base_result["business_type"] = business_type
        return base_result

    
    def _simple_radius_count(self, lat: float, lon: float, radius_km: float,
                             super_category: str, complementary_cats: List[str]) -> Tuple[int, int]:
        """Fallback: count POIs within a simple radius (approximation)"""
        # Approximate degrees for the radius
        lat_delta = radius_km / 111.0  # ~111km per degree latitude
        lon_delta = radius_km / (111.0 * abs(cos(radians(lat))))
        
        min_lat, max_lat = lat - lat_delta, lat + lat_delta
        min_lon, max_lon = lon - lon_delta, lon + lon_delta
        
        # Count competitors
        query = """
            SELECT COUNT(*) FROM points_super
            WHERE super_category = %s
            AND ST_Y(geom) BETWEEN %s AND %s
            AND ST_X(geom) BETWEEN %s AND %s
        """
        result = execute_query(query, (super_category, min_lat, max_lat, min_lon, max_lon))
        competitor_count = result[0][0] if result else 0
        
        # Count complementary
        if complementary_cats:
            placeholders = ','.join(['%s'] * len(complementary_cats))
            query = f"""
                SELECT COUNT(*) FROM points_super
                WHERE super_category IN ({placeholders})
                AND ST_Y(geom) BETWEEN %s AND %s
                AND ST_X(geom) BETWEEN %s AND %s
            """
            params = tuple(complementary_cats) + (min_lat, max_lat, min_lon, max_lon)
            result = execute_query(query, params)
            complementary_count = result[0][0] if result else 0
        else:
            complementary_count = 0
        
        return (competitor_count, complementary_count)


# Add missing import
from math import cos, radians


# Singleton instance
_recommender = None

def get_recommender() -> LocationRecommender:
    """Get singleton instance of LocationRecommender"""
    global _recommender
    if _recommender is None:
        _recommender = LocationRecommender()
    return _recommender
