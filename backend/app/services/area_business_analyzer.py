"""
Area Business Analyzer Service
Analyzes what businesses would be good to open in a specific area
by looking at gaps (underserved categories) and complementary opportunities.
"""
import os
import pandas as pd
from typing import Dict, List, Any, Optional
from app.core.db import execute_query
from app.services.location_recommender import WEIGHTS, COMPLEMENTARY_CATEGORIES

# Path to area scores CSV
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data')
AREA_SCORES_CSV = os.path.join(DATA_DIR, 'Delhi_Areas_All_11_Criteria_Real_Data.csv')

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
        self._load_area_scores()
    
    def _load_area_scores(self):
        """Load area scores from CSV"""
        try:
            self.areas_df = pd.read_csv(AREA_SCORES_CSV)
        except FileNotFoundError:
            self.areas_df = None
    
    def get_area_base_score(self, area_name: str, super_category: str) -> Optional[float]:
        """Calculate base score for an area and business category"""
        if self.areas_df is None:
            return None
        
        weights = WEIGHTS.get(super_category, WEIGHTS.get('Other / Misc', {}))
        if not weights:
            return None
        
        # Find the area in dataframe (case-insensitive)
        area_row = self.areas_df[self.areas_df['name'].str.lower() == area_name.lower()]
        if area_row.empty:
            # Try fuzzy match
            area_row = self.areas_df[self.areas_df['name'].str.lower().str.contains(area_name.lower())]
        
        if area_row.empty:
            return None
        
        row = area_row.iloc[0]
        score = 0.0
        for feature, weight in weights.items():
            if feature in row:
                score += (row[feature] * weight / 100)
        
        return round(score, 2)
    
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
    
    def get_delhi_total_stats(self) -> Dict[str, Any]:
        """Get city-wide statistics for trend comparison"""
        # Get total POI count
        total_query = "SELECT COUNT(*) FROM points_super"
        total_result = execute_query(total_query, ())
        total_pois = total_result[0][0] if total_result else 0
        
        # Get number of areas
        area_count_query = "SELECT COUNT(*) FROM delhi_area"
        area_result = execute_query(area_count_query, ())
        num_areas = area_result[0][0] if area_result else 1
        
        # Get category count
        cat_query = "SELECT COUNT(DISTINCT super_category) FROM points_super"
        cat_result = execute_query(cat_query, ())
        total_categories = cat_result[0][0] if cat_result else 0
        
        return {
            "total_pois": total_pois,
            "num_areas": num_areas,
            "avg_pois_per_area": total_pois / num_areas if num_areas > 0 else 0,
            "total_categories": total_categories
        }
    
    def calculate_area_trend(self, area_distribution: Dict[str, int], 
                             delhi_average: Dict[str, float],
                             delhi_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate area trend indicator based on:
        1. POI density relative to city average
        2. Category diversity (how many categories are present)
        3. Competition concentration (how evenly distributed businesses are)
        
        Returns: {
            'indicator': 'emerging' | 'growing' | 'saturated',
            'emoji': '🌱' | '📈' | '🔴',
            'label': 'Emerging Market' | 'Growing Market' | 'Saturated Market',
            'reason': explanation string,
            'metrics': detailed breakdown
        }
        """
        total_pois = sum(area_distribution.values())
        avg_pois_per_area = delhi_stats.get("avg_pois_per_area", 1)
        total_categories = delhi_stats.get("total_categories", 1)
        
        # 1. POI Density Score (0-100)
        # Ratio of area POIs to city average
        density_ratio = total_pois / avg_pois_per_area if avg_pois_per_area > 0 else 0
        
        # 2. Category Diversity Score (0-100)
        # How many of the total categories are present
        categories_present = len(area_distribution)
        diversity_ratio = categories_present / total_categories if total_categories > 0 else 0
        
        # 3. Competition Concentration (0-100, higher = more concentrated = less diverse)
        # Using Herfindahl-Hirschman Index style calculation
        if total_pois > 0:
            shares = [(count / total_pois) ** 2 for count in area_distribution.values()]
            concentration = sum(shares)  # 0 to 1, where 1 = perfectly concentrated
        else:
            concentration = 0
        
        # Build metrics for detailed breakdown
        metrics = {
            "poi_density": round(density_ratio * 100, 1),
            "category_diversity": round(diversity_ratio * 100, 1),
            "competition_concentration": round(concentration * 100, 1),
            "total_pois": total_pois,
            "categories_present": categories_present,
            "city_avg_pois": round(avg_pois_per_area, 1)
        }
        
        # Classification logic
        # Emerging: Low density, low diversity
        # Growing: Medium density, good diversity, moderate concentration
        # Saturated: High density, high diversity, varied concentration
        
        reasons = []
        
        if density_ratio < 0.5:
            # Low POI density - Emerging
            indicator = "emerging"
            emoji = "🌱"
            label = "Emerging Market"
            reasons.append(f"Low business density ({total_pois} POIs vs {round(avg_pois_per_area)} city avg)")
            if diversity_ratio < 0.5:
                reasons.append(f"Only {categories_present} of {total_categories} categories present")
            else:
                reasons.append("Room for early movers in multiple categories")
                
        elif density_ratio < 1.2:
            # Medium density - Growing
            indicator = "growing"
            emoji = "📈"
            label = "Growing Market"
            reasons.append(f"Moderate business activity ({total_pois} POIs, {round(density_ratio * 100)}% of city avg)")
            if concentration < 0.3:
                reasons.append("Balanced business mix with opportunities")
            else:
                # Find dominant category
                dominant = max(area_distribution.items(), key=lambda x: x[1])
                reasons.append(f"Some concentration in {dominant[0]} ({dominant[1]} POIs)")
                
        else:
            # High density - Saturated
            indicator = "saturated"
            emoji = "🔴"
            label = "Saturated Market"
            reasons.append(f"High business density ({total_pois} POIs, {round(density_ratio * 100)}% of city avg)")
            if diversity_ratio > 0.7:
                reasons.append(f"All major categories well-represented ({categories_present} categories)")
            # Find dominant category
            dominant = max(area_distribution.items(), key=lambda x: x[1])
            dominant_pct = round((dominant[1] / total_pois) * 100)
            if dominant_pct > 30:
                reasons.append(f"Heavy competition in {dominant[0]} ({dominant_pct}% market share)")
        
        return {
            "indicator": indicator,
            "emoji": emoji,
            "label": label,
            "reason": " • ".join(reasons),
            "metrics": metrics
        }
    
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
                
                # Generate data-driven cons for gap opportunities
                gap_cons = []
                if gap['area_count'] == 0:
                    gap_cons.append(f"Zero existing {gap['category']} businesses - unproven market")
                elif gap['area_count'] < 5:
                    gap_cons.append(f"Only {gap['area_count']} existing businesses - limited proven demand")
                
                # Check if the gap is extreme (might indicate area isn't suitable)
                if gap['gap_score'] > 90:
                    gap_cons.append(f"Very low presence ({gap['area_count']} vs {gap['delhi_average']} avg) - may indicate unsuitable location")
                
                # Check if complementary businesses exist to drive traffic
                complementary_cats = COMPLEMENTARY_MAP.get(gap['category'], [])
                complementary_count = sum(area_distribution.get(c, 0) for c in complementary_cats)
                if complementary_count < 10:
                    gap_cons.append(f"Limited supporting businesses ({complementary_count} complementary POIs)")
                
                # Calculate scoring breakdown
                base_score = self.get_area_base_score(actual_area, gap['category'])
                # Opportunity score: inverse of competition (higher when fewer competitors)
                opportunity_score = gap['gap_score']  # Already calculated as gap score
                # Ecosystem score: based on complementary businesses
                ecosystem_score = min(100, (complementary_count / 50) * 100) if complementary_count > 0 else 0
                
                top_recommendations.append({
                    'rank': len(top_recommendations) + 1,
                    'category': gap['category'],
                    'reason': f"Gap opportunity - only {gap['area_count']} vs {gap['delhi_average']} Delhi avg",
                    'score': gap['gap_score'],
                    'examples': examples[:4],
                    'type': 'gap',
                    'cons': gap_cons[:2] if gap_cons else ["Low competition - first mover advantage but unproven demand"],
                    'competitors': gap['area_count'],
                    'complementary': complementary_count,
                    'base_score': base_score,
                    'opportunity_score': round(opportunity_score, 2),
                    'ecosystem_score': round(ecosystem_score, 2)
                })
        
        # Add top complementary opportunities
        for comp in complementary:
            if comp['category'] not in seen_categories and len(top_recommendations) < 5:
                seen_categories.add(comp['category'])
                examples = BUSINESS_EXAMPLES.get(comp['category'], [])
                
                # Generate data-driven cons for complementary opportunities
                comp_cons = []
                existing_count = comp['existing_complementary']
                
                if existing_count > 0:
                    comp_cons.append(f"{existing_count} similar businesses already compete in this area")
                
                # Check saturation relative to Delhi average
                cat_delhi_avg = delhi_average.get(comp['category'], 0)
                if cat_delhi_avg > 0 and existing_count > cat_delhi_avg:
                    saturation_pct = round((existing_count / cat_delhi_avg) * 100)
                    comp_cons.append(f"Above Delhi average ({saturation_pct}% saturation)")
                
                # Check dependency on complementary businesses
                comp_cons.append(f"Depends on traffic from {comp['reason'].split('(')[0].strip().split()[-1]} businesses")
                
                # Get complementary business count for this category
                complementary_cats = COMPLEMENTARY_CATEGORIES.get(comp['category'], [])
                complementary_count = sum(area_distribution.get(c, 0) for c in complementary_cats)
                
                # Calculate scoring breakdown
                base_score = self.get_area_base_score(actual_area, comp['category'])
                # Opportunity score: inverse of competition
                opportunity_score = max(0, 100 - (existing_count / max(cat_delhi_avg, 1) * 50)) if cat_delhi_avg > 0 else 50
                # Ecosystem score: high because this is complementary (driven by existing businesses)
                ecosystem_score = min(100, (complementary_count / 30) * 100)
                
                top_recommendations.append({
                    'rank': len(top_recommendations) + 1,
                    'category': comp['category'],
                    'reason': comp['reason'],
                    'score': comp['opportunity_score'],
                    'examples': examples[:4],
                    'type': 'complementary',
                    'cons': comp_cons[:2],
                    'competitors': existing_count,
                    'complementary': complementary_count,
                    'base_score': base_score,
                    'opportunity_score': round(opportunity_score, 2),
                    'ecosystem_score': round(ecosystem_score, 2)
                })
        
        # Calculate total POIs
        total_pois = sum(area_distribution.values())
        
        # Find dominant categories
        dominant = sorted(area_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Calculate area trend indicator
        delhi_stats = self.get_delhi_total_stats()
        trend_indicator = self.calculate_area_trend(area_distribution, delhi_average, delhi_stats)
        
        return {
            "success": True,
            "area": actual_area,
            "centroid": centroid,
            "location_source": location_source,  # "area" or "poi"
            "radius_km": 1.0 if location_source == "poi" else None,  # radius used for POI-based analysis
            "total_pois": total_pois,
            "trend_indicator": trend_indicator,
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
    
    def analyze_with_research(self, area_name: str) -> Dict[str, Any]:
        """
        Enhanced analysis that includes deep research insights for top 3 business categories.
        
        Args:
            area_name: Name of the area to analyze
            
        Returns:
            Standard analysis with added 'research' field for top 3 recommendations
        """
        # Get base analysis
        base_result = self.analyze_area(area_name)
        
        if not base_result.get("success"):
            return base_result
        
        # Import research agent
        from app.services.deep_research_agent import get_research_agent
        research_agent = get_research_agent()
        
        if not research_agent.is_available():
            # Return base results with empty research
            for rec in base_result.get("recommendations", [])[:3]:
                rec["research"] = {
                    "market_potential": "Deep research not available. Set TAVILY_API_KEY to enable.",
                    "trends": [],
                    "opportunities": [],
                    "challenges": [],
                    "sources": []
                }
            base_result["research_enabled"] = False
            return base_result
        
        # Get area name and research top 3 categories
        area = base_result.get("area", area_name)
        top_categories = [rec['category'] for rec in base_result.get("recommendations", [])[:3]]
        research_results = research_agent.research_multiple_categories(top_categories, area)
        
        # Merge research into recommendations
        research_map = {r['category']: r for r in research_results}
        for rec in base_result.get("recommendations", [])[:3]:
            cat_research = research_map.get(rec['category'], {})
            rec["research"] = {
                "market_potential": cat_research.get("market_potential", ""),
                "trends": cat_research.get("trends", []),
                "opportunities": cat_research.get("opportunities", []),
                "challenges": cat_research.get("challenges", []),
                "sources": cat_research.get("sources", [])
            }
        
        # Mark recommendations beyond top 3 as not researched
        for rec in base_result.get("recommendations", [])[3:]:
            rec["research"] = None
        
        base_result["research_enabled"] = True
        return base_result


# Singleton instance
_analyzer = None

def get_area_analyzer() -> AreaBusinessAnalyzer:
    """Get singleton instance of AreaBusinessAnalyzer"""
    global _analyzer
    if _analyzer is None:
        _analyzer = AreaBusinessAnalyzer()
    return _analyzer
