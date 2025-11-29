import duckdb
import json
import os
from groq import Groq
from typing import Tuple, Optional, Dict, Any, List
import pandas as pd
import numpy as np
from uuid import UUID
from decimal import Decimal

class TextToSQLService:
    """
    Service for converting natural language questions to SQL queries
    and executing them against the DuckDB database.
    """
    
    def __init__(self, database_path: str = "atlas.duckdb"):
        self.database_path = database_path
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
        self.client = Groq(api_key=groq_api_key)
        self.model = "llama-3.3-70b-versatile"
        
    def get_database_schema(self) -> str:
        """
        Extract database schema (tables, columns, types) from DuckDB.
        Returns a formatted string representation of the schema.
        """
        conn = duckdb.connect(self.database_path)
        
        # Load extensions
        try:
            conn.install_extension("spatial")
            conn.load_extension("spatial")
            conn.install_extension("h3", repository="community")
            conn.load_extension("h3")
        except:
            pass  # Extensions might already be loaded
        
        schema_context = "Database Schema:\n\n"
        
        # Get all tables
        tables = conn.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'main'
        """).fetchall()
        
        for table_tuple in tables:
            table_name = table_tuple[0]
            schema_context += f"Table: {table_name}\n"
            
            # Get columns for each table
            columns = conn.execute(f"""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = '{table_name}'
            """).fetchall()
            
            for col in columns:
                schema_context += f"  - {col[0]} ({col[1]})\n"
            schema_context += "\n"
        
        # Add additional context about the database
        schema_context += """
Additional Context:
- The 'delhi_area' table contains area/district boundaries for Delhi
- The 'delhi_city' table contains city boundary data for Delhi
- The 'delhi_pincode' table contains pincode/postal code boundaries for Delhi
- The 'delhi_points' table contains points of interest in Delhi with spatial data
- Use ST_Y(geom) for latitude and ST_X(geom) for longitude from GEOMETRY columns
- All tables use 'geom' column for geometric data (POINT, POLYGON, MULTIPOLYGON)
- The 'delhi_points' table contains various categories of points of interest
- For point data, use ST_AsText(geom) to get WKT format or ST_X/ST_Y to extract coordinates
"""
        
        conn.close()
        return schema_context
    
    def create_system_prompt(self, schema_context: str) -> str:
        """
        Create the system prompt for SQL generation with schema context.
        """
        return f"""You are a SQL expert specializing in DuckDB with spatial extensions. Convert natural language questions to SQL queries.

{schema_context}

IMPORTANT RULES:
- Only use tables and columns that exist in the schema above
- Write valid DuckDB SQL syntax
- For spatial queries, use ST_X() for longitude and ST_Y() for latitude
- Use proper spatial functions like ST_Distance, ST_Within, etc. when needed
- Return ONLY valid JSON with this exact format:
{{
  "sql": "SELECT * FROM table WHERE ...",
  "explanation": "Brief explanation of what this query does"
}}

Do NOT include markdown formatting, code blocks, or any extra text outside the JSON."""
    
    def text_to_sql(self, user_question: str) -> Tuple[str, str]:
        """
        Convert a natural language question to SQL using Groq LLM.
        Returns: (sql_query, explanation)
        """
        schema_context = self.get_database_schema()
        system_prompt = self.create_system_prompt(schema_context)
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Question: {user_question}"}
                ],
                response_format={"type": "json_object"},
                temperature=0,
                max_tokens=1024
            )
            
            response_text = completion.choices[0].message.content
            result = json.loads(response_text)
            
            return result.get("sql", ""), result.get("explanation", "")
        except Exception as e:
            raise Exception(f"Failed to generate SQL: {str(e)}")
    
    def execute_query(self, sql_query: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
        """
        Execute SQL query against the database.
        Returns: (results_dataframe, error_message)
        """
        conn = duckdb.connect(self.database_path)
        
        # Load extensions
        try:
            conn.install_extension("spatial")
            conn.load_extension("spatial")
            conn.install_extension("h3", repository="community")
            conn.load_extension("h3")
        except:
            pass
        
        try:
            results = conn.execute(sql_query).fetchdf()
            conn.close()
            return results, None
        except Exception as e:
            conn.close()
            return None, str(e)
    
    def validate_and_fix_sql(self, sql_query: str, error_message: str) -> str:
        """
        Use LLM to fix a failed SQL query based on the error message.
        """
        schema_context = self.get_database_schema()
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": f"You are a SQL expert. Fix invalid DuckDB SQL queries.\n\n{schema_context}"
                    },
                    {
                        "role": "user", 
                        "content": f"""This SQL query failed with the following error:
