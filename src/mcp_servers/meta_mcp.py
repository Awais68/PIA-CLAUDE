"""Meta Social MCP Server — Facebook and Instagram integration for Zoya.

Provides Claude Code with tools to post content and read analytics for
Facebook Pages and Instagram Business accounts via Meta Graph API.

Tools:
    - post_to_facebook: Queue a Facebook Page post (HITL approval)
    - post_to_instagram: Queue an Instagram post (HITL approval)
    - get_page_insights: Get Facebook Page analytics
    - get_instagram_insights: Get Instagram account insights
    - list_recent_posts: List recent posts with engagement metrics

SAFETY: All posts go through HITL approval — nothing publishes directly.

Setup:
    1. Create a Meta Business App at developers.facebook.com
    2. Get Page Access Token and Instagram Business Account ID
    3. Set in .env:
       META_ACCESS_TOKEN=your-long-lived-page-access-token
       META_PAGE_ID=your-facebook-page-id
       META_INSTAGRAM_ID=your-instagram-business-account-id

Dependencies:
    uv add mcp requests

TODO: Implement full Meta Graph API integration.
      See: https://developers.facebook.com/docs/graph-api
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

try:
    from mcp.server.fastmcp import FastMCP
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False
    print("[meta_mcp] WARNING: mcp package not installed. Run: uv add mcp")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
VAULT_PATH = PROJECT_ROOT / "AI_Employee_Vault"
PENDING_APPROVAL = VAULT_PATH / "Pending_Approval"

META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
META_PAGE_ID = os.getenv("META_PAGE_ID", "")
META_INSTAGRAM_ID = os.getenv("META_INSTAGRAM_ID", "")
GRAPH_API_VERSION = "v19.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def _graph_get(endpoint: str, params: dict | None = None):
    """Make a GET request to Meta Graph API.

    TODO: Implement with requests library.
    """
    # import requests
    # params = params or {}
    # params["access_token"] = META_ACCESS_TOKEN
    # resp = requests.get(f"{GRAPH_BASE}/{endpoint}", params=params, timeout=10)
    # resp.raise_for_status()
    # return resp.json()
    raise NotImplementedError("TODO: Implement Graph API GET")


if _MCP_AVAILABLE:
    mcp = FastMCP("meta_social")

    @mcp.tool()
    def post_to_facebook(message: str, link: str = "", image_url: str = "") -> str:
        """Queue a Facebook Page post for HITL approval.

        Args:
            message: Post text (supports emojis and hashtags)
            link: URL to share (optional)
            image_url: Public image URL to attach (optional)

        Returns:
            Path to the approval file in /Pending_Approval/.
        """
        PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d_%H%M%S")
        approval_file = PENDING_APPROVAL / f"META_FB_{ts}.md"

        content = (
            f"---\n"
            f"type: facebook_post\n"
            f"platform: facebook\n"
            f"created_at: {now.isoformat()}\n"
            f"approval_required: true\n"
            f"status: pending_approval\n"
            f"page_id: {META_PAGE_ID or 'NOT_SET'}\n"
            f"---\n\n"
            f"## Facebook Post Draft\n\n"
            f"{message}\n\n"
        )
        if link:
            content += f"**Link:** {link}\n"
        if image_url:
            content += f"**Image:** {image_url}\n"
        content += (
            f"\n## Actions\n"
            f"- Move to /Approved/ to publish to Facebook Page\n"
            f"- Move to /Rejected/ to discard\n\n"
            f"## TODO After Approval\n"
            f"POST to: {GRAPH_BASE}/{META_PAGE_ID}/feed\n"
            f"Body: {{message: ..., link: ..., access_token: META_ACCESS_TOKEN}}\n"
        )
        approval_file.write_text(content, encoding="utf-8")
        return json.dumps({"approval_file": str(approval_file), "status": "pending_approval"})

    @mcp.tool()
    def post_to_instagram(caption: str, image_url: str) -> str:
        """Queue an Instagram post for HITL approval.

        Args:
            caption: Post caption (up to 2200 chars, hashtags supported)
            image_url: Publicly accessible image URL (JPEG/PNG)

        Returns:
            Path to the approval file in /Pending_Approval/.

        TODO: Implement two-step Instagram Graph API media creation + publish.
        """
        PENDING_APPROVAL.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        ts = now.strftime("%Y%m%d_%H%M%S")
        approval_file = PENDING_APPROVAL / f"META_IG_{ts}.md"

        content = (
            f"---\n"
            f"type: instagram_post\n"
            f"platform: instagram\n"
            f"created_at: {now.isoformat()}\n"
            f"approval_required: true\n"
            f"status: pending_approval\n"
            f"instagram_id: {META_INSTAGRAM_ID or 'NOT_SET'}\n"
            f"---\n\n"
            f"## Instagram Post Draft\n\n"
            f"**Image:** {image_url}\n\n"
            f"**Caption:**\n{caption}\n\n"
            f"## Actions\n"
            f"- Move to /Approved/ to publish\n"
            f"- Move to /Rejected/ to discard\n\n"
            f"## TODO After Approval\n"
            f"Step 1: POST {GRAPH_BASE}/{META_INSTAGRAM_ID}/media (create container)\n"
            f"Step 2: POST {GRAPH_BASE}/{META_INSTAGRAM_ID}/media_publish (publish)\n"
        )
        approval_file.write_text(content, encoding="utf-8")
        return json.dumps({"approval_file": str(approval_file), "status": "pending_approval"})

    @mcp.tool()
    def get_page_insights(metric: str = "page_impressions,page_engaged_users", period: str = "week") -> str:
        """Get Facebook Page insights/analytics.

        Args:
            metric: Comma-separated insight metric names
            period: "day" | "week" | "month" | "lifetime"

        Returns:
            JSON with metric values.

        TODO: Implement using Graph API /{page_id}/insights endpoint.
        """
        return json.dumps({
            "stub": True,
            "message": f"TODO: GET {GRAPH_BASE}/{META_PAGE_ID}/insights?metric={metric}&period={period}",
            "data": [],
        })

    @mcp.tool()
    def get_instagram_insights(metric: str = "impressions,reach,profile_views", period: str = "week") -> str:
        """Get Instagram Business account insights.

        Args:
            metric: Comma-separated insight metric names
            period: "day" | "week" | "month"

        TODO: Implement using Graph API /{ig_user_id}/insights.
        """
        return json.dumps({
            "stub": True,
            "message": f"TODO: GET {GRAPH_BASE}/{META_INSTAGRAM_ID}/insights",
            "data": [],
        })

    @mcp.tool()
    def list_recent_posts(platform: str = "facebook", limit: int = 10) -> str:
        """List recent posts with engagement metrics.

        Args:
            platform: "facebook" or "instagram"
            limit: Number of posts to return (default 10)

        TODO: Implement using Graph API feed endpoint with engagement fields.
        """
        return json.dumps({
            "stub": True,
            "message": f"TODO: Fetch last {limit} {platform} posts",
            "posts": [],
        })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not _MCP_AVAILABLE:
        print("ERROR: mcp package required. Run: uv add mcp")
        raise SystemExit(1)
    if not META_ACCESS_TOKEN:
        print("WARNING: META_ACCESS_TOKEN not set — running in stub mode")
    print("Starting Meta Social MCP server...")
    mcp.run()
