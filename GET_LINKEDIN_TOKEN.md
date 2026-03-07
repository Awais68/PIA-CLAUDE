# LinkedIn OAuth Token Setup (5 minutes)

## Step 1: Create LinkedIn App
1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/apps)
2. Click **Create app**
3. Fill in:
   - **App name**: Zoya LinkedIn Poster
   - **Company**: (your company)
   - **Legal agreement**: Check ✅
4. Click **Create app**

## Step 2: Get Client ID & Secret
1. Go to your app's **Auth** tab
2. Copy:
   - **Client ID** → `LINKEDIN_CLIENT_ID`
   - **Client Secret** → `LINKEDIN_CLIENT_SECRET`

## Step 3: Set Redirect URI
1. In **Auth** tab → **Authorized redirect URLs**
2. Add: `http://localhost:8888/callback`
3. Save

## Step 4: Get Access Token
Run this script:
```bash
python3 get_linkedin_token.py
```

This opens a browser → you login → redirected back with token.

## Step 5: Get Your Person URN
The script automatically extracts it! Or manually:
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  https://api.linkedin.com/v2/me | grep -o '"id":"[^"]*"'
```

## Step 6: Update .env
```bash
LINKEDIN_CLIENT_ID=your_client_id_here
LINKEDIN_CLIENT_SECRET=your_client_secret_here
LINKEDIN_ACCESS_TOKEN=your_access_token_here
LINKEDIN_PERSON_URN=urn:li:person:YOUR_PERSON_ID
LINKEDIN_DRY_RUN=false
```

## Step 7: Test
```bash
python3 src/linkedin_poster.py
```

---

⏱️ **Total time**: ~5 minutes
🔐 **Token expires**: 2 months (auto-refresh via refresh token coming soon)
