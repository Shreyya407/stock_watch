# GrowwPulse — Change-First Smart Market Watchlist for Indian Equities

> **"What meaningfully changed since I last checked, and what deserves my attention now?"**

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

---

## 4. Architecture

A clean, monolithic, highly performant architecture:

```
┌─────────────────────────────────────────────────────────┐
│                 React + Vite Frontend                   │
│          (Vanilla CSS, Lucide Icons, IST Clock)         │
└────────────────────────────┬────────────────────────────┘
                             │  HTTP / JSON + Bearer JWT
                             ▼
┌─────────────────────────────────────────────────────────┐
│                   FastAPI Monolith                      │
│                                                         │
│   ├── Auth (Supabase JWT Verification)                 │
│   ├── Storage (Supabase PostgreSQL / Local Fallback)    │
│   ├── Real Market Data (NSE Primary + Yahoo Fallback)   │
│   ├── 15s In-Memory Symbol TTL Cache                    │
│   └── Analytics & Attention Scoring Engine              │
└──────────────┬───────────────────────────┬──────────────┘
               │                           │
               ▼                           ▼
┌───────────────────────────┐   ┌───────────────────────────┐
│   Supabase PostgreSQL     │   │     Live Market Data      │
│  - auth.users             │   │  - Primary: NSE India     │
│  - watchlists (RLS)       │   │  - Fallback: Yahoo (.NS)  │
│  - snapshots (RLS)        │   │  - Stale Cache Handling   │
└───────────────────────────┘   └───────────────────────────┘
```

---

## 5. Data Flow
1. **User Request:** Frontend queries `GET /api/watchlist/changes`.
2. **Authentication:** FastAPI inspects Bearer JWT and extracts `user_id`.
3. **Baseline Lookup:** Storage loads user-specific baseline snapshots (`price`, `volume`, `timestamp`).
4. **Market Data Fetch:**
   - Checks 15-second TTL cache per symbol.
   - On cache miss: queries official NSE endpoints.
   - On NSE rate limit/error: falls back to Yahoo Finance (`{SYMBOL}.NS`).
   - On total network outage: serves last cached quote marked `STALE`.
5. **Analytics Execution:** Computes Price Delta %, Rupee Change, Volume Multiplier, Volatility-Adjusted Move, Opening Gap %, and Attention Score.
6. **Response:** Frontend renders the "Since you last checked" summary, Market Pulse strip, and ranked Stock Cards.

---

## 6. Analytics Formulas

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

## 7. Attention Score Algorithm

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

## 8. Snapshot Logic
- **Baseline Initialization:** When a symbol is added, current price & volume are stored as the baseline.
- **Normal Refreshes:** Polling or manual refresh compares live prices against the **existing baseline**. Snapshots are **NEVER overwritten** during normal refresh.
- **Mark Current as Seen:** When the user clicks "Mark Current as Seen", the backend updates baseline snapshots to the live quotes. Deviations immediately reset to $\sim 0\%$.

---

## 9. Market Data Resilience & Zero Mock Data
- **Real Data Only:** Zero fabricated prices.
- **15-Second TTL Cache:** Prevents rate-limiting and external latency.
- **Clear UI Badges:**
  - `LIVE • NSE`
  - `LIVE • YAHOO FINANCE`
  - `STALE • Last updated X min ago`
- **Graceful Partial Failure:** If one stock's network request fails, all other stocks continue loading without crashing.

---

## 10. Supabase Setup

### Database Tables (PostgreSQL):
```sql
-- Watchlist table
CREATE TABLE watchlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    symbol VARCHAR(30) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, symbol)
);

-- Snapshots table
CREATE TABLE snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    symbol VARCHAR(30) NOT NULL,
    price NUMERIC(14, 2) NOT NULL,
    volume BIGINT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT now(),
    UNIQUE(user_id, symbol)
);

-- Enable RLS
ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE snapshots ENABLE ROW LEVEL SECURITY;

-- Policies
CREATE POLICY "Users can access their own watchlists"
ON watchlists FOR ALL USING (auth.uid() = user_id);

CREATE POLICY "Users can access their own snapshots"
ON snapshots FOR ALL USING (auth.uid() = user_id);
```

---

## 11. Environment Variables

### Backend (`groww/backend/.env`)
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
PORT=8000
HOST=0.0.0.0
```

### Frontend (`groww/frontend/.env`)
```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
VITE_API_BASE_URL=http://localhost:8000/api
```

---

## 12. Local Setup & Running

### Prerequisites
- Python 3.10+
- Node.js 18+ & npm

### 1. Run Backend
```bash
cd groww/backend
python -m pip install -r requirements.txt
python run.py
```
Backend will start at: `http://localhost:8000`

Verify:
```bash
curl http://localhost:8000/api/health
```

### 2. Run Frontend
```bash
cd groww/frontend
npm install
npm run dev
```
Frontend will start at: `http://localhost:5173`

---

## 13. Testing
Run the backend test suite:
```bash
cd groww/backend
python -m pytest
```

---

## 14. Trade-offs & Limitations
- **Intraday Tick Granularity:** To avoid high data costs, historical volatility and 20-day volumes leverage 1-month daily and 15-minute intraday charts from Yahoo Finance / NSE quotes.
- **NSE WAF / IP Challenges:** Direct NSE scraping may encounter Cloudflare/Akamai rate-limits from certain hosting providers, which is seamlessly mitigated by our Yahoo Finance fallback layer.
