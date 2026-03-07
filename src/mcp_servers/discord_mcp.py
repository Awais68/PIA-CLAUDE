"""Discord MCP Server - Orchestrator integration for Discord interactions."""

import logging
from pathlib import Path

from mcp.server.models import InitializationOptions
from mcp.server import Server
import mcp.types as types

from src.config import VAULT_PATH, INBOX
from src.utils import log_action

logger = logging.getLogger(__name__)

server = Server("discord-mcp")


class DiscordMCPServer:
    """MCP server for Discord bot integration."""

    def __init__(self):
        """Initialize Discord MCP server."""
        self.vault_path = VAULT_PATH
        self.inbox = INBOX

    def get_pending_requests(self) -> list[dict]:
        """Get pending requests from Inbox/ created by Discord bot."""
        requests = []

        if not self.inbox.exists():
            return requests

        # Find EXPENSE_, TASK_, EMAIL_DRAFT_, RESEARCH_REQUEST_ files
        for request_file in self.inbox.glob("*.md"):
            if any(prefix in request_file.name for prefix in ["EXPENSE_", "TASK_", "EMAIL_DRAFT_", "RESEARCH_REQUEST_"]):
                try:
                    content = request_file.read_text()
                    requests.append({
                        "file": request_file.name,
                        "path": str(request_file),
                        "type": self._detect_request_type(request_file.name),
                        "preview": content[:200]
                    })
                except Exception as e:
                    logger.warning(f"Failed to read {request_file.name}: {e}")

        return requests

    def _detect_request_type(self, filename: str) -> str:
        """Detect request type from filename."""
        if "EXPENSE_" in filename:
            return "expense"
        elif "TASK_" in filename:
            return "task"
        elif "EMAIL_DRAFT_" in filename:
            return "email_draft"
        elif "RESEARCH_REQUEST_" in filename:
            return "research"
        return "unknown"

    def process_discord_request(self, file_path: str, action: str = "approve") -> dict:
        """Process a Discord request.

        Args:
            file_path: Path to the request file
            action: approve, reject, or process

        Returns:
            Result dict
        """
        path = Path(file_path)
        if not path.exists():
            return {"status": "error", "message": "File not found"}

        try:
            content = path.read_text()
            request_type = self._detect_request_type(path.name)

            if action == "approve":
                # Move to Pending_Approval if needed
                from src.config import PENDING_APPROVAL
                PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
                dest = PENDING_APPROVAL / path.name
                path.rename(dest)
                status = "approved"

            elif action == "reject":
                # Move to Rejected
                from src.config import REJECTED
                REJECTED.mkdir(parents=True, exist_ok=True)
                dest = REJECTED / path.name
                path.rename(dest)
                status = "rejected"

            else:
                status = "processed"

            log_action("discord_mcp", f"{status}: {path.name}", result="success")

            return {
                "status": "success",
                "action": action,
                "file": path.name,
                "type": request_type
            }

        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            return {"status": "error", "message": str(e)}


# Initialize MCP server
discord_mcp = DiscordMCPServer()


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="get_discord_requests",
            description="Get pending Discord requests (expenses, tasks, emails, research)",
            inputSchema={
                "type": "object",
                "properties": {
                    "request_type": {
                        "type": "string",
                        "description": "Filter by type: expense, task, email_draft, research, or all",
                        "enum": ["expense", "task", "email_draft", "research", "all"]
                    }
                }
            }
        ),
        types.Tool(
            name="process_discord_request",
            description="Process a Discord request (approve, reject, process)",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the request file"
                    },
                    "action": {
                        "type": "string",
                        "description": "Action to take",
                        "enum": ["approve", "reject", "process"]
                    }
                },
                "required": ["file_path", "action"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> str:
    """Execute a tool."""
    if name == "get_discord_requests":
        request_type = arguments.get("request_type", "all")
        requests = discord_mcp.get_pending_requests()

        if request_type != "all":
            requests = [r for r in requests if r["type"] == request_type]

        return f"Found {len(requests)} requests:\n" + "\n".join([
            f"- {r['file']} ({r['type']})" for r in requests
        ])

    elif name == "process_discord_request":
        file_path = arguments.get("file_path")
        action = arguments.get("action", "process")

        result = discord_mcp.process_discord_request(file_path, action)
        return str(result)

    else:
        return f"Unknown tool: {name}"


async def main():
    """Run the server."""
    async with server:
        logger.info("Discord MCP server started")
        await server.wait_for_shutdown()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
