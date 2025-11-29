"""
Test script for Text-to-SQL functionality
Run this to verify the implementation works correctly
"""
from app.services.text_to_sql_service import TextToSQLService
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_text_to_sql():
    """Test the text-to-SQL service with sample queries"""
    
    print("=" * 60)
    print("Testing Text-to-SQL Service")
    print("=" * 60)
    
    # Initialize service
    sql_service = TextToSQLService(database_path="../atlas.duckdb")
    
    # Test queries
    test_queries = [
        "How many POIs are in the database?",
        "Show me all the different categories of POIs",
        "List the first 5 restaurants",
        "What are all the tables in the database?",
    ]
    
    for i, question in enumerate(test_queries, 1):
        print(f"\n{i}. Question: {question}")
        print("-" * 60)
        
        result = sql_service.query_database_with_nl(question)
        
        if result.get("success"):
            print(f"✓ Success!")
            print(f"SQL: {result['sql']}")
            print(f"Explanation: {result['explanation']}")
            print(f"Rows returned: {result['row_count']}")
            print(f"Summary: {result['summary']}")
            
            if result['row_count'] > 0 and result['row_count'] <= 5:
                print(f"\nResults:")
                for row in result['results']:
                    print(f"  {row}")
        else:
            print(f"✗ Error: {result.get('error')}")
        
        print()

if __name__ == "__main__":
    # Check if GROQ_API_KEY is set
    if not os.getenv("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY environment variable is not set!")
        print("Please set it in your .env file")
        exit(1)
    
    test_text_to_sql()
