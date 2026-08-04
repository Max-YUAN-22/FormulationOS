# FormulationOS Deployment Guide

## 🚀 Deploy to Render

### Prerequisites
- GitHub account
- Render account (free tier available)
- API keys (GPT/Claude/MiniMax)

---

## 📋 Step-by-Step Deployment

### 1. Push to GitHub

```bash
cd /Users/Apple/FormulationOS
git add .
git commit -m "Add Render deployment configuration"
git push origin main
```

### 2. Create Render Web Service

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the **FormulationOS** repository

### 3. Configure Service

Render will auto-detect `render.yaml`. Verify settings:

- **Name:** `formulationos`
- **Environment:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `streamlit run FormulationOS_Enterprise.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true`
- **Plan:** `Free`

### 4. Set Environment Variables

Go to **Environment** tab and add:

#### Required (at least one):
```
GPT_API_KEY=sk-your-gpt-key-here
CLAUDE_API_KEY=sk-ant-your-claude-key-here
MINIMAX_API_KEY=your-minimax-key-here
```

#### Optional (Base URLs):
```
GPT_BASE_URL=https://www.cun.ai/v1
CLAUDE_BASE_URL=https://www.cun.ai
MINIMAX_BASE_URL=https://api.minimaxi.com/v1
```

#### Optional (Tool APIs):
```
PREFORMULATION_AI_API_KEY=your-key
FORMULATION_AI_API_KEY=your-key
```

### 5. Deploy

Click **"Create Web Service"**

Render will:
1. Clone your repository
2. Install dependencies
3. Start Streamlit application
4. Provide a public URL (e.g., `https://formulationos.onrender.com`)

---

## 🔧 Post-Deployment

### Access Your Application
- URL: `https://your-app-name.onrender.com`
- First load may take 30-60 seconds (free tier cold start)

### Monitor Logs
- Go to **Logs** tab in Render dashboard
- Check for any errors during startup

### Update Application
```bash
git add .
git commit -m "Update application"
git push origin main
```
Render auto-deploys on push to main branch.

---

## 📊 Database Persistence

**Note:** Render free tier has ephemeral storage. The SQLite database (`formulation_knowledge.db`) will reset on service restart.

### Options for Persistence:

#### Option A: PostgreSQL (Recommended for Production)
1. Add PostgreSQL database on Render
2. Modify code to use PostgreSQL instead of SQLite

#### Option B: External Storage
1. Use AWS S3 / Google Cloud Storage
2. Backup/restore database periodically

#### Option C: Git-based Backup
```bash
# Schedule periodic commits of database
git add formulation_knowledge.db
git commit -m "Update knowledge base"
git push
```

---

## 🐛 Troubleshooting

### Issue: Application Won't Start
**Check:**
- `requirements.txt` has all dependencies
- Environment variables are set correctly
- Logs show actual error message

### Issue: API Errors
**Check:**
- API keys are valid
- Base URLs are correct
- API rate limits not exceeded

### Issue: Database Errors
**Solution:**
- Delete `formulation_knowledge.db` (will be recreated)
- Or run: `python scripts/populate_demo_data.py`

---

## 💰 Cost Considerations

### Free Tier Limits:
- ✅ 750 hours/month
- ✅ Automatic sleep after 15min inactivity
- ✅ Wake on request (cold start ~30s)
- ❌ No persistent disk storage

### Paid Tier Benefits ($7/month):
- ✅ Always on (no cold starts)
- ✅ Persistent disk storage
- ✅ More CPU/memory
- ✅ Custom domain support

---

## 🔐 Security Notes

1. **Never commit API keys to Git**
   - Use environment variables only
   - Add `.streamlit/secrets.toml` to `.gitignore`

2. **Production Checklist:**
   - [ ] Enable XSRF protection (already in config)
   - [ ] Use HTTPS (automatic on Render)
   - [ ] Rate limiting for API calls
   - [ ] Input validation

---

## 📞 Support

- **Render Docs:** https://render.com/docs
- **Streamlit Deployment:** https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app
- **FormulationOS Issues:** Create GitHub issue

---

**Deployment Status:** ✅ Ready to deploy
**Last Updated:** 2026-08-05
