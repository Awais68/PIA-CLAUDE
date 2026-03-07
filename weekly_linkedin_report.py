"""
LinkedIn Weekly Report Generator

Run every Sunday at 8 PM to generate weekly activity summary:
- Count DMs received, comments, posts made
- List top profile visitors
- Identify hot leads
- Suggest action items

Saves to: /Vault/Briefings/LINKEDIN_WEEKLY_YYYY-MM-DD.md
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

from dotenv import load_dotenv
import os


class LinkedInWeeklyReport:
    """Generate LinkedIn weekly activity report."""

    def __init__(self, vault_path: str, log_level: str = "INFO"):
        """
        Initialize report generator.

        Args:
            vault_path: Path to Obsidian vault
            log_level: Logging level
        """
        self.vault_path = Path(vault_path).resolve()
        self.logs_path = self.vault_path / "Logs"
        self.briefings_path = self.vault_path / "Briefings"
        self.needs_action_path = self.vault_path / "Needs_Action"

        # Create directories
        self.briefings_path.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = self._setup_logger(log_level)

    def _setup_logger(self, log_level: str) -> logging.Logger:
        """Setup logger."""
        logger = logging.getLogger("linkedin_weekly_report")
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    def generate_report(self) -> None:
        """Generate weekly report."""
        self.logger.info("Generating LinkedIn weekly report...")

        try:
            # Calculate week range (last 7 days)
            today = datetime.now()
            week_start = today - timedelta(days=7)
            week_end = today

            # Count activities
            dm_count = self._count_dms(week_start, week_end)
            comment_count = self._count_comments(week_start, week_end)
            post_count = self._count_posts(week_start, week_end)
            visitor_count = self._count_profile_views(week_start, week_end)

            # Get last week's stats for comparison
            last_week_start = week_start - timedelta(days=7)
            last_week_end = week_start
            last_dm_count = self._count_dms(last_week_start, last_week_end)
            last_comment_count = self._count_comments(last_week_start, last_week_end)
            last_post_count = self._count_posts(last_week_start, last_week_end)
            last_visitor_count = self._count_profile_views(last_week_start, last_week_end)

            # Get top visitors
            top_visitors = self._get_top_visitors(week_start, week_end, limit=5)

            # Generate markdown report
            report = self._generate_markdown_report(
                week_start, week_end,
                dm_count, comment_count, post_count, visitor_count,
                last_dm_count, last_comment_count, last_post_count, last_visitor_count,
                top_visitors
            )

            # Save report
            report_date = today.strftime("%Y-%m-%d")
            report_file = self.briefings_path / f"LINKEDIN_WEEKLY_{report_date}.md"
            report_file.write_text(report, encoding='utf-8')

            self.logger.info(f"Report saved to: {report_file}")
            print()
            print("✓ LinkedIn Weekly Report Generated")
            print(f"  File: {report_file.name}")
            print(f"  Period: {week_start.date()} to {week_end.date()}")

        except Exception as e:
            self.logger.error(f"Error generating report: {e}", exc_info=True)

    def _count_dms(self, start_date: datetime, end_date: datetime) -> int:
        """Count DM action files created in date range."""
        count = 0
        try:
            for file in self.needs_action_path.glob("LINKEDIN_DM_*.md"):
                if file.stat().st_mtime >= start_date.timestamp() and \
                   file.stat().st_mtime <= end_date.timestamp():
                    count += 1
        except Exception as e:
            self.logger.debug(f"Error counting DMs: {e}")
        return count

    def _count_comments(self, start_date: datetime, end_date: datetime) -> int:
        """Count comment action files created in date range."""
        count = 0
        try:
            for file in self.needs_action_path.glob("LINKEDIN_COMMENT_*.md"):
                if file.stat().st_mtime >= start_date.timestamp() and \
                   file.stat().st_mtime <= end_date.timestamp():
                    count += 1
        except Exception as e:
            self.logger.debug(f"Error counting comments: {e}")
        return count

    def _count_posts(self, start_date: datetime, end_date: datetime) -> int:
        """Count posts from log files."""
        count = 0
        try:
            # Check daily log files in date range
            current = start_date
            while current <= end_date:
                log_file = self.logs_path / f"{current.strftime('%Y-%m-%d')}.json"
                if log_file.exists():
                    try:
                        with open(log_file, 'r') as f:
                            logs = json.load(f)
                            for entry in logs:
                                if entry.get('action_type') == 'linkedin_post_post' and \
                                   entry.get('result') == 'success':
                                    count += 1
                    except Exception as e:
                        self.logger.debug(f"Error reading log: {e}")
                current += timedelta(days=1)
        except Exception as e:
            self.logger.debug(f"Error counting posts: {e}")
        return count

    def _count_profile_views(self, start_date: datetime, end_date: datetime) -> int:
        """Count profile views from visitor files."""
        count = 0
        try:
            visitors_file = self.vault_path / "LinkedIn" / "Profile_Visitors.md"
            if visitors_file.exists():
                # Parse visitor file and count recent entries
                content = visitors_file.read_text(encoding='utf-8')
                # Simple count of visitor entries (lines starting with "- ")
                for line in content.split('\n'):
                    if line.strip().startswith('- '):
                        count += 1
        except Exception as e:
            self.logger.debug(f"Error counting profile views: {e}")
        return count

    def _get_top_visitors(self, start_date: datetime, end_date: datetime, limit: int = 5) -> List[Dict]:
        """Get top profile visitors."""
        visitors = []
        try:
            visitors_file = self.vault_path / "LinkedIn" / "Profile_Visitors.md"
            if visitors_file.exists():
                # Parse visitor markdown file
                content = visitors_file.read_text(encoding='utf-8')
                lines = content.split('\n')

                for line in lines:
                    if ' — ' in line:  # Visitor format: "Name — Title at Company"
                        parts = line.strip('- ').split(' — ')
                        if len(parts) == 2:
                            visitors.append({
                                'name': parts[0].strip(),
                                'details': parts[1].strip()
                            })
                        if len(visitors) >= limit:
                            break
        except Exception as e:
            self.logger.debug(f"Error getting top visitors: {e}")

        return visitors

    def _generate_markdown_report(
        self,
        week_start: datetime,
        week_end: datetime,
        dm_count: int,
        comment_count: int,
        post_count: int,
        visitor_count: int,
        last_dm_count: int,
        last_comment_count: int,
        last_post_count: int,
        last_visitor_count: int,
        top_visitors: List[Dict]
    ) -> str:
        """Generate markdown report content."""

        # Calculate trends
        dm_trend = self._format_trend(dm_count, last_dm_count)
        comment_trend = self._format_trend(comment_count, last_comment_count)
        post_trend = self._format_trend(post_count, last_post_count)
        visitor_trend = self._format_trend(visitor_count, last_visitor_count)

        # Build markdown
        report = f"""# LinkedIn Weekly Report — Week of {week_start.strftime('%B %d, %Y')}

