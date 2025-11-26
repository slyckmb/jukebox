# Cloudflare Access Setup for Jukebox

**Purpose**: Add OAuth authentication layer via Cloudflare Zero Trust to protect jukebox.bikejeepyoga.com

**Last Updated**: 2025-11-23

---

## Overview

Cloudflare Access provides an additional authentication layer before users reach the Jukebox login page. This creates defense-in-depth:

1. **Cloudflare OAuth** → Validates user identity via Google/GitHub/Email
2. **Jukebox Login** → Application-level authentication with username/password

---

## Option 1: Manual Configuration (Quick Setup - 5-10 minutes)

### Prerequisites
- Access to Cloudflare dashboard
- Zero Trust account enabled (free tier available)
- Admin access to bikejeepyoga.com domain

### Steps

#### 1. Access Zero Trust Dashboard
1. Log into Cloudflare dashboard: https://dash.cloudflare.com
2. Select your account
3. Navigate to **Zero Trust** (left sidebar)
4. If prompted, enable Zero Trust (free tier is sufficient)

#### 2. Configure Identity Provider (One-time setup)
1. Go to **Settings → Authentication**
2. Click **Add new** under "Login methods"
3. Choose your preferred provider:
   - **Google**: Free, easy setup, good for personal/family use
   - **GitHub**: Good for developers
   - **One-time PIN**: Email-based, no OAuth required
   - **Okta/Azure AD**: Enterprise options
4. Follow provider-specific setup (usually just OAuth client ID/secret)
5. Click **Save**

#### 3. Create Access Application for Jukebox
1. Navigate to **Access → Applications**
2. Click **Add an application**
3. Select **Self-hosted**
4. Configure application:
   - **Application name**: `Jukebox`
   - **Session Duration**: `24h` (or your preference)
   - **Application domain**:
     - Subdomain: `jukebox`
     - Domain: `bikejeepyoga.com`
   - Click **Next**

#### 4. Create Access Policy
1. **Add a policy**:
   - **Policy name**: `Allow Authorized Users`
   - **Action**: `Allow`
   - **Session duration**: `24h`

2. **Configure Include rules** (choose one or combine):

   **Option A: Specific Emails**
   - Rule type: `Emails`
   - Enter email addresses: `user1@example.com`, `user2@example.com`

   **Option B: Email Domain**
   - Rule type: `Emails ending in`
   - Enter domain: `@yourdomain.com`

   **Option C: Everyone (not recommended)**
   - Rule type: `Everyone`
   - Note: Only use for testing, not production

3. Click **Next**

#### 5. Additional Settings (Optional but Recommended)
1. **Enable automatic HTTPS rewrites**: `On`
2. **Enable browser rendering**: `On`
3. **CORS settings**: Leave as default
4. Click **Add application**

#### 6. Verify Configuration
1. Open incognito/private browser window
2. Navigate to `https://jukebox.bikejeepyoga.com`
3. You should be redirected to Cloudflare Access login
4. Authenticate with your chosen provider
5. After successful OAuth, you should see the Jukebox login page
6. Log in with your Jukebox credentials (second authentication layer)

---

## Option 2: Automated Configuration via CLI/API

### Prerequisites
- Cloudflare Zero Trust API token (see "Creating API Token" section below)
- Cloudflare Account ID
- `curl` and `jq` installed

### Creating Zero Trust API Token

1. Go to **Cloudflare Dashboard → My Profile → API Tokens**
2. Click **Create Token**
3. Use **Create Custom Token** template
4. Configure permissions:
   - **Account → Access: Apps and Policies → Edit**
   - **Account → Access: Organizations, Identity Providers, and Groups → Read**
