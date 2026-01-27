"""
Delta Detection module for Planner Delta Tracker

Compares current Planner state with previous snapshot to detect changes.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TaskChange:
    """Represents a single task change."""
    change_type: str  # "new", "deleted", "bucket_changed", "assignee_changed", "completed", "description_changed", "progress_changed"
    task_id: str
    task_title: str
    assignees: str
    old_value: Optional[str] = None
    new_value: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "change_type": self.change_type,
            "task_id": self.task_id,
            "task_title": self.task_title,
            "assignees": self.assignees,
            "old_value": self.old_value,
            "new_value": self.new_value,
        }

    def describe(self) -> str:
        """Human-readable description of the change."""
        if self.change_type == "new":
            return f"Neuer Lead: '{self.task_title}' (Owner: {self.assignees}) in Bucket '{self.new_value}'"

        elif self.change_type == "deleted":
            return f"Gelöscht: '{self.task_title}' (war in Bucket '{self.old_value}')"

        elif self.change_type == "bucket_changed":
            return f"Verschoben: '{self.task_title}' (Owner: {self.assignees}) von '{self.old_value}' nach '{self.new_value}'"

        elif self.change_type == "assignee_changed":
            return f"Owner geändert: '{self.task_title}' von '{self.old_value}' zu '{self.new_value}'"

        elif self.change_type == "completed":
            return f"Abgeschlossen: '{self.task_title}' (Owner: {self.assignees})"

        elif self.change_type == "reopened":
            return f"Wieder geöffnet: '{self.task_title}' (Owner: {self.assignees})"

        elif self.change_type == "description_changed":
            return f"Beschreibung geändert: '{self.task_title}' (Owner: {self.assignees})"

        elif self.change_type == "progress_changed":
            return f"Status geändert: '{self.task_title}' (Owner: {self.assignees}) von {self.old_value} auf {self.new_value}"

        else:
            return f"Änderung: '{self.task_title}'"


class DeltaDetector:
    """Detects changes between Planner snapshots."""

    def __init__(self, previous_snapshot: Dict, current_snapshot: Dict):
        """
        Initialize delta detector.

        Args:
            previous_snapshot: The older snapshot to compare from
            current_snapshot: The newer snapshot to compare to
        """
        self.previous = previous_snapshot
        self.current = current_snapshot

        # Index tasks by ID for quick lookup
        self.previous_tasks = {t["id"]: t for t in previous_snapshot.get("tasks", [])}
        self.current_tasks = {t["id"]: t for t in current_snapshot.get("tasks", [])}

    def detect_changes(self) -> List[TaskChange]:
        """
        Detect all changes between snapshots.

        Returns:
            List of TaskChange objects describing each change
        """
        changes = []

        # Find new and modified tasks
        for task_id, current_task in self.current_tasks.items():
            if task_id not in self.previous_tasks:
                # New task
                changes.append(TaskChange(
                    change_type="new",
                    task_id=task_id,
                    task_title=current_task["title"],
                    assignees=current_task.get("assignees_str", "Unassigned"),
                    new_value=current_task.get("bucket_name", "Unknown")
                ))
            else:
                # Existing task - check for modifications
                previous_task = self.previous_tasks[task_id]

                # Check bucket change
                if current_task.get("bucket_id") != previous_task.get("bucket_id"):
                    changes.append(TaskChange(
                        change_type="bucket_changed",
                        task_id=task_id,
                        task_title=current_task["title"],
                        assignees=current_task.get("assignees_str", "Unassigned"),
                        old_value=previous_task.get("bucket_name", "Unknown"),
                        new_value=current_task.get("bucket_name", "Unknown")
                    ))

                # Check assignee change
                if current_task.get("assignees_str") != previous_task.get("assignees_str"):
                    changes.append(TaskChange(
                        change_type="assignee_changed",
                        task_id=task_id,
                        task_title=current_task["title"],
                        assignees=current_task.get("assignees_str", "Unassigned"),
                        old_value=previous_task.get("assignees_str", "Unassigned"),
                        new_value=current_task.get("assignees_str", "Unassigned")
                    ))

                # Check completion status and progress changes
                prev_complete = previous_task.get("percent_complete", 0)
                curr_complete = current_task.get("percent_complete", 0)

                if prev_complete < 100 and curr_complete == 100:
                    changes.append(TaskChange(
                        change_type="completed",
                        task_id=task_id,
                        task_title=current_task["title"],
                        assignees=current_task.get("assignees_str", "Unassigned"),
                        old_value=str(prev_complete) + "%",
                        new_value="100%"
                    ))
                elif prev_complete == 100 and curr_complete < 100:
                    changes.append(TaskChange(
                        change_type="reopened",
                        task_id=task_id,
                        task_title=current_task["title"],
                        assignees=current_task.get("assignees_str", "Unassigned"),
                        old_value="100%",
                        new_value=str(curr_complete) + "%"
                    ))
                elif prev_complete != curr_complete:
                    changes.append(TaskChange(
                        change_type="progress_changed",
                        task_id=task_id,
                        task_title=current_task["title"],
                        assignees=current_task.get("assignees_str", "Unassigned"),
                        old_value=str(prev_complete) + "%",
                        new_value=str(curr_complete) + "%"
                    ))

                # Check description changes
                prev_desc = previous_task.get("description", "")
                curr_desc = current_task.get("description", "")
                if prev_desc != curr_desc:
                    changes.append(TaskChange(
                        change_type="description_changed",
                        task_id=task_id,
                        task_title=current_task["title"],
                        assignees=current_task.get("assignees_str", "Unassigned"),
                    ))

        # Find deleted tasks
        for task_id, previous_task in self.previous_tasks.items():
            if task_id not in self.current_tasks:
                changes.append(TaskChange(
                    change_type="deleted",
                    task_id=task_id,
                    task_title=previous_task["title"],
                    assignees=previous_task.get("assignees_str", "Unassigned"),
                    old_value=previous_task.get("bucket_name", "Unknown")
                ))

        return changes

    def get_summary(self, changes: List[TaskChange] = None) -> Dict:
        """
        Get a summary of changes.

        Returns:
            Dict with change counts and metadata
        """
        if changes is None:
            changes = self.detect_changes()

        summary = {
            "total_changes": len(changes),
            "new_tasks": sum(1 for c in changes if c.change_type == "new"),
            "deleted_tasks": sum(1 for c in changes if c.change_type == "deleted"),
            "bucket_changes": sum(1 for c in changes if c.change_type == "bucket_changed"),
            "assignee_changes": sum(1 for c in changes if c.change_type == "assignee_changed"),
            "completed_tasks": sum(1 for c in changes if c.change_type == "completed"),
            "reopened_tasks": sum(1 for c in changes if c.change_type == "reopened"),
            "description_changes": sum(1 for c in changes if c.change_type == "description_changed"),
            "progress_changes": sum(1 for c in changes if c.change_type == "progress_changed"),
            "previous_snapshot_date": self.previous.get("created_at", "Unknown"),
            "current_snapshot_date": self.current.get("created_at", "Unknown"),
            "previous_task_count": len(self.previous_tasks),
            "current_task_count": len(self.current_tasks),
        }

        return summary


def detect_changes_from_snapshots(previous: Dict, current: Dict) -> tuple:
    """
    Convenience function to detect changes between two snapshots.

    Returns:
        Tuple of (changes list, summary dict)
    """
    detector = DeltaDetector(previous, current)
    changes = detector.detect_changes()
    summary = detector.get_summary(changes)

    return changes, summary


def format_changes_text(changes: List[TaskChange], summary: Dict) -> str:
    """Format changes as plain text."""
    lines = []
    lines.append("=" * 60)
    lines.append("PLANNER DELTA REPORT")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"Zeitraum: {summary['previous_snapshot_date']} bis {summary['current_snapshot_date']}")
    lines.append(f"Tasks vorher: {summary['previous_task_count']}, Tasks jetzt: {summary['current_task_count']}")
    lines.append("")

    if summary['total_changes'] == 0:
        lines.append("Keine Änderungen gefunden.")
    else:
        lines.append(f"Gefundene Änderungen: {summary['total_changes']}")
        lines.append("-" * 40)

        # Group by change type
        if summary['bucket_changes'] > 0:
            lines.append(f"\nBUCKET-AENDERUNGEN ({summary['bucket_changes']}):")
            for c in changes:
                if c.change_type == "bucket_changed":
                    lines.append(f"  • {c.describe()}")

        if summary['new_tasks'] > 0:
            lines.append(f"\nNEUE TASKS ({summary['new_tasks']}):")
            for c in changes:
                if c.change_type == "new":
                    lines.append(f"  • {c.describe()}")

        if summary['completed_tasks'] > 0:
            lines.append(f"\nABGESCHLOSSEN ({summary['completed_tasks']}):")
            for c in changes:
                if c.change_type == "completed":
                    lines.append(f"  • {c.describe()}")

        if summary['assignee_changes'] > 0:
            lines.append(f"\nOWNER-AENDERUNGEN ({summary['assignee_changes']}):")
            for c in changes:
                if c.change_type == "assignee_changed":
                    lines.append(f"  • {c.describe()}")

        if summary['deleted_tasks'] > 0:
            lines.append(f"\nGELOESCHT ({summary['deleted_tasks']}):")
            for c in changes:
                if c.change_type == "deleted":
                    lines.append(f"  • {c.describe()}")

        if summary['reopened_tasks'] > 0:
            lines.append(f"\nWIEDER GEOEFFNET ({summary['reopened_tasks']}):")
            for c in changes:
                if c.change_type == "reopened":
                    lines.append(f"  • {c.describe()}")

        if summary.get('description_changes', 0) > 0:
            lines.append(f"\nBESCHREIBUNG GEAENDERT ({summary['description_changes']}):")
            for c in changes:
                if c.change_type == "description_changed":
                    lines.append(f"  • {c.describe()}")

        if summary.get('progress_changes', 0) > 0:
            lines.append(f"\nSTATUS GEAENDERT ({summary['progress_changes']}):")
            for c in changes:
                if c.change_type == "progress_changed":
                    lines.append(f"  • {c.describe()}")

    lines.append("")
    lines.append("=" * 60)

    return "\n".join(lines)
