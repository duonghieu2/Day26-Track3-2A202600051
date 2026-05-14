import sqlite3
import os
from typing import List, Dict, Any, Optional

class ValidationError(Exception):
    """Raised when a request cannot be safely executed."""
    pass

class SQLiteAdapter:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._allowed_tables = {}
        self._refresh_schema_cache()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _refresh_schema_cache(self):
        """Caches the list of tables and their columns for validation."""
        if not os.path.exists(self.db_path):
            return

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row['name'] for row in cursor.fetchall()]
            
            self._allowed_tables = {}
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                self._allowed_tables[table] = [row['name'] for row in cursor.fetchall()]

    def list_tables(self) -> List[str]:
        self._refresh_schema_cache()
        return list(self._allowed_tables.keys())

    def get_table_schema(self, table: str) -> List[Dict[str, Any]]:
        if table not in self._allowed_tables:
            raise ValidationError(f"Unknown table: {table}")
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"PRAGMA table_info({table})")
            return [dict(row) for row in cursor.fetchall()]

    def get_full_schema(self) -> Dict[str, List[Dict[str, Any]]]:
        schema = {}
        for table in self.list_tables():
            schema[table] = self.get_table_schema(table)
        return schema

    def _validate_identifiers(self, table: str, columns: Optional[List[str]] = None):
        if table not in self._allowed_tables:
            raise ValidationError(f"Unknown table: {table}")
        
        if columns:
            allowed = self._allowed_tables[table]
            for col in columns:
                if col not in allowed:
                    raise ValidationError(f"Unknown column '{col}' in table '{table}'")

    def search(self, table: str, columns: Optional[List[str]] = None, filters: Optional[Dict[str, Any]] = None, 
               limit: int = 20, offset: int = 0, order_by: Optional[str] = None, descending: bool = False):
        self._refresh_schema_cache()
        self._validate_identifiers(table, columns)
        
        if order_by:
            self._validate_identifiers(table, [order_by])

        query = f"SELECT {', '.join(columns) if columns else '*'} FROM {table}"
        params = []

        if filters:
            where_clauses = []
            for col, value in filters.items():
                self._validate_identifiers(table, [col])
                # Supporting basic equality for now, can be extended
                where_clauses.append(f"{col} = ?")
                params.append(value)
            query += " WHERE " + " AND ".join(where_clauses)

        if order_by:
            direction = "DESC" if descending else "ASC"
            query += f" ORDER BY {order_by} {direction}"

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def insert(self, table: str, values: Dict[str, Any]):
        self._refresh_schema_cache()
        if not values:
            raise ValidationError("Cannot insert empty values")
        
        self._validate_identifiers(table, list(values.keys()))

        cols = ", ".join(values.keys())
        placeholders = ", ".join(["?"] * len(values))
        query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, list(values.values()))
            last_id = cursor.lastrowid
            conn.commit()
            
            # Return the inserted row
            cursor.execute(f"SELECT * FROM {table} WHERE rowid = ?", (last_id,))
            return dict(cursor.fetchone())

    def aggregate(self, table: str, metric: str, column: Optional[str] = None, 
                  filters: Optional[Dict[str, Any]] = None, group_by: Optional[str] = None):
        self._refresh_schema_cache()
        allowed_metrics = ["COUNT", "AVG", "SUM", "MIN", "MAX"]
        metric = metric.upper()
        if metric not in allowed_metrics:
            raise ValidationError(f"Unsupported metric: {metric}. Allowed: {allowed_metrics}")

        if column:
            self._validate_identifiers(table, [column])
        elif metric != "COUNT":
            raise ValidationError(f"Metric {metric} requires a column")

        if group_by:
            self._validate_identifiers(table, [group_by])

        agg_expr = f"{metric}({column if column else '*'})"
        query = f"SELECT {agg_expr} AS value"
        if group_by:
            query += f", {group_by}"
        
        query += f" FROM {table}"
        params = []

        if filters:
            where_clauses = []
            for col, val in filters.items():
                self._validate_identifiers(table, [col])
                where_clauses.append(f"{col} = ?")
                params.append(val)
            query += " WHERE " + " AND ".join(where_clauses)

        if group_by:
            query += f" GROUP BY {group_by}"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
