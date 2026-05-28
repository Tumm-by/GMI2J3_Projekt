import unittest
import json
import sqlite3
import Project_Work


class TestAuditLogSA(unittest.TestCase):
    def setUp(self):
        # Arrange
        self.db = Project_Work.Database(":memory:")
        self.user_manager = Project_Work.User(self.db)
        self.audit_manager = Project_Work.AuditLog(self.db)
        self.user_id = self.user_manager.create_user(
            "samuser",
            "sam@test.com",
            "pass123"
        )

    def tearDown(self):
        # Cleanup
        self.db.close()

    def test_log_action_success(self):
        """Rule 1: Valid user and action -> Return log_id"""
        # Arrange
        action = "created_task"
        entity_type = "task"
        entity_id = "task123"

        # Act
        log_id = self.audit_manager.log_action(
            self.user_id,
            action,
            entity_type,
            entity_id
        )

        # Validate
        self.assertIsInstance(log_id, str)

    def test_log_action_saved_in_database(self):
        """Rule 2: Valid log action -> Log is saved in database"""
        # Arrange
        action = "updated_task"

        # Act
        self.audit_manager.log_action(
            self.user_id,
            action,
            "task",
            "task123"
        )

        logs = self.audit_manager.get_user_actions(self.user_id)

        # Validate
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["action"], action)
        self.assertEqual(logs[0]["entity_type"], "task")
        self.assertEqual(logs[0]["entity_id"], "task123")

    def test_log_action_with_changes_json(self):
        """Rule 3: Changes dictionary -> Saved as JSON string"""
        # Arrange
        changes = {"status": "completed", "priority": "high"}

        # Act
        self.audit_manager.log_action(
            self.user_id,
            "updated_task",
            "task",
            "task123",
            changes
        )

        logs = self.audit_manager.get_user_actions(self.user_id)
        saved_changes = json.loads(logs[0]["changes"])

        # Validate
        self.assertEqual(saved_changes["status"], "completed")
        self.assertEqual(saved_changes["priority"], "high")

    def test_get_user_actions_only_returns_correct_user(self):
        """Rule 4: Two users have logs -> Only selected user's logs return"""
        # Arrange
        other_user_id = self.user_manager.create_user(
            "otheruser",
            "other@test.com",
            "pass123"
        )

        self.audit_manager.log_action(self.user_id, "sam_action")
        self.audit_manager.log_action(other_user_id, "other_action")

        # Act
        logs = self.audit_manager.get_user_actions(self.user_id)

        # Validate
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["action"], "sam_action")

    def test_get_entity_history_success(self):
        """Rule 5: Entity has history -> Return all logs for entity"""
        # Arrange
        self.audit_manager.log_action(
            self.user_id,
            "created_task",
            "task",
            "task123"
        )

        self.audit_manager.log_action(
            self.user_id,
            "updated_task",
            "task",
            "task123"
        )

        # Act
        history = self.audit_manager.get_entity_history("task", "task123")

        # Validate
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["entity_type"], "task")
        self.assertEqual(history[0]["entity_id"], "task123")

    def test_get_entity_history_no_result(self):
        """Rule 6: Entity does not exist -> Return empty list"""
        # Act
        history = self.audit_manager.get_entity_history("task", "missing_task")

        # Validate
        self.assertEqual(history, [])

    def test_log_action_invalid_user(self):
        """Rule 7: User does not exist -> Raise IntegrityError"""
        # Act + Validate
        with self.assertRaises(sqlite3.IntegrityError):
            self.audit_manager.log_action(
                "fake_user_id",
                "created_task"
            )


if __name__ == "__main__":
    unittest.main()
