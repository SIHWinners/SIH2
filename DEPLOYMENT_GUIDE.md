# Comprehensive Deployment Guide: Oil India Digital Twin (SIH26120)
**Optimized for GitHub Student Developer Pack & Production Cloud Hosting**

This guide provides step-by-step instructions on where and how to deploy the entire Digital Twin architecture (FastAPI Backend, React Vite Frontend, Machine Learning Models, and PostgreSQL Database) with zero cost using your **GitHub Student Developer Pack**.

---

## 🎓 GitHub Student Developer Pack: Free Cloud Credits

Your GitHub Student Developer Pack includes:
- **DigitalOcean**: **$200 in platform credit** valid for 1 year (Ideal for running the complete Docker stack on a Droplet or App Platform).
- **Microsoft Azure for Students**: **$100 annual credit** with no credit card required + free tier services (Azure App Services, Container Apps, and Flexible PostgreSQL).
- **Heroku**: **$13/month in platform credits** for 12 months.
- **Namecheap / Name.com**: **Free `.me` or `.live` domain** + free SSL certificate for 1 year for your hackathon prototype URL!
- **GitHub Pages / Actions**: Unlimited public repo CI/CD minutes.

---

## 🏆 Recommended Deployment Strategies

| Strategy | Frontend | Backend API | Database | Difficulty | Cost with Student Pack | Best For |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Option A (Fastest & Zero Setup)** | **Vercel** | **Render / Railway** | **Neon / Supabase** | Easy (10 mins) | **$0 / Free** | Instant demo for hackathon judges |
| **Option B (All-in-One Docker Stack)** | **DigitalOcean** | **DigitalOcean** | **PostgreSQL (Docker)** | Medium (15 mins) | **$0** (uses $200 credit) | Enterprise unified production host |
| **Option C (Azure for Students)** | **Azure Web App** | **Azure Container App** | **Azure PostgreSQL** | Medium (20 mins) | **$0** (uses $100 credit) | Enterprise corporate cloud evaluation |

---

## ⚡ Option A: Vercel (Frontend) + Render (Backend & DB) [100% Free & Turnkey]

Both Render and Vercel connect directly to your GitHub repository `https://github.com/SIHWinners/SIH2` and automatically redeploy whenever you push code!

### Step 1: Deploy Backend & Database on Render (1-Click via Blueprint)
1. Go to **[dashboard.render.com](https://dashboard.render.com)** and log in with your GitHub account.
2. Click the **"New +"** button $\rightarrow$ Select **"Blueprint"**.
3. Select your repository: **`SIHWinners/SIH2`**.
4. Render will automatically detect the **[`render.yaml`](file:///c:/Users/SNEH/Desktop/SIH2/render.yaml)** file we created! It will automatically:
   - Provision a free managed **PostgreSQL database** (`oil-india-postgres`).
   - Wire the `DATABASE_URL` connection string automatically.
   - Install all Python dependencies from `requirements.txt`.
   - Start the FastAPI backend server (`oil-india-digital-twin-api`).
5. Click **"Apply"**.
6. Once deployed (typically 2-3 minutes), Render will display your live public API URL:
   - Example: `https://oil-india-digital-twin-api.onrender.com`
   - Test it by opening: `https://oil-india-digital-twin-api.onrender.com/api/v1/health`

### Step 2: Deploy React Frontend on Vercel
1. Go to **[vercel.com](https://vercel.com)** and log in with your GitHub account.
2. Click **"Add New..."** $\rightarrow$ **"Project"**.
3. Import your repository: **`SIHWinners/SIH2`**.
4. Configure the project:
   - **Framework Preset:** `Vite`
   - **Root Directory:** Click "Edit" and select **`web`**
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
5. Expand **"Environment Variables"** and add:
   - **Key:** `VITE_API_URL`
   - **Value:** `https://oil-india-digital-twin-api.onrender.com` *(your Render API URL from Step 1)*
6. Click **"Deploy"**.
7. In ~45 seconds, your live React Digital Twin will be live at:
   - **`https://sih2-yourname.vercel.app`**

---

## 🐳 Option B: All-in-One DigitalOcean Droplet with Docker Compose

Using your **$200 DigitalOcean Student Credit**, you can host the entire Docker stack (PostgreSQL + FastAPI + React Frontend) on an Ubuntu VM.

### Step 1: Create a DigitalOcean Droplet
1. Go to [cloud.digitalocean.com](https://cloud.digitalocean.com) and claim your Student Pack credits.
2. Click **Create** $\rightarrow$ **Droplets**.
3. Choose:
   - **Image:** Ubuntu 22.04 LTS (or Marketplace $\rightarrow$ Docker on Ubuntu)
   - **Plan:** Basic ($12/month, 2 GB RAM / 1 vCPU — fully covered by your credit)
   - **Datacenter:** Bangalore (`BLR1`) for ultra-low latency in India!
   - **Authentication:** SSH Key or Root Password.
4. Click **Create Droplet** and note your public IP (e.g., `159.65.150.12`).

### Step 2: SSH into Server and Deploy
Open your terminal and run:

```bash
# 1. Connect to your Droplet
ssh root@YOUR_DROPLET_IP

# 2. Update and install Docker & Docker Compose (if not pre-installed)
apt update && apt upgrade -y
apt install -y docker.io docker-compose git

# 3. Clone your repository
git clone https://github.com/SIHWinners/SIH2.git
cd SIH2

# 4. Start all 3 containers (PostgreSQL, FastAPI, React/Streamlit)
docker-compose up -d --build
```

### Step 3: Verify Running Services
```bash
docker-compose ps
```

Your services are now accessible at:
- React / Streamlit Dashboard: `http://YOUR_DROPLET_IP:8501` (or port `5173`)
- FastAPI Backend: `http://YOUR_DROPLET_IP:8000`
- Interactive Swagger API: `http://YOUR_DROPLET_IP:8000/docs`

---

## ☁️ Option C: Microsoft Azure for Students ($100 Credit)

1. Activate your **Azure for Students** subscription via your academic `.edu` / university email at [azure.microsoft.com/free/students](https://azure.microsoft.com/free/students).
2. Create an **Azure Container App** or **Azure App Service (Linux)**.
3. Under Deployment Center, select **GitHub Actions** and connect `SIHWinners/SIH2`.
4. Configure Azure Database for PostgreSQL (Flexible Server, Free B1ms instance).

---

## 🔒 Production Environment Variables Reference

| Variable | Recommended Value (Production) | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | `postgresql://user:pass@host:5432/dbname` | PostgreSQL connection URI |
| `API_BASE_URL` | `https://your-api-domain.com` | Base URL used by the frontend to reach FastAPI |
| `FIELD_NAME` | `Oil India Limited - Baghewala Asset` | Display asset name |
| `PORT` | `8000` | Port listened by Uvicorn |
| `SIMULATOR_INTERVAL_SECONDS` | `3.0` | Cadence for background SCADA tick simulation |

---

## 🎯 Smart India Hackathon Demo Checklist

Before presenting to the judges:
- [ ] Ensure database is seeded with historical telemetry (`python scripts/seed_demo_data.py`).
- [ ] Verify `/api/v1/health` returns `{"status": "online"}`.
- [ ] Open the React Web App (`http://127.0.0.1:5173` or your production domain).
- [ ] Test the **AI Copilot** drawer by asking: *"Why is SRP-004 in critical status?"*.
- [ ] Show the animated **Dynamometer Card** and **Sucker Rod Pump nodding donkey**.
- [ ] Display the **Thar Desert live weather integration** pill.
- [ ] Test the **What-If Sandbox** with the *"Fluid Pound Attack"* preset.
