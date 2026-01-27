"""
Snapshot module for Planner Delta Tracker

Creates and manages snapshots of Planner tasks.
Supports Azure Blob Storage (cloud) and local file storage.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from config import LOCAL_SNAPSHOT_FILE
from planner_client import PlannerClient

BLOB_CONTAINER = "planner-snapshots"
BLOB_NAME = "latest_snapshot.json"


class SnapshotManager:
    """Manages Planner task snapshots."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.planner = PlannerClient(access_token)

        # Detect if running in Azure (AzureWebJobsStorage is set and not dev storage)
        storage_conn = os.environ.get("AzureWebJobsStorage", "")
        self.use_blob = bool(storage_conn and storage_conn != "UseDevelopmentStorage=true")

        if self.use_blob:
            from azure.storage.blob import BlobServiceClient
            self.blob_service = BlobServiceClient.from_connection_string(storage_conn)
            # Ensure container exists
            try:
                self.blob_service.create_container(BLOB_CONTAINER)
            except Exception:
                pass  # Container already exists
        else:
            # Local file storage
            snapshot_dir = Path(LOCAL_SNAPSHOT_FILE).parent
            snapshot_dir.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, plan_id: str = None) -> Dict:
        """Create a new snapshot of all tasks in the plan."""
        logging.info("Fetching current Planner tasks...")
        print("Fetching current Planner tasks...")
        tasks = self.planner.get_all_tasks_enriched(plan_id)

        snapshot = {
            "created_at": datetime.utcnow().isoformat() + "Z",
            "plan_id": plan_id,
            "task_count": len(tasks),
            "tasks": tasks
        }

        logging.info(f"Created snapshot with {len(tasks)} tasks")
        print(f"Created snapshot with {len(tasks)} tasks")
        return snapshot

    def save_snapshot(self, snapshot: Dict) -> str:
        """Save snapshot to storage (Blob or local file)."""
        data = json.dumps(snapshot, indent=2, ensure_ascii=False)

        if self.use_blob:
            blob_client = self.blob_service.get_blob_client(BLOB_CONTAINER, BLOB_NAME)
            blob_client.upload_blob(data, overwrite=True)
            location = f"Azure Blob: {BLOB_CONTAINER}/{BLOB_NAME}"
        else:
            with open(LOCAL_SNAPSHOT_FILE, 'w', encoding='utf-8') as f:
                f.write(data)
            location = LOCAL_SNAPSHOT_FILE

        logging.info(f"Snapshot saved to: {location}")
        print(f"Snapshot saved to: {location}")
        return location

    def load_previous_snapshot(self) -> Optional[Dict]:
        """Load the previous snapshot from storage."""
        if self.use_blob:
            try:
                blob_client = self.blob_service.get_blob_client(BLOB_CONTAINER, BLOB_NAME)
                data = blob_client.download_blob().readall()
                return json.loads(data)
            except Exception:
                return None
        else:
            if not os.path.exists(LOCAL_SNAPSHOT_FILE):
                return None
            with open(LOCAL_SNAPSHOT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)

    def create_and_save_snapshot(self, plan_id: str = None) -> Dict:
        """
        Convenience method: Create and immediately save a snapshot.

        Returns:
            The created snapshot
        """
        snapshot = self.create_snapshot(plan_id)
        self.save_snapshot(snapshot)
        return snapshot


def create_initial_snapshot():
    """Create the initial snapshot (first run)."""
    from auth import get_access_token

    print("Creating initial Planner snapshot...")
    print("=" * 50)

    token = get_access_token(interactive=True)
    manager = SnapshotManager(token)

    snapshot = manager.create_and_save_snapshot()

    print("=" * 50)
    print(f"[OK] Initial snapshot created successfully!")
    print(f"  Tasks captured: {snapshot['task_count']}")
    print(f"  Timestamp: {snapshot['created_at']}")

    return snapshot


if __name__ == "__main__":
    create_initial_snapshot()
