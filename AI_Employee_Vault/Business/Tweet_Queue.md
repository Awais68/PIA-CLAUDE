# Tweet Queue

Zoya reads this file every 30 minutes. Add tweets to the `## Scheduled` section
with a `scheduled_for` field. When the time arrives, Zoya creates an approval
request in `/Pending_Approval/` — you must approve before anything is published.

**Format for a scheduled tweet:**
```
- [ ] scheduled_for: YYYY-MM-DD HH:MM UTC | Your tweet text here (max 280 chars) #hashtag
```

**Status markers:**
- `- [ ]` — queued, not yet sent to approval
- `- [x]` — sent to approval (see `/Pending_Approval/` for TWITTER_*.md files)

---

## Scheduled

<!-- Add your tweets below. Zoya processes this list every 30 minutes. -->

- [x] scheduled_for: 2026-02-23 09:00 UTC | Exciting things happening at the studio this week. Stay tuned. #BuildingInPublic #AI
- [x] scheduled_for: 2026-02-24 12:00 UTC | Automation doesn't replace you — it removes the work that was replacing you. #AIEmployee #Productivity
- [ ] scheduled_for: 2026-02-24 18:00 UTC | 🤖 Built an AI that processes 60+ documents without cloud. Multi-channel ingestion, HITL approval, complete audit trail. This is enterprise automation. #AI #Automation
- [ ] scheduled_for: 2026-02-25 10:00 UTC | Email → Invoice Processing. WhatsApp → Business Tasks. File Drop → Auto-categorization. The future is local-first architecture + Claude reasoning. #AIRevolution
- [ ] scheduled_for: 2026-02-25 17:00 UTC | What does your morning routine look like? Ours now: AI reads inbox, processes documents, generates briefing. All audited. Zero magic. #ZoyaAI #Productivity
- [ ] scheduled_for: 2026-02-26 12:00 UTC | 100% processing success rate. 60+ documents. 3 data sources. 0 cloud dependencies. Zoya: When you give an AI proper structure, magic happens. #DeveloperLife

---

## Ideas / Drafts

Use this section for tweet ideas that aren't ready to schedule yet.

- Draft: Share behind-the-scenes of how the AI inbox processing works
- Draft: Thread on why file-based AI architectures are underrated
- Draft: Customer quote / testimonial (need permission first)

---

## Evergreen Content Bank

These can be recycled every 30+ days:

1. "The best meeting is the one replaced by a clear document." #Async #Productivity
2. "Ship small, ship often. Your future self will thank you." #BuildInPublic
3. "AI works best when it augments judgment, not replaces it." #AIethics

---

## Archive

<!-- Processed tweets (auto-updated by Zoya) -->
