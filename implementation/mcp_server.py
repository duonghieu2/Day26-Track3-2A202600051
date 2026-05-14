import os
import json
from fastmcp import FastMCP
from db import SQLiteAdapter, ValidationError

# Initialize FastMCP server
mcp = FastMCP("SQLite Lab MCP Server")

# Initialize database adapter
# Use absolute path for reliability
DB_PATH = os.path.join(os.path.dirname(__file__), "lab.db")
adapter = SQLiteAdapter(DB_PATH)

@mcp.tool()
def search(table: str, filters: dict = None, columns: list = None, limit: int = 20, offset: int = 0, order_by: str = None, descending: bool = False):
    """
    Search records in the database.
    - table: Name of the table to search.
    - filters: Dictionary of column-value pairs for equality filtering.
    - columns: List of columns to return (defaults to all).
    - limit: Maximum number of rows to return.
    - offset: Number of rows to skip.
    - order_by: Column name to sort by.
    - descending: Set to true for descending order.
    """
    try:
        results = adapter.search(table, columns, filters, limit, offset, order_by, descending)
        return json.dumps(results, indent=2)
    except ValidationError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected Error: {str(e)}"

@mcp.tool()
def insert(table: str, values: dict):
    """
    Insert a new record into the database.
    - table: Name of the table.
    - values: Dictionary of column-value pairs to insert.
    """
    try:
        result = adapter.insert(table, values)
        return json.dumps({"status": "success", "data": result}, indent=2)
    except ValidationError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected Error: {str(e)}"

@mcp.tool()
def aggregate(table: str, metric: str, column: str = None, filters: dict = None, group_by: str = None):
    """
    Perform an aggregate query (COUNT, AVG, SUM, MIN, MAX).
    - table: Name of the table.
    - metric: The aggregate function to use.
    - column: The column to aggregate (required for all except COUNT).
    - filters: Optional filters to apply before aggregating.
    - group_by: Optional column to group results by.
    """
    try:
        results = adapter.aggregate(table, metric, column, filters, group_by)
        return json.dumps(results, indent=2)
    except ValidationError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected Error: {str(e)}"

@mcp.resource("schema://database")
def get_database_schema() -> str:
    """
    Returns the schema for all tables in the database.
    """
    try:
        schema = adapter.get_full_schema()
        return json.dumps(schema, indent=2)
    except Exception as e:
        return f"Error retrieving schema: {str(e)}"

@mcp.resource("schema://table/{table_name}")
def get_table_schema(table_name: str) -> str:
    """
    Returns the schema for a specific table.
    """
    try:
        schema = adapter.get_table_schema(table_name)
        return json.dumps(schema, indent=2)
    except ValidationError as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Error retrieving table schema: {str(e)}"

if __name__ == "__main__":
    mcp.run()
