# Plan Creator Skill

## Purpose
Generate structured action plans (Plan.md) for complex tasks that require
multi-step reasoning, research, or human approval before execution.

## When This Skill Is Used
When the orchestrator determines a document requires a non-trivial response
(e.g., drafting a proposal reply, scheduling a meeting, preparing a report).

## Input
- Metadata file in /In_Progress/ with task context
- Company_Handbook.md for business rules and tone guidelines
- Previous plans in /Plans/ for style consistency

## Processing Steps
1. Read the task context from the metadata file
2. Break the task into discrete, actionable steps
3. Identify dependencies between steps
4. Estimate complexity (simple / moderate / complex)
5. Flag any steps requiring human approval (HITL)
6. Write Plan.md to AI_Employee_Vault/Plans/

## Output Format
Create a Plan.md file:
```markdown
---
task_ref: <queued_name from metadata>
created_at: <ISO timestamp>
complexity: <simple|moderate|complex>
requires_approval: <true|false>
status: draft
---

## Objective
<1-2 sentence goal>

## Steps
1. [ ] <step description> — <owner: ai|human>
2. [ ] <step description> — <owner: ai|human>

## Dependencies
- Step 2 depends on Step 1

## Risks / Notes
- <any caveats or risks>
```

## Special Rules
- Plans requiring budget approval (> $100) MUST set `requires_approval: true`
- Plans involving external communication MUST set `requires_approval: true`
- Keep plans concise — max 10 steps
- Reference Company_Handbook.md for approval thresholds
