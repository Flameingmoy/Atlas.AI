# Text-to-SQL Implementation Guide

## Overview

This implementation adds **natural language database querying** to your Atlas AI chat interface using Groq's LLM API. Users can now ask questions about your data in plain English, and the system will automatically generate SQL, execute it, and return results with natural language summaries.

---

## Architecture & Workflow

### **Pipeline Flow:**

```
User Question (Natural Language)
    ↓
LLM (Groq) + Database Schema
    ↓
SQL Query Generation (JSON Mode)
    ↓
Execute Query on DuckDB
    ↓
Error? → Auto-fix with LLM
    ↓
Natural Language Summary
    ↓
Display Results in Chat UI
```

### **Key Components:**

1. **`text_to_sql_service.py`** - Core service handling SQL generation and execution
2. **`ai_agent.py`** - Updated with `query_database` tool
3. **`App.jsx`** - Frontend enhanced to display query results
4. **`requirements.txt`** - Added dependencies: `groq`, `pandas`, `sqlparse`

---

## Files Modified/Created

### ✅ Created Files:
- `atlas/backend/app/services/text_to_sql_service.py` - Main text-to-SQL service
- `atlas/backend/test_text_to_sql.py` - Test script

### ✅ Modified Files:
- `atlas/backend/app/services/ai_agent.py` - Added `query_database` tool
- `atlas/backend/requirements.txt` - Added dependencies
- `atlas/frontend/src/App.jsx` - Enhanced chat UI for database results

---

## Installation & Setup

### 1. Install Dependencies

```bash
cd atlas/backend
pip install -r requirements.txt
```

### 2. Verify Environment Variables

Make sure your `.env` file has:
```
GROQ_API_KEY=your_groq_api_key_here
```

### 3. Test the Implementation

```bash
cd atlas/backend
python test_text_to_sql.py
```

---

## How It Works

### **Backend Flow:**

1. **User asks a question** via chat: *"How many restaurants are in the database?"*

2. **AI Agent** (`ai_agent.py`) recognizes this as a data query and calls the `query_database` tool

3. **TextToSQLService** (`text_to_sql_service.py`):
   - Extracts database schema (tables, columns, types)
   - Sends schema + question to Groq LLM with JSON mode
   - LLM returns: `{"sql": "SELECT COUNT(*) FROM pois WHERE category='restaurant'", "explanation": "..."}`
   - Executes SQL on DuckDB
   - If error occurs, auto-fixes SQL using LLM
   - Generates natural language summary of results

4. **Response sent to frontend** with:
   - Natural language summary
   - SQL query
   - Raw results (as JSON)
   - Row count

### **Frontend Display:**

The chat interface now shows:
- ✅ Natural language answer
- ✅ Generated SQL query (in code block)
- ✅ Data table (first 10 rows)
- ✅ Row count indicator

---

## Example Queries

Users can now ask questions like:

### Data Exploration:
- *"How many POIs are in the database?"*
- *"Show me all categories of POIs"*
- *"List the first 10 restaurants"*

### Aggregations:
- *"What's the average population density?"*
- *"Count POIs by category"*

### Filtering:
- *"Show me all cafes"*
- *"Find POIs with 'coffee' in the name"*

### Spatial Queries:
- *"Show me POIs with their coordinates"*
- *"List demographics data with H3 indices"*

---

## Technical Details

### **TextToSQLService Class Methods:**

| Method | Purpose |
|--------|---------|
| `get_database_schema()` | Extracts schema from DuckDB |
| `text_to_sql(question)` | Converts NL to SQL using Groq |
| `execute_query(sql)` | Runs SQL on database |
| `validate_and_fix_sql(sql, error)` | Auto-fixes failed queries |
| `summarize_results(question, df)` | Generates NL summary |
| `query_database_with_nl(question)` | Main orchestration method |

### **AI Agent Tool:**

```python
@tool
def query_database(question: str):
    """
    Query the database using natural language.
    Use for data questions about POIs, demographics, etc.
    """
    sql_service = TextToSQLService()
    result = sql_service.query_database_with_nl(question)
    return result
```

### **Response Format:**

```json
{
  "success": true,
  "sql": "SELECT COUNT(*) FROM pois",
  "explanation": "Counts total POIs",
  "results": [{"count": 150}],
  "summary": "There are 150 POIs in the database.",
  "row_count": 1
}
```

---

## Database Schema

Your DuckDB database (`atlas.duckdb`) contains:

### **Table: pois**
- `id` (UUID)
- `name` (VARCHAR)
- `category` (VARCHAR)
- `subcategory` (VARCHAR)
- `location` (GEOMETRY)
- `metadata_json` (JSON)

### **Table: demographics**
- `h3_index` (VARCHAR)
- `population_density` (DOUBLE)
- `median_income` (INTEGER)
- `traffic_score` (DOUBLE)
- `boundary` (GEOMETRY)

---

## Best Practices Implemented

✅ **JSON Mode** - LLM outputs structured JSON for reliable parsing  
✅ **Schema Context** - Full schema provided to LLM for accurate SQL  
✅ **Error Handling** - Auto-fix failed queries using LLM  
✅ **Natural Language Summaries** - User-friendly result presentation  
✅ **Spatial Support** - Handles DuckDB spatial functions (ST_X, ST_Y)  
✅ **Result Limiting** - Shows first 10 rows in UI to prevent overload  

---

## Testing

### Manual Testing via Chat:

1. Start the backend:
```bash
cd atlas/backend
uvicorn app.main:app --reload
```

2. Start the frontend:
```bash
cd atlas/frontend
npm run dev
```

3. Ask questions in the chat:
   - *"How many POIs are there?"*
   - *"Show me all restaurant names"*
   - *"What categories exist?"*

### Automated Testing:

```bash
cd atlas/backend
python test_text_to_sql.py
```

---

## Troubleshooting

### Issue: "GROQ_API_KEY not set"
**Solution:** Add your Groq API key to `atlas/backend/.env`

### Issue: "Failed to generate SQL"
**Solution:** Check your Groq API key is valid and has credits

### Issue: "Failed to execute query"
**Solution:** The auto-fix mechanism should handle this, but check the error message in the response

### Issue: Database not found
**Solution:** Ensure `atlas.duckdb` exists in the project root

---

## Future Enhancements

Potential improvements:

- 🔄 **Query History** - Save and reuse past queries
- 📊 **Visualizations** - Auto-generate charts from results
- 🔍 **Query Suggestions** - Suggest relevant queries based on schema
- 💾 **Export Results** - Download query results as CSV/JSON
- 🎯 **Smart Filtering** - Context-aware query refinement
- 🗺️ **Map Integration** - Plot spatial query results on the map

---

## API Reference

### Chat Endpoint

**POST** `/api/v1/chat`

**Request:**
```json
{
  "message": "How many restaurants are there?"
}
```

**Response:**
```json
{
  "text": "There are 42 restaurants in the database.",
  "actions": [
    {
      "type": "databaseQuery",
      "result": {
        "success": true,
        "sql": "SELECT COUNT(*) FROM pois WHERE category='restaurant'",
        "results": [{"count": 42}],
        "summary": "There are 42 restaurants in the database.",
        "row_count": 1
      }
    }
  ]
}
```

---

## Credits

Implementation based on:
- **Groq Cloud API** - Fast LLM inference
- **DuckDB** - Embedded analytical database
- **LangChain** - LLM framework
- **Your Guide** - `text-to-sql-groq-guide.md`

---

**Implementation Complete! 🎉**

Your Atlas AI chat now supports natural language database queries with automatic SQL generation, execution, and result visualization.
