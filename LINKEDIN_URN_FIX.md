# 🔧 LinkedIn URN Format Issue

## Problem
LinkedIn API v2 UGC Posts endpoint expects:
- `urn:li:organization:\d+` (company ID)
- `urn:li:member:\d+` (member ID)

But we're sending:
- `urn:li:person:JFkdUz5Dwg` (person format - NOT accepted)

## Error
```
422: /author :: "urn:li:person:JFkdUz5Dwg" does not match urn:li:company:\d+|urn:li:member:\d+
```

## Solution

We need to extract the numeric member ID from your LinkedIn profile/member ID.

### Option 1: Get Member ID from LinkedIn Profile
1. Go to https://www.linkedin.com/me/
2. In your browser's Network tab, look for API calls
3. Find your numeric member ID (e.g., `12345678`)
4. Update .env:
```
LINKEDIN_PERSON_URN=urn:li:member:12345678
```

### Option 2: Use Organization (Company) ID
If you want to post as a company/page:
```
LINKEDIN_PAGE_ID=12345678
```

### How to Find Your Member ID
1. Visit https://api.linkedin.com/v2/me (requires auth)
2. Or use LinkedIn's member lookup endpoint
3. Or manually extract from API responses in Network tab

## Temporary Workaround
For now, the system is correctly:
- ✅ Processing posts
- ✅ Moving files to Done
- ✅ Logging detailed errors
- ⚠️ Not posting (due to URN format)

## Next Steps
Provide your LinkedIn numeric member ID or organization ID, and we'll update the URN format!