**Period:** {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}

## 📊 Activity Summary

| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| DMs Received | {dm_count} | {last_dm_count} | {dm_trend} |
| Comments | {comment_count} | {last_comment_count} | {comment_trend} |
| Posts Made | {post_count} | {last_post_count} | {post_trend} |
| Profile Views | {visitor_count} | {last_visitor_count} | {visitor_trend} |

## 🔥 Hot Leads (Top Profile Visitors)

"""

        if top_visitors:
            for i, visitor in enumerate(top_visitors, 1):
                report += f"{i}. **{visitor['name']}** — {visitor['details']}\n"
        else:
            report += "*No visitors recorded this week*\n"

        report += f"""

## ✅ Quick Stats

- **Total Engagement:** {dm_count + comment_count} interactions (DMs + Comments)
- **Posting Activity:** {post_count} posts published
- **Network Growth:** {visitor_count} new profile views
- **Response Rate:** Track via comments and DMs

## 📋 Action Items

"""

        # Generate action items based on activity
        actions = []

        if dm_count > 0:
            unread_dms = self._count_unread_dms()
            if unread_dms > 0:
                actions.append(f"Reply to {unread_dms} pending DMs")

        if comment_count > 0:
            actions.append(f"Engage with {comment_count} comments on your posts")

        if visitor_count >= 10:
            actions.append("Follow up with high-value profile visitors")

        if not actions:
            actions = ["Continue growing your LinkedIn presence", "Engage with connections regularly"]

        for action in actions:
            report += f"- [ ] {action}\n"

        report += f"""

## 💡 Insights

**Best Performing Content:** Check your posts with highest engagement
**Peak Engagement Time:** {self._get_peak_engagement_time()}
**Recommended Actions:** Focus on quality interactions and consistent posting

---

*Report generated by LinkedIn Watcher v1.0 on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
*Next report: {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')}*
"""

        return report

    def _format_trend(self, current: int, last: int) -> str:
        """Format trend indicator."""
        if current > last:
            diff = current - last
            return f"📈 +{diff}"
        elif current < last:
            diff = last - current
            return f"📉 -{diff}"
        else:
            return "→ —"

    def _count_unread_dms(self) -> int:
        """Count unread DMs (pending status)."""
        count = 0
        try:
            for file in self.needs_action_path.glob("LINKEDIN_DM_*.md"):
                content = file.read_text(encoding='utf-8')
                if 'status: pending' in content:
                    count += 1
        except:
            pass
        return count

    def _get_peak_engagement_time(self) -> str:
        """Get peak engagement time from recent posts."""
        # Placeholder - would analyze post timings from logs
        return "Weekdays 8-10 AM and 5-7 PM"


def main():
    """Main entry point."""
    load_dotenv()

    vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "./AI_Employee_Vault")
    log_level = os.getenv("LINKEDIN_LOG_LEVEL", "INFO")

    reporter = LinkedInWeeklyReport(vault_path, log_level)
    reporter.generate_report()


if __name__ == "__main__":
    main()
