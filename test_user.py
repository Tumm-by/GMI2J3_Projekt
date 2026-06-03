
from Project_Work import User, Comment, Database, Project, Task
import unittest
import sqlite3
import uuid
from unittest.mock import patch
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
        with self.assertRaises(ValueError):
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
        with self.assertRaises(ValueError):
            self.user_manager.create_user("existinguser", "second@test.com", "pass")

    def test_create_user_duplicate_email(self):
        """Rule 3: Username unique, Email duplicate -> Raise IntegrityError"""
        self.user_manager.create_user("user_one", "shared@test.com", "pass")
        with self.assertRaises(ValueError):
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

        with self.assertRaises(ValueError):
            self.user_manager.update_user(user2_id, email="user1@test.com")

    def test_get_user_not_found(self):
        """Rule: Invalid user_id -> Return None"""
        fake_id = str(uuid.uuid4())
        user = self.user_manager.get_user(fake_id)
        self.assertIsNone(user)

    def test_update_user_duplicate_username(self):
        """Rule: Username violates UNIQUE constraint -> Raise ValueError"""
        self.user_manager.create_user("target_user", "target@test.com", "pass")
        user2_id = self.user_manager.create_user("other_user", "other@test.com", "pass")

        with self.assertRaises(ValueError) as context:
            self.user_manager.update_user(user2_id, username="target_user")
        
        self.assertIn("is already taken", str(context.exception))

    def test_list_users_success(self):
        """Rule: Retrieve paginated list of users"""
        self.user_manager.create_user("list1", "list1@test.com", "pass")
        self.user_manager.create_user("list2", "list2@test.com", "pass")
        
        users = self.user_manager.list_users()
        
        self.assertIsInstance(users, list)
        self.assertTrue(len(users) >= 2)
        usernames = [u['username'] for u in users]
        self.assertIn("list1", usernames)
        self.assertIn("list2", usernames)

    def test_create_user_generic_integrity_error(self):
        """Rule: Unknown integrity error during creation -> Raise generic ValueError"""
        # Patch the entire cursor object on the database instance instead of the SQLite class
        with patch.object(self.user_manager.db, 'cursor') as mock_cursor:
            mock_cursor.execute.side_effect = sqlite3.IntegrityError("unknown constraint")
            with self.assertRaises(ValueError) as context:
                self.user_manager.create_user("fail_user", "fail@test.com", "pass")
            self.assertIn("Could not create user due to integrity constraint", str(context.exception))

    def test_update_user_generic_integrity_error(self):
        """Rule: Unknown integrity error during update -> Raise generic ValueError"""
        user_id = self.user_manager.create_user("gen_upd", "gen_upd@test.com", "pass")
        
        with patch.object(self.user_manager.db, 'cursor') as mock_cursor:
            mock_cursor.execute.side_effect = sqlite3.IntegrityError("unknown constraint")
            with self.assertRaises(ValueError) as context:
                self.user_manager.update_user(user_id, username="new_gen_upd")
            self.assertIn("Could not update user", str(context.exception))

if __name__ == '__main__':
    unittest.main()