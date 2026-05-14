import sqlite3
import os

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    cohort TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    code TEXT UNIQUE NOT NULL,
    credits INTEGER DEFAULT 3
);

CREATE TABLE IF NOT EXISTS enrollments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id INTEGER NOT NULL,
    course_id INTEGER NOT NULL,
    grade REAL,
    FOREIGN KEY (student_id) REFERENCES students(id),
    FOREIGN KEY (course_id) REFERENCES courses(id)
);
"""

SEED_SQL = """
INSERT OR IGNORE INTO students (name, email, cohort) VALUES 
('Alice Johnson', 'alice@example.com', 'A1'),
('Bob Smith', 'bob@example.com', 'A1'),
('Charlie Brown', 'charlie@example.com', 'B2'),
('Diana Prince', 'diana@example.com', 'B2'),
('Edward Norton', 'edward@example.com', 'C3');

INSERT OR IGNORE INTO courses (title, code, credits) VALUES 
('Introduction to Computer Science', 'CS101', 4),
('Database Systems', 'CS302', 4),
('Web Development', 'CS204', 3),
('Machine Learning', 'AI401', 4);

INSERT OR IGNORE INTO enrollments (student_id, course_id, grade) VALUES 
(1, 1, 85.5),
(1, 2, 90.0),
(2, 1, 78.0),
(3, 3, 92.5),
(4, 4, 88.0),
(5, 1, 95.0),
(5, 2, 89.5);
"""

def create_database(db_path="lab.db"):
    """
    Creates the SQLite database, executes schema SQL and seeds it with data.
    """
    print(f"Initializing database at {db_path}...")
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.executescript(SCHEMA_SQL)
        cursor.executescript(SEED_SQL)
        conn.commit()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    return os.path.abspath(db_path)

if __name__ == "__main__":
    create_database()
