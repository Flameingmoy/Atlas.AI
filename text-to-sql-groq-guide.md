# Building a Text-to-SQL App with Groq Cloud API

## Overview

This guide outlines how to create your own **Text-to-SQL** system—similar to HuggingFace's smol-agents example—using the Groq Cloud API. You get natural language (text) input from the user, use a large language model to generate SQL, run that SQL on your database, and return results. Groq's API enables extremely fast, accurate LLM responses with structured JSON output.

---

## Architecture

**Pipeline Steps:**

1. **Schema Comprehension**: Parse the schema (tables, columns, and relationships) of your database.
2. **Question Understanding**: Allow the user to ask questions in plain English.
3. **SQL Generation**: Use LLM (Groq) to translate the question into SQL, providing the schema as context.
4. **Query Execution**: Run the SQL against your database.
5. **Natural Language Response**: Optionally use the LLM to summarize the SQL query results in plain English.

---

## Implementation Details

### 1. Setup & Dependencies

- **Groq API** for inference
- **DuckDB/SQLite** (you can swap for any SQL database)
- Python libraries: `groq`, `duckdb`, `json`, `sqlparse`, `os`

**Install with:**

```bash
pip install groq duckdb sqlparse
```

### 2. Extract and Represent Your Schema

Write a function to extract all tables and columns in your database. This ensures the LLM outputs valid SQL referencing only real columns/tables.

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

### 3. LLM Prompt with JSON Mode

Prompt the LLM to output a JSON response containing only the SQL (not extra text, no markdown). This makes parsing and error handling reliable.

```python
def create_system_prompt(schema_context):
    return f"""You are a SQL expert. Convert natural language questions to SQL queries.\n\n{schema_context}\n\nIMPORTANT:\n- Only use tables and columns that exist in the schema\n- Write valid SQL syntax\n- Return ONLY valid JSON with this format:\n{{\n  \"sql\": \"SELECT * FROM table WHERE ...\",\n  \"explanation\": \"Brief explanation of the query\"\n}}\n\nDo NOT include markdown formatting or extra text."""
```

### 4. Generate SQL with Groq API

```python
def text_to_sql(user_question, schema_context, model="llama-3.3-70b-versatile"):
    system_prompt = create_system_prompt(schema_context)
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
    response_text = completion.choices[0].message.content
    result = json.loads(response_text)
    return result["sql"], result["explanation"]
```

### 5. Run Query and Handle Errors

```python
def execute_query(sql_query, database_path):
    conn = duckdb.connect(database_path)
    try:
        results = conn.execute(sql_query).fetchdf()
        return results, None
    except Exception as e:
        return None, str(e)
    finally:
        conn.close()
```

### 6. LLM-Based SQL Debugging (Optional)

Automatically use the LLM to fix queries that fail:

```python
def validate_and_fix_sql(sql_query, error_message, schema_context):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": f"You are a SQL expert. Fix invalid SQL queries.\n\n{schema_context}"},
            {"role": "user", "content": f"This SQL failed with error: {error_message}\n\nFix it:\n{sql_query}\n\nReturn ONLY valid SQL."}
        ],
        temperature=0,
        max_tokens=512
    )
    return completion.choices[0].message.content.strip()
```

### 7. Natural Language Response Summarization (Optional)

Summarize the returned results for the user in plain English:

```python
def summarize_results(question, df):
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "user", "content": f"Question: {question}\n\nData:\n{df.to_string()}\n\nProvide a natural language summary."}
        ],
        temperature=0
    )
    return completion.choices[0].message.content
```

### 8. Main Orchestration Function

```python
def query_database_with_nl(user_question, database_path):
    schema = get_database_schema(database_path)
    sql_query, explanation = text_to_sql(user_question, schema)
    results, error = execute_query(sql_query, database_path)
    if error:
        fixed_sql = validate_and_fix_sql(sql_query, error, schema)
        results, error = execute_query(fixed_sql, database_path)
    if error:
        return None, f"Failed to execute query: {error}"
    response = summarize_results(user_question, results)
    return results, response
```

---

## Best Practices

- **Always provide precise schema context** (not just table names, but also columns, types, and relationships)
- **Use JSON mode** so the LLM produces structured output (easier to parse and handle)
- **Prompt clearly**, including instructions about SQL syntax, schema, and result format
- **Log and validate** both the generated SQL and the execution errors
- **Automatically correct** failed SQL using the LLM

---

## Additional Tips

- For very large databases, retrieve only relevant tables/columns based on user question
- Use pay-as-you-go Groq API for fast, affordable queries
- Replace DuckDB with PostgreSQL or SQLite as needed (just adapt the schema introspection code)
- Use the latest Llama 3.3 or Mixtral models for best SQL accuracy
- You can build a Streamlit or Gradio front-end for interactive demos

---

## Example Usage

```python
db_path = "your_database.duckdb"
results, response = query_database_with_nl(
    "What are the top 5 products by sales?",
    db_path
)
print(response)
```

---

## References

- [Groq Community: JSON Mode SQL Querying][artifact:1]
- [Promethium: LLM Text-to-SQL Architecture][artifact:2]
- [Groq Cookbook][artifact:13]

---

**For more advanced features** (streaming, UI, advanced prompt engineering, schema chunking), see Groq community and cookbook resources.
