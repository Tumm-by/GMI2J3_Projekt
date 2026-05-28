import unittest
import sqlite3
import uuid

import Project_Work

class Test_TimeLog(unittest.TestCase):
    def setUp(self):
        self.db = Project_Work.Database(":memory:")
        self.user_manager = Project_Work.User(self.db)
        self.project_manager = Project_Work.Project(self.db)
        self.task_manager = Project_Work.Task(self.db)
        self.time_manager = Project_Work.TimeLog(self.db)

        self.user_id = self.user_manager.create_user(
            "timelogger", "time@test.com", "pass"
        )
        self.project_id = self.project_manager.create_project(
            self.user_id, "Time Project"
        )
        self.task_id = self.task_manager.create_task(
            self.project_id, "Time Task"
        )

    def tearDown(self):
        self.db.close()

    def test_log_time_success(self):
        log_id = self.time_manager.log_time(
            self.task_id, self.user_id, 2.5, "Work description"
        )
        self.assertIsInstance(log_id, str)
        logs = self.time_manager.get_task_time_logs(self.task_id)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["hours"], 2.5)
        self.assertEqual(logs[0]["description"], "Work description")

    def test_log_time_zero_hours_allowed(self):
        log_id = self.time_manager.log_time(self.task_id, self.user_id, 0)
        logs = self.time_manager.get_task_time_logs(self.task_id)
        self.assertEqual(logs[0]["hours"], 0.0)

    def test_log_time_invalid_task(self):
        fake_task = str(uuid.uuid4())
        with self.assertRaises(sqlite3.IntegrityError):
            self.time_manager.log_time(fake_task, self.user_id, 1.0)

    def test_log_time_invalid_user(self):
        fake_user = str(uuid.uuid4())
        with self.assertRaises(sqlite3.IntegrityError):
            self.time_manager.log_time(self.task_id, fake_user, 1.0)

    def test_get_task_time_logs_multiple(self):
        self.time_manager.log_time(self.task_id, self.user_id, 1.0, "First")
        self.time_manager.log_time(self.task_id, self.user_id, 2.0, "Second")
        logs = self.time_manager.get_task_time_logs(self.task_id)
        self.assertEqual(len(logs), 2)
        # Most recent first (by date DESC)
        self.assertEqual(logs[0]["description"], "First")
        self.assertEqual(logs[1]["description"], "Second")

    def test_get_task_time_logs_empty(self):
        logs = self.time_manager.get_task_time_logs(self.task_id)
        self.assertEqual(logs, [])

    def test_get_task_total_hours_sum(self):
        self.time_manager.log_time(self.task_id, self.user_id, 1.5)
        self.time_manager.log_time(self.task_id, self.user_id, 2.5)
        total = self.time_manager.get_task_total_hours(self.task_id)
        self.assertEqual(total, 4.0)

    def test_get_task_total_hours_no_logs(self):
        total = self.time_manager.get_task_total_hours(self.task_id)
        self.assertEqual(total, 0.0)

    def test_get_user_hours_last_30_days(self):
        self.time_manager.log_time(self.task_id, self.user_id, 3.0)
        task2 = self.task_manager.create_task(self.project_id, "Another Task")
        self.time_manager.log_time(task2, self.user_id, 2.0)
        hours = self.time_manager.get_user_hours(self.user_id, days=30)
        self.assertEqual(hours, 5.0)

    def test_get_user_hours_no_logs(self):
        new_user = self.user_manager.create_user("nologs", "no@test.com", "pass")
        hours = self.time_manager.get_user_hours(new_user)
        self.assertEqual(hours, 0.0)

    def test_delete_time_log_success(self):
        log_id = self.time_manager.log_time(self.task_id, self.user_id, 1.0)
        result = self.time_manager.delete_time_log(log_id)
        self.assertTrue(result)
        logs = self.time_manager.get_task_time_logs(self.task_id)
        self.assertEqual(len(logs), 0)

    def test_delete_time_log_nonexistent(self):
        fake_id = str(uuid.uuid4())
        result = self.time_manager.delete_time_log(fake_id)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()