"""
Report Generation and Delivery module for Planner Delta Tracker

Generates HTML reports and sends them via email using Microsoft Graph API.
"""

import requests
from typing import List, Dict
from datetime import datetime
from delta import TaskChange
from config import GRAPH_BASE_URL, REPORT_RECIPIENTS, REPORT_SENDER


class ReportGenerator:
    """Generates HTML reports from delta changes."""

    @staticmethod
    def generate_html_report(changes: List[TaskChange], summary: Dict) -> str:
        """
        Generate an HTML email report.

        Args:
            changes: List of TaskChange objects
            summary: Summary dict from DeltaDetector

        Returns:
            HTML string for the report
        """
        # Format dates nicely
        prev_date = summary.get('previous_snapshot_date', 'Unknown')
        curr_date = summary.get('current_snapshot_date', 'Unknown')

        try:
            prev_dt = datetime.fromisoformat(prev_date.replace('Z', '+00:00'))
            prev_date = prev_dt.strftime('%d.%m.%Y %H:%M')
        except:
            pass

        try:
            curr_dt = datetime.fromisoformat(curr_date.replace('Z', '+00:00'))
            curr_date = curr_dt.strftime('%d.%m.%Y %H:%M')
        except:
            pass

        # --- Professional email template (table-based for email client compatibility) ---
        html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sales Report</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f5f7;-webkit-font-smoothing:antialiased;">

<!-- Outer wrapper -->
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f5f7;">
<tr><td align="center" style="padding:32px 16px;">

<!-- Main card -->
<table role="presentation" width="640" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border:1px solid #e2e4e9;">

<!-- Top accent line -->
<tr><td style="height:3px;background-color:#1a2332;font-size:0;line-height:0;">&nbsp;</td></tr>

<!-- Header -->
<tr><td style="padding:32px 40px 24px 40px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td>
      <p style="margin:0 0 2px 0;font-family:Georgia,'Times New Roman',serif;font-size:11px;letter-spacing:2.5px;text-transform:uppercase;color:#8a9099;">Alpine Leadership</p>
      <h1 style="margin:0;font-family:Georgia,'Times New Roman',serif;font-size:22px;font-weight:400;color:#1a2332;line-height:1.3;">Sales-Pipeline &mdash; Wochenbericht</h1>
    </td>
    <td align="right" valign="bottom">
      <p style="margin:0;font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:12px;color:#8a9099;line-height:1.5;">{prev_date}<br>&mdash; {curr_date}</p>
    </td>
  </tr>
  </table>
</td></tr>

<!-- Divider -->
<tr><td style="padding:0 40px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="height:1px;background-color:#e2e4e9;font-size:0;line-height:0;">&nbsp;</td></tr></table></td></tr>

<!-- Stats row -->
<tr><td style="padding:24px 40px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td align="center" width="20%" style="padding:12px 0;">
      <p style="margin:0;font-family:Georgia,'Times New Roman',serif;font-size:28px;font-weight:400;color:#1a2332;line-height:1;">{summary['total_changes']}</p>
      <p style="margin:6px 0 0 0;font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:#8a9099;">Gesamt</p>
    </td>
    <td align="center" width="20%" style="padding:12px 0;border-left:1px solid #e2e4e9;">
      <p style="margin:0;font-family:Georgia,'Times New Roman',serif;font-size:28px;font-weight:400;color:#1a2332;line-height:1;">{summary['bucket_changes']}</p>
      <p style="margin:6px 0 0 0;font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:#8a9099;">Verschoben</p>
    </td>
    <td align="center" width="20%" style="padding:12px 0;border-left:1px solid #e2e4e9;">
      <p style="margin:0;font-family:Georgia,'Times New Roman',serif;font-size:28px;font-weight:400;color:#1a2332;line-height:1;">{summary['new_tasks']}</p>
      <p style="margin:6px 0 0 0;font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:#8a9099;">Neu</p>
    </td>
    <td align="center" width="20%" style="padding:12px 0;border-left:1px solid #e2e4e9;">
      <p style="margin:0;font-family:Georgia,'Times New Roman',serif;font-size:28px;font-weight:400;color:#1a2332;line-height:1;">{summary['completed_tasks']}</p>
      <p style="margin:6px 0 0 0;font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:#8a9099;">Erledigt</p>
    </td>
    <td align="center" width="20%" style="padding:12px 0;border-left:1px solid #e2e4e9;">
      <p style="margin:0;font-family:Georgia,'Times New Roman',serif;font-size:28px;font-weight:400;color:#1a2332;line-height:1;">{summary['current_task_count']}</p>
      <p style="margin:6px 0 0 0;font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:10px;letter-spacing:1.5px;text-transform:uppercase;color:#8a9099;">Total</p>
    </td>
  </tr>
  </table>
