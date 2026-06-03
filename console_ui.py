import os
import sys
from datetime import datetime, timedelta
from Project_Work import TaskManager, EmailUnavailableError, UserNameUnavailableError

# ─────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def header(title):
    print("\n" + "═" * 50)
    print(f"  {title}")
    print("═" * 50)

def success(msg):
    print(f"\n  ✔  {msg}")

def error(msg):
    print(f"\n  ✘  {msg}")

def info(msg):
    print(f"  →  {msg}")

def pause():
    input("\n  Press Enter to continue...")

def pick(options):
    """Show numbered options and return chosen index (0-based)."""
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    while True:
        choice = input("\n  Choose: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return int(choice) - 1
        error("Invalid choice, try again.")

# ─────────────────────────────────────────
#  AUTH SCREENS
# ─────────────────────────────────────────

def screen_register(manager: TaskManager):
    header("REGISTER NEW ACCOUNT")
    username = input("  Username : ").strip()
    email    = input("  Email    : ").strip()
    password = input("  Password : ").strip()
    try:
        uid = manager.register(username, email, password)
        success(f"Account created! ID: {uid}")
    except UserNameUnavailableError:
        error(f"Username '{username}' is already taken.")
    except EmailUnavailableError:
        error(f"Email '{email}' is already registered.")
    except Exception as e:
        error(str(e))
    pause()

def screen_login(manager: TaskManager) -> bool:
    header("LOGIN")
    username = input("  Username : ").strip()
    password = input("  Password : ").strip()
    if manager.login(username, password):
        success(f"Welcome back, {username}!")
        pause()
        return True
    else:
        error("Wrong username or password.")
        pause()
        return False

# ─────────────────────────────────────────
#  PROJECT SCREENS
# ─────────────────────────────────────────

def screen_projects(manager: TaskManager):
    while True:
        header("PROJECTS")
        options = [
            "List my projects",
            "Create project",
            "View project details & statistics",
            "Update project",
            "Delete project",
            "Back"
        ]
        choice = pick(options)

        if choice == 0:
            projects = manager.project.list_user_projects(manager._current_user)
            print()
            if not projects:
                info("No projects found.")
            for p in projects:
                info(f"[{p['id'][:8]}...] {p['name']} — {p['status']}")
            pause()

        elif choice == 1:
            header("CREATE PROJECT")
            name = input("  Name        : ").strip()
            desc = input("  Description : ").strip()
            pid = manager.project.create_project(manager._current_user, name, desc)
            success(f"Project created! ID: {pid}")
            pause()

        elif choice == 2:
            header("PROJECT DETAILS")
            pid = input("  Project ID : ").strip()
            proj = manager.project.get_project(pid)
            if not proj:
                error("Project not found.")
            else:
                print()
                for k, v in proj.items():
                    info(f"{k:<20}: {v}")
                stats = manager.project.get_project_statistics(pid)
                print()
                info(f"Total tasks      : {stats['total_tasks']}")
                info(f"Todo             : {stats['todo_tasks']}")
                info(f"In progress      : {stats['in_progress_tasks']}")
                info(f"Completed        : {stats['completed_tasks']}")
                info(f"Completion       : {stats['completion_percentage']:.1f}%")
            pause()

        elif choice == 3:
            header("UPDATE PROJECT")
            pid  = input("  Project ID  : ").strip()
            name = input("  New name (leave blank to skip) : ").strip()
            desc = input("  New description (leave blank to skip) : ").strip()
            status = input("  New status [active/archived] (leave blank to skip) : ").strip()
            kwargs = {}
            if name:   kwargs['name'] = name
            if desc:   kwargs['description'] = desc
            if status: kwargs['status'] = status
            result = manager.project.update_project(pid, **kwargs)
            success("Project updated!") if result else error("Project not found or nothing to update.")
            pause()

        elif choice == 4:
            header("DELETE PROJECT")
            pid = input("  Project ID : ").strip()
            confirm = input("  Are you sure? (yes/no) : ").strip().lower()
            if confirm == "yes":
                result = manager.project.delete_project(pid)
                success("Project deleted!") if result else error("Project not found.")
            else:
                info("Cancelled.")
            pause()

        elif choice == 5:
            break

# ─────────────────────────────────────────
#  TASK SCREENS
# ─────────────────────────────────────────

def screen_tasks(manager: TaskManager):
    while True:
        header("TASKS")
        options = [
            "List project tasks",
            "Create task",
            "Get task details",
            "Update task",
            "Delete task",
            "View overdue tasks",
            "View my assigned tasks",
            "Back"
        ]
        choice = pick(options)

        if choice == 0:
            header("LIST PROJECT TASKS")
            pid    = input("  Project ID         : ").strip()
            status = input("  Filter by status (leave blank for all) : ").strip() or None
            prio   = input("  Filter by priority (leave blank for all) : ").strip() or None
            tasks  = manager.task.list_project_tasks(pid, status=status, priority=prio)
            print()
            if not tasks:
                info("No tasks found.")
            for t in tasks:
                info(f"[{t['id'][:8]}...] {t['title']} | {t['status']} | {t['priority']}")
            pause()

        elif choice == 1:
            header("CREATE TASK")
            pid   = input("  Project ID  : ").strip()
            title = input("  Title       : ").strip()
            desc  = input("  Description : ").strip()
            prio  = input("  Priority [low/medium/high] (default: medium) : ").strip() or "medium"
            due   = input("  Due date [YYYY-MM-DD] (leave blank to skip) : ").strip()
            due_date = f"{due} 00:00:00" if due else None
            assigned = input("  Assign to user ID (leave blank to skip) : ").strip() or None
            try:
                tid = manager.task.create_task(pid, title, desc, prio, assigned, due_date)
                success(f"Task created! ID: {tid}")
            except ValueError as e:
                error(str(e))
            pause()

        elif choice == 2:
            header("TASK DETAILS")
            tid  = input("  Task ID : ").strip()
            task = manager.task.get_task(tid)
            if not task:
                error("Task not found.")
            else:
                print()
                for k, v in task.items():
                    info(f"{k:<20}: {v}")
                pct = manager.subtask.get_subtask_completion_percentage(tid)
                info(f"{'Subtask progress':<20}: {pct:.1f}%")
            pause()

        elif choice == 3:
            header("UPDATE TASK")
            tid    = input("  Task ID : ").strip()
            title  = input("  New title (leave blank to skip) : ").strip()
            status = input("  New status [todo/in_progress/completed] (leave blank to skip) : ").strip()
            prio   = input("  New priority [low/medium/high] (leave blank to skip) : ").strip()
            desc   = input("  New description (leave blank to skip) : ").strip()
            kwargs = {}
            if title:  kwargs['title'] = title
            if status: kwargs['status'] = status
            if prio:   kwargs['priority'] = prio
            if desc:   kwargs['description'] = desc
            try:
                result = manager.task.update_task(tid, **kwargs)
                success("Task updated!") if result else error("Nothing to update.")
            except ValueError as e:
                error(str(e))
            pause()

        elif choice == 4:
            header("DELETE TASK")
            tid     = input("  Task ID : ").strip()
            confirm = input("  Are you sure? (yes/no) : ").strip().lower()
            if confirm == "yes":
                try:
                    manager.task.delete_task(tid)
                    success("Task deleted!")
                except ValueError as e:
                    error(str(e))
            else:
                info("Cancelled.")
            pause()

        elif choice == 5:
            header("OVERDUE TASKS")
            pid   = input("  Project ID : ").strip()
            tasks = manager.task.get_overdue_tasks(pid)
            print()
            if not tasks:
                info("No overdue tasks.")
            for t in tasks:
                info(f"[{t['id'][:8]}...] {t['title']} | due: {t['due_date']}")
            pause()

        elif choice == 6:
            header("MY ASSIGNED TASKS")
            tasks = manager.task.get_user_assigned_tasks(manager._current_user)
            print()
            if not tasks:
                info("No assigned tasks.")
            for t in tasks:
                info(f"[{t['id'][:8]}...] {t['title']} | {t['status']} | due: {t['due_date']}")
            pause()

        elif choice == 7:
            break

# ─────────────────────────────────────────
#  SUBTASK SCREENS
# ─────────────────────────────────────────

def screen_subtasks(manager: TaskManager):
    while True:
        header("SUBTASKS")
        options = [
            "List subtasks for a task",
            "Create subtask",
            "Toggle subtask (complete/uncomplete)",
            "Delete subtask",
            "Subtask completion percentage",
            "Back"
        ]
        choice = pick(options)

        if choice == 0:
            header("LIST SUBTASKS")
            tid      = input("  Task ID : ").strip()
            subtasks = manager.subtask.list_task_subtasks(tid)
            print()
            if not subtasks:
                info("No subtasks found.")
            for s in subtasks:
                done = "✔" if s['completed'] else "○"
                info(f"[{s['id'][:8]}...] {done} {s['title']}")
            pause()

        elif choice == 1:
            header("CREATE SUBTASK")
            tid   = input("  Task ID : ").strip()
            title = input("  Title   : ").strip()
            try:
                sid = manager.subtask.create_subtask(tid, title)
                success(f"Subtask created! ID: {sid}")
            except ValueError as e:
                error(str(e))
            pause()

        elif choice == 2:
            header("TOGGLE SUBTASK")
            sid    = input("  Subtask ID : ").strip()
            result = manager.subtask.toggle_subtask(sid)
            success("Subtask toggled!") if result else error("Subtask not found.")
            pause()

        elif choice == 3:
            header("DELETE SUBTASK")
            sid     = input("  Subtask ID : ").strip()
            confirm = input("  Are you sure? (yes/no) : ").strip().lower()
            if confirm == "yes":
                try:
                    manager.subtask.delete_subtask(sid)
                    success("Subtask deleted!")
                except ValueError as e:
                    error(str(e))
            else:
                info("Cancelled.")
            pause()

        elif choice == 4:
            header("SUBTASK COMPLETION")
            tid = input("  Task ID : ").strip()
            pct = manager.subtask.get_subtask_completion_percentage(tid)
            info(f"Completion: {pct:.1f}%")
            pause()

        elif choice == 5:
            break

# ─────────────────────────────────────────
#  COMMENT SCREENS
# ─────────────────────────────────────────

def screen_comments(manager: TaskManager):
    while True:
        header("COMMENTS")
        options = [
            "List comments for a task",
            "Add comment",
            "Delete comment",
            "Back"
        ]
        choice = pick(options)

        if choice == 0:
            tid      = input("  Task ID : ").strip()
            comments = manager.comment.list_task_comments(tid)
            print()
            if not comments:
                info("No comments.")
            for c in comments:
                info(f"[{c['username']}] {c['content']}  ({c['created_at']})")
            pause()

        elif choice == 1:
            tid     = input("  Task ID : ").strip()
            content = input("  Comment : ").strip()
            cid = manager.comment.create_comment(tid, manager._current_user, content)
            success(f"Comment added! ID: {cid}")
            pause()

        elif choice == 2:
            cid     = input("  Comment ID : ").strip()
            confirm = input("  Are you sure? (yes/no) : ").strip().lower()
            if confirm == "yes":
                result = manager.comment.delete_comment(cid)
                success("Comment deleted!") if result else error("Comment not found.")
            pause()

        elif choice == 3:
            break

# ─────────────────────────────────────────
#  TIME LOG SCREENS
# ─────────────────────────────────────────

def screen_timelogs(manager: TaskManager):
    while True:
        header("TIME LOGS")
        options = [
            "Log time on a task",
            "View time logs for a task",
            "Total hours on a task",
            "My total hours (last 30 days)",
            "Delete time log",
            "Back"
        ]
        choice = pick(options)

        if choice == 0:
            tid   = input("  Task ID     : ").strip()
            hours = input("  Hours       : ").strip()
            desc  = input("  Description : ").strip()
            try:
                lid = manager.time_log.log_time(tid, manager._current_user, float(hours), desc)
                success(f"Time logged! ID: {lid}")
            except Exception as e:
                error(str(e))
            pause()

        elif choice == 1:
            tid  = input("  Task ID : ").strip()
            logs = manager.time_log.get_task_time_logs(tid)
            print()
            if not logs:
                info("No time logs.")
            for l in logs:
                info(f"[{l['username']}] {l['hours']}h — {l['description']}  ({l['date']})")
            pause()

        elif choice == 2:
            tid   = input("  Task ID : ").strip()
            total = manager.time_log.get_task_total_hours(tid)
            info(f"Total hours: {total:.1f}h")
            pause()

        elif choice == 3:
            hours = manager.time_log.get_user_hours(manager._current_user, days=30)
            info(f"Your hours last 30 days: {hours:.1f}h")
            pause()

        elif choice == 4:
            lid     = input("  Log ID : ").strip()
            confirm = input("  Are you sure? (yes/no) : ").strip().lower()
            if confirm == "yes":
                result = manager.time_log.delete_time_log(lid)
                success("Log deleted!") if result else error("Log not found.")
            pause()

        elif choice == 5:
            break

# ─────────────────────────────────────────
#  NOTIFICATION SCREENS
# ─────────────────────────────────────────

def screen_notifications(manager: TaskManager):
    while True:
        header("NOTIFICATIONS")
        options = [
            "View all notifications",
            "View unread only",
            "Mark notification as read",
            "Mark all as read",
            "Back"
        ]
        choice = pick(options)

        if choice == 0:
            notifs = manager.notification.get_user_notifications(manager._current_user)
            print()
            if not notifs:
                info("No notifications.")
            for n in notifs:
                status = "READ" if n['read'] else "UNREAD"
                info(f"[{status}] {n['message']}  ({n['created_at']})")
            pause()

        elif choice == 1:
            notifs = manager.notification.get_user_notifications(manager._current_user, unread_only=True)
            print()
            if not notifs:
                info("No unread notifications.")
            for n in notifs:
                info(f"[{n['id'][:8]}...] {n['message']}")
            pause()

        elif choice == 2:
            nid    = input("  Notification ID : ").strip()
            result = manager.notification.mark_as_read(nid)
            success("Marked as read!") if result else error("Notification not found.")
            pause()

        elif choice == 3:
            manager.notification.mark_all_as_read(manager._current_user)
            success("All notifications marked as read!")
            pause()

        elif choice == 4:
            break

# ─────────────────────────────────────────
#  AUDIT LOG SCREENS
# ─────────────────────────────────────────

def screen_auditlogs(manager: TaskManager):
    while True:
        header("AUDIT LOGS")
        options = [
            "View my actions",
            "View entity history",
            "Back"
        ]
        choice = pick(options)

        if choice == 0:
            logs = manager.audit_log.get_user_actions(manager._current_user)
            print()
            if not logs:
                info("No actions logged.")
            for l in logs:
                info(f"[{l['action']}] {l['entity_type']} {l['entity_id']}  ({l['created_at']})")
            pause()

        elif choice == 1:
            etype = input("  Entity type (e.g. task, project) : ").strip()
            eid   = input("  Entity ID : ").strip()
            logs  = manager.audit_log.get_entity_history(etype, eid)
            print()
            if not logs:
                info("No history found.")
            for l in logs:
                info(f"[{l['action']}] by {l['user_id'][:8]}...  ({l['created_at']})")
            pause()

        elif choice == 2:
            break

# ─────────────────────────────────────────
#  ANALYTICS SCREENS
# ─────────────────────────────────────────

def screen_analytics(manager: TaskManager):
    while True:
        header("ANALYTICS")
        options = [
            "My productivity stats",
            "Team productivity for a project",
            "Project burndown",
            "Back"
        ]
        choice = pick(options)

        if choice == 0:
            stats = manager.analytics.get_user_productivity_stats(manager._current_user)
            print()
            info(f"Total assigned   : {stats['total_assigned']}")
            info(f"Completed        : {stats['completed']}")
            info(f"Completion rate  : {stats['completion_rate']:.1f}%")
            info(f"Hours (30 days)  : {stats['hours_logged_30days']:.1f}h")
            pause()

        elif choice == 1:
            pid  = input("  Project ID : ").strip()
            team = manager.analytics.get_team_productivity(pid)
            print()
            if not team:
                info("No team data.")
            for username, s in team.items():
                info(f"{username}: {s['completed_tasks']}/{s['total_tasks']} tasks ({s['completion_rate']:.1f}%)")
            pause()

        elif choice == 2:
            pid    = input("  Project ID : ").strip()
            burndown = manager.analytics.get_project_burndown(pid)
            print()
            info(f"Todo        : {burndown['todo']}")
            info(f"In progress : {burndown['in_progress']}")
            info(f"Completed   : {burndown['completed']}")
            pause()

        elif choice == 3:
            break

# ─────────────────────────────────────────
#  MAIN MENU
# ─────────────────────────────────────────

def main_menu(manager: TaskManager):
    while True:
        clear()
        header(f"TASK MANAGER  —  logged in as: {manager._current_user[:8]}...")
        options = [
            "Projects",
            "Tasks",
            "Subtasks",
            "Comments",
            "Time Logs",
            "Notifications",
            "Audit Logs",
            "Analytics",
            "Logout"
        ]
        choice = pick(options)

        if choice == 0:   screen_projects(manager)
        elif choice == 1: screen_tasks(manager)
        elif choice == 2: screen_subtasks(manager)
        elif choice == 3: screen_comments(manager)
        elif choice == 4: screen_timelogs(manager)
        elif choice == 5: screen_notifications(manager)
        elif choice == 6: screen_auditlogs(manager)
        elif choice == 7: screen_analytics(manager)
        elif choice == 8:
            manager.logout()
            success("Logged out.")
            pause()
            break

# ─────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────

def main():
    clear()
    print("\n" + "═" * 50)
    print("  TASK MANAGEMENT SYSTEM")
    print("  GMI2J3 — Group 7")
    print("═" * 50)

    manager = TaskManager("tasks.db")

    while True:
        print("\n  [1] Login")
        print("  [2] Register")
        print("  [3] Exit")
        choice = input("\n  Choose: ").strip()

        if choice == "1":
            if screen_login(manager):
                main_menu(manager)
        elif choice == "2":
            screen_register(manager)
        elif choice == "3":
            manager._db.close()
            print("\n  Goodbye!\n")
            sys.exit(0)
        else:
            error("Invalid choice.")

if __name__ == "__main__":
    main()
