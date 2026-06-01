import unittest
from unittest.mock import patch
import Project_Work
import re
import sqlite3
import uuid

EXPECTED_SQL = """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'todo',
                assigned_to TEXT,
                due_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id),
                FOREIGN KEY (assigned_to) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS subtasks (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                title TEXT NOT NULL,
                completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );

            CREATE TABLE IF NOT EXISTS comments (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS time_logs (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                hours REAL NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL CHECK (length(message) > 0),
                read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS audit_logs (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                entity_type TEXT,
                entity_id TEXT,
                changes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """

def extract_schema(conn):#Från co-pilot
    schema = {}
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()

    for (table, ) in tables:
        columns = conn.execute(f"PRAGMA table_info({table})").fetchall()
        fks = conn.execute(f"PRAGMA foreign_key_list({table})").fetchall()
        indexes = conn.execute(f"PRAGMA index_list({table})").fetchall()

        schema[table] = {
            "columns": [(c[1], c[2], c[3], c[4], c[5]) for c in columns],
            "foreign_keys": [(fk[3], fk[2], fk[4]) for fk in fks],
            "indexes": [(idx[1], idx[2]) for idx in indexes],
        }
    return schema

class Test_Database(unittest.TestCase):
    def test_init_db(self):
        #Arrange
        expected_conn = sqlite3.connect(":memory:")
        expected_conn.executescript(EXPECTED_SQL)

        #Act & validate
        actual_conn = Project_Work.Database(":memory:").conn
        expected_schema = extract_schema(expected_conn)
        actual_schema = extract_schema(actual_conn)

        #Act & Validate. Compare to expected SQL
        self.assertDictEqual(expected_schema, actual_schema)

    def test_db_name_length_0(self):
        #Arrange & Act
        try:
            conn = Project_Work.Database("")
        #Validate
        except ValueError as ex:
            message = str(ex)
            if "length 0" in message:
                self.assertTrue(True, "Correct Exception")
                return
            else:
                self.fail("Wrong Exception")
                return
        self.fail("No Exception thrown")

    def test_db_invalid_path_value_error(self):
        try:
            actual_conn = Project_Work.Database(":memory").conn
        except ValueError:
            self.assertTrue(True, "Correct error thrown")
            return
        self.fail("Expected Error not thrown")

    def test_connect(self):
        #Arrange
        test_db = Project_Work.Database(":memory:")
        test_db.close()

        #Act
        test_db.connect()

        #Validate
        try:
            test_db.conn.execute("SELECT 1")
            self.assertTrue(True, "DB Connection Established")
        except sqlite3.ProgrammingError:
            self.fail("DB Connection Failed")

    def test_close(self):
        #Arrange
        test_db = Project_Work.Database(":memory:")

        #Act
        test_db.close()

        #Validate
        try:
            test_db.conn.execute("SELECT 1")
            self.fail("DB failed to close properly")
        except sqlite3.ProgrammingError:
            self.assertTrue(True, "Expected exception occurs")

if __name__ == '__main__':
    unittest.main()