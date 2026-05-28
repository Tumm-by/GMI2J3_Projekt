from Project_Work_Grupp_7 import User, Database, Project, Task
import unittest
import sqlite3
import uuid
class Test_comment(unittest.TestCase):

    def test_create_comment_success(self):
        """Rule 1: Valid task_id and valid user_id -> Return comment_id"""
        user_id = self.user_manager.create_user("commenter", "comm@test.com", "pass")
        project_id = self.project_manager.create_project(user_id, "Project X")
        task_id = self.task_manager.create_task(project_id, "Task X")

        comment_id = self.comment_manager.create_comment(task_id, user_id, "Looks good!")
        self.assertIsInstance(comment_id, str)

    def test_create_comment_invalid_task(self):
        """Rule 2: Invalid task_id -> Raise IntegrityError due to Foreign Key constraint"""
        user_id = self.user_manager.create_user("commenter2", "comm2@test.com", "pass")
        fake_task_id = str(uuid.uuid4())

        with self.assertRaises(sqlite3.IntegrityError):
            self.comment_manager.create_comment(fake_task_id, user_id, "Where is the task?")

    def test_create_comment_invalid_user(self):
        """Rule 3: Invalid user_id -> Raise IntegrityError due to Foreign Key constraint"""
        user_id = self.user_manager.create_user("commenter3", "comm3@test.com", "pass")
        project_id = self.project_manager.create_project(user_id, "Project Y")
        task_id = self.task_manager.create_task(project_id, "Task Y")

        fake_user_id = str(uuid.uuid4())

        with self.assertRaises(sqlite3.IntegrityError):
            self.comment_manager.create_comment(task_id, fake_user_id, "Who am I?")

    def test_delete_comment_success(self):
        """Rule 1: comment_id exists -> Delete row and return True"""
        user_id = self.user_manager.create_user("del_user", "del@test.com", "pass")
        project_id = self.project_manager.create_project(user_id, "Project Z")
        task_id = self.task_manager.create_task(project_id, "Task Z")
        comment_id = self.comment_manager.create_comment(task_id, user_id, "To be deleted")

        result = self.comment_manager.delete_comment(comment_id)
        self.assertTrue(result)

        # Verify it is gone
        comments = self.comment_manager.list_task_comments(task_id)
        self.assertEqual(len(comments), 0)

    def test_delete_comment_nonexistent(self):
        """Rule 2: comment_id does not exist -> Return False"""
        fake_comment_id = str(uuid.uuid4())
        result = self.comment_manager.delete_comment(fake_comment_id)
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()
