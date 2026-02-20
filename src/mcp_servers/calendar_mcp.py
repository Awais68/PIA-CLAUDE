"""Calendar MCP Server — Google Calendar integration for Zoya.

Provides Claude Code with tools to read and create calendar events.

Tools:
    - list_events: List upcoming events in a date range
    - find_free_slots: Find available time slots for a meeting
    - create_event: Create a calendar event (HITL approval required)
    - get_today: Get today's schedule

SAFETY: create_event writes an approval file to /Pending_Approval/ and
        does NOT create the event directly until human approves.

Setup:
    1. Enable Google Calendar API in Google Cloud Console
    2. Use same credentials.json / token.json as Gmail (scopes include calendar)
    3. Add calendar scope to SCOPES list in gmail_watcher.py:
       "https://www.googleapis.com/auth/calendar"

Dependencies:
    uv add mcp google-auth google-api-python-client

TODO: Implement full Google Calendar API integration.
      Current implementation returns stub responses for testing.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Attempt FastMCP import — fail gracefully so the stub is importable
# ---------------------------------------------------------------------------
try:
    from mcp.server.fastmcp import FastMCP
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    print("[calendar_mcp] WARNING: mcp package not installed. Run: uv add mcp")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VAULT_PATH = PROJECT_ROOT / "AI_Employee_Vault"
PENDING_APPROVAL = VAULT_PATH / "Pending_Approval"

if _MCP_AVAILABLE:
    mcp = FastMCP("calendar")

    @mcp.tool()
    def list_events(start_date: str, end_date: str, calendar_id: str = "primary") -> str:
        """List Google Calendar events in a date range.

        Args:
            start_date: ISO date string, e.g. "2026-02-20"
            end_date: ISO date string, e.g. "2026-02-27"
            calendar_id: Calendar ID (default: "primary")

        Returns:
            JSON string with list of events.

        TODO: Replace stub with real Google Calendar API call.
              See: https://developers.google.com/calendar/api/v3/reference/events/list
        """
        # TODO: Implement Google Calendar API integration
        # credentials = _get_credentials()
        # service = build("calendar", "v3", credentials=credentials)
        # events = service.events().list(
        #     calendarId=calendar_id,
        #     timeMin=f"{start_date}T00:00:00Z",
        #     timeMax=f"{end_date}T23:59:59Z",
        #     singleEvents=True,
        #     orderBy="startTime",
        # ).execute()
        # return json.dumps(events.get("items", []))

        return json.dumps({
            "stub": True,
            "message": "TODO: Connect Google Calendar API",
            "start_date": start_date,
            "end_date": end_date,
            "events": [],
        })

    @mcp.tool()
    def find_free_slots(
        date: str,
        duration_minutes: int = 60,
        working_hours_start: int = 9,
        working_hours_end: int = 18,
    ) -> str:
        """Find free time slots on a given day.

        Args:
            date: ISO date string, e.g. "2026-02-20"
            duration_minutes: Meeting duration needed (default 60)
            working_hours_start: Start of working day (24h, default 9)
            working_hours_end: End of working day (24h, default 18)

        Returns:
            JSON string with list of available slots.

        TODO: Implement using Google Calendar freebusy API.
        """
        # TODO: Use Calendar API freebusy query
        # service.freebusy().query(body={...}).execute()

        return json.dumps({
            "stub": True,
            "message": "TODO: Implement freebusy query",
            "date": date,
            "duration_minutes": duration_minutes,
            "free_slots": [],
        })

    @mcp.tool()
    def create_event(
        title: str,
        start_datetime: str,
        end_datetime: str,
        description: str = "",
        attendees: str = "",
        location: str = "",
    ) -> str:
        """Request creation of a calendar event (requires HITL approval).

        Args:
            title: Event title
            start_datetime: ISO datetime, e.g. "2026-02-20T10:00:00Z"
            end_datetime: ISO datetime, e.g. "2026-02-20T11:00:00Z"
            description: Event description (optional)
            attendees: Comma-separated email addresses (optional)
            location: Meeting location or video link (optional)

        Returns:
            Path to the approval file created in /Pending_Approval/.
        """
        PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d_%H%M%S")
        approval_file = PENDING_APPROVAL / f"CALENDAR_EVENT_{ts}.md"

        content = (
            f"---\n"
            f"type: calendar_event_request\n"
            f"created_at: {now.isoformat()}\n"
            f"approval_required: true\n"
            f"status: pending_approval\n"
            f"---\n\n"
            f"## Calendar Event Request\n\n"
            f"**Title:** {title}\n"
            f"**Start:** {start_datetime}\n"
            f"**End:** {end_datetime}\n"
            f"**Location:** {location or 'TBD'}\n"
            f"**Attendees:** {attendees or 'None'}\n\n"
            f"## Description\n{description}\n\n"
            f"## Actions\n"
            f"- Move to /Approved/ to create this event\n"
            f"- Move to /Rejected/ to discard\n\n"
            f"## TODO\n"
            f"After approval, implement: Calendar API events.insert() call\n"
        )
        approval_file.write_text(content, encoding="utf-8")
        return json.dumps({"approval_file": str(approval_file), "status": "pending_approval"})

    @mcp.tool()
    def get_today() -> str:
        """Get today's calendar schedule.

        Returns:
            JSON string with today's events.

        TODO: Call list_events for today's date range.
        """
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return list_events(start_date=today, end_date=today)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not _MCP_AVAILABLE:
        print("ERROR: mcp package required. Run: uv add mcp")
        raise SystemExit(1)
    print("Starting Calendar MCP server...")
    mcp.run()