5. Set **Account Resources**: `Include → Specific account → [Your Account]`
6. Click **Continue to summary**
7. Click **Create Token**
8. **Copy the token** (you won't see it again!)
9. Save to secrets file:
   ```bash
   # Create secrets file
   mkdir -p /mnt/config/secrets/cloudflare
   echo "ZERO_TRUST_TOKEN=your_token_here" > /mnt/config/secrets/cloudflare/zero-trust-token.env
   chmod 600 /mnt/config/secrets/cloudflare/zero-trust-token.env
   ```

### Get Account ID

```bash
# Source the token
source /mnt/config/secrets/cloudflare/zero-trust-token.env

# Get account ID
curl -s -X GET "https://api.cloudflare.com/client/v4/accounts" \
  -H "Authorization: Bearer ${ZERO_TRUST_TOKEN}" \
  -H "Content-Type: application/json" | jq -r '.result[0].id'

# Save it for later
export CF_ACCOUNT_ID="your_account_id_here"
```

### Run Automated Setup Script

```bash
# Navigate to cloudflared directory
cd /home/michael/dev/work/glider/glider-docker/cloudflared/bin

# Make script executable
chmod +x setup-jukebox-access.sh

# Run the script
./setup-jukebox-access.sh

# Follow prompts to configure:
# - Identity provider selection
# - Allowed emails or domains
# - Session duration
```

See `cloudflared/bin/setup-jukebox-access.sh` for script details.

---

## Verification Steps

After configuration (manual or automated):

### 1. Test OAuth Flow
```bash
# Open in private/incognito browser
# Visit: https://jukebox.bikejeepyoga.com

# Expected flow:
# 1. Cloudflare Access login page appears
# 2. Click your OAuth provider (Google/GitHub/etc)
# 3. Authenticate with OAuth provider
# 4. Redirected to Jukebox login page
# 5. Log in with Jukebox credentials
# 6. Access granted to application
```

### 2. Test Session Persistence
```bash
# In same browser (not incognito):
# 1. Close jukebox tab
# 2. Reopen https://jukebox.bikejeepyoga.com
# 3. Should NOT prompt for OAuth again (session active)
# 4. May still need Jukebox login (separate session)
```

### 3. Test Access Denial
```bash
# In incognito with unauthorized email:
# 1. Visit https://jukebox.bikejeepyoga.com
# 2. Authenticate with OAuth provider using non-allowed email
# 3. Should see "Access Denied" page
# 4. Should NOT reach Jukebox login page
```

### 4. Check Access Logs
```bash
# View authentication logs in Cloudflare dashboard:
# Zero Trust → Logs → Access

# Look for:
# - Successful authentications
# - Denied attempts
# - Session durations
```

---

## Troubleshooting

### Issue: "Access Denied" for authorized email
**Solution**:
1. Check Access policy includes the email
2. Verify identity provider is configured correctly
3. Check if email verification is required
4. Wait 1-2 minutes for policy propagation

### Issue: Redirect loop
**Solution**:
1. Check Application domain matches exactly: `jukebox.bikejeepyoga.com`
2. Ensure no conflicting Cloudflare Page Rules
3. Clear browser cookies for `*.bikejeepyoga.com`
4. Disable "Always Use HTTPS" temporarily to test

### Issue: OAuth provider error
**Solution**:
1. Verify OAuth client ID/secret in Zero Trust settings
2. Check redirect URI is whitelisted in OAuth provider
3. Ensure OAuth app is not restricted by organization policy

### Issue: Can't access Zero Trust dashboard
**Solution**:
1. Ensure your Cloudflare account has Zero Trust enabled
2. Check you have account admin permissions
3. Try accessing via direct link: https://one.dash.cloudflare.com/

---

## Security Best Practices

### Recommended Settings
- ✅ Use session duration of 8-24 hours (not longer)
- ✅ Enable "Require existing session" for sensitive actions
- ✅ Use email domain restrictions instead of "Everyone"
- ✅ Enable automatic HTTPS rewrites
- ✅ Configure CORS only if needed (default deny is safer)

### Policy Configuration
- ✅ Use explicit allow lists (specific emails or domains)
- ❌ Avoid "Everyone" rule in production
- ✅ Create separate policies for admins vs regular users (future)
- ✅ Review Access logs monthly
- ✅ Rotate OAuth client secrets annually

### Session Management
- ✅ Set reasonable session timeout (24h recommended)
- ✅ Configure "Re-authentication period" for sensitive operations
- ✅ Enable "Binding cookie" to prevent session fixation
- ✅ Use "Purpose justification" for audit trails (optional)

---

## Removing/Disabling Access

To remove Cloudflare Access (not recommended for production):

1. Navigate to **Access → Applications**
2. Find "Jukebox" application
3. Click **Delete**
4. Confirm deletion
5. Traffic will bypass OAuth and go directly to Jukebox login

---

## Integration with Jukebox

After Cloudflare Access is configured:

1. Users will authenticate twice:
   - **First**: Cloudflare OAuth (email/Google/GitHub)
   - **Second**: Jukebox login (username/password)

2. Jukebox application code requires **no changes**
   - Cloudflare Access operates transparently
   - All authentication headers are handled by Cloudflare
   - Jukebox continues to manage its own sessions

3. Optional: Extract OAuth email from headers
   - Cloudflare passes `Cf-Access-Authenticated-User-Email` header
   - Could be used for audit logging in future
   - Not currently implemented in Jukebox

---

## Related Documentation

- [Cloudflare Access Documentation](https://developers.cloudflare.com/cloudflare-one/applications/)
- [Jukebox HANDOFF-JUKEBOX.md](./HANDOFF-JUKEBOX.md)
- [Cloudflare Access API Reference](https://developers.cloudflare.com/api/operations/access-applications-list-access-applications)
- **Glider Tunnel/Access home**: `glider-docker/cloudflared/docs/README.md` (centralized tunnel + Access docs/scripts for all services)

---

## Maintenance

### Regular Tasks
- **Monthly**: Review Access logs for suspicious activity
- **Quarterly**: Review allowed emails/domains, remove inactive users
- **Annually**: Rotate OAuth client secrets
- **As needed**: Update session duration based on usage patterns

### Monitoring
- Check Access logs in Zero Trust dashboard
- Monitor failed authentication attempts
- Set up alerts for unusual patterns (available in paid tiers)

---

**Status**: Manual setup can be completed now. Automated script ready once Zero Trust API token is created.
