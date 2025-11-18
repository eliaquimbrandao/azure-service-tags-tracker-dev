# GitHub Secrets Configuration

To enable automated email notifications, you need to configure the following secrets in your GitHub repository.

## Required Secrets

Go to **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

### 1. `MONGODB_URI`

Your MongoDB Atlas connection string.

**Format:**
```
mongodb+srv://username:password@cluster.mongodb.net/?appName=your-app
```

**How to get it:**
1. Go to MongoDB Atlas Dashboard
2. Click **Connect** on your cluster
3. Choose **Connect your application**
4. Copy the connection string
5. Replace `<password>` with your actual password

---

### 2. `SENDGRID_API_KEY`

Your SendGrid API key for sending emails.

**Format:**
```
SG.xxxxxxxxxxxxxxxxxxxxxxxx.yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
```

**How to get it:**
1. Log in to [SendGrid](https://app.sendgrid.com/)
2. Go to **Settings** → **API Keys**
3. Click **Create API Key**
4. Name it (e.g., "Azure Service Tags Tracker")
5. Select **Full Access** or **Restricted Access** with Mail Send permissions
6. Copy the API key (you'll only see it once!)

---

### 3. `FROM_EMAIL`

The verified sender email address for notifications.

**Format:**
```
noreply@your-domain.com
```

**Requirements:**
- Must be verified in SendGrid
- Should match your domain authentication setup
- Use a no-reply or notifications address

**How to set up:**
1. Go to SendGrid → **Settings** → **Sender Authentication**
2. Authenticate your domain
3. Add DNS records (CNAME, TXT) to your domain provider
4. Use an email from that domain

---

### 4. `FROM_NAME`

Display name that appears in email "From" field.

**Format:**
```
Azure Service Tags Tracker [DEV]
```

**Example values:**
- `Azure Service Tags Tracker`
- `Azure IP Monitor`
- `Your Company - Azure Updates`

---

## Verification

After adding all secrets, they should appear in:
**Settings** → **Secrets and variables** → **Actions** → **Repository secrets**

You should see:
- ✅ `MONGODB_URI`
- ✅ `SENDGRID_API_KEY`
- ✅ `FROM_EMAIL`
- ✅ `FROM_NAME`

## Testing the Workflow

Once secrets are configured:

1. Go to **Actions** tab
2. Select **Update Azure Service Tags** workflow
3. Click **Run workflow**
4. ✅ Check **"Setup initial baseline (first run)"** (if first time)
5. Click **Run workflow**

The workflow will:
1. Download Azure Service Tags data
2. Detect changes (if any)
3. Commit to repository
4. Deploy to GitHub Pages
5. **Send email notifications** to all subscribers

## Troubleshooting

### Emails not sending?

**Check workflow logs:**
1. Go to **Actions** tab
2. Click on the latest workflow run
3. Expand **"Send Email Notifications to Subscribers"** step
4. Look for error messages

**Common issues:**
- ⚠️ `MONGODB_URI not configured` - Secret not set or empty
- ⚠️ `SENDGRID_API_KEY not configured` - Secret not set or empty
- ❌ `Failed to connect to database` - Check MongoDB connection string format
- ❌ `Authentication failed` - Check SendGrid API key validity
- ❌ `From email not verified` - Verify sender email in SendGrid

### Test locally first

Before relying on GitHub Actions, test locally:

```bash
# Create .env file with your credentials
cp .env.example .env
# Edit .env with your actual values

# Run notification script
python scripts/send_notifications.py
```

## Security Notes

🔒 **Never commit secrets to the repository!**

- Secrets are encrypted by GitHub
- They're only available during workflow execution
- They won't appear in logs or pull requests
- Rotate your keys regularly for security

## Email Preview

Subscribers will receive emails that look like this:

**Subject:** 🔔 Azure Service Tags Updated - X Services Changed

**Content:**
- Change summary with total services affected
- List of top 20 changed services with added/removed IP counts
- Link to view full change history on dashboard
- Manage subscription link (unsubscribe)

**Design:**
- Professional gradient header (purple theme)
- Responsive layout (mobile-friendly)
- Clear call-to-action buttons
- Service change details in organized cards

---

## Next Steps

After configuring secrets:

1. ✅ Test the workflow manually (Actions → Run workflow)
2. ✅ Check that emails are received
3. ✅ Verify unsubscribe links work
4. ✅ Wait for next Monday at midnight UTC for automatic run

The workflow runs **every Monday at 00:00 UTC** automatically.
