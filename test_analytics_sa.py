import unittest
import Project_Work


class TestAnalyticsSA(unittest.TestCase):
    def setUp(self):
        # Arrange
        self.db = Project_Work.Database(":memory:")
        self.user_manager = Project_Work.User(self.db)
        self.project_manager = Project_Work.Project(self.db)
        self.task_manager = Project_Work.Task(self.db)
        self.time_manager = Project_Work.TimeLog(self.db)
        self.analytics_manager = Project_Work.Analytics(self.db)

        self.user_id = self.user_manager.create_user(
            "samuser",
            "sam@test.com",
            "pass123"
        )

        self.other_user_id = self.user_manager.create_user(
            "otheruser",
            "other@test.com",
            "pass123"
        )

        self.project_id = self.project_manager.create_project(
            self.user_id,
            "Test Project",
            "Project for testing"
        )

    def tearDown(self):
        # Cleanup
        self.db.close()

    def test_user_productivity_no_tasks(self):
        """Rule 1: User has no tasks -> Return zero stats"""
        # Act
        stats = self.analytics_manager.get_user_productivity_stats(self.user_id)

        # Validate
        self.assertEqual(stats["total_assigned"], 0)
        self.assertEqual(stats["completed"], 0)
        self.assertEqual(stats["completion_rate"], 0)
        self.assertEqual(stats["hours_logged_30days"], 0)

    def test_user_productivity_with_tasks(self):
        """Rule 2: User has tasks -> Return correct productivity stats"""
        # Arrange
        task1_id = self.task_manager.create_task(
            self.project_id,
            "Task 1",
            assigned_to=self.user_id
        )

        self.task_manager.create_task(
            self.project_id,
            "Task 2",
            assigned_to=self.user_id
        )

        self.task_manager.update_task(task1_id, status="completed")
        self.time_manager.log_time(task1_id, self.user_id, 4.5, "Worked on task")

        # Act
        stats = self.analytics_manager.get_user_productivity_stats(self.user_id)

        # Validate
        self.assertEqual(stats["total_assigned"], 2)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["completion_rate"], 50)
        self.assertEqual(stats["hours_logged_30days"], 4.5)

    def test_team_productivity_success(self):
        """Rule 3: Project has assigned tasks -> Return team statistics"""
        # Arrange
        task1_id = self.task_manager.create_task(
            self.project_id,
            "Task 1",
            assigned_to=self.user_id
        )

        self.task_manager.create_task(
            self.project_id,
            "Task 2",
            assigned_to=self.user_id
        )

        task3_id = self.task_manager.create_task(
            self.project_id,
            "Task 3",
            assigned_to=self.other_user_id
        )

        self.task_manager.update_task(task1_id, status="completed")
        self.task_manager.update_task(task3_id, status="completed")

        # Act
        result = self.analytics_manager.get_team_productivity(self.project_id)

        # Validate
        self.assertIn("samuser", result)
        self.assertIn("otheruser", result)
        self.assertEqual(result["samuser"]["total_tasks"], 2)
        self.assertEqual(result["samuser"]["completed_tasks"], 1)
        self.assertEqual(result["samuser"]["completion_rate"], 50)
        self.assertEqual(result["otheruser"]["total_tasks"], 1)
        self.assertEqual(result["otheruser"]["completed_tasks"], 1)
        self.assertEqual(result["otheruser"]["completion_rate"], 100)

    def test_team_productivity_empty_project(self):
        """Rule 4: Project has no assigned tasks -> Return empty dictionary"""
        # Act
        result = self.analytics_manager.get_team_productivity(self.project_id)

        # Validate
        self.assertEqual(result, {})

    def test_project_burndown_success(self):
        """Rule 5: Project has tasks with different status -> Return correct burndown"""
        # Arrange
        task1_id = self.task_manager.create_task(self.project_id, "Todo Task")
        task2_id = self.task_manager.create_task(self.project_id, "In Progress Task")
        task3_id = self.task_manager.create_task(self.project_id, "Completed Task")

        self.task_manager.update_task(task2_id, status="in_progress")
        self.task_manager.update_task(task3_id, status="completed")

        # Act
        result = self.analytics_manager.get_project_burndown(self.project_id)

        # Validate
        self.assertEqual(result["todo"], 1)
        self.assertEqual(result["in_progress"], 1)
        self.assertEqual(result["completed"], 1)

    def test_project_burndown_empty_project(self):
        """Rule 6: Project has no tasks -> Return zero for every status"""
        # Act
        result = self.analytics_manager.get_project_burndown(self.project_id)

        # Validate
        self.assertEqual(result["todo"], 0)
        self.assertEqual(result["in_progress"], 0)
        self.assertEqual(result["completed"], 0)


if __name__ == "__main__":
    unittest.main()
