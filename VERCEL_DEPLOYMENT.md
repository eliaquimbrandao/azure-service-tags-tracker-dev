# Vercel Deployment Guide

## Quick Deploy to Vercel

### 1. Install Vercel CLI (Optional)
```bash
npm install -g vercel
```

### 2. Deploy via Vercel Dashboard (Recommended)

1. **Sign up/Login to Vercel**
   - Go to https://vercel.com/signup
   - Sign up with GitHub

2. **Import Your Repository**
   - Click "Add New" → "Project"
   - Select your GitHub repository: `azure-service-tags-tracker`
   - Click "Import"

3. **Configure Project Settings**
   - **Framework Preset**: Other
   - **Root Directory**: `./`
   - **Build Command**: (leave empty)
   - **Output Directory**: (leave empty)
   - **Install Command**: `pip install -r requirements-api.txt`

4. **Add Environment Variables**
   Click "Environment Variables" and add:
   
   - `MONGODB_URI`
     ```
     mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority
     ```
     ⚠️ **Replace with your actual MongoDB connection string from `.env` file**
   
   - `SENDGRID_API_KEY`
     ```
     SG.xxxxxxxxxxxxxxxxxxxxx.yyyyyyyyyyyyyyyyyyyyyyyyyyyy
     ```
     ⚠️ **Replace with your actual SendGrid API key**
   
   - `FROM_EMAIL`
     ```
     noreply@your-domain.com
     ```
   
   - `FROM_NAME`
     ```
     Azure Service Tags Tracker [DEV]
     ```
   
   - `APP_URL`
     ```
     https://eliaquimbrandao.github.io/azure-service-tags-tracker-dev
     ```

5. **Deploy**
   - Click "Deploy"
   - Wait for deployment to complete (~2 minutes)
   - Your API will be live at: `https://your-project-name.vercel.app`

### 3. Update Frontend with Vercel URL

After deployment, update `docs/js/subscription.js`:

```javascript
this.apiBaseUrl = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:3000'
    : 'https://YOUR-VERCEL-PROJECT.vercel.app';  // ← Update this!
```

### 4. Test Your API Endpoints

**Subscribe Endpoint:**
```bash
curl -X POST https://YOUR-VERCEL-PROJECT.vercel.app/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "subscriptionType": "all",
    "selectedServices": [],
    "selectedRegions": []
  }'
```

**Unsubscribe Endpoint:**
```bash
curl -X GET "https://YOUR-VERCEL-PROJECT.vercel.app/api/unsubscribe?email=test@example.com&token=YOUR_TOKEN"
```

### 5. Commit and Push Changes

```bash
git add .
git commit -m "Add Vercel serverless API for subscriptions"
git push origin main
```

Vercel will automatically redeploy on every push to main!

## Alternative: Deploy via CLI

```bash
# Login to Vercel
vercel login

# Deploy
cd c:\Users\ebrandao\gitlab\azure-service-tags-tracker
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name? azure-service-tags-tracker
# - Directory? ./
# - Override settings? No

# Add environment variables
vercel env add MONGODB_URI
vercel env add SENDGRID_API_KEY
vercel env add FROM_EMAIL
vercel env add FROM_NAME
vercel env add APP_URL

# Deploy to production
vercel --prod
```

## Troubleshooting

### CORS Errors
If you see CORS errors, the API already includes proper headers for GitHub Pages. Make sure your GitHub Pages URL matches the one in the CORS configuration.

### MongoDB Connection Errors
- Verify MongoDB Atlas network access allows `0.0.0.0/0`
- Check that environment variables are set correctly in Vercel dashboard
- Ensure connection string includes database name and proper encoding

### API Not Responding
- Check Vercel deployment logs in the dashboard
- Verify `vercel.json` is in the root directory
- Ensure `requirements-api.txt` exists and has all dependencies

## Project Structure

```
azure-service-tags-tracker/
├── api/
│   ├── subscribe.py          # Subscribe endpoint (Vercel Function)
│   ├── unsubscribe.py         # Unsubscribe endpoint (Vercel Function)
│   ├── db_config.py           # MongoDB configuration
│   ├── subscription_manager.py # Subscription logic
│   └── email_service.py       # Email sending
├── docs/                       # GitHub Pages site
│   └── js/
│       └── subscription.js    # Frontend (calls Vercel API)
├── vercel.json                 # Vercel configuration
└── requirements-api.txt        # Python dependencies
```

## Next Steps

1. Deploy to Vercel
2. Get your Vercel URL (e.g., `https://azure-service-tags-tracker.vercel.app`)
3. Update `docs/js/subscription.js` with your Vercel URL
4. Commit and push
5. Test subscription form on GitHub Pages
6. Set up SendGrid for email sending (optional)
