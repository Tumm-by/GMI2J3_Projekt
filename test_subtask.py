import unittest
import Project_Work
import re
import sqlalchemy
import sqlite3
from datetime import datetime, timedelta

class Test_SubTask(unittest.TestCase):
    def setUp(self):
        self.db = Project_Work.Database(":memory:")
        self.task = Project_Work.Task(self.db)
        self.subtask = Project_Work.SubTask(self.db)
        self.db.cursor.execute("""
        INSERT INTO users (id, username, email, password_hash)
        VALUES ('user-1', 'testuser', 'test@test.com', 'hash123')
    """)
        # Skapa ett projekt och en task att koppla subtasks till
        self.db.cursor.execute("""
            INSERT INTO projects (id, user_id, name)
            VALUES ('proj-1', 'user-1', 'Test Project')
        """)
        self.db.conn.commit()
        self.task_id = self.task.create_task("proj-1", "Test Task")

    def test_create_subtask_returns_id(self):
        # Arrange & Act
        result = self.subtask.create_subtask(self.task_id, "Min subtask")

        # Validate
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_create_subtask_empty_title(self):
        # Arrange & Act & Validate
        with self.assertRaises(ValueError):
            self.subtask.create_subtask(self.task_id, "")
    def test_list_task_subtasks_returns_list(self):
        # Arrange
        self.subtask.create_subtask(self.task_id, "Subtask 1")
        self.subtask.create_subtask(self.task_id, "Subtask 2")

        # Act
        result = self.subtask.list_task_subtasks(self.task_id)

        # Validate
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_list_task_subtasks_empty(self):
        # Arrange & Act
        result = self.subtask.list_task_subtasks(self.task_id)

        # Validate
        self.assertEqual(len(result), 0)
    def test_toggle_subtask_returns_true(self):
        # Arrange
        subtask_id = self.subtask.create_subtask(self.task_id, "Min subtask")

        # Act
        result = self.subtask.toggle_subtask(subtask_id)

        # Validate
        self.assertTrue(result)

    def test_toggle_subtask_changes_completed(self):
        # Arrange
        subtask_id = self.subtask.create_subtask(self.task_id, "Min subtask")

        # Act - toggla tvÃ¥ gÃ¥nger
        self.subtask.toggle_subtask(subtask_id)
        self.subtask.toggle_subtask(subtask_id)

        # Validate - ska vara tillbaka pÃ¥ 0
        result = self.subtask.list_task_subtasks(self.task_id)
        self.assertEqual(result[0]["completed"], 0)
    def test_delete_subtask_returns_true(self):
        # Arrange
        subtask_id = self.subtask.create_subtask(self.task_id, "Min subtask")

        # Act
        result = self.subtask.delete_subtask(subtask_id)

        # Validate
        self.assertTrue(result)

    def test_delete_subtask_not_found(self):
        # Arrange & Act & Validate
        with self.assertRaises(ValueError):
            self.subtask.delete_subtask("finns-inte")
    def test_get_subtask_completion_percentage_returns_correct(self):
        # Arrange - skapa 2 subtasks och slutfÃ¶r 1
        subtask_id = self.subtask.create_subtask(self.task_id, "Subtask 1")
        self.subtask.create_subtask(self.task_id, "Subtask 2")
        self.subtask.toggle_subtask(subtask_id)

        # Act
        result = self.subtask.get_subtask_completion_percentage(self.task_id)

        # Validate
        self.assertEqual(result, 50.0)

    def test_get_subtask_completion_percentage_no_subtasks(self):
        # Arrange & Act
        result = self.subtask.get_subtask_completion_percentage(self.task_id)

        # Validate - ska returnera 0 om inga subtasks finns
        self.assertEqual(result, 0)