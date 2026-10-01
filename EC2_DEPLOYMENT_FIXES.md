# EC2 Deployment Fixes

## Issues Identified

1. **Frontend API URL:** Hardcoded to localhost instead of EC2 IP
2. **Deployment Method:** Inconsistent (Docker frontend + direct Python backend)
3. **Disk Space:** 8GB EBS volume too small for Docker images
4. **API Keys:** Using development keys on production

---

## Fixes Applied

### 1. Frontend API URL Updated ✅

**File:** `frontend/src/components/UserProfileForm.tsx`

**Change:**
- Before: `http://localhost:8000/api/tavily/orchestrate`
- After: `http://13.62.229.119:8000/api/tavily/orchestrate`

---

### 2. Backend Fixes Applied ✅

**Files Updated:**
- `backend/app/services/eligibility_engine_v2.py` - String-to-list conversions, error handling
- `backend/app/services/tavily_search.py` - Domain filtering for social media, dictionaries
- `backend/app/api/routes_tavily.py` - Fixed API route to return correct results key
- `backend/main.py` - Unbuffered output for logs
- `backend/app/agents/scholarship_orchestrator.py` - Full orchestration enabled

**Key Changes:**
- Added string-to-list conversion for category, education, year, state comparisons
- Added domain filtering to exclude Facebook, Instagram, Wikipedia, etc.
- Fixed API route to return "results" instead of "final_results"
- Added full traceback logging for eligibility engine errors
- Enabled full orchestration pipeline (not simplified)

---

**File:** `frontend/src/components/UserProfileForm.tsx`

**Change:**
- Before: `http://localhost:8000/api/tavily/orchestrate`
- After: `http://13.62.229.119:8000/api/tavily/orchestrate`

---

## Deployment Steps

### Step 1: Commit All Changes on Windows

**On Windows:**

```bash
cd C:\Users\DELL\Desktop\eligiblAI
git add .
git commit -m "Deploy to EC2: frontend API URL fix, backend eligibility fixes, Tavily domain filtering"
git push origin main
```

This will commit:
- Frontend API URL change (localhost → EC2 IP)
- Frontend query construction improvement
- Backend eligibility engine fixes (string-to-list conversions)
- Backend Tavily domain filtering
- Backend API route fix
- Backend unbuffered output

---

### Step 2: Update Backend Code on EC2

**On EC2:**

```bash
cd ~/EligibAI/backend
git pull origin main
```

---

### Step 3: Restart Backend on EC2

**On EC2:**

```bash
pkill -f "python3 main.py"
cd ~/EligibAI/backend
nohup python3 main.py > backend.log 2>&1 &
```

---

### Step 4: Rebuild and Push Frontend Image

**On Windows:**

```bash
cd C:\Users\DELL\Desktop\eligiblAI\frontend
docker build -t pushwanthdharavath/eligibai-frontend:latest .
docker push pushwanthdharavath/eligibai-frontend:latest
```

```bash
cd C:\Users\DELL\Desktop\eligiblAI\frontend
docker build -t pushwanthdharavath/eligibai-frontend:latest .
docker push pushwanthdharavath/eligibai-frontend:latest
```

---

### Step 5: Pull and Restart Frontend on EC2

**On EC2:**

```bash
docker pull pushwanthdharavath/eligibai-frontend:latest
docker stop frontend
docker rm frontend
docker run -d -p 3000:3000 --name frontend pushwanthdharavath/eligibai-frontend:latest
```

---

### Step 6: Verify Backend is Running on EC2

**On EC2:**

```bash
ps aux | grep python3
```

Should show backend process running.

If not running:

```bash
cd ~/EligibAI/backend
nohup python3 main.py > backend.log 2>&1 &
```

---

### Step 7: Test Application

**In Browser:**

1. Go to: `http://13.62.229.119:3000`
2. Fill out the form
3. Click "Search Scholarships"
4. Verify results appear

---

## Recommended Deployment Strategy

### ✅ Recommended: Docker Frontend + Direct Backend (No Cost)

**Frontend:** Docker container
**Backend:** Direct Python execution (not Docker)

**Pros:**
- ✅ Saves disk space (no backend Docker image)
- ✅ Faster deployment
- ✅ Works with 8GB disk
- ✅ No additional AWS cost
- ✅ Reliable and tested

**Cons:**
- ⚠️ Inconsistent deployment method (Docker vs direct)
- ⚠️ Harder to scale in future

**Commands:**

```bash
# Backend (direct execution)
cd ~/EligibAI/backend
nohup python3 main.py > backend.log 2>&1 &

# Frontend (Docker)
docker run -d -p 3000:3000 --name frontend pushwanthdharavath/eligibai-frontend:latest
```

