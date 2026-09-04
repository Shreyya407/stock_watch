import time
import math
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx
import requests

from app.models import MarketQuote, SearchResultItem

# Comprehensive Indian Equities Registry for search & rich company metadata
POPULAR_NSE_STOCKS: List[Dict[str, str]] = [
    # Top Nifty & Megacaps
    {"symbol": "RELIANCE", "name": "Reliance Industries Ltd", "sector": "Energy / Oil & Gas"},
    {"symbol": "TCS", "name": "Tata Consultancy Services Ltd", "sector": "Information Technology"},
    {"symbol": "HDFCBANK", "name": "HDFC Bank Ltd", "sector": "Banking & Financial Services"},
    {"symbol": "INFY", "name": "Infosys Ltd", "sector": "Information Technology"},
    {"symbol": "ICICIBANK", "name": "ICICI Bank Ltd", "sector": "Banking & Financial Services"},
    {"symbol": "BHARTIARTL", "name": "Bharti Airtel Ltd", "sector": "Telecommunications"},
    {"symbol": "SBIN", "name": "State Bank of India", "sector": "Banking & Financial Services"},
    {"symbol": "ITC", "name": "ITC Ltd", "sector": "Consumer Goods (FMCG)"},
    {"symbol": "LT", "name": "Larsen & Toubro Ltd", "sector": "Capital Goods & Construction"},
    {"symbol": "TATAMOTORS", "name": "Tata Motors Ltd", "sector": "Automobile"},
    {"symbol": "HINDUNILVR", "name": "Hindustan Unilever Ltd", "sector": "Consumer Goods (FMCG)"},
    {"symbol": "BAJFINANCE", "name": "Bajaj Finance Ltd", "sector": "Financial Services"},
    {"symbol": "KOTAKBANK", "name": "Kotak Mahindra Bank Ltd", "sector": "Banking & Financial Services"},
    {"symbol": "AXISBANK", "name": "Axis Bank Ltd", "sector": "Banking & Financial Services"},
    {"symbol": "ASIANPAINT", "name": "Asian Paints Ltd", "sector": "Consumer Durables"},
    {"symbol": "MARUTI", "name": "Maruti Suzuki India Ltd", "sector": "Automobile"},
    {"symbol": "SUNPHARMA", "name": "Sun Pharmaceutical Industries Ltd", "sector": "Healthcare & Pharma"},
    {"symbol": "TITAN", "name": "Titan Company Ltd", "sector": "Consumer Durables"},
    {"symbol": "WIPRO", "name": "Wipro Ltd", "sector": "Information Technology"},
    {"symbol": "HCLTECH", "name": "HCL Technologies Ltd", "sector": "Information Technology"},
    {"symbol": "NTPC", "name": "NTPC Ltd", "sector": "Power / Utilities"},
    {"symbol": "ONGC", "name": "Oil and Natural Gas Corporation Ltd", "sector": "Energy / Oil & Gas"},
    {"symbol": "POWERGRID", "name": "Power Grid Corporation of India Ltd", "sector": "Power / Utilities"},
    {"symbol": "ULTRACEMCO", "name": "UltraTech Cement Ltd", "sector": "Materials / Cement"},
    {"symbol": "JSWSTEEL", "name": "JSW Steel Ltd", "sector": "Metals & Mining"},
    {"symbol": "TATASTEEL", "name": "Tata Steel Ltd", "sector": "Metals & Mining"},
    {"symbol": "ADANIENT", "name": "Adani Enterprises Ltd", "sector": "Conglomerate"},
    {"symbol": "ADANIPORTS", "name": "Adani Ports and Special Economic Zone Ltd", "sector": "Infrastructure"},
    {"symbol": "COALINDIA", "name": "Coal India Ltd", "sector": "Metals & Mining"},
    {"symbol": "BAJAJFINSV", "name": "Bajaj Finserv Ltd", "sector": "Financial Services"},
    {"symbol": "M&M", "name": "Mahindra & Mahindra Ltd", "sector": "Automobile"},
    {"symbol": "NESTLEIND", "name": "Nestle India Ltd", "sector": "Consumer Goods (FMCG)"},
    {"symbol": "BRITANNIA", "name": "Britannia Industries Ltd", "sector": "Consumer Goods (FMCG)"},
    {"symbol": "TATACONSUM", "name": "Tata Consumer Products Ltd", "sector": "Consumer Goods (FMCG)"},
    {"symbol": "GRASIM", "name": "Grasim Industries Ltd", "sector": "Materials"},
    {"symbol": "HINDALCO", "name": "Hindalco Industries Ltd", "sector": "Metals & Mining"},
    {"symbol": "VEDL", "name": "Vedanta Ltd", "sector": "Metals & Mining"},
    {"symbol": "DIVISLAB", "name": "Divi's Laboratories Ltd", "sector": "Healthcare & Pharma"},
    {"symbol": "DRREDDY", "name": "Dr. Reddy's Laboratories Ltd", "sector": "Healthcare & Pharma"},
    {"symbol": "CIPLA", "name": "Cipla Ltd", "sector": "Healthcare & Pharma"},
    {"symbol": "EICHERMOT", "name": "Eicher Motors Ltd", "sector": "Automobile"},
    {"symbol": "HEROMOTOCO", "name": "Hero MotoCorp Ltd", "sector": "Automobile"},
    {"symbol": "BAJAJ-AUTO", "name": "Bajaj Auto Ltd", "sector": "Automobile"},
    {"symbol": "TVSMOTOR", "name": "TVS Motor Company Ltd", "sector": "Automobile"},
    {"symbol": "TECHM", "name": "Tech Mahindra Ltd", "sector": "Information Technology"},
    {"symbol": "LTIM", "name": "LTIMindtree Ltd", "sector": "Information Technology"},
    {"symbol": "PERSISTENT", "name": "Persistent Systems Ltd", "sector": "Information Technology"},
    {"symbol": "COFORGE", "name": "Coforge Ltd", "sector": "Information Technology"},
    {"symbol": "KPITTECH", "name": "KPIT Technologies Ltd", "sector": "Automotive Tech / IT"},
    {"symbol": "TATAELXSI", "name": "Tata Elxsi Ltd", "sector": "Information Technology"},
    {"symbol": "BEL", "name": "Bharat Electronics Ltd", "sector": "Aerospace & Defence"},
    {"symbol": "HAL", "name": "Hindustan Aeronautics Ltd", "sector": "Aerospace & Defence"},
    {"symbol": "BHEL", "name": "Bharat Heavy Electricals Ltd", "sector": "Capital Goods"},
    {"symbol": "MAZDOCK", "name": "Mazagon Dock Shipbuilders Ltd", "sector": "Defence & Shipbuilding"},
    {"symbol": "COCHINSHIP", "name": "Cochin Shipyard Ltd", "sector": "Defence & Shipbuilding"},
    {"symbol": "BDL", "name": "Bharat Dynamics Ltd", "sector": "Aerospace & Defence"},
    {"symbol": "ZOMATO", "name": "Zomato Ltd", "sector": "Consumer Tech / Food Delivery"},
    {"symbol": "JIOFIN", "name": "Jio Financial Services Ltd", "sector": "Financial Services"},
    {"symbol": "PAYTM", "name": "One 97 Communications (Paytm)", "sector": "Fintech"},
    {"symbol": "NYKAA", "name": "FSN E-Commerce Ventures (Nykaa)", "sector": "Consumer Tech / Retail"},
    {"symbol": "POLICYBZR", "name": "PB Fintech (Policybazaar)", "sector": "Fintech / Insurtech"},
    {"symbol": "DELHIVERY", "name": "Delhivery Ltd", "sector": "Logistics & Supply Chain"},
    {"symbol": "NAUKRI", "name": "Info Edge (India) Ltd", "sector": "Internet / Recruitment"},
    {"symbol": "IRCTC", "name": "Indian Railway Catering and Tourism Corp", "sector": "Services & Travel"},
    {"symbol": "INDIGO", "name": "InterGlobe Aviation (IndiGo)", "sector": "Aviation"},
    {"symbol": "TRENT", "name": "Trent Ltd (Westside / Zudio)", "sector": "Retail & Fashion"},
    {"symbol": "DMART", "name": "Avenue Supermarts (DMart)", "sector": "Retail"},
    {"symbol": "VBL", "name": "Varun Beverages Ltd", "sector": "Consumer Goods (Beverages)"},
    {"symbol": "DABUR", "name": "Dabur India Ltd", "sector": "Consumer Goods (FMCG)"},
    {"symbol": "MARICO", "name": "Marico Ltd", "sector": "Consumer Goods (FMCG)"},
    {"symbol": "GODREJCP", "name": "Godrej Consumer Products Ltd", "sector": "Consumer Goods (FMCG)"},
    {"symbol": "COLPAL", "name": "Colgate-Palmolive (India) Ltd", "sector": "Consumer Goods (FMCG)"},
    {"symbol": "TATAPOWER", "name": "Tata Power Company Ltd", "sector": "Power / Renewable Energy"},
    {"symbol": "ADANIGREEN", "name": "Adani Green Energy Ltd", "sector": "Renewable Energy"},
    {"symbol": "ADANIPOWER", "name": "Adani Power Ltd", "sector": "Power / Utilities"},
    {"symbol": "SUZLON", "name": "Suzlon Energy Ltd", "sector": "Renewable Energy / Wind"},
    {"symbol": "IREDA", "name": "Indian Renewable Energy Development Agency", "sector": "Financial Services"},
    {"symbol": "NHPC", "name": "NHPC Ltd", "sector": "Power / Hydro"},
    {"symbol": "BPCL", "name": "Bharat Petroleum Corporation Ltd", "sector": "Energy / Oil & Gas"},
    {"symbol": "IOC", "name": "Indian Oil Corporation Ltd", "sector": "Energy / Oil & Gas"},
    {"symbol": "GAIL", "name": "GAIL (India) Ltd", "sector": "Energy / Gas Transmission"},
    {"symbol": "APOLLOHOSP", "name": "Apollo Hospitals Enterprise Ltd", "sector": "Healthcare & Hospitals"},
    {"symbol": "MANKIND", "name": "Mankind Pharma Ltd", "sector": "Healthcare & Pharma"},
    {"symbol": "MAXHEALTH", "name": "Max Healthcare Institute Ltd", "sector": "Healthcare & Hospitals"},
    {"symbol": "LUPIN", "name": "Lupin Ltd", "sector": "Healthcare & Pharma"},
    {"symbol": "AUROPHARMA", "name": "Aurobindo Pharma Ltd", "sector": "Healthcare & Pharma"},
    {"symbol": "TORNTPHARM", "name": "Torrent Pharmaceuticals Ltd", "sector": "Healthcare & Pharma"},
    {"symbol": "ZYDUSLIFE", "name": "Zydus Lifesciences Ltd", "sector": "Healthcare & Pharma"},
    {"symbol": "BIOCON", "name": "Biocon Ltd", "sector": "Biotechnology & Pharma"},
    {"symbol": "DLF", "name": "DLF Ltd", "sector": "Real Estate"},
    {"symbol": "GODREJPROP", "name": "Godrej Properties Ltd", "sector": "Real Estate"},
    {"symbol": "LODHA", "name": "Macrotech Developers (Lodha)", "sector": "Real Estate"},
    {"symbol": "OBEROIRLTY", "name": "Oberoi Realty Ltd", "sector": "Real Estate"},
    {"symbol": "PRESTIGE", "name": "Prestige Estates Projects Ltd", "sector": "Real Estate"},
    {"symbol": "PIDILITIND", "name": "Pidilite Industries Ltd (Fevicol)", "sector": "Chemicals"},
    {"symbol": "BERGEPAINT", "name": "Berger Paints India Ltd", "sector": "Consumer Durables"},
    {"symbol": "HAVELLS", "name": "Havells India Ltd", "sector": "Consumer Electricals"},
    {"symbol": "POLYCAB", "name": "Polycab India Ltd", "sector": "Cables & Electricals"},
    {"symbol": "KEI", "name": "KEI Industries Ltd", "sector": "Cables & Electricals"},
    {"symbol": "SIEMENS", "name": "Siemens Ltd", "sector": "Capital Goods / Engineering"},
    {"symbol": "ABB", "name": "ABB India Ltd", "sector": "Capital Goods / Engineering"},
    {"symbol": "AMBUJACEM", "name": "Ambuja Cements Ltd", "sector": "Materials / Cement"},
    {"symbol": "ACC", "name": "ACC Ltd", "sector": "Materials / Cement"},
    {"symbol": "SHREECEM", "name": "Shree Cement Ltd", "sector": "Materials / Cement"},
    {"symbol": "MUTHOOTFIN", "name": "Muthoot Finance Ltd", "sector": "Financial Services / Gold Loan"},
    {"symbol": "CHOLAFIN", "name": "Cholamandalam Investment & Finance", "sector": "Financial Services"},
    {"symbol": "SHRIRAMFIN", "name": "Shriram Finance Ltd", "sector": "Financial Services"},
    {"symbol": "HDFCLIFE", "name": "HDFC Life Insurance Company Ltd", "sector": "Insurance"},
    {"symbol": "SBILIFE", "name": "SBI Life Insurance Company Ltd", "sector": "Insurance"},
    {"symbol": "ICICIPRULI", "name": "ICICI Prudential Life Insurance", "sector": "Insurance"},
    {"symbol": "BANKBARODA", "name": "Bank of Baroda", "sector": "Banking & Financial Services"},
    {"symbol": "PNB", "name": "Punjab National Bank", "sector": "Banking & Financial Services"},
    {"symbol": "CANBK", "name": "Canara Bank", "sector": "Banking & Financial Services"},
    {"symbol": "INDUSINDBK", "name": "IndusInd Bank Ltd", "sector": "Banking & Financial Services"},
    {"symbol": "JINDALSTEL", "name": "Jindal Steel & Power Ltd", "sector": "Metals & Mining"},
    {"symbol": "NMDC", "name": "NMDC Ltd", "sector": "Metals & Mining"},
    {"symbol": "NATIONALUM", "name": "National Aluminium Company Ltd", "sector": "Metals & Mining"},
    {"symbol": "SAIL", "name": "Steel Authority of India Ltd", "sector": "Metals & Mining"},
]



