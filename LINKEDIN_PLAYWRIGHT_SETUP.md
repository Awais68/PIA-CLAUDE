# LinkedIn Playwright Setup Guide

## ✅ Prerequisites Check

```
✅ Playwright installed
✅ Chromium browser ready
✅ LinkedIn Playwright files exist:
   - linkedin_playwright_login.py
   - linkedin_playwright_validator.py
   - linkedin_watcher.py
   - linkedin_poster.py
```

All ready to go! 🚀

---

## Step 1: Get Your LinkedIn Credentials

You need your LinkedIn email and password (the ones you use to log in).

```
📧 Email: your_email@example.com
🔐 Password: your_password
```

⚠️ **Security Note**:
- Never share these credentials
- Keep them in `.env` (git-ignored)
- They'll be stored locally in `~/.linkedin_session/`

---

## Step 2: Add to .env File

Add these two lines to your `.env` file:

```bash
# LinkedIn Playwright Authentication (Email + Password)
LINKEDIN_EMAIL=your_email@example.com
LINKEDIN_PASSWORD=your_password
LINKEDIN_SESSION_PATH=~/.linkedin_session
```

**Example**:
```bash
# LinkedIn Playwright Authentication (Email + Password)
LINKEDIN_EMAIL=john.doe@gmail.com
LINKEDIN_PASSWORD=MySecurePassword123!
LINKEDIN_SESSION_PATH=~/.linkedin_session
```

---

## Step 3: Test the Connection

Run the login script to authenticate:

```bash
python3 linkedin_playwright_login.py
```

### Expected Output

```
========================================
LinkedIn Playwright Login
========================================

📧 Authenticating with Email & Password...
🌐 Loading LinkedIn...
📝 Logging in as: john.doe@gmail.com
⏳ Waiting for page load...
✅ Email/password authentication successful!
💾 Session saved to: ~/.linkedin_session/

Session Files:
├── cookies.json      ← Login cookies
└── storage/          ← Browser data

Ready to post! 🚀
```

---

## Step 4: Verify Session

Check that session was created:

```bash
python3 linkedin_playwright_validator.py
```

### Expected Output

```
========================================
LinkedIn Session Validator
========================================

✅ Session exists at: ~/.linkedin_session/
✅ Cookies found
✅ Session is valid
✅ Ready to post!
```

---

## Step 5: Test Posting

Create a test post:

```bash
python3 << 'EOF'
import asyncio
from linkedin_playwright_login import LinkedInPlaywrightLogin

async def test_post():
    # Login
    login = LinkedInPlaywrightLogin()

    # Your session is already saved, so it will use that
    print("✅ Session loaded from ~/.linkedin_session/")
    print("✅ Ready to post to LinkedIn!")

asyncio.run(test_post())
EOF
```

---

## Configuration Checklist

```
Setup Completion Checklist:

[ ] 1. Added LINKEDIN_EMAIL to .env
[ ] 2. Added LINKEDIN_PASSWORD to .env
[ ] 3. Added LINKEDIN_SESSION_PATH to .env
[ ] 4. Ran: python3 linkedin_playwright_login.py
[ ] 5. Successfully authenticated
[ ] 6. Session saved to ~/.linkedin_session/
[ ] 7. Ran validator script
[ ] 8. Validator passed
[ ] 9. Ready to post!
```

---

## What Happens Behind the Scenes

```
1. Script loads .env credentials
   LINKEDIN_EMAIL=john.doe@gmail.com
   LINKEDIN_PASSWORD=MySecurePassword123!

2. Playwright launches headless Chrome browser
   (runs silently, no window visible)

3. Browser navigates to https://www.linkedin.com/login

4. Script fills in:
   - Email field
   - Password field
   - Clicks login button

5. Waits for feed to load (proves login successful)

6. Saves session to ~/.linkedin_session/
   - cookies.json (login session)
   - storage/ (browser storage)

7. Session reused for future posts
   (no need to login again!)
```

---

## Using the Session for Posting

Once authenticated, all LinkedIn operations use the saved session:

```python
# Example 1: Post directly
from linkedin_playwright_login import LinkedInPlaywrightLogin

async def post_content():
    login = LinkedInPlaywrightLogin()
    # Session auto-loaded from ~/.linkedin_session/
    # Post using the browser
    await login.post_to_feed("My new post! 🚀")

# Example 2: Check messages
from linkedin_watcher import LinkedInWatcher

watcher = LinkedInWatcher()
# Uses session automatically
messages = await watcher.check_messages()

# Example 3: Validate session is still active
from linkedin_playwright_validator import LinkedInPlaywrightValidator

validator = LinkedInPlaywrightValidator()
is_valid = await validator.validate_session()
```

---

## Session Management

### Session Files Location
```bash
~/.linkedin_session/
├── cookies.json              ← Login cookies (encrypted)
└── storage/
    ├── localStorage.json     ← Browser storage
    └── sessionStorage.json   ← Session data
```

