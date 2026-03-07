"""Todo Manager - Full CRUD operations for todo.md with Dashboard sync."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
import re

from src.config import TODO_FILE, DASHBOARD, INBOX, NEEDS_ACTION
from src.utils import log_action

logger = logging.getLogger(__name__)

class TodoManager:
    """Manages todo CRUD operations and Dashboard sync."""

    def __init__(self):
        """Initialize todo manager."""
        self.todo_file = TODO_FILE
        self._ensure_todo_file()

    def _ensure_todo_file(self) -> None:
        """Ensure todo.md exists with initial structure."""
        if not self.todo_file.exists():
            self.todo_file.write_text("""---
last_updated: 2026-03-07T00:00:00
total: 0
pending: 0
done: 0
---

# Todo List

## High Priority
| ID | Task | Due | Recurrence | Status | Created |
|----|------|-----|------------|--------|---------|

## Medium Priority
| ID | Task | Due | Recurrence | Status | Created |
|----|------|-----|------------|--------|---------|

## Low Priority
| ID | Task | Due | Recurrence | Status | Created |
|----|------|-----|------------|--------|---------|

## Done
| ID | Task | Completed | Recurrence |
|----|------|-----------|------------|
""")

    def _generate_todo_id(self) -> str:
        """Generate unique todo ID (T001, T002, ...)."""
        content = self.todo_file.read_text()
        # Find all existing IDs
        ids = re.findall(r'\| (T\d+) \|', content)
        if not ids:
            return "T001"
        # Extract numbers and find max
        numbers = [int(id[1:]) for id in ids]
        return f"T{max(numbers) + 1:03d}"

    def create_todo(
        self,
        title: str,
        priority: str = "Medium",
        due_date: Optional[str] = None,
        recurrence: str = "None"
    ) -> str:
        """Create a new todo item.

        Args:
            title: Todo task description
            priority: High/Medium/Low
            due_date: YYYY-MM-DD format
            recurrence: None/Daily/Weekly/Monthly

        Returns:
            Todo ID (T001, T002, etc.)
        """
        todo_id = self._generate_todo_id()
        created = datetime.now().strftime("%Y-%m-%d")

        content = self.todo_file.read_text()

        # Format priority for section lookup
        priority_section = f"## {priority} Priority"
        if priority_section not in content:
            priority = "Medium"
            priority_section = "## Medium Priority"

        # Insert new row
        row = f"| {todo_id} | {title} | {due_date or 'N/A'} | {recurrence} | pending | {created} |"

        # Find the section and insert after header
        lines = content.split('\n')
        result = []
        for i, line in enumerate(lines):
            result.append(line)
            if line == priority_section and i + 1 < len(lines):
                # Skip the existing table header
                if lines[i + 1].startswith("|"):
                    result.append(lines[i + 1])
                    result.append(row)
                    i += 1

        content = '\n'.join(result)
        self._update_metadata(content)
        self.todo_file.write_text(content)

        log_action("todo_manager", f"Created todo {todo_id}: {title}", result="success")
        return todo_id

    def read_todo(self, todo_id: str) -> Optional[dict]:
        """Read a specific todo by ID."""
        content = self.todo_file.read_text()

        # Find the row with this ID
        pattern = rf'\| {todo_id} \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|'
        match = re.search(pattern, content)

        if not match:
            return None

        return {
            "id": todo_id,
            "task": match.group(1).strip(),
            "due": match.group(2).strip(),
            "recurrence": match.group(3).strip(),
            "status": match.group(4).strip(),
            "created": match.group(5).strip(),
        }

    def update_todo(self, todo_id: str, **kwargs) -> bool:
        """Update a todo by ID.

        Supported kwargs: task, due, recurrence, status
        """
        content = self.todo_file.read_text()
        todo = self.read_todo(todo_id)

        if not todo:
            return False

        # Build updated row
        task = kwargs.get("task", todo["task"])
        due = kwargs.get("due", todo["due"])
        recurrence = kwargs.get("recurrence", todo["recurrence"])
        status = kwargs.get("status", todo["status"])
        created = todo["created"]

        old_row = f"| {todo_id} | {todo['task']} | {todo['due']} | {todo['recurrence']} | {todo['status']} | {created} |"
        new_row = f"| {todo_id} | {task} | {due} | {recurrence} | {status} | {created} |"

        content = content.replace(old_row, new_row)
        self._update_metadata(content)
        self.todo_file.write_text(content)

        log_action("todo_manager", f"Updated todo {todo_id}", result="success")
        return True

    def delete_todo(self, todo_id: str) -> bool:
        """Delete a todo by ID."""
        content = self.todo_file.read_text()
        todo = self.read_todo(todo_id)

        if not todo:
            return False

        # Find and remove the row
        created = todo["created"]
        row = f"| {todo_id} | {todo['task']} | {todo['due']} | {todo['recurrence']} | {todo['status']} | {created} |"

        lines = content.split('\n')
        lines = [line for line in lines if row not in line]
        content = '\n'.join(lines)

        self._update_metadata(content)
        self.todo_file.write_text(content)

        log_action("todo_manager", f"Deleted todo {todo_id}", result="success")
        return True

    def complete_todo(self, todo_id: str) -> bool:
        """Mark a todo as complete (move to Done section)."""
        todo = self.read_todo(todo_id)
        if not todo:
            return False

        # Delete from current section
        self.delete_todo(todo_id)

        # Add to Done section
        content = self.todo_file.read_text()
        completed = datetime.now().strftime("%Y-%m-%d")
        done_row = f"| {todo_id} | {todo['task']} | {completed} | {todo['recurrence']} |"

        # Insert in Done section
        done_section = "## Done"
        if done_section in content:
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line == done_section and i + 1 < len(lines):
                    if lines[i + 1].startswith("|"):
                        lines.insert(i + 2, done_row)
                        break
            content = '\n'.join(lines)

        self._update_metadata(content)
        self.todo_file.write_text(content)

        log_action("todo_manager", f"Completed todo {todo_id}", result="success")
        return True

    def list_todos(self, priority: Optional[str] = None, status: Optional[str] = None) -> list[dict]:
        """List all todos, optionally filtered by priority or status."""
        content = self.todo_file.read_text()
        todos = []

        # Find all todo rows
        pattern = r'\| (T\d+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \| ([^|]+) \|'
        for match in re.finditer(pattern, content):
            todo = {
                "id": match.group(1),
                "task": match.group(2).strip(),
                "due": match.group(3).strip(),
                "recurrence": match.group(4).strip(),
                "status": match.group(5).strip(),
                "created": match.group(6).strip(),
            }

            # Apply filters
            if status and todo["status"] != status:
                continue

            todos.append(todo)

        return todos

    def sync_dashboard(self) -> None:
        """Update Dashboard.md with active todos section."""
        dashboard = DASHBOARD
        if not dashboard.exists():
            return

        content = dashboard.read_text()

        # Get active todos (not done)
        active = self.list_todos(status="pending")[:5]

        # Generate todo section
        todo_section = "## Active Todos\n\n"
        if active:
            todo_section += "| Task | Due | Priority |\n"
            todo_section += "|------|-----|----------|\n"
            for todo in active:
                todo_section += f"| {todo['task']} | {todo['due']} | Pending |\n"
        else:
            todo_section += "No active todos.\n"

        # Update or insert section
        if "## Active Todos" in content:
            # Replace existing section
            parts = content.split("## Active Todos")
            before = parts[0]
            after = parts[1].split("\n##")[1:] if len(parts) > 1 else []
            after_str = "\n##" + "\n##".join(after) if after else ""
            content = before + todo_section + after_str
        else:
            # Insert before other sections
            content = todo_section + "\n" + content

        dashboard.write_text(content)
        log_action("todo_manager", "Synced Dashboard.md", result="success")

    def create_inbox_task(self, todo_id: str) -> None:
        """Create a task file in Inbox/ for orchestrator processing."""
        todo = self.read_todo(todo_id)
        if not todo:
            return

        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        task_file = INBOX / f"TASK_{now}_todo_{todo_id}.md"

        content = f"""---
