import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import hashlib
import uuid
from abc import ABC, abstractmethod
import statistics

# Task Management Application - Full-featured system for managing projects and tasks

class Database:
    """Database management for tasks and projects"""

    def __init__(self, db_name: str = "tasks.db"):
        self.db_name = db_name
        self.connect()
        self.init_db()

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.conn.execute("PRAGMA foreign_keys = ON;")
        except sqlite3.OperationalError:
            raise ValueError(f"Could not open/create database '{self.db_name}'")
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def init_db(self):
        """Initialize database tables"""
        self.cursor.executescript("""
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
        """)
        self.conn.commit()

    def close(self):
        self.conn.close()


class User:
    """User management"""

    def __init__(self, db: Database):
        self.db = db

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username: str, email: str, password: str) -> str:
        user_id = str(uuid.uuid4())
        password_hash = self.hash_password(password)

        self.db.cursor.execute("""
            INSERT INTO users (id, username, email, password_hash)
            VALUES (?, ?, ?, ?)
        """, (user_id, username, email, password_hash))
        self.db.conn.commit()
        return user_id

    def authenticate(self, username: str, password: str) -> Optional[str]:
        password_hash = self.hash_password(password)
        self.db.cursor.execute("""
            SELECT id FROM users WHERE username = ? AND password_hash = ?
        """, (username, password_hash))
        result = self.db.cursor.fetchone()
        return result['id'] if result else None

    def get_user(self, user_id: str) -> Optional[Dict]:
        self.db.cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = self.db.cursor.fetchone()
        return dict(row) if row else None

    def update_user(self, user_id: str, **kwargs) -> bool:
        allowed_fields = ['username', 'email']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [user_id]

        self.db.cursor.execute(f"""
            UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, values)
        self.db.conn.commit()
        return True

    def list_users(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        self.db.cursor.execute("""
            SELECT id, username, email, created_at FROM users
            LIMIT ? OFFSET ?
        """, (limit, offset))
        return [dict(row) for row in self.db.cursor.fetchall()]


class Project:
    """Project management"""

    def __init__(self, db: Database):
        self.db = db

    def create_project(self, user_id: str, name: str, description: str = "") -> str:
        project_id = str(uuid.uuid4())

        self.db.cursor.execute("""
            INSERT INTO projects (id, user_id, name, description)
            VALUES (?, ?, ?, ?)
        """, (project_id, user_id, name, description))
        self.db.conn.commit()
        return project_id

    def get_project(self, project_id: str) -> Optional[Dict]:
        self.db.cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
        row = self.db.cursor.fetchone()
        return dict(row) if row else None

    def list_user_projects(self, user_id: str, status: str = None) -> List[Dict]:
        if status:
            self.db.cursor.execute("""
                SELECT * FROM projects WHERE user_id = ? AND status = ?
                ORDER BY created_at DESC
            """, (user_id, status))
        else:
            self.db.cursor.execute("""
                SELECT * FROM projects WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
        return [dict(row) for row in self.db.cursor.fetchall()]

    def update_project(self, project_id: str, **kwargs) -> bool:
        allowed_fields = ['name', 'description', 'status']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [project_id]

        self.db.cursor.execute(f"""
            UPDATE projects SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, values)
        self.db.conn.commit()
        return True

    def delete_project(self, project_id: str) -> bool:
        self.db.cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        self.db.conn.commit()
        return self.db.cursor.rowcount > 0

    def get_project_statistics(self, project_id: str) -> Dict:
        self.db.cursor.execute("""
            SELECT
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress_tasks,
                SUM(CASE WHEN status = 'todo' THEN 1 ELSE 0 END) as todo_tasks
            FROM tasks WHERE project_id = ?
        """, (project_id,))

        row = self.db.cursor.fetchone()
        return {
            'total_tasks': row[0] or 0,
            'completed_tasks': row[1] or 0,
            'in_progress_tasks': row[2] or 0,
            'todo_tasks': row[3] or 0,
            'completion_percentage': (row[1] or 0) / (row[0] or 1) * 100
        }


class Task:
    """Task management"""

    def __init__(self, db: Database):
        self.db = db

    def create_task(self, project_id: str, title: str, description: str = "",
                   priority: str = "medium", assigned_to: str = None,
                   due_date: datetime = None) -> str:
        task_id = str(uuid.uuid4())

        self.db.cursor.execute("""
            INSERT INTO tasks (id, project_id, title, description, priority, assigned_to, due_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (task_id, project_id, title, description, priority, assigned_to, due_date))
        self.db.conn.commit()
        return task_id

    def get_task(self, task_id: str) -> Optional[Dict]:
        self.db.cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = self.db.cursor.fetchone()
        return dict(row) if row else None

    def list_project_tasks(self, project_id: str, status: str = None,
                          priority: str = None) -> List[Dict]:
        query = "SELECT * FROM tasks WHERE project_id = ?"
        params = [project_id]

        if status:
            query += " AND status = ?"
            params.append(status)
        if priority:
            query += " AND priority = ?"
            params.append(priority)

        query += " ORDER BY due_date ASC, priority DESC"
        self.db.cursor.execute(query, params)
        return [dict(row) for row in self.db.cursor.fetchall()]

    def update_task(self, task_id: str, **kwargs) -> bool:
        allowed_fields = ['title', 'description', 'priority', 'status', 'assigned_to', 'due_date']
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not updates:
            return False

        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [task_id]

        self.db.cursor.execute(f"""
            UPDATE tasks SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, values)
        self.db.conn.commit()
        return True

    def delete_task(self, task_id: str) -> bool:
        self.db.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.db.conn.commit()
        return self.db.cursor.rowcount > 0

    def get_overdue_tasks(self, project_id: str) -> List[Dict]:
        self.db.cursor.execute("""
            SELECT * FROM tasks
            WHERE project_id = ? AND due_date < datetime('now') AND status != 'completed'
            ORDER BY due_date ASC
        """, (project_id,))
        return [dict(row) for row in self.db.cursor.fetchall()]

    def get_user_assigned_tasks(self, user_id: str) -> List[Dict]:
        self.db.cursor.execute("""
            SELECT * FROM tasks WHERE assigned_to = ? AND status != 'completed'
            ORDER BY due_date ASC
        """, (user_id,))
        return [dict(row) for row in self.db.cursor.fetchall()]


class SubTask:
    """SubTask management"""

    def __init__(self, db: Database):
        self.db = db

    def create_subtask(self, task_id: str, title: str) -> str:
        subtask_id = str(uuid.uuid4())

        self.db.cursor.execute("""
            INSERT INTO subtasks (id, task_id, title)
            VALUES (?, ?, ?)
        """, (subtask_id, task_id, title))
        self.db.conn.commit()
        return subtask_id

    def list_task_subtasks(self, task_id: str) -> List[Dict]:
        self.db.cursor.execute("""
            SELECT * FROM subtasks WHERE task_id = ?
            ORDER BY created_at ASC
        """, (task_id,))
        return [dict(row) for row in self.db.cursor.fetchall()]

    def toggle_subtask(self, subtask_id: str) -> bool:
        self.db.cursor.execute("""
            UPDATE subtasks SET completed = NOT completed WHERE id = ?
        """, (subtask_id,))
        self.db.conn.commit()
        return self.db.cursor.rowcount > 0

    def delete_subtask(self, subtask_id: str) -> bool:
        self.db.cursor.execute("DELETE FROM subtasks WHERE id = ?", (subtask_id,))
        self.db.conn.commit()
        return self.db.cursor.rowcount > 0

    def get_subtask_completion_percentage(self, task_id: str) -> float:
        self.db.cursor.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN completed = 1 THEN 1 ELSE 0 END) as completed
            FROM subtasks WHERE task_id = ?
        """, (task_id,))

        row = self.db.cursor.fetchone()
        total = row[0] or 0
        completed = row[1] or 0
        return (completed / total * 100) if total > 0 else 0


class Comment:
    """Comment management"""

    def __init__(self, db: Database):
        self.db = db

    def create_comment(self, task_id: str, user_id: str, content: str) -> str:
        comment_id = str(uuid.uuid4())

        self.db.cursor.execute("""
            INSERT INTO comments (id, task_id, user_id, content)
            VALUES (?, ?, ?, ?)
        """, (comment_id, task_id, user_id, content))
        self.db.conn.commit()
        return comment_id

    def list_task_comments(self, task_id: str) -> List[Dict]:
        self.db.cursor.execute("""
            SELECT c.*, u.username FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.task_id = ?
            ORDER BY c.created_at DESC
        """, (task_id,))
        return [dict(row) for row in self.db.cursor.fetchall()]

    def delete_comment(self, comment_id: str) -> bool:
        self.db.cursor.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        self.db.conn.commit()
        return self.db.cursor.rowcount > 0


class TimeLog:
    """Time tracking"""

    def __init__(self, db: Database):
        self.db = db

    def log_time(self, task_id: str, user_id: str, hours: float, description: str = "") -> str:
        log_id = str(uuid.uuid4())

        self.db.cursor.execute("""
            INSERT INTO time_logs (id, task_id, user_id, hours, description)
            VALUES (?, ?, ?, ?, ?)
        """, (log_id, task_id, user_id, hours, description))
        self.db.conn.commit()
        return log_id

    def get_task_time_logs(self, task_id: str) -> List[Dict]:
        self.db.cursor.execute("""
            SELECT tl.*, u.username FROM time_logs tl
            JOIN users u ON tl.user_id = u.id
            WHERE tl.task_id = ?
            ORDER BY tl.date DESC
        """, (task_id,))
        return [dict(row) for row in self.db.cursor.fetchall()]

    def get_task_total_hours(self, task_id: str) -> float:
        self.db.cursor.execute("""
            SELECT SUM(hours) FROM time_logs WHERE task_id = ?
        """, (task_id,))
        result = self.db.cursor.fetchone()[0]
        return result or 0.0

    def get_user_hours(self, user_id: str, days: int = 30) -> float:
        self.db.cursor.execute("""
            SELECT SUM(hours) FROM time_logs
            WHERE user_id = ? AND date > datetime('now', '-' || ? || ' days')
        """, (user_id, days))
        result = self.db.cursor.fetchone()[0]
        return result or 0.0

    def delete_time_log(self, log_id: str) -> bool:
        self.db.cursor.execute("DELETE FROM time_logs WHERE id = ?", (log_id,))
        self.db.conn.commit()
        return self.db.cursor.rowcount > 0


class Notification: #!!*
    """Notification management"""

    def __init__(self, db: Database):
        if not isinstance(db, Database):
            raise TypeError("db is not of the type Database")
            return

        self.db = db

    def create_notification(self, user_id: str, message: str) -> str:
        notification_id = str(uuid.uuid4())
        try:
            self.db.cursor.execute("""
                INSERT INTO notifications (id, user_id, message)
                VALUES (?, ?, ?)
            """, (notification_id, user_id, message))
            self.db.conn.commit()
        except sqlite3.IntegrityError as ex:
            error_message = str(ex)
            if "UNIQUE constraint failed: notifications.id" in error_message:
                pass
            elif "FOREIGN KEY constraint failed" in error_message:
                raise ValueError("This user doesn't exist")
            elif "NOT NULL constraint failed: notifications.message" in error_message:
                raise ValueError("Message was null")
            elif "CHECK constraint failed" in error_message:
                raise ValueError("Message of length 0")
        return notification_id

    def get_user_notifications(self, user_id: str, unread_only: bool = False) -> List[Dict]:
        if unread_only:
            self.db.cursor.execute("""
                SELECT * FROM notifications WHERE user_id = ? AND read = 0
                ORDER BY created_at DESC
            """, (user_id,))
        else:
            self.db.cursor.execute("""
                SELECT * FROM notifications WHERE user_id = ?
                ORDER BY created_at DESC
            """, (user_id,))
        return [dict(row) for row in self.db.cursor.fetchall()]

    def mark_as_read(self, notification_id: str) -> bool:
        self.db.cursor.execute("""
            UPDATE notifications SET read = 1 WHERE id = ?
        """, (notification_id,))
        self.db.conn.commit()
        return self.db.cursor.rowcount > 0

    def mark_all_as_read(self, user_id: str) -> bool:
        self.db.cursor.execute("""
            UPDATE notifications SET read = 1 WHERE user_id = ?
        """, (user_id,))
        self.db.conn.commit()
        return self.db.cursor.rowcount > 0


class AuditLog:
    """Audit logging"""

    def __init__(self, db: Database):
        self.db = db

    def log_action(self, user_id: str, action: str, entity_type: str = None,
                   entity_id: str = None, changes: Dict = None) -> str:
        log_id = str(uuid.uuid4())
        changes_json = json.dumps(changes) if changes else None

        self.db.cursor.execute("""
            INSERT INTO audit_logs (id, user_id, action, entity_type, entity_id, changes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (log_id, user_id, action, entity_type, entity_id, changes_json))
        self.db.conn.commit()
        return log_id

    def get_user_actions(self, user_id: str, limit: int = 100) -> List[Dict]:
        self.db.cursor.execute("""
            SELECT * FROM audit_logs WHERE user_id = ?
            ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
        return [dict(row) for row in self.db.cursor.fetchall()]

    def get_entity_history(self, entity_type: str, entity_id: str) -> List[Dict]:
        self.db.cursor.execute("""
            SELECT * FROM audit_logs WHERE entity_type = ? AND entity_id = ?
            ORDER BY created_at DESC
        """, (entity_type, entity_id))
        return [dict(row) for row in self.db.cursor.fetchall()]


class Analytics:
    """Analytics and reporting"""

    def __init__(self, db: Database):
        self.db = db

    def get_user_productivity_stats(self, user_id: str) -> Dict:
        # Tasks assigned
        self.db.cursor.execute("""
            SELECT COUNT(*) FROM tasks WHERE assigned_to = ?
        """, (user_id,))
        total_assigned = self.db.cursor.fetchone()[0] or 0

        # Completed tasks
        self.db.cursor.execute("""
            SELECT COUNT(*) FROM tasks WHERE assigned_to = ? AND status = 'completed'
        """, (user_id,))
        completed = self.db.cursor.fetchone()[0] or 0

        # Hours logged (last 30 days)
        self.db.cursor.execute("""
            SELECT SUM(hours) FROM time_logs
            WHERE user_id = ? AND date > datetime('now', '-30 days')
        """, (user_id,))
        hours_logged = self.db.cursor.fetchone()[0] or 0

        return {
            'total_assigned': total_assigned,
            'completed': completed,
            'completion_rate': (completed / total_assigned * 100) if total_assigned > 0 else 0,
            'hours_logged_30days': hours_logged
        }

    def get_team_productivity(self, project_id: str) -> Dict:
        self.db.cursor.execute("""
            SELECT
                assigned_to,
                COUNT(*) as task_count,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM tasks WHERE project_id = ? AND assigned_to IS NOT NULL
            GROUP BY assigned_to
        """, (project_id,))

        team_data = {}
        for row in self.db.cursor.fetchall():
            user_id = row[0]
            self.db.cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            user = self.db.cursor.fetchone()
            username = user['username'] if user else 'Unknown'

            team_data[username] = {
                'total_tasks': row[1],
                'completed_tasks': row[2],
                'completion_rate': (row[2] / row[1] * 100) if row[1] > 0 else 0
            }

        return team_data

    def get_project_burndown(self, project_id: str) -> Dict:
        self.db.cursor.execute("""
            SELECT status, COUNT(*) as count FROM tasks WHERE project_id = ?
            GROUP BY status
        """, (project_id,))

        status_counts = {}
        for row in self.db.cursor.fetchall():
            status_counts[row[0]] = row[1]

        return {
            'todo': status_counts.get('todo', 0),
            'in_progress': status_counts.get('in_progress', 0),
            'completed': status_counts.get('completed', 0)
        }


class TaskManager: #!!*
    """Main application manager"""

    def __init__(self, db_name: str = "tasks.db"):
        self._db = Database(db_name)
        self._user = User(self._db)
        self._project = Project(self._db)
        self._task = Task(self._db)
        self._subtask = SubTask(self._db)
        self._comment = Comment(self._db)
        self._time_log = TimeLog(self._db)
        self._notification = Notification(self._db)
        self._audit_log = AuditLog(self._db)
        self._analytics = Analytics(self._db)
        self._current_user = None

    @property
    def db(self) -> Database:
        if self.logged_in():
            return self._db
        raise PermissionError("Not logged in")

    @property
    def user(self) -> User:
        if self.logged_in():
            return self._user
        raise PermissionError("Not logged in")

    @property
    def project(self) -> Project:
        if self.logged_in():
            return self._project
        raise PermissionError("Not logged in")

    @property
    def task(self) -> Task:
        if self.logged_in():
            return self._task
        raise PermissionError("Not logged in")

    @property
    def subtask(self) -> SubTask:
        if self.logged_in():
            return self._subtask
        raise PermissionError("Not logged in")

    @property
    def comment(self) -> Comment:
        if self.logged_in():
            return self._comment
        raise PermissionError("Not logged in")

    @property
    def time_log(self) -> TimeLog:
        if self.logged_in():
            return self._time_log
        raise PermissionError("Not logged in")

    @property
    def notification(self) -> Notification:
        if self.logged_in():
            return self._notification
        raise PermissionError("Not logged in")

    @property
    def audit_log(self) -> AuditLog:
        if self.logged_in():
            return self._audit_log
        raise PermissionError("Not logged in")

    @property
    def analytics(self) -> Analytics:
        if self.logged_in():
            return self._analytics
        raise PermissionError("Not logged in")

    @property
    def project(self) -> str | None:
        if self.logged_in():
            return self._project
        raise PermissionError("Not logged in")

    def logged_in(self) -> bool:
        return not self._current_user == None

    def login(self, username: str, password: str) -> bool:
        user_id = self._user.authenticate(username, password)
        if user_id:
            self._current_user = user_id
            return True
        return False

    def logout(self):
        self._current_user = None

    def register(self, username: str, email: str, password: str) -> str:
        try:
            return self._user.create_user(username, email, password)
        except ValueError as ex:
            message = str.lower(ex)
            if "username" in message:
                raise self.UserNameUnavailableError(f"username: {username} is unavailable")
            elif "email" in message:
                raise self.EmailUnavailableError(f"email: {email} is unavailable")

    def close(self):
        self.db.close()

    def EmailUnavailableError(Exception):
        """Raised when an email address is not available for use"""
        pass
    def UserNameUnavailableError(Exception):
        """Raised when an email address is not available for use"""
        pass


# Demo and testing
def run_demo():
    """Run demonstration of the task management system"""
    manager = TaskManager(":memory:")
    #manager = TaskManager("test_tasks.db")

    # Register users
    print("=== User Registration ===")
    user1_id = manager.register("john_doe", "john@example.com", "password123")
    user2_id = manager.register("jane_smith", "jane@example.com", "password456")
    print(f"Created user 1: {user1_id}")
    print(f"Created user 2: {user2_id}")

    # Login
    print("\n=== User Login ===")
    manager.login("john_doe", "password123")
    print(f"Logged in as: john_doe")

    # Create projects
    print("\n=== Project Creation ===")
    project1_id = manager.project.create_project(user1_id, "Website Redesign", "Redesign company website")
    project2_id = manager.project.create_project(user1_id, "Mobile App", "Build iOS and Android app")
    print(f"Created project 1: {project1_id}")
    print(f"Created project 2: {project2_id}")

    # Create tasks
    print("\n=== Task Creation ===")
    due_date1 = (datetime.now() + timedelta(days=7)).isoformat()
    task1_id = manager.task.create_task(
        project1_id, "Design mockups", "Create UI mockups for website",
        priority="high", assigned_to=user1_id, due_date=due_date1
    )
    task2_id = manager.task.create_task(
        project1_id, "Set up database", "Configure PostgreSQL database",
        priority="high", assigned_to=user2_id, due_date=due_date1
    )
    task3_id = manager.task.create_task(
        project2_id, "API design", "Design REST API endpoints",
        priority="medium", assigned_to=user1_id
    )
    print(f"Created {task1_id}, {task2_id}, {task3_id}")

    # Add subtasks
    print("\n=== Subtask Creation ===")
    sub1_id = manager.subtask.create_subtask(task1_id, "Create wireframes")
    sub2_id = manager.subtask.create_subtask(task1_id, "Get stakeholder approval")
    sub3_id = manager.subtask.create_subtask(task1_id, "Create final mockups")
    print(f"Created subtasks: {sub1_id}, {sub2_id}, {sub3_id}")

    # Add comments
    print("\n=== Adding Comments ===")
    comment1_id = manager.comment.create_comment(task1_id, user1_id, "Starting on the mockups")
    comment2_id = manager.comment.create_comment(task1_id, user2_id, "Looking good so far!")
    print(f"Added comments: {comment1_id}, {comment2_id}")

    # Log time
    print("\n=== Time Logging ===")
    log1_id = manager.time_log.log_time(task1_id, user1_id, 4.5, "Wireframe work")
    log2_id = manager.time_log.log_time(task1_id, user2_id, 2.0, "Design review")
    log3_id = manager.time_log.log_time(task2_id, user2_id, 3.5, "Initial setup")
    print(f"Logged time: {log1_id}, {log2_id}, {log3_id}")

    # Update task status
    print("\n=== Task Status Updates ===")
    manager.task.update_task(task1_id, status="in_progress")
    print("Updated task statuses")

    # Get task details
    print("\n=== Task Details ===")
    task = manager.task.get_task(task1_id)
    print(f"Task: {task['title']}")
    print(f"Status: {task['status']}")
    print(f"Priority: {task['priority']}")

    # Get comments
    print("\n=== Task Comments ===")
    comments = manager.comment.list_task_comments(task1_id)
    for comment in comments:
        print(f"{comment['username']}: {comment['content']}")

    # Get project tasks
    print("\n=== Project Tasks ===")
    tasks = manager.task.list_project_tasks(project1_id)
    for t in tasks:
        print(f"- {t['title']} ({t['status']})")

    # Project statistics
    print("\n=== Project Statistics ===")
    stats = manager.project.get_project_statistics(project1_id)
    print(f"Total tasks: {stats['total_tasks']}")
    print(f"Completed: {stats['completed_tasks']}")
    print(f"In progress: {stats['in_progress_tasks']}")
    print(f"Todo: {stats['todo_tasks']}")
    print(f"Completion: {stats['completion_percentage']:.1f}%")

    # User productivity
    print("\n=== User Productivity Stats ===")
    user_stats = manager.analytics.get_user_productivity_stats(user1_id)
    print(f"Total assigned: {user_stats['total_assigned']}")
    print(f"Completed: {user_stats['completed']}")
    print(f"Completion rate: {user_stats['completion_rate']:.1f}%")
    print(f"Hours logged (30 days): {user_stats['hours_logged_30days']:.1f}")

    # Team productivity
    print("\n=== Team Productivity ===")
    team_stats = manager.analytics.get_team_productivity(project1_id)
    for username, stats in team_stats.items():
        print(f"{username}: {stats['completed_tasks']}/{stats['total_tasks']} tasks")

    # Create notifications
    print("\n=== Notifications ===")
    manager.notification.create_notification(user1_id, "Task assigned to you: Design mockups")
    manager.notification.create_notification(user1_id, "Comment added to: Design mockups")
    notifs = manager.notification.get_user_notifications(user1_id)
    print(f"Unread notifications: {len([n for n in notifs if not n['read']])}")

    # Audit logs
    print("\n=== Audit Logs ===")
    manager.audit_log.log_action(user1_id, "created_task", "task", task1_id)
    manager.audit_log.log_action(user1_id, "updated_task", "task", task1_id, {"status": "in_progress"})
    logs = manager.audit_log.get_user_actions(user1_id)
    print(f"User actions logged: {len(logs)}")

    # Cleanup
    manager.close()
    print("\n=== Demo Complete ===")


if __name__ == "__main__":
    run_demo()
