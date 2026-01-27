"""
Main orchestration script for Planner Delta Tracker

This script:
1. Loads the previous snapshot
2. Gets current Planner state
3. Detects changes
4. Generates and sends report
5. Saves new snapshot

Usage:
    python main.py                  # Run full delta detection and report
    python main.py --init           # Create initial snapshot only
    python main.py --test           # Test mode: save report locally instead of emailing
    python main.py --show-plans     # List available Planner plans
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Load .env file for local development
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ.setdefault(key.strip(), val.strip())

from auth import get_access_token, test_authentication
from planner_client import PlannerClient
from snapshot import SnapshotManager
from delta import DeltaDetector, format_changes_text
from report import send_delta_report, save_report_locally
from config import PLAN_ID


def show_available_plans(token: str):
    """Show all Planner plans accessible to the user."""
    print("\nVerfuegbare Planner Plaene:")
    print("=" * 60)

    client = PlannerClient(token)
    plans = client.list_my_plans()

    if not plans:
        print("Keine Plaene gefunden.")
        print("\nMoegliche Gruende:")
        print("  - Der Account hat keinen Zugriff auf Planner")
        print("  - Es wurden noch keine Plaene erstellt")
        return

    for i, plan in enumerate(plans, 1):
        print(f"\n{i}. {plan['title']}")
        print(f"   Plan ID: {plan['id']}")

        # Get buckets for this plan
        try:
            buckets = client.get_buckets(plan['id'])
            if buckets:
                print(f"   Buckets: {', '.join(b['name'] for b in buckets)}")
            tasks = client.get_tasks(plan['id'])
            print(f"   Tasks: {len(tasks)}")
        except Exception as e:
            print(f"   (Details nicht verfuegbar: {e})")

    print("\n" + "=" * 60)
    print("Kopiere die gewuenschte Plan ID in config.py (PLAN_ID)")


def run_initial_snapshot(token: str):
    """Create the initial snapshot."""
    print("\nErstelle initialen Snapshot...")
    print("=" * 60)

    manager = SnapshotManager(token)
    snapshot = manager.create_and_save_snapshot()

    print("\n[OK] Initialer Snapshot erstellt!")
    print(f"  Tasks erfasst: {snapshot['task_count']}")
    print(f"  Zeitstempel: {snapshot['created_at']}")
    print("\nBeim naechsten Lauf werden Aenderungen erkannt.")


def run_delta_detection(token: str, test_mode: bool = False):
    """Run the full delta detection and reporting process."""
    print("\nStarte Delta-Erkennung...")
    print("=" * 60)

    manager = SnapshotManager(token)

    # Load previous snapshot
    print("\n1. Lade vorherigen Snapshot...")
    previous = manager.load_previous_snapshot()

    if previous is None:
        print("   [!] Kein vorheriger Snapshot gefunden!")
        print("   Erstelle initialen Snapshot stattdessen...")
        run_initial_snapshot(token)
        return

    print(f"   Gefunden: {previous['task_count']} Tasks vom {previous['created_at']}")

    # Create current snapshot
    print("\n2. Hole aktuellen Planner-Stand...")
    current = manager.create_snapshot()
    print(f"   Aktuell: {current['task_count']} Tasks")

    # Detect changes
    print("\n3. Erkenne Aenderungen...")
    detector = DeltaDetector(previous, current)
    changes = detector.detect_changes()
    summary = detector.get_summary(changes)

    # Display results
    print("\n" + format_changes_text(changes, summary))

    # Send report or save locally
    print("\n4. Generiere Report...")
    if test_mode:
        print("   [TEST MODE] Speichere Report lokal...")
        save_report_locally(changes, summary)
    else:
        print("   Sende Report per E-Mail...")
        send_delta_report(changes, summary, token)

    # Save new snapshot
    print("\n5. Speichere neuen Snapshot...")
    manager.save_snapshot(current)

    print("\n" + "=" * 60)
    print("[OK] Delta-Erkennung abgeschlossen!")


def main():
    parser = argparse.ArgumentParser(
        description="Microsoft Planner Delta Tracker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  python main.py --init         Erstelle initialen Snapshot
  python main.py                Fuehre Delta-Erkennung aus
  python main.py --test         Delta-Erkennung ohne E-Mail-Versand
  python main.py --show-plans   Zeige verfuegbare Planner Plaene
        """
    )

    parser.add_argument(
        '--init',
        action='store_true',
        help='Erstelle nur den initialen Snapshot'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test-Modus: Report lokal speichern statt per E-Mail senden'
    )

    parser.add_argument(
        '--show-plans',
        action='store_true',
        help='Zeige alle verfuegbaren Planner Plaene'
    )

    parser.add_argument(
        '--check-auth',
        action='store_true',
        help='Teste nur die Authentifizierung'
    )

    args = parser.parse_args()

    print("=" * 58)
    print("  Microsoft Planner Delta Tracker")
    print("  Alpine Leadership")
    print("=" * 58)

    # Check authentication
    if args.check_auth:
        print("\nPruefe Authentifizierung...")
        success = test_authentication()
        sys.exit(0 if success else 1)

    # Get access token (interactive for first run)
    print("\nAuthentifiziere bei Microsoft...")
    try:
        token = get_access_token(interactive=True)
        print("[OK] Authentifizierung erfolgreich")
    except Exception as e:
        print(f"[FEHLER] Authentifizierung fehlgeschlagen: {e}")
        print("\nBitte pruefe die Konfiguration in config.py:")
        print("  - TENANT_ID")
        print("  - CLIENT_ID")
        print("  - CLIENT_SECRET")
        sys.exit(1)

    # Execute requested operation
    try:
        if args.show_plans:
            show_available_plans(token)
        elif args.init:
            run_initial_snapshot(token)
        else:
            run_delta_detection(token, test_mode=args.test)
    except Exception as e:
        print(f"\n[FEHLER] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