Error: {error_message}

Original SQL:
{sql_query}

Please fix the SQL query and return ONLY the corrected SQL statement without any markdown formatting or explanation."""
                    }
                ],
                temperature=0,
                max_tokens=512
            )
            
            fixed_sql = completion.choices[0].message.content.strip()
            # Remove markdown code blocks if present
            if fixed_sql.startswith("```"):
                lines = fixed_sql.split("\n")
                fixed_sql = "\n".join(lines[1:-1]) if len(lines) > 2 else fixed_sql
            
            return fixed_sql
        except Exception as e:
            raise Exception(f"Failed to fix SQL: {str(e)}")
    
    def summarize_results(self, question: str, df: pd.DataFrame) -> str:
        """
        Generate a natural language summary of query results.
        """
        # Limit dataframe size for the prompt
        df_preview = df.head(20).to_string() if len(df) > 20 else df.to_string()
        row_count = len(df)
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user", 
                        "content": f"""Question: {question}

Data (showing {min(20, row_count)} of {row_count} rows):
{df_preview}

Provide a concise, natural language summary of these results. Be specific with numbers and insights."""
                    }
                ],
                temperature=0,
                max_tokens=512
            )
            
            return completion.choices[0].message.content
        except Exception as e:
            return f"Query returned {row_count} results. Here's a preview: {df.head(3).to_dict('records')}"
    
    def sanitize_results(self, results_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert non-JSON-serializable types to JSON-compatible formats.
        Handles: UUID, numpy types, geometry objects, decimals, dates, etc.
        """
        sanitized = []
        
        for row in results_list:
            sanitized_row = {}
            for key, value in row.items():
                # Handle None
                if value is None:
                    sanitized_row[key] = None
                # Handle UUID
                elif isinstance(value, UUID):
                    sanitized_row[key] = str(value)
                # Handle numpy types
                elif isinstance(value, (np.integer, np.floating)):
                    sanitized_row[key] = value.item()
                elif isinstance(value, np.bool_):
                    sanitized_row[key] = bool(value)
                elif isinstance(value, np.ndarray):
                    sanitized_row[key] = value.tolist()
                # Handle Decimal
                elif isinstance(value, Decimal):
                    sanitized_row[key] = float(value)
                # Handle datetime/date
                elif hasattr(value, 'isoformat'):
                    sanitized_row[key] = value.isoformat()
                # Handle bytes
                elif isinstance(value, bytes):
                    sanitized_row[key] = value.decode('utf-8', errors='replace')
                # Handle geometry objects (convert to WKT string)
                elif hasattr(value, '__class__') and 'geometry' in str(type(value)).lower():
                    sanitized_row[key] = str(value)
                # Native Python types (str, int, float, bool, list, dict) pass through
                elif isinstance(value, (str, int, float, bool, list, dict)):
                    sanitized_row[key] = value
                # Fallback: convert to string
                else:
                    sanitized_row[key] = str(value)
            
            sanitized.append(sanitized_row)
        
        return sanitized
    
    def query_database_with_nl(self, user_question: str) -> Dict[str, Any]:
        """
        Main orchestration function: converts natural language to SQL,
        executes it, and returns results with natural language summary.
        
        Returns: {
            "success": bool,
            "sql": str,
            "explanation": str,
            "results": list of dicts,
            "summary": str,
            "error": str (if failed)
        }
        """
        try:
            # Generate SQL
            sql_query, explanation = self.text_to_sql(user_question)
            
            # Execute query
            results_df, error = self.execute_query(sql_query)
            
            # If error, try to fix the SQL
            if error:
                try:
                    fixed_sql = self.validate_and_fix_sql(sql_query, error)
                    results_df, error = self.execute_query(fixed_sql)
                    if not error:
                        sql_query = fixed_sql  # Update to the fixed version
                except:
                    pass  # If fixing fails, continue with original error
            
            # If still error, return error response
            if error:
                return {
                    "success": False,
                    "sql": sql_query,
                    "explanation": explanation,
                    "error": f"Failed to execute query: {error}"
                }
            
            # Convert results to list of dicts
            results_list = results_df.to_dict('records') if results_df is not None else []
            
            # Sanitize results to ensure JSON serialization
            sanitized_results = self.sanitize_results(results_list)
            
            # Generate natural language summary
            summary = self.summarize_results(user_question, results_df)
            
            return {
                "success": True,
                "sql": sql_query,
                "explanation": explanation,
                "results": sanitized_results,
                "summary": summary,
                "row_count": len(sanitized_results)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
