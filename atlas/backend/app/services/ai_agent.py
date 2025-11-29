from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List, Dict, Any
import json
import os
from app.services.text_to_sql_service import TextToSQLService

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
def get_delhi_info():
    """
    Returns general information about Delhi, India.
    Useful for answering questions about Delhi's characteristics.
    """
    return {
        "city": "Delhi",
        "capital": "National Capital Territory of India",
        "population": "~20 million (metro area)",
        "area": "1,484 km²",
        "known_for": "Historical monuments, government center, diverse culture"
    }

@tool
def query_database(question: str):
    """
    Query the database using natural language.
    Use this tool when the user asks data questions like:
    - "How many points of interest are there?"
    - "Show me all areas in Delhi"
    - "What are the categories in delhi_points?"
    - "List all pincodes"
    - "Show me points by category"
    Returns structured data results from the database.
    """
    sql_service = TextToSQLService()
    result = sql_service.query_database_with_nl(question)
    return result

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
        self.tools = [set_map_layer, get_delhi_info, query_database]
        self.llm_with_tools = self.llm.bind_tools(self.tools)
        
        self.system_prompt = SystemMessage(content="""
        You are Atlas, an intelligent geospatial assistant.
        Your goal is to help users explore and analyze geographic data for Delhi, India (National Capital Territory).
        
        You have control over a map interface and can query the database.
        
        TOOL USAGE:
        - If the user asks to see something visual (e.g., "Show me areas", "Where are the points?"), 
          call the `set_map_layer` tool.
        - If the user asks for general information about Delhi, call `get_delhi_info`.
        - If the user asks specific data questions about areas, pincodes, points of interest, or wants to query the database,
          call the `query_database` tool with their question.
        
        The database contains:
        - delhi_area: Area/district boundaries
        - delhi_city: City boundaries
        - delhi_pincode: Pincode boundaries
        - delhi_points: Points of interest with categories
        
        Examples of when to use query_database:
        - "How many points are in the database?"
        - "Show me all areas"
        - "What categories exist in delhi_points?"
        - "List all pincodes"
        
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
                
                elif tool_name == "get_delhi_info":
                    # Return Delhi general info
                    pass
                
                elif tool_name == "query_database":
                    # Execute the database query tool
                    from app.services.text_to_sql_service import TextToSQLService
                    sql_service = TextToSQLService()
                    query_result = sql_service.query_database_with_nl(tool_args.get("question", ""))
                    
                    response_data["actions"].append({
                        "type": "databaseQuery",
                        "result": query_result
                    })
                    
                    # Update text response with the summary
                    if query_result.get("success"):
                        response_data["text"] = query_result.get("summary", "Query executed successfully.")
                    else:
                        response_data["text"] = f"Sorry, I encountered an error: {query_result.get('error', 'Unknown error')}"

        return response_data
