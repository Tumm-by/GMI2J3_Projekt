import unittest
from unittest.mock import patch
import Project_Work
import uuid

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

        try:
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
            self.fail("Wrong Exception triggered")


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

if __name__ == '__main__':
    unittest.main()