### Session Lifespan
- ✅ Lasts for **30-60 days** (LinkedIn's default)
- ✅ Auto-refreshed when you post
- ❌ Expires if LinkedIn forces re-authentication
- ❌ Expires if you change password
- ❌ Expires if you enable 2FA (may need manual login)

### Reset Session (if needed)
```bash
# If session expires or stops working:
rm -rf ~/.linkedin_session/

# Then login again:
python3 linkedin_playwright_login.py
```

---

## Integration with Vault System

Once authenticated, your posts will work like this:

```
1. You create post in: Pending_Approval/social/LINKEDIN_*.md

2. Orchestrator detects it (every 30 seconds)

3. Calls Playwright LinkedIn client:
   - Loads session from ~/.linkedin_session/
   - Posts to your feed
   - Returns success/failure

4. File moves to Done/

5. Logged to Logs/2026-03-05.json
```

---

## Headless vs Headed Mode

### Headless Mode (Default - Recommended)
```python
# Browser runs silently in background
# Perfect for servers/automation
browser = await playwright.chromium.launch(headless=True)  # ✅ Default
```

Pros:
- ✅ Faster
- ✅ No window popup
- ✅ Works on servers
- ✅ Better for automation

### Headed Mode (For Debugging)
```python
# Browser opens a visible window
# Useful to watch what's happening
browser = await playwright.chromium.launch(headless=False)
```

Pros:
- ✅ See what browser is doing
- ✅ Debug issues visually
- ✅ Verify session works

To enable: Set `LINKEDIN_BROWSER_HEADLESS=false` in .env

---

## Troubleshooting

### Error: "Login failed or took too long"
**Cause**: Password incorrect or 2FA enabled
**Fix**:
```bash
1. Verify email/password in .env
2. If 2FA enabled: Login manually in browser first
3. Delete session: rm -rf ~/.linkedin_session/
4. Try again
```

### Error: "Session invalid"
**Cause**: Session expired (> 60 days) or password changed
**Fix**:
```bash
rm -rf ~/.linkedin_session/
python3 linkedin_playwright_login.py
```

### Error: "LinkedIn detected bot activity"
**Cause**: Too many automated posts too fast
**Fix**:
```bash
1. Wait 24 hours
2. Add delays between posts
3. Vary post content (don't spam same message)
4. Reset session and try again
```

### Error: "Chromium not found"
**Cause**: Playwright browsers not installed
**Fix**:
```bash
python3 -m playwright install chromium
```

---

## Security Best Practices

### ✅ DO:
- [x] Keep email/password in `.env` (git-ignored)
- [x] Use `.gitignore` to prevent accidental commit
- [x] Store `.env` securely on server
- [x] Use strong password
- [x] Session stored locally only (`~/.linkedin_session/`)

### ❌ DON'T:
- [ ] Commit `.env` to Git
- [ ] Share credentials in messages
- [ ] Use weak/reused passwords
- [ ] Leave `.env` in public folders
- [ ] Log credentials in error messages

### 2FA Consideration
If you have 2FA enabled:
1. Disable it temporarily for setup
2. OR: Log in manually once in browser
3. OR: Use an app password if LinkedIn offers one

---

## Verification Checklist

Once setup complete, verify everything works:

```bash
# Test 1: Session exists
ls -la ~/.linkedin_session/

# Test 2: Credentials in .env
grep LINKEDIN_EMAIL .env | head -1

# Test 3: Playwright installed
python3 -c "import playwright; print('✅ Playwright OK')"

# Test 4: Login script works
python3 linkedin_playwright_login.py

# Test 5: Validator works
python3 linkedin_playwright_validator.py

# Test 6: Can post
python3 << 'EOF'
import asyncio
from linkedin_playwright_login import LinkedInPlaywrightLogin
async def test():
    login = LinkedInPlaywrightLogin()
    print("✅ Ready to post!")
asyncio.run(test())
EOF
```

---

## Next Steps

1. ✅ You've set up Playwright
2. 📝 Create posts in `Pending_Approval/social/`
3. 🚀 Orchestrator will auto-post
4. 📊 Check `Logs/` for success/failures
5. ✨ Watch LinkedIn posts appear!

---

## File Reference

All files you need are already in the repo:

| File | Purpose |
|------|---------|
| `linkedin_playwright_login.py` | Authentication & login |
| `linkedin_playwright_validator.py` | Verify session valid |
| `linkedin_watcher.py` | Monitor messages |
| `linkedin_poster.py` | Create posts |
| `src/linkedin_poster.py` | Vault integration |

---

## Summary

**Playwright Setup = DONE ✅**

You now have:
- ✅ Playwright installed & ready
- ✅ Chromium browser ready
- ✅ Email/password in .env
- ✅ Session management configured
- ✅ Ready to post to LinkedIn

**No token refresh needed. No URN lookup. Just post!** 🎉

---

## Quick Start Command

```bash
# One command to do everything:
python3 linkedin_playwright_login.py && echo "✅ You're ready to post on LinkedIn!"
```

---

**Need help?** Check the error messages in troubleshooting section above, or look at:
- `linkedin_playwright_login.py` - for login details
- `linkedin_playwright_validator.py` - for session validation
