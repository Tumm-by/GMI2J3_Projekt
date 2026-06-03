import unittest
import sqlite3
import uuid

import Project_Work


class TestProject(unittest.TestCase):
    def setUp(self):
        self.db = Project_Work.Database(":memory:")
        self.user_manager = Project_Work.User(self.db)
        self.project_manager = Project_Work.Project(self.db)
        self.task_manager = Project_Work.Task(self.db)

        self.user_id = self.user_manager.create_user(
            "project_tester",
            "project@test.com",
            "pass123"
        )

    def tearDown(self):
        self.db.close()

    def test_create_project_success(self):
        project_id = self.project_manager.create_project(
            self.user_id, "Test Project", "Description"
        )
        self.assertIsInstance(project_id, str)
        self.assertTrue(len(project_id) > 0)

        proj = self.project_manager.get_project(project_id)
        self.assertEqual(proj["name"], "Test Project")
        self.assertEqual(proj["description"], "Description")
        self.assertEqual(proj["user_id"], self.user_id)


    def test_get_project_exists(self):
        pid = self.project_manager.create_project(self.user_id, "Get Me")
        proj = self.project_manager.get_project(pid)
        self.assertIsNotNone(proj)
        self.assertEqual(proj["id"], pid)
        self.assertEqual(proj["name"], "Get Me")

    def test_get_project_not_found(self):
        fake_id = str(uuid.uuid4())
        proj = self.project_manager.get_project(fake_id)
        self.assertIsNone(proj)

    def test_list_user_projects_multiple(self):
        self.project_manager.create_project(self.user_id, "Proj A")
        self.project_manager.create_project(self.user_id, "Proj B")
        projects = self.project_manager.list_user_projects(self.user_id)
        self.assertEqual(len(projects), 2)
        names = [p["name"] for p in projects]
        self.assertIn("Proj A", names)
        self.assertIn("Proj B", names)

    def test_list_user_projects_no_projects(self):
        # Create a new user without projects
        new_user_id = self.user_manager.create_user("empty", "empty@test.com", "pass")
        projects = self.project_manager.list_user_projects(new_user_id)
        self.assertEqual(projects, [])

    def test_list_user_projects_with_status_filter(self):
        """Test list_user_projects with status filter"""
        # Create projects with different statuses
        pid1 = self.project_manager.create_project(self.user_id, "Active Project 1")
        pid2 = self.project_manager.create_project(self.user_id, "Archived Project")
        pid3 = self.project_manager.create_project(self.user_id, "Active Project 2")
        
        # Update one to archived status
        self.project_manager.update_project(pid2, status="archived")
        
        # List with status filter
        active_projects = self.project_manager.list_user_projects(self.user_id, status="active")
        archived_projects = self.project_manager.list_user_projects(self.user_id, status="archived")
        
        # Verify filtering works
        self.assertEqual(len(active_projects), 2)
        self.assertEqual(len(archived_projects), 1)
        self.assertEqual(archived_projects[0]["name"], "Archived Project")
        
    def test_list_user_projects_no_status_returns_all(self):
        """Test that calling list_user_projects without status returns all projects"""
        self.project_manager.create_project(self.user_id, "Project 1")
        self.project_manager.create_project(self.user_id, "Project 2")
        self.project_manager.create_project(self.user_id, "Project 3")
        
        all_projects = self.project_manager.list_user_projects(self.user_id)
        self.assertEqual(len(all_projects), 3)

    def test_update_project_success(self):
        pid = self.project_manager.create_project(self.user_id, "Old Name")
        result = self.project_manager.update_project(pid, name="New Name", status="archived")
        self.assertTrue(result)
        proj = self.project_manager.get_project(pid)
        self.assertEqual(proj["name"], "New Name")
        self.assertEqual(proj["status"], "archived")

    def test_update_project_no_valid_updates(self):
        """Test update_project with no valid fields returns False"""
        pid = self.project_manager.create_project(self.user_id, "Test Project")
        original = self.project_manager.get_project(pid)
        
        # Try to update with invalid fields (should be filtered out)
        result = self.project_manager.update_project(pid, invalid_field="should be ignored")
        
        # Should return False because no valid fields were provided
        self.assertFalse(result)
        
        # Project should remain unchanged
        updated = self.project_manager.get_project(pid)
        self.assertEqual(updated["name"], original["name"])
        self.assertEqual(updated["status"], original["status"])

    def test_update_project_multiple_fields(self):
        """Test updating multiple allowed fields at once"""
        pid = self.project_manager.create_project(self.user_id, "Original", "Original Desc")
        
        result = self.project_manager.update_project(
            pid, 
            name="Updated Name",
            description="Updated Description",
            status="archived"
        )
        
        self.assertTrue(result)
        proj = self.project_manager.get_project(pid)
        self.assertEqual(proj["name"], "Updated Name")
        self.assertEqual(proj["description"], "Updated Description")
        self.assertEqual(proj["status"], "archived")

    def test_update_project_only_name(self):
        """Test updating only the name field"""
        pid = self.project_manager.create_project(self.user_id, "Old Name", "Keep Desc")
        original_desc = self.project_manager.get_project(pid)["description"]
        
        result = self.project_manager.update_project(pid, name="New Name Only")
        
        self.assertTrue(result)
        proj = self.project_manager.get_project(pid)
        self.assertEqual(proj["name"], "New Name Only")
        self.assertEqual(proj["description"], original_desc)

    def test_update_project_filters_invalid_fields(self):
        """Test that update_project filters out invalid fields"""
        pid = self.project_manager.create_project(self.user_id, "Test")
        
        # Try to update with mix of valid and invalid fields
        result = self.project_manager.update_project(
            pid,
            name="Valid Update",
            user_id="should be ignored",  # Not in allowed_fields
            created_at="should be ignored"  # Not in allowed_fields
        )
        
        # Should still return True because name is valid
        self.assertTrue(result)
        proj = self.project_manager.get_project(pid)
        self.assertEqual(proj["name"], "Valid Update")

    def test_update_project_nonexistent_id(self):
        fake_id = str(uuid.uuid4())
        result = self.project_manager.update_project(fake_id, name="Ignored")
        self.assertFalse(result)

    def test_delete_project_success(self):
        pid = self.project_manager.create_project(self.user_id, "To Delete")
        result = self.project_manager.delete_project(pid)
        self.assertTrue(result)
        self.assertIsNone(self.project_manager.get_project(pid))


    def test_project_statistics_with_tasks(self):
        pid = self.project_manager.create_project(self.user_id, "Stats Project")
        t1 = self.task_manager.create_task(pid, "Todo task")
        t2 = self.task_manager.create_task(pid, "In Progress task")
        t3 = self.task_manager.create_task(pid, "Completed task")
        self.task_manager.update_task(t2, status="in_progress")
        self.task_manager.update_task(t3, status="completed")

        stats = self.project_manager.get_project_statistics(pid)

        self.assertEqual(stats["total_tasks"], 3)
        self.assertEqual(stats["todo_tasks"], 1)
        self.assertEqual(stats["in_progress_tasks"], 1)
        self.assertEqual(stats["completed_tasks"], 1)
        self.assertAlmostEqual(stats["completion_percentage"], 33.33, places=1)

    def test_project_statistics_no_tasks(self):
        pid = self.project_manager.create_project(self.user_id, "Empty Project")
        stats = self.project_manager.get_project_statistics(pid)
        self.assertEqual(stats["total_tasks"], 0)
        self.assertEqual(stats["completed_tasks"], 0)
        self.assertEqual(stats["completion_percentage"], 0.0)


if __name__ == "__main__":
    unittest.main()