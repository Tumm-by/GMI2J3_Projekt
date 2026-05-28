import unittest
import Project_Work
import re
import sqlalchemy
import sqlite3
from datetime import datetime, timedelta

class Test_Task(unittest.TestCase):
    def setUp(self):
        self.db = Project_Work.Database(":memory:")
        self.task = Project_Work.Task(self.db)
        self.db.cursor.execute("""
        INSERT INTO users (id, username, email, password_hash)
        VALUES ('user-1', 'testuser', 'test@test.com', 'hash123')
    """)
        # Skapa ett projekt att koppla tasks till
        self.db.cursor.execute("""
            INSERT INTO projects (id, user_id, name)
            VALUES ('proj-1', 'user-1', 'Test Project')
        """)
        self.db.conn.commit()

    def test_create_task_returns_id(self):
        # Arrange & Act
        result = self.task.create_task("proj-1", "Min task")

        # Validate
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_create_task_empty_title(self):
        # Arrange & Act & Validate
        with self.assertRaises(ValueError):
            self.task.create_task("proj-1", "")

    def test_create_task_invalid_priority(self):
        # Arrange & Act & Validate
        with self.assertRaises(ValueError):
            self.task.create_task("proj-1", "Min task", priority="ogiltig")
    def test_get_task_returns_dict(self):
        # Arrange
        task_id = self.task.create_task("proj-1", "Min task")

        # Act
        result = self.task.get_task(task_id)

        # Validate
        self.assertIsInstance(result, dict)
        self.assertEqual(result["title"], "Min task")

    def test_get_task_not_found_returns_none(self):
        # Arrange & Act
        result = self.task.get_task("finns-inte")

        # Validate
        self.assertIsNone(result)
    def test_list_project_tasks_returns_list(self):
        # Arrange
        self.task.create_task("proj-1", "Task 1")
        self.task.create_task("proj-1", "Task 2")

        # Act
        result = self.task.list_project_tasks("proj-1")

        # Validate
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_list_project_tasks_filter_status(self):
        # Arrange
        task_id = self.task.create_task("proj-1", "Task 1")
        self.task.update_task(task_id, status="in_progress")

        # Act
        result = self.task.list_project_tasks("proj-1", status="in_progress")

        # Validate
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["status"], "in_progress")

    def test_update_task_returns_true(self):
        # Arrange
        task_id = self.task.create_task("proj-1", "Min task")

        # Act
        result = self.task.update_task(task_id, status="in_progress")

        # Validate
        self.assertTrue(result)

    def test_update_task_no_valid_fields(self):
        # Arrange
        task_id = self.task.create_task("proj-1", "Min task")

        # Act & Validate
        with self.assertRaises(ValueError):
            self.task.update_task(task_id, ogiltigt_falt="test")
    def test_delete_task_returns_true(self):
        # Arrange
        task_id = self.task.create_task("proj-1", "Min task")

        # Act
        result = self.task.delete_task(task_id)

        # Validate
        self.assertTrue(result)

    def test_delete_task_not_found(self):
        # Arrange & Act & Validate
        with self.assertRaises(ValueError):
            self.task.delete_task("finns-inte")
    def test_get_overdue_tasks_returns_list(self):
        # Arrange - skapa en task med ett datum som redan passerat
        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        self.task.create_task("proj-1", "FÃ¶rsenad task", due_date=past_date)

        # Act
        result = self.task.get_overdue_tasks("proj-1")

        # Validate
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    def test_get_overdue_tasks_excludes_completed(self):
        # Arrange
        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
        ask_id = self.task.create_task("proj-1", "Klar task", due_date=past_date)
        self.task.update_task(ask_id, status="completed")

        # Act
        result = self.task.get_overdue_tasks("proj-1")

        # Validate
        self.assertEqual(len(result), 0)
    def test_get_user_assigned_tasks_returns_list(self):
        # Arrange
        self.task.create_task("proj-1", "Min task", assigned_to="user-1")

        # Act
        result = self.task.get_user_assigned_tasks("user-1")

        # Validate
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    def test_get_user_assigned_tasks_excludes_completed(self):
        # Arrange
        task_id = self.task.create_task("proj-1", "Min task", assigned_to="user-1")
        self.task.update_task(task_id, status="completed")

        # Act
        result = self.task.get_user_assigned_tasks("user-1")

        # Validate
        self.assertEqual(len(result), 0)