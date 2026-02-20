"""Odoo Community MCP Server — Zoya Gold Tier.

Exposes Odoo ERP operations as MCP tools so Claude Code can interact with
an Odoo Community Edition instance on behalf of the user.

SAFETY: Any write operations (create invoice, create task) that affect
external systems first create an approval file in Pending_Approval/. The
action is only executed after the human moves the file to Approved/.

Odoo Community XML-RPC API:
  - Auth:    {url}/xmlrpc/2/common
  - Models:  {url}/xmlrpc/2/object

Configuration (env vars or .env):
  ODOO_URL      = http://localhost:8069
  ODOO_DB       = mydb
  ODOO_USERNAME = admin
  ODOO_PASSWORD = admin

Usage (add to .claude/mcp.json):
  {
    "mcpServers": {
      "zoya-odoo": {
        "command": "uv",
        "args": ["run", "zoya-odoo-mcp"]
      }
    }
  }
"""

from __future__ import annotations

import xmlrpc.client
from datetime import datetime, timezone
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Config — read from environment (loaded via python-dotenv in config.py)
# ---------------------------------------------------------------------------

from src.config import (
    ODOO_URL,
    ODOO_DB,
    ODOO_USERNAME,
    ODOO_PASSWORD,
    PENDING_APPROVAL,
    VAULT_PATH,
)

mcp = FastMCP("zoya-odoo")

# ---------------------------------------------------------------------------
# Odoo connection helpers
# ---------------------------------------------------------------------------


def _authenticate() -> tuple[int, xmlrpc.client.ServerProxy]:
    """Authenticate with Odoo and return (uid, models_proxy).

    Raises RuntimeError if authentication fails.
    """
    if not ODOO_URL or not ODOO_DB:
        raise RuntimeError(
            "Odoo not configured. Set ODOO_URL, ODOO_DB, ODOO_USERNAME, "
            "ODOO_PASSWORD in your .env file."
        )

    common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
    uid: int = common.authenticate(ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD, {})

    if not uid:
        raise RuntimeError(
            f"Odoo authentication failed for user '{ODOO_USERNAME}' on db '{ODOO_DB}'. "
            "Check credentials in .env."
        )

    models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")
    return uid, models


def _execute(model: str, method: str, args: list, kwargs: dict | None = None) -> object:
    """Execute an Odoo XML-RPC call with the configured credentials."""
    uid, models = _authenticate()
    return models.execute_kw(
        ODOO_DB, uid, ODOO_PASSWORD,
        model, method, args, kwargs or {},
    )


def _format_record_list(records: list[dict], fields: list[str]) -> str:
    """Format a list of Odoo records as a markdown table."""
    if not records:
        return "(no records found)"
    header = " | ".join(fields)
    separator = " | ".join("---" for _ in fields)
    rows = []
    for r in records:
        row = " | ".join(str(r.get(f, "")) for f in fields)
        rows.append(row)
    return f"| {header} |\n| {separator} |\n" + "\n".join(f"| {row} |" for row in rows)


def _create_approval_file(action: str, details: dict, description: str) -> str:
    """Create a Pending_Approval file for a proposed Odoo action.

    Returns the filename created.
    """
    PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S")
    safe_action = action.replace(" ", "_")[:40]
    filename = f"ODOO_{ts}_{safe_action}.md"
    path = PENDING_APPROVAL / filename

    details_md = "\n".join(f"- **{k}:** {v}" for k, v in details.items())

    path.write_text(
        f"---\n"
        f"type: odoo_action\n"
        f"action: {action}\n"
        f"status: pending_approval\n"
        f"created_at: {now.isoformat()}\n"
        f"source: mcp_odoo_server\n"
        f"approval_required: true\n"
        f"---\n\n"
        f"# Odoo Action: {action}\n\n"
        f"**Proposed at:** {now.strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        f"## Details\n\n"
        f"{details_md}\n\n"
        f"## Description\n\n"
        f"{description}\n\n"
        f"---\n"
        f"## To Approve\n"
        f"Move this file to `/Approved/` in Obsidian. "
        f"The action will be executed on the next orchestrator cycle.\n\n"
        f"## To Reject\n"
        f"Move this file to `/Rejected/` in Obsidian.\n",
        encoding="utf-8",
    )
    return filename


# ---------------------------------------------------------------------------
# MCP Tools — Read operations (safe, no approval needed)
# ---------------------------------------------------------------------------