type: todo_task
todo_id: {todo_id}
approval_required: false
source: discord
created: {datetime.now().isoformat()}
---

# Todo Task: {todo['task']}

**Priority**: Medium
**Due**: {todo['due']}
**Recurrence**: {todo['recurrence']}

## Status
Pending approval

## Actions
- Review task
- Mark as done
- Update due date
"""

        task_file.write_text(content)
        log_action("todo_manager", f"Created inbox task for {todo_id}", result="success")

    def _update_metadata(self, content: str) -> None:
        """Update frontmatter metadata (counts, timestamp)."""
        # Count todos
        all_todos = re.findall(r'\| (T\d+) \|', content)
        total = len(all_todos)

        # Count pending and done
        pending_pattern = r'\| T\d+ \| [^|]+ \| [^|]+ \| [^|]+ \| pending \|'
        pending = len(re.findall(pending_pattern, content))
        done = total - pending

        # Update frontmatter
        now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        new_frontmatter = f"""---
last_updated: {now}
total: {total}
pending: {pending}
done: {done}
---
"""

        # Replace old frontmatter
        lines = content.split('\n')
        if lines[0] == '---':
            # Find closing ---
            end_idx = 1
            for i in range(1, len(lines)):
                if lines[i] == '---':
                    end_idx = i + 1
                    break
            content = new_frontmatter + '\n'.join(lines[end_idx:])

        return content


def main():
    """CLI entry point for todo manager."""
    import sys

    tm = TodoManager()

    if len(sys.argv) < 2:
        print("Usage: zoya-todo [create|read|update|delete|list|complete|sync]")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "create":
        title = sys.argv[2] if len(sys.argv) > 2 else "Untitled"
        priority = sys.argv[3] if len(sys.argv) > 3 else "Medium"
        due_date = sys.argv[4] if len(sys.argv) > 4 else None
        todo_id = tm.create_todo(title, priority, due_date)
        print(f"Created: {todo_id}")

    elif cmd == "read":
        todo_id = sys.argv[2] if len(sys.argv) > 2 else "T001"
        todo = tm.read_todo(todo_id)
        if todo:
            print(json.dumps(todo, indent=2))
        else:
            print(f"Todo {todo_id} not found")

    elif cmd == "list":
        todos = tm.list_todos()
        for todo in todos:
            print(f"{todo['id']}: {todo['task']} ({todo['status']})")

    elif cmd == "complete":
        todo_id = sys.argv[2] if len(sys.argv) > 2 else "T001"
        if tm.complete_todo(todo_id):
            print(f"Completed: {todo_id}")
        else:
            print(f"Could not complete {todo_id}")

    elif cmd == "sync":
        tm.sync_dashboard()
        print("Dashboard synced")

    else:
        print(f"Unknown command: {cmd}")


if __name__ == "__main__":
    main()
