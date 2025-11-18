# Azure Service Tags Tracker - MongoDB Integration Setup

## Quick Start Guide

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Your MongoDB Atlas connection string
MONGODB_URI=mongodb+srv://eliaquimbrandao_db_user:<password>@azure-tracker-01.ruwra7j.mongodb.net/?appName=azure-tracker-01

# SendGrid API Key (get from https://app.sendgrid.com/)
SENDGRID_API_KEY=your_sendgrid_api_key

# Email settings
FROM_EMAIL=noreply@your-domain.com
FROM_NAME=Azure Service Tags Tracker

# App URL
APP_URL=https://eliaquimbrandao.github.io/azure-service-tags-tracker-dev
```

**Important:** Replace `<password>` in MONGODB_URI with your actual database password!

### 3. Test MongoDB Connection

```bash
python scripts/test_mongodb.py
```

This will:
- Test database connection
- Create indexes
- Verify subscription manager
- Check email service configuration

### 4. Update Frontend JavaScript

The frontend (`docs/js/subscription.js`) needs to be updated to call an API endpoint instead of using localStorage. You have two options:

#### Option A: GitHub Pages + Serverless Function (Recommended)
- Use Vercel/Netlify serverless functions
- Deploy API endpoints separately

#### Option B: Direct MongoDB from Browser (Not Recommended)
- Requires MongoDB Data API
- Exposes database to client-side

**I recommend Option A** - I can help you set this up next!

### 5. Add GitHub Secrets

Go to your repository: Settings → Secrets and variables → Actions

Add these secrets:
- `MONGODB_URI` - Your MongoDB connection string
- `SENDGRID_API_KEY` - Your SendGrid API key

### 6. Update GitHub Actions Workflow

The workflow (`.github/workflows/update-data.yml`) will be updated to:
1. Detect changes in Azure Service Tags
2. Query MongoDB for active subscribers
3. Send email notifications automatically

## Database Schema

### Subscriptions Collection

```javascript
{
  id: "sub_abc123...",                    // Unique subscription ID
  email: "user@example.com",              // User's email
  email_hash: "sha256_hash",              // Hashed email for analytics
  subscriptionType: "all" | "filtered",   // Subscription type
  selectedServices: ["service1", ...],    // Selected services (if filtered)
  selectedRegions: ["eastus", ...],       // Selected regions (if filtered)
  timestamp: "2025-11-18T10:30:00Z",      // ISO 8601 timestamp
  status: "active" | "unsubscribed",      // Subscription status
  unsubscribe_token: "64-char-hex",       // Secure unsubscribe token
  created_at: ISODate("2025-11-18"),      // Creation date
  updated_at: ISODate("2025-11-18")       // Last update date
}
```

## Testing

### Test Database Connection
```bash
python scripts/test_mongodb.py
```

### Send Test Notifications (requires changes detected)
```bash
python scripts/send_notifications.py
```

## Next Steps

1. ✅ MongoDB Atlas cluster created
2. ✅ Python integration files created
3. ⏳ Install dependencies: `pip install -r requirements.txt`
4. ⏳ Configure `.env` file with your credentials
5. ⏳ Test connection: `python scripts/test_mongodb.py`
6. ⏳ Update frontend to call API endpoints
7. ⏳ Set up serverless functions (Vercel/Netlify)
8. ⏳ Configure GitHub Actions with secrets
9. ⏳ Deploy and test end-to-end

## Security Notes

- Never commit `.env` file (already in `.gitignore`)
- Use GitHub Secrets for production credentials
- MongoDB connection uses TLS encryption
- Unsubscribe tokens are cryptographically secure (64 characters)
- Email addresses are hashed for analytics
- Network access controlled via IP whitelist

## Support

If you encounter issues:
1. Check `.env` file configuration
2. Verify MongoDB Atlas network access (0.0.0.0/0)
3. Confirm database user has read/write permissions
4. Run test script to diagnose: `python scripts/test_mongodb.py`