@mcp.tool()
def odoo_test_connection() -> str:
    """Test the Odoo connection and return server info.

    Returns:
        Server version info and authentication status.
    """
    try:
        common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
        version_info = common.version()
        uid, _ = _authenticate()
        return (
            f"Odoo connection successful.\n"
            f"- Server: {ODOO_URL}\n"
            f"- Database: {ODOO_DB}\n"
            f"- Odoo version: {version_info.get('server_version', 'unknown')}\n"
            f"- User UID: {uid}\n"
            f"- User: {ODOO_USERNAME}"
        )
    except Exception as e:
        return f"Odoo connection failed: {e}"


@mcp.tool()
def odoo_list_customers(limit: int = 20, search: str = "") -> str:
    """List customers/partners from Odoo.

    Args:
        limit: Maximum number of records to return (default: 20).
        search: Optional name filter (searches 'name' field).

    Returns:
        Markdown table of customers with id, name, email, phone.
    """
    try:
        domain: list = [["is_company", "=", True]]
        if search:
            domain.append(["name", "ilike", search])

        ids = _execute("res.partner", "search", [domain], {"limit": limit})
        if not ids:
            return "No customers found."

        records = _execute(
            "res.partner", "read",
            [ids],
            {"fields": ["id", "name", "email", "phone", "street", "city"]},
        )
        return _format_record_list(records, ["id", "name", "email", "phone", "city"])
    except Exception as e:
        return f"Error listing customers: {e}"


@mcp.tool()
def odoo_list_invoices(state: str = "posted", limit: int = 20) -> str:
    """List invoices from Odoo.

    Args:
        state: Invoice state filter — 'draft', 'posted' (confirmed), 'cancel', or 'all'.
        limit: Maximum number of records to return (default: 20).

    Returns:
        Markdown table of invoices with id, name, partner, amount, state, date.
    """
    try:
        domain: list = [["move_type", "=", "out_invoice"]]
        if state != "all":
            domain.append(["state", "=", state])

        ids = _execute("account.move", "search", [domain], {"limit": limit, "order": "invoice_date desc"})
        if not ids:
            return f"No invoices found with state='{state}'."

        records = _execute(
            "account.move", "read",
            [ids],
            {"fields": ["id", "name", "partner_id", "amount_total", "state", "invoice_date", "payment_state"]},
        )

        # Flatten partner_id (it's [id, name] in Odoo)
        for r in records:
            if isinstance(r.get("partner_id"), list):
                r["partner_id"] = r["partner_id"][1]

        return _format_record_list(
            records,
            ["id", "name", "partner_id", "amount_total", "state", "payment_state", "invoice_date"],
        )
    except Exception as e:
        return f"Error listing invoices: {e}"


@mcp.tool()
def odoo_list_projects(limit: int = 20) -> str:
    """List active projects from Odoo.

    Args:
        limit: Maximum number of records to return (default: 20).

    Returns:
        Markdown table of projects with id, name, partner, task count.
    """
    try:
        domain: list = [["active", "=", True]]
        ids = _execute("project.project", "search", [domain], {"limit": limit})
        if not ids:
            return "No active projects found."

        records = _execute(
            "project.project", "read",
            [ids],
            {"fields": ["id", "name", "partner_id", "task_count", "date_start", "date"]},
        )
        for r in records:
            if isinstance(r.get("partner_id"), list):
                r["partner_id"] = r["partner_id"][1]

        return _format_record_list(records, ["id", "name", "partner_id", "task_count"])
    except Exception as e:
        return f"Error listing projects: {e}"


@mcp.tool()
def odoo_get_record(model: str, record_id: int, fields: str = "") -> str:
    """Read a specific Odoo record by model and ID.

    Args:
        model: Odoo model name (e.g., 'res.partner', 'account.move', 'project.task').
        record_id: The record ID.
        fields: Comma-separated list of fields to read. Leave empty for all fields.

    Returns:
        Formatted record details.
    """
    try:
        field_list = [f.strip() for f in fields.split(",") if f.strip()] if fields else []
        kwargs = {"fields": field_list} if field_list else {}
        records = _execute(model, "read", [[record_id]], kwargs)
        if not records:
            return f"Record {model}#{record_id} not found."
        record = records[0]
        lines = [f"## {model} #{record_id}\n"]
        for k, v in record.items():
            lines.append(f"- **{k}:** {v}")
        return "\n".join(lines)
    except Exception as e:
        return f"Error reading {model}#{record_id}: {e}"


