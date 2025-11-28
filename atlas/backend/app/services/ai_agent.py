from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict, Any
import json
import os

# Define Tools
@tool
def set_map_layer(layer_name: str):
    """
    Switches the map layer to the specified layer.
    Valid layers are: 'competitors', 'heatmap'.
    Use 'competitors' to show individual points of interest.
    Use 'heatmap' to show demand density.
    """
    return {"action": "setLayer", "layer": layer_name}

@tool
def get_bangalore_demographics():
    """
    Returns demographic data for Bangalore, India.
    Useful for answering questions about population, income, or traffic.
    """
    return {
        "city": "Bangalore",
        "population_density": "Very High (11,000/sq km)",
        "median_income": "₹8,00,000 (Tech Sector High)",
        "traffic_hotspots": ["Silk Board", "Tin Factory", "MG Road", "Outer Ring Road"]
    }

class AIAgentService:
    def __init__(self):
        # Initialize ChatGroq with API key from environment
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0,
            api_key=groq_api_key
        )
        
        # Bind tools to the LLM
        self.tools = [set_map_layer, get_bangalore_demographics]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        self.system_prompt = SystemMessage(content="""
        You are Atlas, an intelligent geospatial assistant.
        Your goal is to help users find optimal business locations in Bangalore, India (the Silicon Valley of India).
        
        You have control over a map interface.
        - If the user asks to see something visual (e.g., "Show me traffic", "Where are the competitors?"), 
          call the `set_map_layer` tool.
        - If the user asks for data/stats, call `get_bangalore_demographics` or answer from your knowledge.
        
        Always be concise and professional.
        """)

    def process_message(self, user_message: str) -> Dict[str, Any]:
        messages = [self.system_prompt, HumanMessage(content=user_message)]
        
        # Invoke the LLM
        result = self.llm_with_tools.invoke(messages)
        
        response_data = {
            "text": result.content,
            "actions": []
        }
        
        # Check for tool calls
        if result.tool_calls:
            for tool_call in result.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # Execute tool (simulated for map control, we just return the action to frontend)
                if tool_name == "set_map_layer":
                    response_data["actions"].append({
                        "type": "setLayer",
                        "layer": tool_args.get("layer_name")
                    })
                    # Add a confirmation message if the LLM didn't generate one
                    if not response_data["text"]:
                        response_data["text"] = f"I've switched the map to show {tool_args.get('layer_name')}."
                
                elif tool_name == "get_austin_demographics":
                    # For data tools, we might want to feed the result back to the LLM
                    # But for this prototype, let's just return the data or have the LLM describe it.
                    # Since qwen3:32b is powerful, let's actually run the tool and feed it back?
                    # For simplicity/speed in prototype, let's just return the raw data in text if needed,
                    # or let the LLM hallucinate/use its internal knowledge if it didn't call the tool for data.
                    # Actually, let's just let the LLM handle the conversation.
                    pass

        return response_data
