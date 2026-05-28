import unittest
from unittest.mock import patch
import Project_Work
import re
import sqlite3
import uuid

class Test_Taskmanager(unittest.TestCase):
    TEST_USERNAME = "testUser123"
    TEST_USERNAME_MISSING = "missingUser123"
    TEST_USER_EMAIL = "testUserMail@example.com"
    TEST_USER_PASSWORD = "pass1234"
    TEST_USER_WRONG_PASSWORD = "wrongPassWord"

    def create_task_manager(self, register: bool, login: bool) -> Project_Work.TaskManager:
        test_manager = Project_Work.TaskManager(":memory:")
        if register:
            test_manager.register(self.TEST_USERNAME, self.TEST_USER_EMAIL, self.TEST_USER_PASSWORD)
        if login:
            test_manager.login(self.TEST_USERNAME, self.TEST_USER_PASSWORD)
        return test_manager

    ######################
    #Happy path properties
    def test_get_db_sucess(self):
        #Arrange
        test_manager = self.create_task_manager(True, True)

        #Act & Validate
        try:
            db = test_manager.db
            self.assertTrue(True, "Successfully retrieved property")
        except:
            self.fail("Failed to retrieve property")

    def test_get_user_sucess(self):
        #Arrange
        test_manager = self.create_task_manager(True, True)

        #Act & Validate
        try:
            user = test_manager.user
            self.assertTrue(True, "Successfully retrieved property")
        except:
            self.fail("Failed to retrieve property")

    def test_get_project_sucess(self):
        #Arrange
        test_manager = self.create_task_manager(True, True)

        #Act & Validate
        try:
            project = test_manager.project
            self.assertTrue(True, "Successfully retrieved property")
        except:
            self.fail("Failed to retrieve property")

    def test_get_task_sucess(self):
        #Arrange
        test_manager = self.create_task_manager(True, True)

        #Act & Validate
        try:
            task = test_manager.task
            self.assertTrue(True, "Successfully retrieved property")
        except:
            self.fail("Failed to retrieve property")

    def test_get_subtask_sucess(self):
        #Arrange
        test_manager = self.create_task_manager(True, True)

        #Act & Validate
        try:
            subtask = test_manager.subtask
            self.assertTrue(True, "Successfully retrieved property")
        except:
            self.fail("Failed to retrieve property")

    def test_get_comment_sucess(self):
        #Arrange
        test_manager = self.create_task_manager(True, True)

        #Act & Validate
        try:
            comment = test_manager.comment
            self.assertTrue(True, "Successfully retrieved property")
        except:
            self.fail("Failed to retrieve property")

    def test_get_time_log_sucess(self):
        #Arrange
        test_manager = self.create_task_manager(True, True)

        #Act & Validate
        try:
            time_log = test_manager.time_log
            self.assertTrue(True, "Successfully retrieved property")
        except:
            self.fail("Failed to retrieve property")

    def test_get_notification_sucess(self):
        #Arrange
        test_manager = self.create_task_manager(True, True)

        #Act & Validate
        try:
            notification = test_manager.notification
            self.assertTrue(True, "Successfully retrieved property")
        except:
            self.fail("Failed to retrieve property")

    def test_get_audit_log_sucess(self):
        #Arrange
        test_manager = self.create_task_manager(True, True)

        #Act & Validate
        try:
            db = test_manager.audit_log
            self.assertTrue(True, "Successfully retrieved property")
        except:
            self.fail("Failed to retrieve property")

    def test_get_analytics_sucess(self):
        #Arrange
        test_manager = self.create_task_manager(True, True)

        #Act & Validate
        try:
            analytics = test_manager.analytics
            self.assertTrue(True, "Successfully retrieved property")
        except:
            self.fail("Failed to retrieve property")

    def test_get_current_user_sucess(self):
        #Arrange
        test_manager = self.create_task_manager(True, True)

        #Act & Validate
        try:
            current_user = test_manager._current_user
            self.assertTrue(True, "Successfully retrieved property")
        except:
            self.fail("Failed to retrieve property")

    #########################
    # Unhappy path properties
    def test_get_db_failure(self):
        # Arrange
        test_manager = self.create_task_manager(False, False)

        # Act & Validate
        try:
            db = test_manager.db
            self.fail("Successfully retrieved property")
        except:
            self.assertTrue(True, "Failed to retrieve property")

    def test_get_user_failure(self):
        test_manager = self.create_task_manager(False, False)
        try:
            user = test_manager.user
            self.fail("Successfully retrieved property")
        except:
            self.assertTrue(True, "Failed to retrieve property")

    def test_get_project_failure(self):
        test_manager = self.create_task_manager(False, False)
        try:
            project = test_manager.project
            self.fail("Successfully retrieved property")
        except:
            self.assertTrue(True, "Failed to retrieve property")

    def test_get_task_failure(self):
        test_manager = self.create_task_manager(False, False)
        try:
            task = test_manager.task
            self.fail("Successfully retrieved property")
        except:
            self.assertTrue(True, "Failed to retrieve property")

    def test_get_subtask_failure(self):
        test_manager = self.create_task_manager(False, False)
        try:
            subtask = test_manager.subtask
            self.fail("Successfully retrieved property")
        except:
            self.assertTrue(True, "Failed to retrieve property")

    def test_get_comment_failure(self):
        test_manager = self.create_task_manager(False, False)
        try:
            comment = test_manager.comment
            self.fail("Successfully retrieved property")
        except:
            self.assertTrue(True, "Failed to retrieve property")

    def test_get_time_log_failure(self):
        test_manager = self.create_task_manager(False, False)
        try:
            time_log = test_manager.time_log
            self.fail("Successfully retrieved property")
        except:
            self.assertTrue(True, "Failed to retrieve property")

    def test_get_notification_failure(self):
        test_manager = self.create_task_manager(False, False)
        try:
            notification = test_manager.notification
            self.fail("Successfully retrieved property")
        except:
            self.assertTrue(True, "Failed to retrieve property")

    def test_get_audit_log_failure(self):
        test_manager = self.create_task_manager(False, False)
        try:
            audit_log = test_manager.audit_log
            self.fail("Successfully retrieved property")
        except:
            self.assertTrue(True, "Failed to retrieve property")

    def test_get_analytics_failure(self):
        test_manager = self.create_task_manager(False, False)
        try:
            analytics = test_manager.analytics
            self.fail("Successfully retrieved property")
        except:
            self.assertTrue(True, "Failed to retrieve property")

    def test_get_current_user_failure(self):
        test_manager = self.create_task_manager(False, False)
        try:
            current_user = test_manager.current_user
            self.fail("Successfully retrieved property")
        except:
            self.assertTrue(True, "Failed to retrieve property")

    #Methods
    def test_logged_in(self):
        test_manager = self.create_task_manager(True, True)
        self.assertTrue(test_manager.logged_in(), "Is Logged in")

    def test_not_logged_in(self):
        test_manager = self.create_task_manager(False, False)
        self.assertFalse(test_manager.logged_in(), "Is Logged out")

    def test_logout(self):
        test_manager = self.create_task_manager(True, True)
        test_manager.logout()
        self.assertFalse(test_manager.logged_in(), "Sucessfully logged out")

    def test_login_success(self):
        test_manager = self.create_task_manager(True, False)#Arrange
        test_manager.login(self.TEST_USERNAME, self.TEST_USER_PASSWORD)#Act
        self.assertTrue(test_manager.logged_in(), "Successfully Logged in")#Validate

    def test_login_failure_password(self):
        test_manager = self.create_task_manager(True, False)
        test_manager.login(self.TEST_USERNAME, self.TEST_USER_WRONG_PASSWORD)
        self.assertFalse(test_manager.logged_in(), "Failed to login, wrong password")

    def test_login_failure_user_not_found(self):
        test_manager = self.create_task_manager(True, False)
        test_manager.login(self.TEST_USERNAME_MISSING, self.TEST_USER_WRONG_PASSWORD)
        self.assertFalse(test_manager.logged_in(), "User Not found")

    def test_register_success(self):
        #Arrange
        test_manager = self.create_task_manager(False, False)

        #Act
        test_user_id = test_manager.register(self.TEST_USERNAME, self.TEST_USER_EMAIL, self.TEST_USER_PASSWORD)

        #Validate
        test_manager.login(self.TEST_USERNAME, self.TEST_USER_PASSWORD)
        test_user = test_manager.user.get_user(test_user_id)
        self.assertEqual(test_user['id'], test_user_id)
        self.assertEqual(test_user['username'], self.TEST_USERNAME)
        self.assertEqual(test_user['email'], self.TEST_USER_EMAIL)
        self.assertEqual(test_user['password_hash'], Project_Work.User.hash_password(self.TEST_USER_PASSWORD))

    def test_register_username_unavailable(self):
        #Arrange
        test_manager = self.create_task_manager(True, True)

        #Act & Validate
        try:
            with patch("Project_Work.User.create_user", side_effect=ValueError(f"USERNAME: {self.TEST_USERNAME} is unavailable")):
                test_user_id = test_manager.register(self.TEST_USERNAME, self.TEST_USER_EMAIL + '3', self.TEST_USER_PASSWORD)
            self.fail("Successfull registration despite duplicate username")
        except Project_Work.UserNameUnavailableError:
            self.assertTrue(True, "Correct Exception")
        except Exception:
            self.fail("Wrong Exception")

    def test_register_email_unavailable(self):
        #Arrange
        test_manager = self.create_task_manager(True, True)

        #Act & Validate
        try:
            with patch("Project_Work.User.create_user", side_effect=ValueError(f"EMAIL: {self.TEST_USER_EMAIL} is unavailable")):
                test_user_id = test_manager.register(self.TEST_USERNAME, self.TEST_USER_EMAIL + '3', self.TEST_USER_PASSWORD)
            self.fail("Successfull registration despite duplicate username")
        except Project_Work.EmailUnavailableError:
            self.assertTrue(True, "Correct Exception")
        except Exception:
            self.fail("Wrong Exception")

    def test_close(self):
        #Arrange
        test_manager = self.create_task_manager(True, True)

        #Act
        test_manager.close()

        #Validate
        try:
            test_manager.db.conn.execute("SELECT 1")
            self.fail("Succeeded in using connection that is supposed to be closed")
        except Exception:
            self.assertTrue(True, "Successfully closed")
