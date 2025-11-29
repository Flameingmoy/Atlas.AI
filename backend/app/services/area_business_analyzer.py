"""
Area Business Analyzer Service
Analyzes what businesses would be good to open in a specific area
by looking at gaps (underserved categories) and complementary opportunities.
"""
import os
from typing import Dict, List, Any, Optional
from app.core.db import execute_query

# Complementary business relationships
COMPLEMENTARY_MAP = {
    'Food & Beverages': ['Shopping & Retail', 'Entertainment & Leisure', 'Fitness & Wellness'],
    'Shopping & Retail': ['Food & Beverages', 'Entertainment & Leisure', 'Financial & Legal Services'],
    'Health & Medical': ['Fitness & Wellness', 'Food & Beverages', 'Shopping & Retail'],
    'Education & Training': ['Food & Beverages', 'Shopping & Retail', 'Transport & Auto Services'],
    'Fitness & Wellness': ['Health & Medical', 'Food & Beverages', 'Shopping & Retail'],
    'Entertainment & Leisure': ['Food & Beverages', 'Shopping & Retail', 'Transport & Auto Services'],
    'Accommodation & Lodging': ['Food & Beverages', 'Transport & Auto Services', 'Entertainment & Leisure'],
    'Financial & Legal Services': ['Shopping & Retail', 'Food & Beverages', 'Education & Training'],
    'Transport & Auto Services': ['Food & Beverages', 'Shopping & Retail', 'Accommodation & Lodging'],
    'Parks & Outdoor Recreation': ['Food & Beverages', 'Fitness & Wellness', 'Entertainment & Leisure'],
    'Religious & Spiritual Places': ['Food & Beverages', 'Shopping & Retail', 'Accommodation & Lodging'],
    'Government & Public Services': ['Food & Beverages', 'Financial & Legal Services', 'Shopping & Retail'],
    'Other / Misc': ['Food & Beverages', 'Shopping & Retail', 'Entertainment & Leisure'],
}

# Business examples for each super category
BUSINESS_EXAMPLES = {
    'Food & Beverages': ['Cafe', 'Restaurant', 'Bakery', 'Juice Bar', 'Cloud Kitchen', 'Food Truck'],
    'Shopping & Retail': ['Clothing Store', 'Electronics Shop', 'Grocery Store', 'Bookstore', 'Gift Shop'],
    'Health & Medical': ['Clinic', 'Pharmacy', 'Diagnostic Lab', 'Dental Clinic', 'Physiotherapy Center'],
    'Education & Training': ['Coaching Center', 'Language School', 'Music Classes', 'Computer Training', 'Preschool'],
    'Fitness & Wellness': ['Gym', 'Yoga Studio', 'Spa', 'Salon', 'Wellness Center'],
    'Entertainment & Leisure': ['Gaming Zone', 'Bowling Alley', 'Escape Room', 'Art Studio', 'Dance Studio'],
    'Accommodation & Lodging': ['Boutique Hotel', 'Guest House', 'Co-living Space', 'Service Apartment'],
    'Financial & Legal Services': ['CA Office', 'Insurance Agency', 'Tax Consultant', 'Legal Consultancy'],
    'Transport & Auto Services': ['Car Wash', 'Bike Service', 'Auto Parts Shop', 'Parking Facility'],
    'Parks & Outdoor Recreation': ['Sports Academy', 'Adventure Sports', 'Outdoor Gym'],
    'Religious & Spiritual Places': ['Meditation Center', 'Yoga Retreat'],
    'Government & Public Services': ['Document Services', 'Notary'],
    'Other / Misc': ['Co-working Space', 'Photography Studio', 'Pet Shop', 'Laundry Service'],
}


