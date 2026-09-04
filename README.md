# GrowwPulse — Change-First Smart Market Watchlist for Indian Equities

> **"What meaningfully changed since I last checked, and what deserves my attention now?"**

[![Live Demo](https://img.shields.io/badge/Vercel-Live_Demo-black?style=for-the-badge&logo=vercel)](https://stock-watch-gamma.vercel.app)
[![Backend API](https://img.shields.io/badge/Render-API_Live-46E3B7?style=for-the-badge&logo=render&logoColor=black)](https://stock-watch-oabd.onrender.com/api/health)
[![API Docs](https://img.shields.io/badge/FastAPI-Swagger_Docs-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://stock-watch-oabd.onrender.com/docs)
[![Database](https://img.shields.io/badge/Supabase-PostgreSQL_Database-3ECF8E?style=for-the-badge&logo=supabase&logoColor=white)](https://supabase.com)

---

## 🌐 Live Deployments

| Component | Provider | Live URL | Description |
| :--- | :--- | :--- | :--- |
| **Frontend Web App** | **Vercel** | [stock-watch-gamma.vercel.app](https://stock-watch-gamma.vercel.app) | React + Vite UI with Realtime PostgreSQL subscriptions |
| **Backend Service** | **Render** | [stock-watch-oabd.onrender.com](https://stock-watch-oabd.onrender.com) | FastAPI cloud server with NSE & Yahoo market feeds |
| **Interactive API Docs** | **FastAPI Swagger** | [stock-watch-oabd.onrender.com/docs](https://stock-watch-oabd.onrender.com/docs) | Full interactive REST API documentation |
| **Health Check** | **Render API** | [stock-watch-oabd.onrender.com/api/health](https://stock-watch-oabd.onrender.com/api/health) | Live system status & IST market hours clock |
| **Database & Auth** | **Supabase** | `antgmodxxshcaxeqjbdj.supabase.co` | PostgreSQL with Row Level Security & Auth triggers |
| **Source Code** | **GitHub** | [Shreyya407/stock_watch](https://github.com/Shreyya407/stock_watch) | Monorepo containing backend, frontend & SQL schema |

---

## 1. Product Pitch
GrowwPulse is a modern, intelligent, change-first equity watchlist built for active retail and institutional market participants in the Indian stock market (NSE). Instead of presenting endless tables of flashing prices that create cognitive fatigue, GrowwPulse anchors your market observation against your **last visit baseline**, deterministically highlighting what changed, why it matters, and where anomalies demand your immediate focus.

```
LAST VISIT ──> WHAT CHANGED ──> WHY IT MATTERS ──> WHAT DESERVES ATTENTION
```

---

## 2. Problem
Traditional stock watchlists have critical UX and analytical flaws:
- **Noise overload:** Static lists of red/green percentage changes reset to market open or yesterday's close, offering zero context regarding what occurred *since you stepped away*.
- **No volatility context:** A 3% jump in a high-beta stock might be normal, whereas a 3% jump in a low-volatility bluechip is an anomaly.
- **Unexplained changes:** Platforms state numbers without explaining the underlying signal (volume anomaly vs price breakout vs volatility expansion).
- **Constant anxiety:** Users repeatedly refresh dashboards without knowing whether anything actually requires their attention.

---

## 3. Solution
GrowwPulse solves this with **Baseline Snapshot Intelligence**:
1. **Persistent Baseline Snapshot:** Every stock is captured at your baseline visit (price, volume, timestamp).
2. **Deterministic Attention Scoring:** A 0–100 composite score based on Price Delta, Volume Multiplier, and Volatility Expansion.
3. **Signal Explainability:** "Why am I seeing this?" provides mathematical transparency into the score without speculative narratives.
4. **Mark Current as Seen:** Users can review changes and explicitly reset their baseline when satisfied.
5. **Real-time Synchronization:** Powered by Supabase PostgreSQL Realtime channels.

---

## 4. Architecture

A clean, resilient, cloud-ready architecture:

```
┌─────────────────────────────────────────────────────────┐
│                 React + Vite Frontend                   │
│      Hosted on Vercel • Supabase Realtime Channels      │
└────────────────────────────┬────────────────────────────┘
                             │  HTTPS / JSON + Bearer JWT
                             ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI Monolith (on Render)               │
│                                                         │
│   ├── Auth (Supabase JWT Verification)                 │
│   ├── Storage (Supabase PostgreSQL Single Source)       │
│   ├── Real Market Data (NSE Primary + Yahoo Fallback)   │
│   ├── 15s In-Memory Symbol TTL Cache                    │
│   └── Analytics & Attention Scoring Engine              │
└──────────────┬───────────────────────────┬──────────────┘
               │                           │
               ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│   Supabase PostgreSQL     │   │     Live Market Data      │
│  - auth.users             │   │  - Primary: NSE India     │
│  - profiles               │   │  - Fallback: Yahoo (.NS)  │
│  - watchlists (RLS)       │   │  - Stale Cache Handling   │
│  - snapshots (RLS)        │   │  - 118 NSE Companies      │
│  - snapshot_history       │   │    Enriched with Industry │
│  - companies (Master)     │   │    & Market Cap           │
└───────────────────────────┘   └───────────────────────────┘
```

---

## 5. Analytics Formulas

### 1. Price Delta %
$$\text{PriceDeltaPct} = \left( \frac{\text{CurrentPrice} - \text{SnapshotPrice}}{\text{SnapshotPrice}} \right) \times 100$$

### 2. Absolute ₹ Change
$$\Delta ₹ = \text{CurrentPrice} - \text{SnapshotPrice}$$

### 3. Volume Multiplier
$$\text{VolumeMultiplier} = \frac{\text{CurrentVolume}}{\text{AvgVolume20D}}$$

### 4. Volatility-Adjusted Movement
$$\text{VolatilityAdjustedMovement} = \frac{|\text{PriceDeltaPct}|}{\max(\text{TypicalDailyVolatilityPct}, 0.25)}$$

### 5. Opening Gap %
$$\text{OpeningGapPct} = \left( \frac{\text{TodayOpen} - \text{PreviousClose}}{\text{PreviousClose}} \right) \times 100$$

---

## 6. Attention Score Algorithm

A transparent, deterministic formula bounded from **0 to 100**:

$$\text{AttentionScore} = \text{PriceScore (40\%)} + \text{VolumeScore (30\%)} + \text{VolatilityScore (30\%)}$$

- **Price Score (0–40 pts):** $\min\left(40.0, \frac{|\text{PriceDeltaPct}|}{4.0} \times 40\right)$
- **Volume Anomaly (0–30 pts):** $\min\left(30.0, \max\left(0.0, \frac{\text{VolumeMultiplier} - 1.0}{2.0} \times 30\right)\right)$
- **Volatility Context (0–30 pts):** $\min\left(30.0, \frac{\text{VolatilityAdjustedMovement}}{3.0} \times 30\right)$

### Attention Categories:
- **70 – 100:** `SIGNIFICANT` (Red edge glow, high urgency)
- **40 – 69:** `WORTH CHECKING` (Amber indicator, moderate deviation)
- **0 – 39:** `QUIET` (Green/subtle, stable baseline)

---

## 7. Database Schema (Supabase PostgreSQL)

Full schema available in [`backend/supabase_schema.sql`](backend/supabase_schema.sql):

- **`public.profiles`**: User profile & personalization preferences with automatic trigger on `auth.users`.
- **`public.watchlists`**: User-selected watchlist equities with Row Level Security.
- **`public.snapshots`**: Baseline snapshot records (`price`, `volume`, `timestamp`) per user and symbol.
- **`public.snapshot_history`**: Audit trail and timeline of every baseline reset event.
- **`public.companies`**: Master catalog of 118+ NSE equities with sectors, specific industry classifications, 52-week ranges, and market capitalization.

---

## 8. Local Setup & Running

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 1. Run Backend Locally
```bash
cd groww/backend
pip install -r requirements.txt
python run.py
```
Backend will start at: `http://localhost:8000`

### 2. Run Frontend Locally
```bash
cd groww/frontend
npm install
npm run dev
```
Frontend will start at: `http://localhost:5173`

---

## 9. Deployment Guide

### Deploy Backend to Render:
1. Create a **Web Service** pointing to `Shreyya407/stock_watch`.
2. **Root Directory**: `backend`
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. **Environment Variables**:
   - `SUPABASE_URL`: `https://antgmodxxshcaxeqjbdj.supabase.co`
   - `SUPABASE_SERVICE_ROLE_KEY`: `<service-role-key>`
   - `SUPABASE_ANON_KEY`: `<anon-key>`
   - `JWT_SECRET`: `growwpulse-jwt-secret-key-2026-secure`

### Deploy Frontend to Vercel:
1. Import repository on Vercel.
2. **Root Directory**: `frontend`
3. **Environment Variables**:
   - `VITE_API_BASE_URL`: `https://stock-watch-oabd.onrender.com/api`
   - `VITE_SUPABASE_URL`: `https://antgmodxxshcaxeqjbdj.supabase.co`
   - `VITE_SUPABASE_ANON_KEY`: `<anon-key>`

---

## 10. Automated Tests
Run the pytest test suite:
```bash
cd groww/backend
python -m pytest
```

---

## 11. Author & Acknowledgments
Built with ❤️ for Indian equity market traders.
- **Frontend:** React, Vite, Lucide Icons, Vanilla CSS Design System
- **Backend:** FastAPI, Python, Uvicorn
- **Market Data:** NSE India & Yahoo Finance (.NS)
- **Database:** Supabase PostgreSQL with Realtime Pub/Sub