</td></tr>

<!-- Divider -->
<tr><td style="padding:0 40px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="height:1px;background-color:#e2e4e9;font-size:0;line-height:0;">&nbsp;</td></tr></table></td></tr>
"""

        if summary['total_changes'] == 0:
            html += """
<!-- No changes -->
<tr><td style="padding:48px 40px;text-align:center;">
  <p style="margin:0;font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:14px;color:#8a9099;">Keine Bewegungen in diesem Zeitraum.</p>
</td></tr>
"""
        else:
            # --- Helper to render a section ---
            def render_section(title, items, render_item_fn):
                """Render a report section with title and items."""
                s = f"""
<!-- Section: {title} -->
<tr><td style="padding:24px 40px 8px 40px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td><p style="margin:0;font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#8a9099;">{title}</p></td>
    <td align="right"><p style="margin:0;font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:11px;color:#8a9099;">{len(items)}</p></td>
  </tr>
  </table>
</td></tr>
<tr><td style="padding:0 40px 4px 40px;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td style="height:1px;background-color:#e2e4e9;font-size:0;line-height:0;">&nbsp;</td></tr></table></td></tr>
"""
                for item in items:
                    s += render_item_fn(item)
                return s

            # Bucket changes
            bucket_changes = [c for c in changes if c.change_type == "bucket_changed"]
            if bucket_changes:
                def render_bucket(c):
                    return f"""<tr><td style="padding:10px 40px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:14px;color:#1a2332;line-height:1.5;">
      {c.task_title}<span style="display:inline-block;margin-left:8px;padding:1px 8px;background-color:#f0f1f3;font-size:11px;color:#5a6270;">{c.assignees}</span>
    </td>
  </tr>
  <tr>
    <td style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:13px;color:#5a6270;padding-top:2px;">
      {c.old_value} <span style="color:#1a2332;font-family:Georgia,'Times New Roman',serif;">&rarr;</span> {c.new_value}
    </td>
  </tr>
  </table>
</td></tr>
"""
                html += render_section("Pipeline-Bewegungen", bucket_changes, render_bucket)

            # New tasks
            new_tasks = [c for c in changes if c.change_type == "new"]
            if new_tasks:
                def render_new(c):
                    return f"""<tr><td style="padding:10px 40px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:14px;color:#1a2332;line-height:1.5;">
      {c.task_title}<span style="display:inline-block;margin-left:8px;padding:1px 8px;background-color:#f0f1f3;font-size:11px;color:#5a6270;">{c.assignees}</span>
    </td>
  </tr>
  <tr>
    <td style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:13px;color:#5a6270;padding-top:2px;">
      Bucket: {c.new_value}
    </td>
  </tr>
  </table>
</td></tr>
"""
                html += render_section("Neue Leads", new_tasks, render_new)

            # Completed tasks
            completed = [c for c in changes if c.change_type == "completed"]
            if completed:
                def render_completed(c):
                    return f"""<tr><td style="padding:10px 40px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:14px;color:#1a2332;line-height:1.5;">
      {c.task_title}<span style="display:inline-block;margin-left:8px;padding:1px 8px;background-color:#f0f1f3;font-size:11px;color:#5a6270;">{c.assignees}</span>
    </td>
  </tr>
  </table>
</td></tr>
"""
                html += render_section("Abgeschlossen", completed, render_completed)

            # Assignee changes
            assignee_changes = [c for c in changes if c.change_type == "assignee_changed"]
            if assignee_changes:
                def render_assignee(c):
                    return f"""<tr><td style="padding:10px 40px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:14px;color:#1a2332;line-height:1.5;">
      {c.task_title}
    </td>
  </tr>
  <tr>
    <td style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:13px;color:#5a6270;padding-top:2px;">
      {c.old_value} <span style="color:#1a2332;font-family:Georgia,'Times New Roman',serif;">&rarr;</span> {c.new_value}
    </td>
  </tr>
  </table>
</td></tr>
"""
                html += render_section("Owner-Wechsel", assignee_changes, render_assignee)

            # Description changes
            desc_changes = [c for c in changes if c.change_type == "description_changed"]
            if desc_changes:
                def render_desc(c):
                    return f"""<tr><td style="padding:10px 40px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:14px;color:#1a2332;line-height:1.5;">
      {c.task_title}<span style="display:inline-block;margin-left:8px;padding:1px 8px;background-color:#f0f1f3;font-size:11px;color:#5a6270;">{c.assignees}</span>
    </td>
  </tr>
  <tr>
    <td style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:13px;color:#5a6270;padding-top:2px;">
      Notizen aktualisiert
    </td>
  </tr>
  </table>
