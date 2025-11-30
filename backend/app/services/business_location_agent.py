"""
Business Location Agent
Uses Groq LLM to understand user's business query and recommend locations.
"""
import os
import json
from typing import Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from app.services.location_recommender import get_recommender, VALID_SUPER_CATEGORIES

# Category mapping from common business types to super categories
BUSINESS_TO_SUPER_CATEGORY = {
    # Food & Beverages
    'cafe': 'Food & Beverages',
    'coffee shop': 'Food & Beverages',
    'restaurant': 'Food & Beverages',
    'bar': 'Food & Beverages',
    'pub': 'Food & Beverages',
    'bakery': 'Food & Beverages',
    'food truck': 'Food & Beverages',
    'pizza': 'Food & Beverages',
    'fast food': 'Food & Beverages',
    'ice cream': 'Food & Beverages',
    'juice bar': 'Food & Beverages',
    'tea shop': 'Food & Beverages',
    'dhaba': 'Food & Beverages',
    'sweet shop': 'Food & Beverages',
    
    # Fitness & Wellness
    'gym': 'Fitness & Wellness',
    'fitness center': 'Fitness & Wellness',
    'yoga studio': 'Fitness & Wellness',
    'spa': 'Fitness & Wellness',
    'salon': 'Fitness & Wellness',
    'beauty parlor': 'Fitness & Wellness',
    'wellness center': 'Fitness & Wellness',
    'pilates': 'Fitness & Wellness',
    'crossfit': 'Fitness & Wellness',
    
    # Health & Medical
    'hospital': 'Health & Medical',
    'clinic': 'Health & Medical',
    'pharmacy': 'Health & Medical',
    'medical store': 'Health & Medical',
    'dentist': 'Health & Medical',
    'doctor': 'Health & Medical',
    'lab': 'Health & Medical',
    'diagnostic center': 'Health & Medical',
    'nursing home': 'Health & Medical',
    
    # Shopping & Retail
    'clothing store': 'Shopping & Retail',
    'boutique': 'Shopping & Retail',
    'electronics': 'Shopping & Retail',
    'mobile shop': 'Shopping & Retail',
    'grocery': 'Shopping & Retail',
    'supermarket': 'Shopping & Retail',
    'mall': 'Shopping & Retail',
    'shoe store': 'Shopping & Retail',
    'jewelry': 'Shopping & Retail',
    'furniture': 'Shopping & Retail',
    'hardware': 'Shopping & Retail',
    'bookstore': 'Shopping & Retail',
    'stationery': 'Shopping & Retail',
    'gift shop': 'Shopping & Retail',
    
    # Entertainment & Leisure
    'cinema': 'Entertainment & Leisure',
    'theatre': 'Entertainment & Leisure',
    'gaming zone': 'Entertainment & Leisure',
    'bowling': 'Entertainment & Leisure',
    'club': 'Entertainment & Leisure',
    'nightclub': 'Entertainment & Leisure',
    'amusement park': 'Entertainment & Leisure',
    'arcade': 'Entertainment & Leisure',
    'escape room': 'Entertainment & Leisure',
    
    # Education & Training
    'school': 'Education & Training',
    'college': 'Education & Training',
    'coaching': 'Education & Training',
    'tuition': 'Education & Training',
    'training center': 'Education & Training',
    'music school': 'Education & Training',
    'dance school': 'Education & Training',
    'driving school': 'Education & Training',
    'language school': 'Education & Training',
    'preschool': 'Education & Training',
    'daycare': 'Education & Training',
    
    # Accommodation & Lodging
    'hotel': 'Accommodation & Lodging',
    'hostel': 'Accommodation & Lodging',
    'guest house': 'Accommodation & Lodging',
    'resort': 'Accommodation & Lodging',
    'motel': 'Accommodation & Lodging',
    'pg': 'Accommodation & Lodging',
    'paying guest': 'Accommodation & Lodging',
    'service apartment': 'Accommodation & Lodging',
    
    # Transport & Auto Services
    'car service': 'Transport & Auto Services',
    'mechanic': 'Transport & Auto Services',
    'garage': 'Transport & Auto Services',
    'car wash': 'Transport & Auto Services',
    'petrol pump': 'Transport & Auto Services',
    'gas station': 'Transport & Auto Services',
    'auto parts': 'Transport & Auto Services',
    'bike service': 'Transport & Auto Services',
    'taxi': 'Transport & Auto Services',
    'parking': 'Transport & Auto Services',
    
    # Financial & Legal Services
    'bank': 'Financial & Legal Services',
    'atm': 'Financial & Legal Services',
    'insurance': 'Financial & Legal Services',
    'ca office': 'Financial & Legal Services',
    'accountant': 'Financial & Legal Services',
    'lawyer': 'Financial & Legal Services',
    'advocate': 'Financial & Legal Services',
    'tax consultant': 'Financial & Legal Services',
    
    # Others
    'office': 'Other / Misc',
    'coworking': 'Other / Misc',
    'warehouse': 'Other / Misc',
}


