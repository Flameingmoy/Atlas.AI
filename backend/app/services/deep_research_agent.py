"""
Deep Research Agent Service
Uses Tavily API to search the web and provide real-time insights
for business location and area analysis recommendations.
"""
import os
import asyncio
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

from langchain_groq import ChatGroq

# Initialize clients
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Thread pool for parallel searches
executor = ThreadPoolExecutor(max_workers=3)


class DeepResearchAgent:
    """Agent that performs web research to validate and enhance recommendations"""
    
    def __init__(self):
        if TAVILY_AVAILABLE and TAVILY_API_KEY:
            self.tavily = TavilyClient(api_key=TAVILY_API_KEY)
        else:
            self.tavily = None
        
        if GROQ_API_KEY:
            self.llm = ChatGroq(
                model="openai/gpt-oss-120b",
                api_key=GROQ_API_KEY,
                temperature=0.3
            )  # type: ignore
        else:
            self.llm = None
    
    def is_available(self) -> bool:
        """Check if research capabilities are available"""
        return self.tavily is not None and self.llm is not None
    
    def _search_tavily(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """Perform a Tavily search and return results"""
        if not self.tavily:
            return {"results": [], "answer": None}
        
        try:
            response = self.tavily.search(
                query=query,
                search_depth="basic",
                max_results=max_results,
                include_answer=True
            )
            return response if isinstance(response, dict) else {"results": [], "answer": None}
        except Exception as e:
            print(f"Tavily search error: {e}")
            return {"results": [], "answer": None}
    
    def _summarize_with_llm(self, context: str, prompt: str) -> str:
        """Use LLM to summarize and extract insights from search results"""
        if not self.llm:
            return ""
        
        try:
            full_prompt = f"""Based on the following web search results, {prompt}

Web Search Results:
{context}

Provide a concise, factual response. Focus on recent information and cite specific details when available.
If the search results don't contain relevant information, say so briefly."""
            
            response = self.llm.invoke(full_prompt)
            content = response.content
            return content if isinstance(content, str) else str(content)
        except Exception as e:
            print(f"LLM summarization error: {e}")
            return ""
    
    def research_area_for_business(self, area: str, business_type: str, city: str = "Delhi") -> Dict[str, Any]:
        """
        Research a specific area for a business type.
        Used by Location Recommender to validate recommended areas.
        
        Returns:
            {
                "area": str,
                "business_type": str,
                "research_summary": str,
                "pros": List[str],
                "cons": List[str],
                "market_insights": str,
                "sources": List[str]
            }
        """
        if not self.is_available():
            return self._empty_research_result(area, business_type)
        
        # Search queries for comprehensive research
        queries = [
            f"{business_type} business in {area} {city} market trends 2024 2025",
            f"{area} {city} commercial real estate footfall business environment",
            f"starting {business_type} in {area} Delhi challenges opportunities"
        ]
        
        all_results = []
        all_sources = []
        answer_parts = []
        
        for query in queries:
            response = self._search_tavily(query, max_results=3)
            if response.get("results"):
                all_results.extend(response["results"])
                all_sources.extend([r.get("url", "") for r in response["results"] if r.get("url")])
            if response.get("answer"):
                answer_parts.append(response["answer"])
        
        # Build context from search results
        context = "\n\n".join([
            f"Source: {r.get('title', 'Unknown')}\n{r.get('content', '')}"
            for r in all_results[:8]  # Limit to top 8 results
        ])
        
        if answer_parts:
            context = "Quick Answers:\n" + "\n".join(answer_parts) + "\n\nDetailed Results:\n" + context
        
        # Extract pros and cons using LLM
        pros_cons_prompt = f"""extract specific PROS and CONS of opening a {business_type} in {area}, {city}.

Format your response EXACTLY as:
PROS:
- [specific pro 1]
- [specific pro 2]
- [specific pro 3]

CONS:
- [specific con 1]
- [specific con 2]
- [specific con 3]

Be specific to {area} and {business_type}. Include facts like rental costs, footfall, competition if mentioned."""
        
        pros_cons_response = self._summarize_with_llm(context, pros_cons_prompt)
        
        # Parse pros and cons
        pros, cons = self._parse_pros_cons(pros_cons_response)
        
        # Get market insights summary
        insights_prompt = f"""provide a brief 2-3 sentence market insight summary for opening a {business_type} in {area}, {city}. 
Focus on: current market conditions, customer demographics, and business viability."""
        
        market_insights = self._summarize_with_llm(context, insights_prompt)
        
        return {
            "area": area,
            "business_type": business_type,
            "research_summary": f"Real-time research on {business_type} opportunities in {area}",
            "pros": pros[:4] if pros else ["Research data limited - area shows general business activity"],
            "cons": cons[:4] if cons else ["Limited specific data available for this business type"],
            "market_insights": market_insights or f"Market research for {business_type} in {area} is being analyzed.",
            "sources": list(set(all_sources))[:5]
        }
    
    def research_business_category_in_area(self, category: str, area: str, city: str = "Delhi") -> Dict[str, Any]:
        """
        Research a business category's potential in a specific area.
        Used by Area Business Analyzer to validate recommended categories.
        
        Returns:
            {
                "category": str,
                "area": str,
                "market_potential": str,
                "trends": List[str],
                "opportunities": List[str],
                "challenges": List[str],
                "sources": List[str]
            }
        """
        if not self.is_available():
            return self._empty_category_research(category, area)
        
        # Search queries
        queries = [
            f"{category} business market potential {area} {city} 2024 2025",
            f"{category} industry trends Delhi NCR growth opportunities",
            f"successful {category} businesses {area} {city} case study"
        ]
        
        all_results = []
        all_sources = []
        answer_parts = []
        
        for query in queries:
            response = self._search_tavily(query, max_results=3)
            if response.get("results"):
                all_results.extend(response["results"])
                all_sources.extend([r.get("url", "") for r in response["results"] if r.get("url")])
            if response.get("answer"):
                answer_parts.append(response["answer"])
        
        # Build context
        context = "\n\n".join([
            f"Source: {r.get('title', 'Unknown')}\n{r.get('content', '')}"
            for r in all_results[:8]
        ])
        
        if answer_parts:
            context = "Quick Answers:\n" + "\n".join(answer_parts) + "\n\nDetailed Results:\n" + context
        
        # Extract market potential
        potential_prompt = f"""assess the market potential for {category} businesses in {area}, {city}.
Provide a brief 2-3 sentence assessment covering demand, growth prospects, and competitive landscape."""
        
        market_potential = self._summarize_with_llm(context, potential_prompt)
        
        # Extract trends, opportunities, challenges
        analysis_prompt = f"""analyze {category} business opportunities in {area}, {city}.

Format your response EXACTLY as:
TRENDS:
- [trend 1]
- [trend 2]

OPPORTUNITIES:
- [opportunity 1]
- [opportunity 2]

CHALLENGES:
- [challenge 1]
- [challenge 2]

Be specific and factual based on the search results."""
        
        analysis_response = self._summarize_with_llm(context, analysis_prompt)
        trends, opportunities, challenges = self._parse_trends_analysis(analysis_response)
        
        return {
            "category": category,
            "area": area,
            "market_potential": market_potential or f"Analyzing market potential for {category} in {area}.",
            "trends": trends[:3] if trends else ["Growing demand for quality services"],
            "opportunities": opportunities[:3] if opportunities else ["Underserved market segments exist"],
            "challenges": challenges[:3] if challenges else ["Competition from established players"],
            "sources": list(set(all_sources))[:5]
        }
    
    def research_multiple_areas(self, areas: List[str], business_type: str, city: str = "Delhi") -> List[Dict]:
        """Research multiple areas in parallel for a business type"""
        if not self.is_available():
            return [self._empty_research_result(area, business_type) for area in areas]
        
        results = []
        for area in areas[:3]:  # Limit to top 3
            result = self.research_area_for_business(area, business_type, city)
            results.append(result)
        
        return results
    
    def research_multiple_categories(self, categories: List[str], area: str, city: str = "Delhi") -> List[Dict]:
        """Research multiple business categories in parallel for an area"""
        if not self.is_available():
            return [self._empty_category_research(cat, area) for cat in categories]
        
        results = []
        for category in categories[:3]:  # Limit to top 3
            result = self.research_business_category_in_area(category, area, city)
            results.append(result)
        
        return results
    
    def _parse_pros_cons(self, text: str) -> tuple:
        """Parse PROS and CONS from LLM response"""
        pros = []
        cons = []
        
        current_section = None
        for line in text.split('\n'):
            line = line.strip()
            if 'PROS:' in line.upper():
                current_section = 'pros'
            elif 'CONS:' in line.upper():
                current_section = 'cons'
            elif line.startswith('-') or line.startswith('•'):
                item = line.lstrip('-•').strip()
                if item and len(item) > 5:
                    if current_section == 'pros':
                        pros.append(item)
                    elif current_section == 'cons':
                        cons.append(item)
        
        return pros, cons
    
    def _parse_trends_analysis(self, text: str) -> tuple:
        """Parse TRENDS, OPPORTUNITIES, CHALLENGES from LLM response"""
        trends = []
        opportunities = []
        challenges = []
        
        current_section = None
        for line in text.split('\n'):
            line = line.strip()
            if 'TRENDS:' in line.upper():
                current_section = 'trends'
            elif 'OPPORTUNITIES:' in line.upper():
                current_section = 'opportunities'
            elif 'CHALLENGES:' in line.upper():
                current_section = 'challenges'
            elif line.startswith('-') or line.startswith('•'):
                item = line.lstrip('-•').strip()
                if item and len(item) > 5:
                    if current_section == 'trends':
                        trends.append(item)
                    elif current_section == 'opportunities':
                        opportunities.append(item)
                    elif current_section == 'challenges':
                        challenges.append(item)
        
        return trends, opportunities, challenges
    
    def _empty_research_result(self, area: str, business_type: str) -> Dict:
        """Return empty result when research is not available"""
        return {
            "area": area,
            "business_type": business_type,
            "research_summary": "Deep research not available",
            "pros": [],
            "cons": [],
            "market_insights": "Enable Tavily API for real-time market research.",
            "sources": []
        }
    
    def _empty_category_research(self, category: str, area: str) -> Dict:
        """Return empty result when research is not available"""
        return {
            "category": category,
            "area": area,
            "market_potential": "Deep research not available",
            "trends": [],
            "opportunities": [],
            "challenges": [],
            "sources": []
        }


# Singleton instance
_research_agent = None

def get_research_agent() -> DeepResearchAgent:
    """Get singleton instance of DeepResearchAgent"""
    global _research_agent
    if _research_agent is None:
        _research_agent = DeepResearchAgent()
    return _research_agent