@mcp.tool()
def odoo_list_tasks(project_id: int = 0, limit: int = 20) -> str:
    """List tasks from Odoo, optionally filtered by project.

    Args:
        project_id: Filter by project ID. Use 0 for all projects.
        limit: Maximum number of records to return (default: 20).

    Returns:
        Markdown table of tasks.
    """
    try:
        domain: list = []
        if project_id:
            domain.append(["project_id", "=", project_id])

        ids = _execute("project.task", "search", [domain], {"limit": limit, "order": "date_deadline asc"})
        if not ids:
            return "No tasks found."

        records = _execute(
            "project.task", "read",
            [ids],
            {"fields": ["id", "name", "project_id", "stage_id", "date_deadline", "user_ids"]},
        )
        for r in records:
            if isinstance(r.get("project_id"), list):
                r["project_id"] = r["project_id"][1]
            if isinstance(r.get("stage_id"), list):
                r["stage_id"] = r["stage_id"][1]
            if isinstance(r.get("user_ids"), list):
                r["user_ids"] = ", ".join(str(u) for u in r["user_ids"])

        return _format_record_list(records, ["id", "name", "project_id", "stage_id", "date_deadline"])
    except Exception as e:
        return f"Error listing tasks: {e}"


# ---------------------------------------------------------------------------
# MCP Tools — Write operations (routed through HITL approval)
# ---------------------------------------------------------------------------


@mcp.tool()
def odoo_create_invoice(
    customer_id: int,
    description: str,
    amount: float,
    currency: str = "USD",
    due_date: str = "",
) -> str:
    """Propose creating a customer invoice in Odoo (requires human approval).

    Does NOT create immediately. Routes through Pending_Approval/ first.

    Args:
        customer_id: Odoo partner ID of the customer.
        description: Invoice line description.
        amount: Invoice amount (excluding tax).
        currency: Currency code (e.g., 'USD', 'EUR', 'GBP'). Default: USD.
        due_date: Due date in YYYY-MM-DD format. Leave empty for default terms.

    Returns:
        Status message with the approval file name.
    """
    details = {
        "Customer ID": customer_id,
        "Description": description,
        "Amount": f"{currency} {amount:.2f}",
        "Due Date": due_date or "(payment terms)",
        "Model": "account.move (out_invoice)",
    }
    desc = (
        f"Create a customer invoice for partner #{customer_id} for "
        f"{currency} {amount:.2f}: '{description}'."
    )
    filename = _create_approval_file("create_invoice", details, desc)
    return (
        f"Invoice proposal created and routed for approval.\n"
        f"Approval file: `{filename}`\n"
        f"Review in Obsidian → Pending_Approval/ and move to Approved/ to confirm."
    )


@mcp.tool()
def odoo_create_task(
    project_id: int,
    task_name: str,
    description: str = "",
    deadline: str = "",
    assigned_to_uid: int = 0,
) -> str:
    """Propose creating a project task in Odoo (requires human approval).

    Does NOT create immediately. Routes through Pending_Approval/ first.

    Args:
        project_id: Odoo project ID.
        task_name: Name of the task.
        description: Optional detailed description.
        deadline: Deadline in YYYY-MM-DD format. Leave empty for no deadline.
        assigned_to_uid: Odoo user ID to assign to. Use 0 for unassigned.

    Returns:
        Status message with the approval file name.
    """
    details = {
        "Project ID": project_id,
        "Task Name": task_name,
        "Description": description or "(none)",
        "Deadline": deadline or "(none)",
        "Assigned To UID": assigned_to_uid or "(unassigned)",
        "Model": "project.task",
    }
    desc = (
        f"Create task '{task_name}' in project #{project_id}"
        + (f" due {deadline}" if deadline else "")
        + "."
    )
    filename = _create_approval_file("create_task", details, desc)
    return (
        f"Task proposal created and routed for approval.\n"
        f"Approval file: `{filename}`\n"
        f"Review in Obsidian → Pending_Approval/ and move to Approved/ to confirm."
    )


@mcp.tool()
def odoo_send_invoice(invoice_id: int) -> str:
    """Propose sending a confirmed invoice to the customer via email (requires approval).

    Args:
        invoice_id: Odoo invoice (account.move) ID to send.

    Returns:
        Status message with the approval file name.
    """
    details = {
        "Invoice ID": invoice_id,
        "Action": "Send invoice by email (action_invoice_sent)",
        "Model": "account.move",
    }
    desc = f"Send invoice #{invoice_id} to the customer via Odoo email."
    filename = _create_approval_file("send_invoice", details, desc)
    return (
        f"Send-invoice proposal created and routed for approval.\n"
        f"Approval file: `{filename}`\n"
        f"Review in Obsidian → Pending_Approval/ and move to Approved/ to confirm."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Run the Odoo MCP server via stdio transport."""
    mcp.run()


if __name__ == "__main__":
    main()