---

### 🔮 Future Option: Full Docker (Requires EBS Resize)

**Frontend:** Docker container
**Backend:** Docker container

**Pros:**
- ✅ Consistent deployment
- ✅ Easier to scale
- ✅ Better isolation

**Cons:**
- ❌ Requires more disk space (backend image ~3GB)
- ❌ 8GB disk is too small
- ❌ Costs ~$1-2/month extra for 20GB EBS

**Requirements:**
- Resize EBS from 8GB to 20GB
- Then use Docker for both

**Commands:**

```bash
# Backend (Docker)
docker run -d -p 8000:8000 --env-file ~/EligibAI/.env --name backend pushwanthdharavath/eligibai-backend:latest

# Frontend (Docker)
docker run -d -p 3000:3000 --name frontend pushwanthdharavath/eligibai-frontend:latest
```

---

### 📋 How to Resize EBS (For Future Full Docker Deployment)

**Steps:**

1. Go to AWS Console → EC2 → Volumes
2. Select the volume attached to your instance
3. Actions → Modify Volume
4. Increase size from 8GB to 20GB or more
5. Extend filesystem on EC2:

```bash
# On EC2
sudo growpart /dev/nvme0n1 1
sudo xfs_growfs /
```

Then use Option B (Full Docker).

---

## Production API Keys

### Current Issue

Development API keys are being used on production:
- Gemini free tier (20 requests/day limit)
- Development Tavily key

### Solution

1. **Upgrade Gemini to Paid Plan:**
   - Go to Google AI Studio
   - Upgrade to paid plan
   - Remove 20 requests/day limit
   - Get production API key

2. **Configure Production Keys on EC2:**

```bash
# On EC2
nano ~/EligibAI/.env
```

Add:
```bash
GEMINI_API_KEY=your-production-gemini-key
TAVILY_API_KEY=your-production-tavily-key
OPENAI_API_KEY=your-production-openai-key
```

3. **Restart Backend:**

```bash
pkill -f "python3 main.py"
cd ~/EligibAI/backend
nohup python3 main.py > backend.log 2>&1 &
```

---

## Monitoring

### Check Backend Logs

```bash
tail -f ~/EligibAI/backend/backend.log
```

### Check Frontend Logs

```bash
docker logs -f frontend
```

### Check Disk Space

```bash
df -h
```

### Check Docker Space

```bash
docker system df
```

---

## Security Considerations

1. **Never commit .env files** to Git
2. **Use production API keys** for production deployment
3. **Rotate API keys** if they were exposed
4. **Use HTTPS** in production (configure SSL with Let's Encrypt)
5. **Restrict security group** to allow only necessary ports

---

## Troubleshooting

### Frontend Shows "Failed to Fetch"

- Check if backend is running: `ps aux | grep python3`
- Check if port 8000 is accessible: `curl http://localhost:8000/health`
- Check security group: Port 8000 should be open

### Backend Not Starting

- Check logs: `tail -f ~/EligibAI/backend/backend.log`
- Check dependencies: `pip list`
- Check .env file: Ensure API keys are set

### Out of Disk Space

- Clean Docker: `docker system prune -a --volumes`
- Clean cache: `rm -rf ~/.cache`
- Resize EBS volume (see Option C above)

---

## Summary

### ✅ Recommended Deployment (Current - No Cost)

**For 8GB EC2 Instance:**
- **Frontend:** Docker container
- **Backend:** Direct Python execution
- **API Keys:** Development keys (upgrade to production later)
- **Security:** Basic (add SSL later)
- **Cost:** $0 additional (uses existing t3.micro)

**Why This Approach:**
- Works with current 8GB disk
- No additional AWS cost
- Reliable and tested
- Fast deployment

---

### 🔮 Future Upgrade Path (When Ready)

**For Production Scaling:**
- **Resize EBS:** 8GB → 20GB (~$1-2/month)
- **Deployment:** Full Docker (both frontend and backend)
- **API Keys:** Production Gemini/OpenAI keys
- **Security:** SSL with Let's Encrypt
- **Monitoring:** Add Prometheus/Grafana
- **Auto-scaling:** Add load balancer

**Estimated Cost:** ~$10-20/month (t3.micro + 20GB EBS + API usage)

---

### 🎯 Immediate Action Items

1. ✅ **Commit and push all changes** (Windows)
2. ✅ **Update backend on EC2** (git pull)
3. ✅ **Restart backend on EC2** (direct Python)
4. ✅ **Build and push frontend image** (Windows)
5. ✅ **Pull and restart frontend on EC2** (Docker)
6. ✅ **Test application** (browser)

**No EBS resize needed for now.**
