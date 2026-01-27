"""
Microsoft Planner API Client

Handles all interactions with Microsoft Planner via Graph API.
"""

import requests
from typing import Dict, List, Optional
from config import GRAPH_BASE_URL, PLAN_ID, GROUP_ID


class PlannerClient:
    """Client for Microsoft Planner Graph API operations."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        self._bucket_cache = {}
        self._user_cache = {}

    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make GET request to Graph API."""
        url = f"{GRAPH_BASE_URL}{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)

        if response.status_code != 200:
            raise Exception(f"API Error {response.status_code}: {response.text}")

        return response.json()

    def get_plan(self, plan_id: str = None) -> dict:
        """Get plan details."""
        plan_id = plan_id or PLAN_ID
        return self._get(f"/planner/plans/{plan_id}")

    def get_buckets(self, plan_id: str = None) -> List[dict]:
        """Get all buckets in a plan."""
        plan_id = plan_id or PLAN_ID
        result = self._get(f"/planner/plans/{plan_id}/buckets")
        buckets = result.get("value", [])

        # Cache bucket names for later lookup
        for bucket in buckets:
            self._bucket_cache[bucket["id"]] = bucket["name"]

        return buckets

    def get_bucket_name(self, bucket_id: str, plan_id: str = None) -> str:
        """Get bucket name by ID (uses cache)."""
        if bucket_id not in self._bucket_cache:
            self.get_buckets(plan_id)
        return self._bucket_cache.get(bucket_id, "Unknown Bucket")

    def get_tasks(self, plan_id: str = None) -> List[dict]:
        """Get all tasks in a plan."""
        plan_id = plan_id or PLAN_ID
        result = self._get(f"/planner/plans/{plan_id}/tasks")
        return result.get("value", [])

    def get_task_details(self, task_id: str) -> dict:
        """Get detailed information about a specific task."""
        return self._get(f"/planner/tasks/{task_id}/details")

    def get_user_name(self, user_id: str) -> str:
        """Get user display name by ID (uses cache)."""
        if not user_id:
            return "Unassigned"

        if user_id not in self._user_cache:
            try:
                user = self._get(f"/users/{user_id}")
                self._user_cache[user_id] = user.get("displayName", user.get("mail", user_id))
            except Exception:
                self._user_cache[user_id] = user_id

        return self._user_cache[user_id]

    def get_all_tasks_enriched(self, plan_id: str = None) -> List[dict]:
        """
        Get all tasks with enriched information (bucket names, assignee names,
        descriptions, and modification timestamps).
        This is the main method for getting a complete snapshot.
        """
        plan_id = plan_id or PLAN_ID

        # Ensure bucket cache is populated
        self.get_buckets(plan_id)

        # Get all tasks
        tasks = self.get_tasks(plan_id)

        enriched_tasks = []
        for task in tasks:
            # Get assignees
            assignees = []
            assignments = task.get("assignments", {})
            for user_id in assignments.keys():
                assignees.append(self.get_user_name(user_id))

            # Get task details (description, checklist)
            description = ""
            checklist_count = 0
            try:
                details = self.get_task_details(task["id"])
                description = details.get("description", "")
                checklist = details.get("checklist", {})
                checklist_count = len(checklist)
            except Exception:
                pass

            enriched_task = {
                "id": task["id"],
                "title": task["title"],
                "bucket_id": task.get("bucketId"),
                "bucket_name": self.get_bucket_name(task.get("bucketId")),
                "assignees": assignees,
                "assignees_str": ", ".join(assignees) if assignees else "Unassigned",
                "percent_complete": task.get("percentComplete", 0),
                "created_date": task.get("createdDateTime"),
                "due_date": task.get("dueDateTime"),
                "start_date": task.get("startDateTime"),
                "priority": task.get("priority", 5),
                "order_hint": task.get("orderHint"),
                "description": description,
                "checklist_count": checklist_count,
                "conversation_thread_id": task.get("conversationThreadId", ""),
                "has_description": bool(description),
            }
            enriched_tasks.append(enriched_task)

        return enriched_tasks

    def list_plans_in_group(self, group_id: str = None) -> List[dict]:
        """List all Planner plans in a group."""
        group_id = group_id or GROUP_ID
        result = self._get(f"/groups/{group_id}/planner/plans")
        return result.get("value", [])

    def list_my_plans(self) -> List[dict]:
        """List all plans the current user has access to."""
        result = self._get("/me/planner/plans")
        return result.get("value", [])


def test_planner_connection():
    """Test Planner API connection."""
    from auth import get_access_token

    print("Testing Planner API connection...")

    try:
        token = get_access_token(interactive=True)
        client = PlannerClient(token)

        # Try to list user's plans
        print("\nYour Planner plans:")
        plans = client.list_my_plans()

        if not plans:
            print("  No plans found. Make sure you have access to Planner.")
        else:
            for plan in plans:
                print(f"  - {plan['title']} (ID: {plan['id']})")

        return True

    except Exception as e:
        print(f"[FEHLER] Planner connection failed: {e}")
        return False


if __name__ == "__main__":
    test_planner_connection()