class AreaBusinessAnalyzer:
    """Analyzes business opportunities in a specific area"""
    
    def __init__(self):
        pass
    
    def get_area_centroid(self, area_name: str) -> Optional[Dict]:
        """Get centroid coordinates for an area"""
        query = """
            SELECT name, longitude, latitude 
            FROM area_with_centroid 
            WHERE LOWER(name) = LOWER(%s)
            LIMIT 1
        """
        results = execute_query(query, (area_name,))
        if results and len(results) > 0:
            return {"name": results[0][0], "lon": results[0][1], "lat": results[0][2]}
        return None
    
    def find_area_by_name(self, area_name: str) -> Optional[str]:
        """Find closest matching area name"""
        # Try exact match first
        query = """
            SELECT name FROM area_with_centroid 
            WHERE LOWER(name) = LOWER(%s)
            LIMIT 1
        """
        results = execute_query(query, (area_name,))
        if results:
            return results[0][0]
        
        # Try fuzzy match
        query = """
            SELECT name FROM area_with_centroid 
            WHERE LOWER(name) LIKE LOWER(%s)
            ORDER BY LENGTH(name)
            LIMIT 1
        """
        results = execute_query(query, (f"%{area_name}%",))
        if results:
            return results[0][0]
        
        return None
    
    def find_location_from_pois(self, location_name: str) -> Optional[Dict]:
        """
        Find a location by searching POI names when area is not found.
        Returns centroid of matching POIs.
        """
        query = """
            SELECT 
                AVG(ST_X(geom)) as lon,
                AVG(ST_Y(geom)) as lat,
                COUNT(*) as count
            FROM points_super
            WHERE LOWER(name) LIKE LOWER(%s)
        """
        results = execute_query(query, (f"%{location_name}%",))
        if results and results[0][0] is not None and results[0][2] > 0:
            return {
                "name": location_name.title(),
                "lon": float(results[0][0]),
                "lat": float(results[0][1]),
                "poi_count": int(results[0][2]),
                "source": "poi"
            }
        return None
    
    def get_category_distribution(self, area_name: str) -> Dict[str, int]:
        """Get count of POIs by super_category in an area using spatial join"""
        # Use spatial containment to find POIs within the area polygon
        query = """
            SELECT ps.super_category, COUNT(*) as count
            FROM points_super ps
            JOIN delhi_area da ON ST_Contains(da.geom, ps.geom)
            WHERE LOWER(da.name) = LOWER(%s)
            GROUP BY ps.super_category
            ORDER BY count DESC
        """
        results = execute_query(query, (area_name,))
        if not results:
            # Try using centroid with radius as fallback
            centroid = self.get_area_centroid(area_name)
            if centroid:
                return self.get_category_distribution_by_radius(
                    centroid['lat'], centroid['lon'], radius_km=1.5
                )
            return {}
        return {r[0]: r[1] for r in results}
    
    def get_category_distribution_by_radius(self, lat: float, lon: float, 
                                            radius_km: float = 1.5) -> Dict[str, int]:
        """Get count of POIs by super_category within a radius"""
        query = """
            SELECT super_category, COUNT(*) as count
            FROM points_super
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_MakePoint(%s, %s), 4326)::geography,
                %s
            )
            GROUP BY super_category
            ORDER BY count DESC
        """
        results = execute_query(query, (lon, lat, radius_km * 1000))
        if not results:
            return {}
        return {r[0]: r[1] for r in results}
    
    def get_delhi_average_distribution(self) -> Dict[str, float]:
        """Get average POI count per super category across Delhi areas"""
        # Get total counts per category and divide by number of areas
        query = """
            SELECT super_category, COUNT(*) as total_count
            FROM points_super
            GROUP BY super_category
        """
        results = execute_query(query, ())
        if not results:
            return {}
        
        # Get number of areas for averaging
        area_count_query = "SELECT COUNT(*) FROM delhi_area"
        area_count_result = execute_query(area_count_query, ())
        num_areas = area_count_result[0][0] if area_count_result else 1
        
        # Calculate average per area
        return {r[0]: float(r[1]) / num_areas for r in results}
    
    def analyze_gaps(self, area_distribution: Dict[str, int], 
                     delhi_average: Dict[str, float]) -> List[Dict]:
        """Find categories that are underrepresented in the area"""
        gaps = []
        
        for category, avg_count in delhi_average.items():
            area_count = area_distribution.get(category, 0)
            if avg_count > 0:
                ratio = area_count / avg_count
                gap_score = max(0, 100 - (ratio * 100))  # Higher = bigger gap
                
                gaps.append({
                    'category': category,
                    'area_count': area_count,
                    'delhi_average': round(avg_count, 1),
                    'gap_score': round(gap_score, 1),
                    'status': 'underserved' if ratio < 0.5 else 'moderate' if ratio < 1.0 else 'saturated'
                })
        
        # Sort by gap score (highest gaps first)
        gaps.sort(key=lambda x: x['gap_score'], reverse=True)
        return gaps
    
    def analyze_complementary_opportunities(self, area_distribution: Dict[str, int]) -> List[Dict]:
        """Find complementary business opportunities based on existing businesses"""
        opportunities = []
        
        # Find dominant categories in the area
        total_pois = sum(area_distribution.values())
        if total_pois == 0:
            return []
        
        for category, count in area_distribution.items():
            percentage = (count / total_pois) * 100
            if percentage > 5:  # Category has significant presence
                complementary = COMPLEMENTARY_MAP.get(category, [])
                for comp_cat in complementary:
                    comp_count = area_distribution.get(comp_cat, 0)
                    # If complementary category is underrepresented, it's an opportunity
                    if comp_count < count * 0.5:
                        opportunities.append({
                            'category': comp_cat,
                            'reason': f"Complements existing {category} businesses ({count} POIs)",
                            'existing_complementary': comp_count,
                            'opportunity_score': round(100 - (comp_count / max(count, 1) * 100), 1)
                        })
        
        # Remove duplicates and sort by score
        seen = set()
        unique_opportunities = []
        for opp in sorted(opportunities, key=lambda x: x['opportunity_score'], reverse=True):
            if opp['category'] not in seen:
                seen.add(opp['category'])
                unique_opportunities.append(opp)
        
        return unique_opportunities[:5]
    
    def analyze_area(self, area_name: str) -> Dict[str, Any]:
        """
        Main analysis function - analyzes what businesses to open in an area.
        
        Returns recommendations based on:
        1. Gap analysis (underserved categories)
        2. Complementary opportunities
        3. Business examples for each category
        """
        # Find the area in area_with_centroid
        actual_area = self.find_area_by_name(area_name)
        centroid = None
        area_distribution = None
        location_source = "area"
        
        if actual_area:
            # Found as a defined area
            centroid = self.get_area_centroid(actual_area)
            area_distribution = self.get_category_distribution(actual_area)
        else:
            # Try to find as a POI location (e.g., "Khan Market")
            poi_location = self.find_location_from_pois(area_name)
            if poi_location:
                actual_area = poi_location["name"]
                centroid = {"name": poi_location["name"], "lon": poi_location["lon"], "lat": poi_location["lat"]}
                # Get distribution by radius around this point
                area_distribution = self.get_category_distribution_by_radius(
                    poi_location["lat"], poi_location["lon"], radius_km=1.0
                )
                location_source = "poi"
            else:
                return {
                    "success": False,
                    "error": f"Could not find area or location '{area_name}' in Delhi"
                }
        
        if not area_distribution:
            return {
                "success": False,
                "error": f"No business data found for '{actual_area}'"
            }
        
        # Get Delhi average
        delhi_average = self.get_delhi_average_distribution()
        
        # Analyze gaps
        gaps = self.analyze_gaps(area_distribution, delhi_average)
        
        # Analyze complementary opportunities
        complementary = self.analyze_complementary_opportunities(area_distribution)
        
        # Generate top recommendations
        top_recommendations = []
        seen_categories = set()
        
        # Add top gaps
        for gap in gaps[:3]:
            if gap['category'] not in seen_categories and gap['status'] in ['underserved', 'moderate']:
                seen_categories.add(gap['category'])
                examples = BUSINESS_EXAMPLES.get(gap['category'], [])
                top_recommendations.append({
                    'rank': len(top_recommendations) + 1,
                    'category': gap['category'],
                    'reason': f"Gap opportunity - only {gap['area_count']} vs {gap['delhi_average']} Delhi avg",
                    'score': gap['gap_score'],
                    'examples': examples[:4],
                    'type': 'gap'
                })
        
        # Add top complementary opportunities
        for comp in complementary:
            if comp['category'] not in seen_categories and len(top_recommendations) < 5:
                seen_categories.add(comp['category'])
                examples = BUSINESS_EXAMPLES.get(comp['category'], [])
                top_recommendations.append({
                    'rank': len(top_recommendations) + 1,
                    'category': comp['category'],
                    'reason': comp['reason'],
                    'score': comp['opportunity_score'],
                    'examples': examples[:4],
                    'type': 'complementary'
                })
        
        # Calculate total POIs
        total_pois = sum(area_distribution.values())
        
        # Find dominant categories
        dominant = sorted(area_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "success": True,
            "area": actual_area,
            "centroid": centroid,
            "total_pois": total_pois,
            "dominant_categories": [{"category": d[0], "count": d[1]} for d in dominant],
            "recommendations": top_recommendations,
            "gap_analysis": gaps[:5],
            "complementary_opportunities": complementary,
            "message": self._generate_message(actual_area, top_recommendations, dominant, total_pois)
        }
    
    def _generate_message(self, area: str, recommendations: List[Dict], 
                          dominant: List, total_pois: int) -> str:
        """Generate a formatted message for the analysis"""
        msg = f"## Business Opportunities in {area}\n\n"
        msg += f"**Area Overview:** {total_pois} total businesses\n\n"
        
        # Dominant categories
        msg += "**Existing Business Landscape:**\n"
        for cat, count in dominant:
            msg += f"- {cat}: {count} businesses\n"
        msg += "\n"
        
        # Top recommendations
        msg += "### 🎯 Top Recommended Business Categories\n\n"
        for rec in recommendations[:5]:
            emoji = "🔵" if rec['type'] == 'gap' else "🟢"
            msg += f"**{rec['rank']}. {rec['category']}** {emoji}\n"
            msg += f"   - *{rec['reason']}*\n"
            msg += f"   - **Ideas:** {', '.join(rec['examples'])}\n\n"
        
        return msg


# Singleton instance
_analyzer = None

def get_area_analyzer() -> AreaBusinessAnalyzer:
    """Get singleton instance of AreaBusinessAnalyzer"""
    global _analyzer
    if _analyzer is None:
        _analyzer = AreaBusinessAnalyzer()
    return _analyzer