class BusinessLocationAgent:
    """Agent that understands business queries and recommends locations"""
    
    def __init__(self):
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        
        # Use a capable model for understanding business intent
        self.llm = ChatGroq(
            model="openai/gpt-oss-120b",
            temperature=0,
            api_key=groq_api_key
        )  # type: ignore
        
        self.recommender = get_recommender()
        
        self.system_prompt = SystemMessage(content=f"""
You are a business location advisor assistant. Your task is to:
1. Understand what type of business the user wants to start
2. Map it to one of these super categories: {json.dumps(VALID_SUPER_CATEGORIES)}
3. Return a JSON response with the extracted information

IMPORTANT: Always respond with valid JSON only. No other text.

Response format:
{{
    "business_type": "the specific business mentioned by user",
    "super_category": "one of the valid super categories",
    "confidence": "high/medium/low",
    "reasoning": "brief explanation"
}}

If you cannot determine the business type, respond with:
{{
    "business_type": null,
    "super_category": null,
    "confidence": "low",
    "reasoning": "explanation of what's unclear"
}}

Examples:
- "I want to open a cafe" -> {{"business_type": "cafe", "super_category": "Food & Beverages", "confidence": "high", "reasoning": "Cafe is clearly a food service business"}}
- "Where should I start a gym?" -> {{"business_type": "gym", "super_category": "Fitness & Wellness", "confidence": "high", "reasoning": "Gym is a fitness facility"}}
- "Best location for my clothing boutique" -> {{"business_type": "clothing boutique", "super_category": "Shopping & Retail", "confidence": "high", "reasoning": "Boutique is retail business"}}
""")
    
    def extract_business_type(self, user_query: str) -> Dict[str, Any]:
        """Use LLM to extract business type from user query"""
        
        # First try simple keyword matching
        query_lower = user_query.lower()
        for business, super_cat in BUSINESS_TO_SUPER_CATEGORY.items():
            if business in query_lower:
                return {
                    "business_type": business,
                    "super_category": super_cat,
                    "confidence": "high",
                    "reasoning": f"Matched keyword '{business}'"
                }
        
        # Use LLM for complex queries
        try:
            messages = [self.system_prompt, HumanMessage(content=user_query)]
            result = self.llm.invoke(messages)
            
            # Parse JSON response
            response_text = result.content
            if isinstance(response_text, list):
                # Handle case where content is a list
                response_text = str(response_text[0]) if response_text else ""
            response_text = response_text.strip()
            
            # Handle markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            
            parsed = json.loads(response_text)
            
            # Validate super category
            if parsed.get("super_category") and parsed["super_category"] not in VALID_SUPER_CATEGORIES:
                # Try to find closest match
                parsed["super_category"] = self._find_closest_category(parsed["super_category"])
            
            return parsed
            
        except Exception as e:
            return {
                "business_type": None,
                "super_category": None,
                "confidence": "low",
                "reasoning": f"Error processing query: {str(e)}"
            }
    
    def _find_closest_category(self, category: str) -> str:
        """Find closest matching super category"""
        category_lower = category.lower()
        for valid_cat in VALID_SUPER_CATEGORIES:
            if category_lower in valid_cat.lower() or valid_cat.lower() in category_lower:
                return valid_cat
        return "Other / Misc"
    
    def recommend_locations(self, user_query: str, isochrone_radius_km: float = 1.0,
                            deep_research: bool = False) -> Dict[str, Any]:
        """
        Main entry point: understand query and return location recommendations.
        
        Args:
            user_query: Natural language query like "I want to open a cafe"
            isochrone_radius_km: Radius for analysis (default 1km)
            deep_research: Enable real-time web research for insights
        
        Returns:
            Dict with business understanding and top 3 location recommendations
        """
        # Step 1: Extract business type
        extraction = self.extract_business_type(user_query)
        
        if not extraction.get("super_category"):
            return {
                "success": False,
                "error": "Could not understand the business type from your query",
                "extraction": extraction,
                "recommendations": []
            }
        
        # Step 2: Get location recommendations
        super_category = extraction["super_category"]
        business_type = extraction.get("business_type", super_category)
        
        if deep_research:
            # Use research-enhanced recommendations
            recommendations = self.recommender.recommend_with_research(
                super_category, business_type, isochrone_radius_km
            )
        else:
            recommendations = self.recommender.find_best_locations(super_category, isochrone_radius_km)
        
        if "error" in recommendations:
            return {
                "success": False,
                "error": recommendations["error"],
                "extraction": extraction,
                "recommendations": []
            }
        
        # Step 3: Format response
        return {
            "success": True,
            "query": user_query,
            "business_type": extraction.get("business_type"),
            "super_category": super_category,
            "confidence": extraction.get("confidence"),
            "reasoning": extraction.get("reasoning"),
            "complementary_categories": recommendations.get("complementary_categories", []),
            "isochrone_radius_km": isochrone_radius_km,
            "recommendations": recommendations.get("recommendations", []),
            "research_enabled": recommendations.get("research_enabled", False),
            "message": self._generate_response_message(extraction, recommendations)
        }
    
    def _generate_response_message(self, extraction: Dict, recommendations: Dict) -> str:
        """Generate a human-friendly response message"""
        business = extraction.get("business_type", "your business")
        super_cat = extraction.get("super_category", "")
        
        if not recommendations.get("recommendations"):
            return f"I couldn't find suitable locations for {business}."
        
        top_3 = recommendations["recommendations"][:3]
        
        message = f"Based on my analysis for **{business}** ({super_cat}), here are the top 3 recommended areas:\n\n"
        
        for i, rec in enumerate(top_3, 1):
            message += f"**{i}. {rec['area']}** - Score: {rec['composite_score']}/100\n"
            message += f"   - Area Score: {rec['area_score']} | "
            message += f"Opportunity: {rec['opportunity_score']} ({rec['competitors']} competitors) | "
            message += f"Ecosystem: {rec['ecosystem_score']} ({rec['complementary']} complementary businesses)\n\n"
        
        message += f"\n💡 **Recommendation:** Start with **{top_3[0]['area']}** - it has the best balance of "
        message += f"location factors, low competition, and a strong ecosystem of complementary businesses."
        
        return message


# Singleton instance
_agent = None

def get_business_location_agent() -> BusinessLocationAgent:
    """Get singleton instance of BusinessLocationAgent"""
    global _agent
    if _agent is None:
        _agent = BusinessLocationAgent()
    return _agent