</td></tr>
"""
                html += render_section("Notizen bearbeitet", desc_changes, render_desc)

            # Progress changes
            progress_changes = [c for c in changes if c.change_type == "progress_changed"]
            if progress_changes:
                def render_progress(c):
                    return f"""<tr><td style="padding:10px 40px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:14px;color:#1a2332;line-height:1.5;">
      {c.task_title}<span style="display:inline-block;margin-left:8px;padding:1px 8px;background-color:#f0f1f3;font-size:11px;color:#5a6270;">{c.assignees}</span>
    </td>
  </tr>
  <tr>
    <td style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:13px;color:#5a6270;padding-top:2px;">
      {c.old_value} <span style="color:#1a2332;font-family:Georgia,'Times New Roman',serif;">&rarr;</span> {c.new_value}
    </td>
  </tr>
  </table>
</td></tr>
"""
                html += render_section("Fortschritt", progress_changes, render_progress)

            # Deleted tasks
            deleted = [c for c in changes if c.change_type == "deleted"]
            if deleted:
                def render_deleted(c):
                    return f"""<tr><td style="padding:10px 40px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
  <tr>
    <td style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:14px;color:#1a2332;line-height:1.5;">
      {c.task_title}
    </td>
  </tr>
  <tr>
    <td style="font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:13px;color:#5a6270;padding-top:2px;">
      Zuletzt in: {c.old_value}
    </td>
  </tr>
  </table>
</td></tr>
"""
                html += render_section("Entfernt", deleted, render_deleted)

        html += f"""
<!-- Footer -->
<tr><td style="padding:32px 40px;border-top:1px solid #e2e4e9;">
  <p style="margin:0;font-family:'Segoe UI',Helvetica,Arial,sans-serif;font-size:11px;color:#adb1b8;text-align:center;line-height:1.6;">
    Automatisch generiert &middot; Planner Delta Tracker<br>
    Alpine Leadership &middot; {datetime.now().strftime('%d.%m.%Y')}
  </p>
</td></tr>

</table>
<!-- End main card -->

</td></tr>
</table>
<!-- End outer wrapper -->

</body>
</html>"""
        return html


class EmailSender:
    """Sends emails via Microsoft Graph API."""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def send_email(self,
                   subject: str,
                   body_html: str,
                   recipients: List[str] = None,
                   sender: str = None) -> bool:
        """
        Send an email via Microsoft Graph API.

        Args:
            subject: Email subject
            body_html: HTML body content
            recipients: List of email addresses (defaults to config)
            sender: Sender email (defaults to config)

        Returns:
            True if successful, False otherwise
        """
        recipients = recipients or REPORT_RECIPIENTS
        sender = sender or REPORT_SENDER

        # Build recipient list
        to_recipients = [
            {"emailAddress": {"address": email}}
            for email in recipients
        ]

        # Build message
        message = {
            "message": {
                "subject": subject,
                "body": {
                    "contentType": "HTML",
                    "content": body_html
                },
                "toRecipients": to_recipients
            },
            "saveToSentItems": True
        }

        # Send via Graph API (using application permissions, send as specific user)
        url = f"{GRAPH_BASE_URL}/users/{sender}/sendMail"
        response = requests.post(url, headers=self.headers, json=message)

        if response.status_code == 202:
            print(f"[OK] Email sent successfully to {', '.join(recipients)}")
            return True
        else:
            print(f"[FEHLER] Failed to send email: {response.status_code}")
            print(f"  Response: {response.text}")
            return False


def send_delta_report(changes: List[TaskChange], summary: Dict, access_token: str) -> bool:
    """
    Generate and send a delta report via email.

    Args:
        changes: List of detected changes
        summary: Summary statistics
        access_token: Microsoft Graph access token

    Returns:
        True if email sent successfully
    """
    # Generate report
    html_report = ReportGenerator.generate_html_report(changes, summary)

    # Create subject line
    if summary['total_changes'] == 0:
        subject = "Sales-Pipeline: Keine Bewegungen"
    else:
        subject = f"Sales-Pipeline: {summary['total_changes']} Aenderung(en)"

    # Send email
    sender = EmailSender(access_token)
    return sender.send_email(subject, html_report)


def save_report_locally(changes: List[TaskChange], summary: Dict, filename: str = None) -> str:
    """
    Save report as local HTML file (for testing/preview).

    Returns:
        Path to saved file
    """
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"report_{timestamp}.html"

    html_report = ReportGenerator.generate_html_report(changes, summary)

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_report)

    print(f"[OK] Report saved to: {filename}")
    return filename