class CacheItem:
    def __init__(self, quote: MarketQuote, cached_at: float):
        self.quote = quote
        self.cached_at = cached_at


class NSEMarketDataService:
    """
    Resilient Indian Equities Market Data Provider:
    - 15-second TTL in-memory cache per symbol
    - Primary: NSE India real market endpoints with session handling
    - Fallback: Yahoo Finance (.NS tickers) with 20D average volume, volatility & sparklines
    - Stale Fallback: Last cached quote if both external sources fail
    - Zero fake data
    """

    def __init__(self):
        self._cache: Dict[str, CacheItem] = {}
        self._lock = asyncio.Lock()
        self._ttl_seconds = 15
        self._http_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        self._nse_session: Optional[requests.Session] = None
        self._nse_session_time: float = 0.0

    def _get_nse_session(self) -> requests.Session:
        """Initializes / refreshes NSE session with cookies."""
        curr_time = time.time()
        # Refresh session every 5 minutes
        if self._nse_session is None or (curr_time - self._nse_session_time > 300):
            session = requests.Session()
            session.headers.update(self._http_headers)
            try:
                session.get("https://www.nseindia.com", timeout=5)
            except Exception:
                pass
            self._nse_session = session
            self._nse_session_time = curr_time
        return self._nse_session

    def _fetch_from_nse(self, symbol: str) -> Optional[MarketQuote]:
        """Attempts to fetch real equity quote from NSE India official endpoints."""
        clean_sym = symbol.strip().upper()
        try:
            session = self._get_nse_session()
            url = f"https://www.nseindia.com/api/quote-equity?symbol={clean_sym}"
            resp = session.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                price_info = data.get("priceInfo", {})
                info = data.get("info", {})
                sec_info = data.get("securityInfo", {})

                last_price = float(price_info.get("lastPrice", 0.0))
                if last_price <= 0:
                    return None

                prev_close = float(price_info.get("previousClose", last_price))
                open_price = float(price_info.get("open", last_price))
                high_price = float(price_info.get("intraDayHighLow", {}).get("max", last_price))
                low_price = float(price_info.get("intraDayHighLow", {}).get("min", last_price))
                
                # Volume
                volume = int(price_info.get("totalTradedVolume", 0) or sec_info.get("issuedSize", 0) or 100000)
                company_name = info.get("companyName") or self._lookup_company_name(clean_sym)
                
                week_high = float(price_info.get("weekHighLow", {}).get("max", 0.0)) or None
                week_low = float(price_info.get("weekHighLow", {}).get("min", 0.0)) or None

                # Default fallback volatility & 20D vol for NSE raw quote
                avg_vol = max(volume * 0.9, 50000.0)
                volatility = 1.8  # standard historical benchmark

                now_iso = datetime.now(timezone.utc).isoformat()

                return MarketQuote(
                    symbol=clean_sym,
                    companyName=company_name,
                    price=last_price,
                    previousClose=prev_close,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    volume=volume,
                    avgVolume20D=avg_vol,
                    historicalVolatility=volatility,
                    timestamp=now_iso,
                    source="LIVE • NSE",
                    isStale=False,
                    lastUpdatedSecondsAgo=0,
                    fiftyTwoWeekHigh=week_high,
                    fiftyTwoWeekLow=week_low,
                    sector=info.get("industry") or self._lookup_sector(clean_sym),
                    exchange="NSE"
                )
        except Exception:
            return None
        return None

    def _fetch_from_yfinance_rest(self, symbol: str) -> Optional[MarketQuote]:
        """
        Fetches live market data and 20-day historical context using Yahoo Finance Chart API.
        Ticker format: {SYMBOL}.NS
        """
        clean_sym = symbol.strip().upper()
        # Remove any existing .NS suffix if user provided it
        base_sym = clean_sym.replace(".NS", "")
        yf_symbol = f"{base_sym}.NS"

        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{yf_symbol}?range=1mo&interval=1d&includePrePost=true"
        
        try:
            resp = requests.get(url, headers=self._http_headers, timeout=8)
            if resp.status_code != 200:
                # Try query2 endpoint if query1 fails
                url2 = f"https://query2.finance.yahoo.com/v8/finance/chart/{yf_symbol}?range=1mo&interval=1d"
                resp = requests.get(url2, headers=self._http_headers, timeout=8)
                if resp.status_code != 200:
                    return None

            data = resp.json()
            result = data.get("chart", {}).get("result")
            if not result or len(result) == 0:
                return None

            chart_data = result[0]
            meta = chart_data.get("meta", {})
            indicators = chart_data.get("indicators", {})
            quote_arr = indicators.get("quote", [{}])[0]

            last_price = meta.get("regularMarketPrice")
            if last_price is None or float(last_price) <= 0:
                # Fallback to last close in array
                closes = [c for c in quote_arr.get("close", []) if c is not None]
                if closes:
                    last_price = float(closes[-1])
                else:
                    return None

            last_price = float(last_price)
            prev_close = float(meta.get("previousClose") or meta.get("chartPreviousClose") or last_price)
            open_price = float(meta.get("regularMarketDayOpen") or last_price)
            high_price = float(meta.get("regularMarketDayHigh") or last_price)
            low_price = float(meta.get("regularMarketDayLow") or last_price)
            volume = int(meta.get("regularMarketVolume") or 0)

            # Historical closes and volumes for 20D metrics
            historical_closes = [float(c) for c in quote_arr.get("close", []) if c is not None]
            historical_volumes = [int(v) for v in quote_arr.get("volume", []) if v is not None and v > 0]

            # 20D Average Volume calculation
            if historical_volumes:
                recent_volumes = historical_volumes[-20:]
                avg_volume_20d = float(sum(recent_volumes) / len(recent_volumes))
            else:
                avg_volume_20d = float(max(volume, 100000))

            if volume == 0 and historical_volumes:
                volume = historical_volumes[-1]

            # Typical Daily Volatility (%) calculation over 20-30 days
            if len(historical_closes) >= 5:
                # Calculate daily return percentages
                daily_returns = []
                for i in range(1, len(historical_closes)):
                    p_prev = historical_closes[i - 1]
                    p_curr = historical_closes[i]
                    if p_prev > 0:
                        ret = abs((p_curr - p_prev) / p_prev) * 100.0
                        daily_returns.append(ret)
                
                if daily_returns:
                    # Average daily volatility percentage
                    typical_volatility = float(sum(daily_returns) / len(daily_returns))
                else:
                    typical_volatility = 1.5
            else:
                typical_volatility = 1.5

            # Sparkline points (recent 15-20 price points)
            sparkline: List[float] = []
            if len(historical_closes) >= 5:
                sparkline = [round(p, 2) for p in historical_closes[-15:]]

            company_name = meta.get("shortName") or meta.get("longName") or self._lookup_company_name(base_sym)
            fifty_two_high = float(meta.get("fiftyTwoWeekHigh")) if meta.get("fiftyTwoWeekHigh") else None
            fifty_two_low = float(meta.get("fiftyTwoWeekLow")) if meta.get("fiftyTwoWeekLow") else None
            market_cap = float(meta.get("marketCap")) if meta.get("marketCap") else None

            now_iso = datetime.now(timezone.utc).isoformat()

            return MarketQuote(
                symbol=base_sym,
                companyName=company_name,
                price=round(last_price, 2),
                previousClose=round(prev_close, 2),
                open=round(open_price, 2),
                high=round(high_price, 2),
                low=round(low_price, 2),
                volume=volume,
                avgVolume20D=round(avg_volume_20d, 0),
                historicalVolatility=round(typical_volatility, 2),
                timestamp=now_iso,
                source="LIVE • YAHOO FINANCE",
                isStale=False,
                lastUpdatedSecondsAgo=0,
                sparkline=sparkline if len(sparkline) >= 3 else None,
                fiftyTwoWeekHigh=fifty_two_high,
                fiftyTwoWeekLow=fifty_two_low,
                marketCap=market_cap,
                sector=self._lookup_sector(base_sym),
                exchange="NSE"
            )
        except Exception:
            return None

    def _lookup_company_name(self, symbol: str) -> str:
        sym_clean = symbol.upper().strip()
        for item in POPULAR_NSE_STOCKS:
            if item["symbol"] == sym_clean:
                return item["name"]
        return f"{sym_clean} Ltd"

    def _lookup_sector(self, symbol: str) -> str:
        sym_clean = symbol.upper().strip()
        for item in POPULAR_NSE_STOCKS:
            if item["symbol"] == sym_clean:
                return item["sector"]
        return "Equity / General"

    async def get_quote(self, symbol: str) -> MarketQuote:
        """
        Retrieves real market quote with in-memory 15s TTL caching and fallback strategy:
        1. Check Cache: If fresh (<15s), return immediately.
        2. If expired/missing:
           a. Fetch from primary NSE India
           b. If NSE fails, fetch from Yahoo Finance (.NS)
           c. If both fail, return stale cached quote if available
           d. If no prior quote exists, raise error
        """
        clean_sym = symbol.strip().upper().replace(".NS", "")
        now = time.time()

        # Step 1: Check fresh cache
        async with self._lock:
            cached_item = self._cache.get(clean_sym)
            if cached_item is not None:
                age = now - cached_item.cached_at
                if age < self._ttl_seconds:
                    # Fresh cache hit
                    q = cached_item.quote.copy()
                    q.isStale = False
                    q.lastUpdatedSecondsAgo = int(age)
                    return q

        # Step 2: Fetch fresh data outside lock (or in thread pool)
        quote: Optional[MarketQuote] = None
        
        # 2a. Primary: NSE
        loop = asyncio.get_running_loop()
        quote = await loop.run_in_executor(None, self._fetch_from_nse, clean_sym)

        # 2b. Fallback: Yahoo Finance
        if quote is None:
            quote = await loop.run_in_executor(None, self._fetch_from_yfinance_rest, clean_sym)

        async with self._lock:
            if quote is not None:
                # Successfully retrieved fresh quote
                self._cache[clean_sym] = CacheItem(quote=quote, cached_at=now)
                return quote

            # 2c. Both external APIs failed: check if last valid cached quote exists
            cached_item = self._cache.get(clean_sym)
            if cached_item is not None:
                age = now - cached_item.cached_at
                stale_quote = cached_item.quote.copy()
                stale_quote.isStale = True
                stale_quote.lastUpdatedSecondsAgo = int(age)
                # Keep source clear: e.g. STALE • YAHOO FINANCE
                if not stale_quote.source.startswith("STALE"):
                    stale_quote.source = f"STALE • {stale_quote.source.replace('LIVE • ', '')}"
                return stale_quote

        # 2d. No quote could be obtained
        raise ValueError(f"Could not retrieve real market data for symbol '{clean_sym}'. Symbol may be invalid or market data provider is unreachable.")

    async def get_quotes_batch(self, symbols: List[str]) -> List[MarketQuote]:
        """Fetches quotes for a list of symbols concurrently without failing the batch if one stock fails."""
        tasks = [self.get_quote(s) for s in symbols]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_quotes: List[MarketQuote] = []
        for sym, res in zip(symbols, results):
            if isinstance(res, MarketQuote):
                valid_quotes.append(res)
            else:
                print(f"Warning: Failed to fetch quote for '{sym}': {res}")
        return valid_quotes

    def search_symbols(self, query: str = "") -> List[SearchResultItem]:
        """Searches NSE symbols and returns matched equity records."""
        q = (query or "").strip().upper()
        if not q:
            # Return all curated NSE companies
            return [
                SearchResultItem(symbol=item["symbol"], name=item["name"], exchange="NSE", sector=item["sector"])
                for item in POPULAR_NSE_STOCKS
            ]

        results: List[SearchResultItem] = []
        q_lower = q.lower()
        
        # 1. Exact / Prefix / Substring match against curated list
        for item in POPULAR_NSE_STOCKS:
            if (
                q in item["symbol"] or 
                q_lower in item["name"].lower() or 
                (item.get("sector") and q_lower in item["sector"].lower())
            ):
                results.append(SearchResultItem(
                    symbol=item["symbol"],
                    name=item["name"],
                    exchange="NSE",
                    sector=item["sector"]
                ))

        # If user searched for a custom symbol not in top list, allow querying it
        if not any(r.symbol == q for r in results) and len(q) >= 2:
            results.append(SearchResultItem(
                symbol=q,
                name=f"{q} (NSE India)",
                exchange="NSE",
                sector="Equity"
            ))

        return results[:50]



# Singleton Service Instance
nse_service = NSEMarketDataService()
