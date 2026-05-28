import unittest
from unittest.mock import patch
import Project_Work
import re
import sqlalchemy
import sqlite3
import uuid
from freezegun import freeze_time

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

    def test_bad_db_name_value_error(self):
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

class Test_Notification(unittest.TestCase):

    TEST_USERNAME = "testUser123"
    TEST_USER_EMAIL = "testUserMail@example.com"
    TEST_USER_PASSWORD = "pass1234"
    TEST_MESSAGE_VALID = "This is a test message"
    
    def test__init__(self):
        #Arrange
        test_db = Project_Work.Database(":memory:")
        
        #Act & Validate
        try:
            test_db.conn.execute("SELECT 1")
            self.assertTrue(True, "Notification Init successfull")
            return
        except Exception as ex:
            self.fail(f"Notification init failed: {ex}")
    
    def test_type_error_no_db__init__(self):     
        #Arrange, Act & Validate
        try:
            notification = Project_Work.Notification("bad_arg")
            self.fail("Notification Init successfull when it should fail")
            return
        except TypeError: #Validate
            self.assertTrue(f"Notification init failed as expected")
            return
        except Exception as ex: #Validate
            self.fail(f"Notification init, wrong exception: {ex}")
            return
        
    def test_create_notification(self):
        #Arrange
        test_user_id = uuid.UUID("11111111-1111-4111-8111-111111111111")
        test_notification_id = uuid.UUID("22222222-1111-4111-8111-111111111111")
        test_db = Project_Work.Database(":memory:")
        test_user = Project_Work.User(test_db)
        with patch("Project_Work.uuid.uuid4", return_value=test_user_id):
            test_user.create_user(self.TEST_USERNAME, self.TEST_USER_EMAIL, self.TEST_USER_PASSWORD)
        test_notications = Project_Work.Notification(test_db)

        #Act
        with patch("Project_Work.uuid.uuid4", return_value=test_notification_id):
            test_notications.create_notification(str(test_user_id), self.TEST_MESSAGE_VALID)

        #Validate
        keys = ['id', 'user_id', 'message', 'read']
        notification_results = test_notications.get_user_notifications(str(test_user_id))[0]
        self.assertEqual(notification_results['id'], str(test_notification_id))
        self.assertEqual(notification_results['user_id'], str(test_user_id))
        self.assertEqual(notification_results['message'], self.TEST_MESSAGE_VALID)
        self.assertEqual(notification_results['read'], 0)
        self.assertIn('created_at', notification_results)

    def test_create_notification_user_id_not_exist(self):
        #Arrange
        test_user_id = uuid.UUID("11111111-1111-4111-8111-111111111111")
        test_db = Project_Work.Database(":memory:")
        test_notications = Project_Work.Notification(test_db)
        try:
            test_notications.create_notification(str(test_user_id), self.TEST_MESSAGE_VALID)
            self.fail("Creation of notification succeeded when it should fail")
        except ValueError as ex:
            message = str(ex)
            if "This user doesn't exist" in message:
                self.assertTrue(True, "Correct exception triggered")
                return
            else:
                self.fail("Correct exception but wrong message")
                return
        except Exception:
            self.fail("Wrong Exception triggered")

    def test_create_notification_null_message(self):
        #Arrange
        test_db = Project_Work.Database(":memory:") 
        test_user = Project_Work.User(test_db)
        test_notications = Project_Work.Notification(test_db)
        test_user_id = test_user.create_user(self.TEST_USERNAME, self.TEST_USER_EMAIL, self.TEST_USER_PASSWORD)

        try:
            test_notications.create_notification(str(test_user_id), None)
            self.fail("Creation of notification succeeded when it should fail")
        except ValueError as ex:
            message = str(ex)
            if "Message was null" in message:
                self.assertTrue(True,"Correct exception")
                return
            else:
                self.fail("Correct exception but wrong message")
                return
        except Exception:
            self.fail("Wrong Exception triggered")

    def test_create_notification_message_length_0(self):
        #Arrange
        test_db = Project_Work.Database(":memory:")
        test_user = Project_Work.User(test_db)
        test_notifications = Project_Work.Notification(test_db)
        test_user_id = test_user.create_user(self.TEST_USERNAME, self.TEST_USER_EMAIL, self.TEST_USER_PASSWORD)

        with self.assertRaisesRegex(ValueError, "Message of length 0"):
            test_notifications.create_notification(str(test_user_id), "")
        """try:
            test_notifications.create_notification(str(test_user_id), "")
            self.fail("Creation of notification succeeded when it should fail")
            return
        except ValueError as ex:
            message = str(ex)
            if "Message of length 0" in message:
                self.assertTrue(True, "Correct exception")
                return
            else:
                self.fail("Correct exception but wrong message")
                return
        except Exception:
            self.fail("Wrong Exception triggered")"""

    
    def test_get_user_notifications_all(self):
        #Arrange
        test_user_id = uuid.UUID("11111111-1111-4111-8111-111111111111")
        test_notification_id = uuid.UUID("22222222-1111-4111-8111-111111111111")
        test_db = Project_Work.Database(":memory:")
        test_user = Project_Work.User(test_db)
        with patch("Project_Work.uuid.uuid4", return_value=test_user_id):
            test_user.create_user(self.TEST_USERNAME, self.TEST_USER_EMAIL, self.TEST_USER_PASSWORD)
        test_notications = Project_Work.Notification(test_db)
        with patch("Project_Work.uuid.uuid4", return_value=test_notification_id):
            test_notications.create_notification(str(test_user_id), self.TEST_MESSAGE_VALID)

        #Act
        notification_results = test_notications.get_user_notifications(str(test_user_id))[0]
        
        #Validate
        self.assertEqual(notification_results['id'], str(test_notification_id))

    def test_get_user_notifications_unread_only(self):
        #Arrange
        test_user_id = uuid.UUID("11111111-1111-4111-8111-111111111111")
        test_notification_read_id = uuid.UUID("22222222-1111-4111-8111-111111111111")
        test_notification_unread_id = uuid.UUID("33333333-1111-4111-8111-111111111111")
        test_db = Project_Work.Database(":memory:")
        test_user = Project_Work.User(test_db)
        with patch("Project_Work.uuid.uuid4", return_value=test_user_id):
            test_user.create_user(self.TEST_USERNAME, self.TEST_USER_EMAIL, self.TEST_USER_PASSWORD)
        test_notications = Project_Work.Notification(test_db)
        with patch("Project_Work.uuid.uuid4", side_effect=[test_notification_read_id, test_notification_unread_id]):
            test_notications.create_notification(str(test_user_id), self.TEST_MESSAGE_VALID+ '1')
            test_notications.create_notification(str(test_user_id), self.TEST_MESSAGE_VALID+ '2')
        test_notications.mark_as_read(str(test_notification_read_id))

        #Act
        notification_results = test_notications.get_user_notifications(str(test_user_id), True)

        #Validate
        self.assertEqual(len(notification_results), 1)
        self.assertEqual(notification_results[0]['id'], str(test_notification_unread_id))
    
    def test_mark_as_read(self):
        #Arrange
        test_user_id = uuid.UUID("11111111-1111-4111-8111-111111111111")
        test_notification_read_id = uuid.UUID("22222222-1111-4111-8111-111111111111")
        test_db = Project_Work.Database(":memory:")
        test_user = Project_Work.User(test_db)
        with patch("Project_Work.uuid.uuid4", return_value=test_user_id):
            test_user.create_user(self.TEST_USERNAME, self.TEST_USER_EMAIL, self.TEST_USER_PASSWORD)
        test_notications = Project_Work.Notification(test_db)
        with patch("Project_Work.uuid.uuid4", return_value=test_notification_read_id):
            test_notications.create_notification(str(test_user_id), self.TEST_MESSAGE_VALID)
        
        #Act
        test_notications.mark_as_read(str(test_notification_read_id))

        #Validate
        test_result = test_notications.get_user_notifications(str(test_user_id))[0]
        self.assertEqual(test_result['id'], str(test_notification_read_id))
        self.assertEqual(1, test_result['read'])

    def test_mark_all_as_read(self):
        #Arrange
        test_user_id = uuid.UUID("11111111-1111-4111-8111-111111111111")
        test_db = Project_Work.Database(":memory:")
        test_user = Project_Work.User(test_db)
        with patch("Project_Work.uuid.uuid4", return_value=test_user_id):
            test_user.create_user(self.TEST_USERNAME, self.TEST_USER_EMAIL, self.TEST_USER_PASSWORD)
        test_notications = Project_Work.Notification(test_db)
        for i in range(5):
            test_notications.create_notification(str(test_user_id), self.TEST_MESSAGE_VALID + f'{i}')

        #Act
        test_notications.mark_all_as_read(str(test_user_id))

        #Validate
        test_results = test_notications.get_user_notifications(str(test_user_id))
        for test_result in test_results:
            self.assertEqual(1, test_result['read'])

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
        test_manager = Project_Work
    



if __name__ == '__main__':
    print("*******************************")
    unittest.main()