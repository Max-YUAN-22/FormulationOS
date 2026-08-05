# Render Deployment Debug Guide

## Current Issue
Render deployment showing old version despite multiple manual deploys.

## Verification Checklist

### 1. Confirm GitHub has latest code
```bash
# Check latest commit
git log --oneline -3
# Expected: 9b908f2 Add version identifier (v3.5.1)

# Verify on GitHub
curl -s "https://raw.githubusercontent.com/Max-YUAN-22/FormulationOS/main/FormulationOS_Enterprise.py" | grep "__version__"
# Expected: __version__ = "3.5.1"
```

### 2. Check Render Dashboard
- Go to https://dashboard.render.com/
- Find `formulationos` service
- Check "Events" tab - should see deploy triggered after commit 9b908f2
- Check "Logs" tab for any errors

### 3. Common Issues & Solutions

#### Issue A: Build failing silently
**Symptoms:** Old version keeps showing
**Check:** Render logs for ImportError, ModuleNotFoundError
**Solution:** Add missing dependencies to requirements.txt

#### Issue B: Render using cached build
**Symptoms:** No errors but old version persists
**Solution:** 
1. Go to Settings → Build & Deploy
2. Click "Clear build cache"
3. Manual Deploy → "Deploy latest commit"

#### Issue C: Environment variables not set
**Symptoms:** App crashes on startup, falls back to old version
**Check:** Settings → Environment Variables
**Required:**
- GPT_API_KEY (sync: false - add manually)
- GPT_BASE_URL: https://www.cun.ai/v1

#### Issue D: Wrong branch deployed
**Symptoms:** Code looks correct on GitHub but wrong on Render
**Check:** Settings → Build & Deploy → Branch
**Expected:** main

### 4. Force Clean Deploy
If all else fails:
1. Delete the service on Render
2. Create new service from GitHub repo
3. Configure environment variables
4. Deploy

### 5. Version Verification
Once deployed, check https://formulationos.onrender.com/
- Title should show "🧬 FormulationOS v3.5.1"
- If version shows, code is loading correctly
- If still old version, the problem is build-level not code-level

## Latest Commits
- 9b908f2: Add version identifier v3.5.1
- 2172c87: Add missing agent modules
- ebed597: Upgrade with detailed platform descriptions

## Expected Features in v3.5.1
✅ PreformulationAI (5 modules) detailed descriptions
✅ FormulationAI (7 modules) detailed descriptions  
✅ Knowledge Base with 4 tabs:
   - 🧪 Drug Database (BCS Classification)
   - 💊 Formulation Strategies
   - 📚 Literature Intelligence
   - 💾 Training Data
✅ Research page (Multi-agent roadmap)
✅ Version number display

## What to Tell User
After checking Render dashboard:
1. Report which commit Render is actually deploying
2. Share any error messages from logs
3. Confirm environment variables are set
4. Check if build cache needs clearing
