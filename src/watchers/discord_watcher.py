"""Discord Bot Watcher - Interactive bot with modals for tasks, expenses, emails, todos, research."""

import asyncio
import json
import logging
import time
from datetime import datetime
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from src.config import DISCORD_TOKEN, DISCORD_GUILD_ID, INBOX, VAULT_PATH
from src.todo_manager import TodoManager
from src.utils import log_action

logger = logging.getLogger(__name__)

# State file for recovery
STATE_FILE = VAULT_PATH / "Logs" / "discord_state.json"


class ExpenseModal(discord.ui.Modal):
    """Modal for adding expenses."""

    def __init__(self, cog):
        super().__init__(title="Add Expense")
        self.cog = cog

    amount = discord.ui.TextInput(
        label="Amount (PKR)",
        placeholder="1500",
        required=True
    )

    category = discord.ui.TextInput(
        label="Category",
        placeholder="Food / Transport / Utilities / Software / Marketing / Other",
        required=True
    )

    description = discord.ui.TextInput(
        label="Description",
        placeholder="What was it for?",
        required=True
    )

    date = discord.ui.TextInput(
        label="Date (YYYY-MM-DD)",
        placeholder=datetime.now().strftime("%Y-%m-%d"),
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        expense_date = self.date.value or datetime.now().strftime("%Y-%m-%d")

        expense_file = INBOX / f"EXPENSE_{now}.md"
        content = f"""---
type: expense
amount: {self.amount.value}
currency: PKR
category: {self.category.value}
date: {expense_date}
source: discord
approval_required: true
created: {datetime.now().isoformat()}
---

# Expense Report

**Amount**: {self.amount.value} PKR
**Category**: {self.category.value}
**Description**: {self.description.value}
**Date**: {expense_date}

## Approval Status
Pending approval
"""

        expense_file.write_text(content)
        log_action("discord_watcher", f"Created expense: {self.amount.value} PKR", result="success")

        await interaction.response.send_message(
            f"✅ Expense saved: {self.amount.value} PKR ({self.category.value})",
            ephemeral=True
        )


class TodoModal(discord.ui.Modal):
    """Modal for adding todos."""

    def __init__(self, cog):
        super().__init__(title="Add Todo")
        self.cog = cog

    task_name = discord.ui.TextInput(
        label="Task Name",
        placeholder="What needs to be done?",
        required=True
    )

    priority = discord.ui.TextInput(
        label="Priority",
        placeholder="High / Medium / Low",
        default="Medium",
        required=True
    )

    due_date = discord.ui.TextInput(
        label="Due Date (YYYY-MM-DD)",
        placeholder="2026-03-15",
        required=False
    )

    recurrence = discord.ui.TextInput(
        label="Recurrence",
        placeholder="None / Daily / Weekly / Monthly",
        default="None",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        try:
            tm = TodoManager()
            todo_id = tm.create_todo(
                title=self.task_name.value,
                priority=self.priority.value,
                due_date=self.due_date.value or None,
                recurrence=self.recurrence.value or "None"
            )
            tm.sync_dashboard()

            await interaction.response.send_message(
                f"✅ Todo created: {todo_id}\n**Task**: {self.task_name.value}",
                ephemeral=True
            )
        except Exception as e:
            logger.error(f"Failed to create todo: {e}")
            await interaction.response.send_message(
                f"❌ Error creating todo: {e}",
                ephemeral=True
            )


class EmailDraftModal(discord.ui.Modal):
    """Modal for drafting emails."""

    def __init__(self, cog):
        super().__init__(title="Draft Email")
        self.cog = cog

    subject = discord.ui.TextInput(
        label="Email Subject",
        placeholder="What's the email about?",
        required=True
    )

    context = discord.ui.TextInput(
        label="Context / Notes",
        placeholder="Any additional context?",
        required=False,
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle modal submission."""
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        draft_file = INBOX / f"EMAIL_DRAFT_{now}.md"

        content = f"""---
type: email_draft
approval_required: true
source: discord
subject: {self.subject.value}
created: {datetime.now().isoformat()}
---

# Email Draft

**Subject**: {self.subject.value}

## Context
{self.context.value or 'No additional context'}

## Body
[Draft email body - to be generated by email_drafter skill]

## Status
Pending approval
"""

        draft_file.write_text(content)
        log_action("discord_watcher", f"Created email draft: {self.subject.value}", result="success")

        await interaction.response.send_message(
            f"✅ Email draft created\n**Subject**: {self.subject.value}",
            ephemeral=True
        )


class ZoyaCog(commands.Cog):
    """Zoya Discord Bot Cog."""

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="zoya", description="Zoya AI Employee Menu")
    async def zoya_menu(self, interaction: discord.Interaction):
        """Main Zoya menu with action options."""
        view = ZoyaMenuView()
        await interaction.response.send_message(
            "**Zoya** - Personal AI Employee\n\nSelect an action:",
            view=view,
            ephemeral=True
        )

    @app_commands.command(name="task", description="Select a task from Needs_Action")
    async def list_tasks(self, interaction: discord.Interaction):
        """List tasks waiting for action."""
        needs_action = VAULT_PATH / "Needs_Action"
        if not needs_action.exists():
            await interaction.response.send_message("No tasks found.", ephemeral=True)
            return

        tasks = list(needs_action.glob("*.md"))[:10]  # Show first 10
        if not tasks:
            await interaction.response.send_message("No tasks found.", ephemeral=True)
            return

        view = TaskSelectView(tasks)
        await interaction.response.send_message(
            f"Found {len(tasks)} task(s):",
            view=view,
            ephemeral=True
        )

    @app_commands.command(name="dashboard", description="View Dashboard")
    async def show_dashboard(self, interaction: discord.Interaction):
        """Show current Dashboard."""
        dashboard = VAULT_PATH / "Dashboard.md"
        if not dashboard.exists():
            await interaction.response.send_message("Dashboard not found.", ephemeral=True)
            return

        content = dashboard.read_text()
        # Show first 1500 chars
        preview = content[:1500] + ("..." if len(content) > 1500 else "")

        embed = discord.Embed(
            title="📊 Dashboard",
            description=preview,
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="expense", description="Add an expense")
    async def add_expense(self, interaction: discord.Interaction):
        """Open expense modal."""
        modal = ExpenseModal(self)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="todo", description="Add a todo")
    async def add_todo(self, interaction: discord.Interaction):
        """Open todo modal."""
        modal = TodoModal(self)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="email", description="Draft an email")
    async def draft_email(self, interaction: discord.Interaction):
        """Open email draft modal."""
        modal = EmailDraftModal(self)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="research", description="Request research on topics")
    async def request_research(self, interaction: discord.Interaction, topics: str):
        """Request research on comma-separated topics."""
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        research_file = INBOX / f"RESEARCH_REQUEST_{now}.md"

        content = f"""---
type: research_request
topics: {topics}
source: discord
created: {datetime.now().isoformat()}
---

# Research Request

**Topics**: {topics}

## Status
Pending research
"""

        research_file.write_text(content)
        log_action("discord_watcher", f"Created research request: {topics}", result="success")

        await interaction.response.send_message(
            f"✅ Research request submitted\n**Topics**: {topics}",
            ephemeral=True
        )


class ZoyaMenuView(discord.ui.View):
    """Main menu view with action buttons."""

    @discord.ui.button(label="1. Tasks", style=discord.ButtonStyle.primary)
    async def tasks_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        # Trigger list_tasks command
        cog = interaction.client.get_cog("ZoyaCog")
        await cog.list_tasks(interaction)

    @discord.ui.button(label="2. Dashboard", style=discord.ButtonStyle.primary)
    async def dashboard_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        cog = interaction.client.get_cog("ZoyaCog")
        await cog.show_dashboard(interaction)

    @discord.ui.button(label="3. Email", style=discord.ButtonStyle.secondary)
    async def email_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        cog = interaction.client.get_cog("ZoyaCog")
        await cog.draft_email(interaction)

    @discord.ui.button(label="4. Expense", style=discord.ButtonStyle.secondary)
    async def expense_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        cog = interaction.client.get_cog("ZoyaCog")
        await cog.add_expense(interaction)

    @discord.ui.button(label="5. Todo", style=discord.ButtonStyle.secondary)
    async def todo_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        cog = interaction.client.get_cog("ZoyaCog")
        await cog.add_todo(interaction)

    @discord.ui.button(label="6. Research", style=discord.ButtonStyle.success)
    async def research_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ResearchModal())


class ResearchModal(discord.ui.Modal):
    """Modal for research requests."""

    def __init__(self):
        super().__init__(title="Request Research")

    topics = discord.ui.TextInput(
        label="Topics (comma-separated)",
        placeholder="BTC, AAPL, USD/PKR",
        required=True
    )

    schedule = discord.ui.TextInput(
        label="Schedule (optional)",
        placeholder="daily 09:00",
        required=False
    )

    async def on_submit(self, interaction: discord.Interaction):
        """Handle research request."""
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        research_file = INBOX / f"RESEARCH_REQUEST_{now}.md"

        content = f"""---
type: research_request
topics: {self.topics.value}
schedule: {self.schedule.value or 'None'}
source: discord
created: {datetime.now().isoformat()}
---

# Research Request

**Topics**: {self.topics.value}
**Schedule**: {self.schedule.value or 'One-time'}

## Status
Pending research
"""

        research_file.write_text(content)
        log_action("discord_watcher", f"Created research request: {self.topics.value}", result="success")

        await interaction.response.send_message(
            f"✅ Research requested\n**Topics**: {self.topics.value}",
            ephemeral=True
        )


class TaskSelectView(discord.ui.View):
    """View for selecting tasks."""

    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks
        for task in tasks[:5]:  # Max 5 buttons
            self.add_item(TaskButton(task))


class TaskButton(discord.ui.Button):
    """Button for each task."""

    def __init__(self, task_file):
        super().__init__(label=task_file.stem[:80], style=discord.ButtonStyle.secondary)
        self.task_file = task_file

    async def callback(self, interaction: discord.Interaction):
        """Show task details."""
        content = self.task_file.read_text()
        preview = content[:500] + ("..." if len(content) > 500 else "")

        embed = discord.Embed(
            title=f"📋 {self.task_file.stem}",
            description=preview,
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ZoyaBot(commands.Bot):
    """Zoya Discord Bot with auto-restart capability."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_time = None

    async def on_ready(self):
        """Bot is ready."""
        logger.info(f"Bot logged in as {self.user}")
        await self.tree.sync()

    async def on_error(self, event_method, *args, **kwargs):
        """Handle bot errors."""
        logger.error(f"Error in {event_method}", exc_info=True)


def save_state(state: dict) -> None:
    """Save bot state for recovery."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2, default=str)


def load_state() -> dict:
    """Load bot state from last session."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
    return {}


async def run_bot_with_retry(max_retries: int = 5, cooldown: int = 30):
    """Run bot with auto-restart on crash.

    Args:
        max_retries: Max crash/restart cycles before giving up
        cooldown: Seconds between restart attempts
    """
    retries = 0

    while retries < max_retries:
        try:
            logger.info(f"Starting Discord bot (attempt {retries + 1}/{max_retries})")

            intents = discord.Intents.default()
            intents.message_content = True
            intents.guilds = True

            bot = ZoyaBot(command_prefix="!", intents=intents)

            @bot.event
            async def on_ready():
                await bot.tree.sync()
                logger.info(f"Bot synced and ready as {bot.user}")
                save_state({"connected": True, "timestamp": datetime.now().isoformat()})

            # Add cog
            await bot.add_cog(ZoyaCog(bot))

            # Run bot
            await bot.start(DISCORD_TOKEN)

        except discord.errors.LoginFailure:
            logger.error("Invalid Discord token")
            break

        except Exception as e:
            logger.error(f"Bot crashed: {e}")
            retries += 1

            if retries < max_retries:
                logger.info(f"Restarting in {cooldown}s... ({retries}/{max_retries})")
                await asyncio.sleep(cooldown)
            else:
                logger.error(f"Max retries ({max_retries}) reached. Giving up.")
                break

    save_state({"connected": False, "last_error": "Max retries exceeded"})


def main():
    """CLI entry point."""
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN not set in .env")
        return

    logger.info("Starting Zoya Discord Bot...")
    asyncio.run(run_bot_with_retry())


if __name__ == "__main__":
    main()
