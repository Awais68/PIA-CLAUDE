#!/bin/bash

###############################################################################
# LinkedIn Automation Setup Script
#
# Creates LinkedIn folder structure and template files
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${BLUE}=== $1 ===${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${BLUE}[*]${NC} $1"
}

# Main
print_header "LinkedIn Automation Setup"

VAULT_PATH="./AI_Employee_Vault"

# Create LinkedIn subdirectories
print_info "Creating LinkedIn folder structure..."

DIRS=(
    "LinkedIn/Post_Queue"
    "LinkedIn/Briefings"
    "LinkedIn/Templates"
)

for dir in "${DIRS[@]}"; do
    DIR_PATH="$VAULT_PATH/$dir"
    if [ ! -d "$DIR_PATH" ]; then
        mkdir -p "$DIR_PATH"
        touch "$DIR_PATH/.gitkeep"
        print_success "Created $DIR_PATH"
    else
        print_success "$DIR_PATH already exists"
    fi
done

# Create template files
print_header "Creating Template Files"

# Post template
print_info "Creating post template..."
cat > "$VAULT_PATH/LinkedIn/Templates/POST_TEMPLATE.md" << 'EOF'
---
scheduled_time: 2026-03-10T09:00:00
post_type: text
status: pending
approval_required: true
image_path:
hashtags: #Business #Leadership #Innovation
language: English
---

**Your post content goes here.**

Write naturally and authentically. This template helps organize your LinkedIn posts.

Consider:
- What value does this add to your network?
- Who is your target audience?
- What action do you want them to take?

Tips:
- Keep it under 3000 characters
- Use line breaks for readability
- Mention specific people (without overdoing it)
- Include a call to action if appropriate
EOF

print_success "Created post template"

# Business Goals template
print_info "Creating business goals template..."
cat > "$VAULT_PATH/LinkedIn/Business_Goals.md" << 'EOF'
# LinkedIn Business Goals

## Current Objectives
- [ ] Build authority in Business/Entrepreneurship
- [ ] Grow engaged audience
- [ ] Generate leads
- [ ] Network with industry leaders

## Target Audience
- Business owners
- Entrepreneurs
- Investors
- Leadership professionals

## Content Pillars
1. **Industry Insights** — Share knowledge and analysis
2. **Business Tips** — Actionable advice and strategies
3. **Success Stories** — Case studies and testimonials
4. **Personal Journey** — Behind-the-scenes and learnings

## Key Messages
- Helping businesses grow through automation and AI
- Empowering entrepreneurs with tools and knowledge
- Building community around innovation

## Monthly Goals
- DMs: 10+
- Comments: 20+
- Posts: 4
- Profile views: 50+

---
*Update this file to match your business objectives*
EOF

print_success "Created business goals template"

# Post queue example
print_info "Creating post queue example..."
cat > "$VAULT_PATH/LinkedIn/Post_Queue/EXAMPLE_POST.md" << 'EOF'
---
scheduled_time: 2026-03-10T09:00:00
post_type: text
status: pending
approval_required: true
image_path:
hashtags: #Business #Entrepreneurship #Leadership
language: English
---

This is an example post in the Post_Queue folder.

To post:
1. Edit this file or create a new one
2. Write your content in the body
3. Set status to "pending"
4. Move file to /Approved folder
5. Set scheduled_time to when you want it posted
6. The poster will automatically post when the time arrives

Once posted, the file will be moved to /Done folder automatically.
EOF

print_success "Created example post"

# DM Templates
print_info "Creating DM response templates..."
cat > "$VAULT_PATH/LinkedIn/Templates/DM_TEMPLATES.md" << 'EOF'
# LinkedIn DM Response Templates

## Welcome Response
Hi [Name],

Thanks for reaching out! I really appreciate your message.

[Your specific response]

Looking forward to connecting further.

Best,
[Your name]

---

## Collaboration Request
Hi [Name],

Thank you for thinking of me for this opportunity. I'm interested in exploring how we might collaborate.

Could we schedule a quick call this week to discuss? I'm available [suggest times].

Best regards,
[Your name]

---

## General Response
Thanks for your message, [Name].

[Your response]

Feel free to reach out anytime.

Cheers,
[Your name]

---

## Professional Inquiry
Hi [Name],

Thanks for the inquiry. I'm happy to help where I can.

[Your detailed response]

Let me know if you have any other questions.

Best,
[Your name]

---

*Keep these templates handy for quick responses*
EOF

print_success "Created DM templates"

# Profile visitors file
print_info "Creating profile visitors tracker..."
cat > "$VAULT_PATH/LinkedIn/Profile_Visitors.md" << 'EOF'
# LinkedIn Profile Visitors

**Updated:** $(date +"%Y-%m-%d")

## Recent Visitors (Last 30 Days)

Track your profile visitors here. The watcher automatically records visits.

*Format:*
- **Name** — Title at Company (viewed X times)

---

*This file is automatically updated by linkedin_watcher.py*
EOF

print_success "Created profile visitors file"

# Configuration file
print_header "Configuration"

if [ ! -f ".env" ]; then
    print_info "Creating .env file from .env.example..."
    cp .env.example .env
    print_success ".env created - edit with your settings"
else
    print_success ".env already exists"
fi

# Summary
print_header "LinkedIn Automation Setup Complete"

echo "Folder structure created:"
echo "  ✓ Post_Queue/      — Put posts here before approval"
echo "  ✓ Briefings/       — Weekly reports generated here"
echo "  ✓ Templates/       — Post and DM templates"
echo ""
echo "Template files created:"
echo "  ✓ POST_TEMPLATE.md     — Use this to write new posts"
echo "  ✓ Business_Goals.md    — Define your LinkedIn strategy"
echo "  ✓ DM_TEMPLATES.md      — Quick response templates"
echo "  ✓ Profile_Visitors.md  — Visitor tracking"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your LinkedIn settings"
echo "  2. ${BLUE}python3 first_login_linkedin.py${NC}  (first time only)"
echo "  3. ${BLUE}python3 linkedin_watcher.py${NC}      (monitor DMs & comments)"
echo "  4. ${BLUE}python3 linkedin_poster.py${NC}       (auto-post approved content)"
echo ""
echo "For more info, see LINKEDIN_AUTOMATION_README.md"
echo ""
