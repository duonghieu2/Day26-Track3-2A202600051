import pytest
import os
import sqlite3
import json
from implementation.db import SQLiteAdapter, ValidationError

@pytest.fixture
def db_path(tmp_path):
    d = tmp_path / "test.db"
    path = str(d)
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE students (id INTEGER PRIMARY KEY, name TEXT, cohort TEXT)")
    cursor.execute("INSERT INTO students (name, cohort) VALUES ('Alice', 'A1'), ('Bob', 'A1'), ('Charlie', 'B2')")
    conn.commit()
    conn.close()
    return path

@pytest.fixture
def adapter(db_path):
    return SQLiteAdapter(db_path)

def test_list_tables(adapter):
    assert "students" in adapter.list_tables()

def test_search_all(adapter):
    results = adapter.search("students")
    assert len(results) == 3
    assert results[0]["name"] == "Alice"

def test_search_filter(adapter):
    results = adapter.search("students", filters={"cohort": "A1"})
    assert len(results) == 2
    assert all(r["cohort"] == "A1" for r in results)

def test_search_invalid_table(adapter):
    with pytest.raises(ValidationError, match="Unknown table"):
        adapter.search("non_existent")

def test_search_invalid_column(adapter):
    with pytest.raises(ValidationError, match="Unknown column"):
        adapter.search("students", columns=["invalid_col"])

def test_insert(adapter):
    new_student = {"name": "Diana", "cohort": "B2"}
    inserted = adapter.insert("students", new_student)
    assert inserted["name"] == "Diana"
    
    results = adapter.search("students", filters={"name": "Diana"})
    assert len(results) == 1

def test_aggregate_count(adapter):
    results = adapter.aggregate("students", "COUNT")
    assert results[0]["value"] == 3

def test_aggregate_group_by(adapter):
    results = adapter.aggregate("students", "COUNT", group_by="cohort")
    assert len(results) == 2
    cohort_counts = {r["cohort"]: r["value"] for r in results}
    assert cohort_counts["A1"] == 2
    assert cohort_counts["B2"] == 1

def test_invalid_metric(adapter):
    with pytest.raises(ValidationError, match="Unsupported metric"):
        adapter.aggregate("students", "INVALID")
