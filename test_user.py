
from Project_Work import User, Comment, Database, Project, Task
import unittest
import sqlite3
import uuid
# Assuming the main code is in a file named task_manager.py
# from task_manager import Database, User, Project, Task, Comment

class Test_User(unittest.TestCase):

    def setUp(self):
        """Set up an in-memory database for isolated testing."""
        self.db = Database(":memory:")
        # Enforce foreign keys for SQLite to trigger IntegrityErrors
        self.db.cursor.execute("PRAGMA foreign_keys = ON;")

        self.user_manager = User(self.db)
        self.comment_manager = Comment(self.db)

        # Setup managers needed for Comment foreign key dependencies
        self.project_manager = Project(self.db)
        self.task_manager = Task(self.db)

    def tearDown(self):
        """Close the database connection after each test."""
        self.db.close()

    def test_create_user_duplicate_both(self):
        """Rule 4: Username duplicate, Email duplicate -> Raise IntegrityError"""
        # Establish the initial user record in the database
        self.user_manager.create_user("duplicate_user", "duplicate@test.com", "pass123")

        # Attempt to create a new user with identical unique identifiers
        with self.assertRaises(sqlite3.IntegrityError):
            self.user_manager.create_user("duplicate_user", "duplicate@test.com", "newpass456")

    def test_authenticate_success(self):
        """Rule 1: Username exists, Password matches -> Return user_id"""
        user_id = self.user_manager.create_user("testuser", "test@test.com", "password123")
        auth_id = self.user_manager.authenticate("testuser", "password123")
        self.assertEqual(user_id, auth_id)

    def test_authenticate_wrong_password(self):
        """Rule 2: Username exists, Password does not match -> Return None"""
        self.user_manager.create_user("testuser", "test@test.com", "password123")
        auth_id = self.user_manager.authenticate("testuser", "wrongpassword")
        self.assertIsNone(auth_id)

    def test_authenticate_nonexistent_user(self):
        """Rule 3: Username does not exist -> Return None"""
        auth_id = self.user_manager.authenticate("ghostuser", "password123")
        self.assertIsNone(auth_id)

    def test_create_user_success(self):
        """Rule 1: Username unique, Email unique -> Return user_id"""
        user_id = self.user_manager.create_user("newuser", "new@test.com", "pass")
        self.assertIsInstance(user_id, str)
        self.assertIsNotNone(self.user_manager.get_user(user_id))

    def test_create_user_duplicate_username(self):
        """Rule 2: Username duplicate, Email unique -> Raise IntegrityError"""
        self.user_manager.create_user("existinguser", "first@test.com", "pass")
        with self.assertRaises(sqlite3.IntegrityError):
            self.user_manager.create_user("existinguser", "second@test.com", "pass")

    def test_create_user_duplicate_email(self):
        """Rule 3: Username unique, Email duplicate -> Raise IntegrityError"""
        self.user_manager.create_user("user_one", "shared@test.com", "pass")
        with self.assertRaises(sqlite3.IntegrityError):
            self.user_manager.create_user("user_two", "shared@test.com", "pass")

    def test_update_user_success(self):
        """Rule 1: Valid fields, no UNIQUE violation -> Return True and update DB"""
        user_id = self.user_manager.create_user("updateuser", "update@test.com", "pass")
        result = self.user_manager.update_user(user_id, email="new_email@test.com")

        self.assertTrue(result)
        updated_user = self.user_manager.get_user(user_id)
        self.assertEqual(updated_user['email'], "new_email@test.com")

    def test_update_user_invalid_fields(self):
        """Rule 2: No valid allowed fields provided -> Return False"""
        user_id = self.user_manager.create_user("invalidfielduse", "inv@test.com", "pass")
        result = self.user_manager.update_user(user_id, password_hash="hacked")

        self.assertFalse(result)

    def test_update_user_duplicate_email(self):
        """Rule 3: Field violates UNIQUE constraint -> Raise IntegrityError"""
        self.user_manager.create_user("user1", "user1@test.com", "pass")
        user2_id = self.user_manager.create_user("user2", "user2@test.com", "pass")

        with self.assertRaises(sqlite3.IntegrityError):
            self.user_manager.update_user(user2_id, email="user1@test.com")

if __name__ == '__main__':
    unittest.main()