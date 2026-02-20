# Odoo MCP Server Skill

## Purpose
Expose Odoo Community Edition as MCP tools so Claude Code can query and
interact with the ERP on behalf of the user. All write operations require
human approval via the standard HITL workflow.

## When This Skill Is Used
- When asked to look up customers, invoices, projects, or tasks in Odoo
- When asked to draft a new invoice or create a project task
- When bank transactions need to be cross-referenced with Odoo customers

## Setup

### 1. Configure Odoo credentials in `.env`
```
ODOO_URL=http://localhost:8069
ODOO_DB=mycompany
ODOO_USERNAME=admin
ODOO_PASSWORD=admin
```

### 2. Add to `.claude/mcp.json`
```json
{
  "mcpServers": {
    "zoya-odoo": {
      "command": "uv",
      "args": ["run", "zoya-odoo-mcp"]
    }
  }
}
```

### 3. Test connection
```
claude mcp list
claude "Test the Odoo connection"
```

## Available Tools

### Read Tools (safe — no approval needed)

| Tool | Description |
|------|-------------|
| `odoo_test_connection` | Test connection + return server version |
| `odoo_list_customers` | List partners/customers (filterable by name) |
| `odoo_list_invoices` | List invoices by state (draft/posted/cancel) |
| `odoo_list_projects` | List active projects |
| `odoo_list_tasks` | List tasks, optionally filtered by project |
| `odoo_get_record` | Read any record by model + ID |

### Write Tools (HITL — routed to Pending_Approval/)

| Tool | Description |
|------|-------------|
| `odoo_create_invoice` | Propose creating a customer invoice |
| `odoo_create_task` | Propose creating a project task |
| `odoo_send_invoice` | Propose sending an invoice by email |

## HITL Safety

All write tools follow the same safety pattern as the email MCP server:

1. **Propose** — Tool creates `ODOO_<timestamp>_<action>.md` in `Pending_Approval/`
2. **Review** — User opens the file in Obsidian and reads the proposed action
3. **Approve** — Move file to `Approved/` → orchestrator executes the action
4. **Reject** — Move file to `Rejected/` → action is abandoned

The actual Odoo API call is **never made** until human approval.

## Supported Odoo Models

| Model | Used For |
|-------|----------|
| `res.partner` | Customers, suppliers, contacts |
| `account.move` | Invoices, bills, credit notes |
| `project.project` | Projects |
| `project.task` | Tasks |

## Example Usage

```
"Show me all unpaid invoices"
→ calls odoo_list_invoices(state="posted")

"Create an invoice for Acme Corp for $1,500 consulting"
→ calls odoo_create_invoice(customer_id=42, description="Consulting", amount=1500)
→ routes to Pending_Approval/ — you must approve in Obsidian

"What tasks are due this week in the Marketing project?"
→ calls odoo_list_tasks(project_id=5)
```

## Technical Notes
- Uses Python stdlib `xmlrpc.client` — no extra dependencies
- XML-RPC API available in all Odoo Community versions (8.0+)
- Server URL: `{ODOO_URL}/xmlrpc/2/object`
- Auth URL: `{ODOO_URL}/xmlrpc/2/common`
