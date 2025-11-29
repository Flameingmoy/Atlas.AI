# Text-to-SQL Implementation

## Overview

Atlas.AI uses Groq's LLM API to convert natural language questions into SQL queries. This enables users to query the database without writing SQL.

## Architecture

```
User Question (Natural Language)
         │
         ▼
┌─────────────────────────┐
│   LLM (Groq)            │
│   + Database Schema     │
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│   SQL Query Generation  │
│   (JSON Mode)           │
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│   Execute on DuckDB     │
└───────────┬─────────────┘
            ▼
    Error? ──Yes──► Auto-fix with LLM
            │
            No
            ▼
┌─────────────────────────┐
│   Natural Language      │
│   Summary               │
└───────────┬─────────────┘
            ▼
   Display in Chat UI
```

## Implementation

### TextToSQLService Class

Located at: `backend/app/services/text_to_sql_service.py`

#### Key Methods

| Method | Purpose |
|--------|---------|
| `get_database_schema()` | Extracts schema from DuckDB |
| `text_to_sql(question)` | Converts NL to SQL using Groq |
| `execute_query(sql)` | Runs SQL on database |
| `validate_and_fix_sql(sql, error)` | Auto-fixes failed queries |
| `summarize_results(question, df)` | Generates NL summary |
| `query_database_with_nl(question)` | Main orchestration method |

### Schema Extraction

```python
def get_database_schema(database_path):
    conn = duckdb.connect(database_path)
    schema_context = "Database Schema:\n\n"
    tables = conn.execute("SELECT name FROM duckdb_tables()").fetchall()

    for table_name in tables:
        schema_context += f"Table: {table_name[0]}\n"
        columns = conn.execute(f"PRAGMA table_info({table_name[0]})").fetchall()
        for col in columns:
            schema_context += f"  - {col[1]} ({col[2]})\n"
        schema_context += "\n"
    conn.close()
    return schema_context
```

### LLM Prompt (JSON Mode)

```python
def create_system_prompt(schema_context):
    return f"""You are a SQL expert. Convert natural language questions to SQL queries.

{schema_context}

IMPORTANT:
- Only use tables and columns that exist in the schema
- Write valid SQL syntax
- Return ONLY valid JSON with this format:
{{
  "sql": "SELECT * FROM table WHERE ...",
  "explanation": "Brief explanation of the query"
}}

Do NOT include markdown formatting or extra text."""
```

### SQL Generation with Groq

```python
def text_to_sql(user_question, schema_context, model="llama-3.3-70b-versatile"):
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {user_question}"}
        ],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=1024
    )
    result = json.loads(completion.choices[0].message.content)
    return result["sql"], result["explanation"]
```

### Auto-Fix on Error

```python
def validate_and_fix_sql(sql_query, error_message, schema_context):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": f"You are a SQL expert. Fix invalid SQL.\n\n{schema_context}"},
            {"role": "user", "content": f"This SQL failed: {error_message}\n\nFix it:\n{sql_query}"}
        ],
        temperature=0
    )
    return completion.choices[0].message.content.strip()
```

## Configuration

### Environment Variables

```env
GROQ_API_KEY=your_groq_api_key_here
```

### Dependencies

```
groq
pandas
sqlparse
duckdb
```

## Example Queries

### Data Exploration
- "How many POIs are in the database?"
- "Show me all categories of POIs"
- "List the first 10 restaurants"

### Aggregations
- "What's the most common POI type?"
- "Count POIs by category"

### Filtering
- "Show me all cafes"
- "Find POIs with 'coffee' in the name"

### Spatial Queries
- "Show me POIs with their coordinates"
- "List demographics data with H3 indices"

## Testing

```bash
cd backend
python test_text_to_sql.py
```
