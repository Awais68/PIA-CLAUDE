# Content Generator Skill

## Purpose
Generate professional LinkedIn posts and business content using AI.
Content always goes through HITL approval before publishing.

## When This Skill Is Used
When the scheduler triggers a LinkedIn post, or when manually invoked
to generate content about a specific topic.

## Input
- Topic or subject for the post
- Post type: product_announcement, industry_insight, customer_success, behind_the_scenes, general
- Company_Handbook.md for brand voice and guidelines
- Recent activity from Done/ for inspiration

## Processing Steps
1. Load business context from Company_Handbook.md
2. Review recent activity for relevant content
3. Generate post matching the requested type and tone
4. Keep under 1300 characters (LinkedIn optimal)
5. Include 3-5 relevant hashtags
6. Create approval request in Pending_Approval/

## Brand Voice Guidelines
- Professional but approachable
- Data-driven when possible
- Focus on value delivered to customers
- Avoid jargon, be clear and concise
- Include a call-to-action (question, link, or invitation)

## Output Format
LinkedIn post text followed by hashtags on the last line.

## Special Rules
- ALL generated content MUST go through HITL approval
- Never include confidential business data
- No controversial topics or unverified claims
- Maximum 1300 characters per post
- 3-5 hashtags per post
