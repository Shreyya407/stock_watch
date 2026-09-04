import math
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
from app.models import MarketQuote, StockAnalytics, WhyBreakdown, WatchlistSummary, MarketPulseSummary


IST_OFFSET = timedelta(hours=5, minutes=30)
IST_TZ = timezone(IST_OFFSET, name="IST")


def get_current_ist_time() -> datetime:
    """Returns the current datetime in Indian Standard Time (IST)."""
    return datetime.now(timezone.utc).astimezone(IST_TZ)


def get_indian_market_status() -> Dict[str, str]:
    """
    Calculates the current Indian stock market status based on IST.
    Market hours: Mon-Fri
    - 09:00 - 09:08: PRE_MARKET
    - 09:15 - 15:30: OPEN
    - Outside these hours / Weekends: CLOSED
    """
    now_ist = get_current_ist_time()
    weekday = now_ist.weekday()  # Monday is 0, Sunday is 6
    time_minutes = now_ist.hour * 60 + now_ist.minute

    # Format human readable IST time
    ist_str = now_ist.strftime("%I:%M %p IST, %b %d")

    if weekday in (5, 6):  # Saturday, Sunday
        return {
            "status": "CLOSED",
            "message": "Market Closed (Weekend)",
            "istTime": ist_str
        }

    # 09:00 = 540 mins, 09:08 = 548 mins
    if 540 <= time_minutes < 548:
        return {
            "status": "PRE_MARKET",
            "message": "Pre-market Session (09:00 - 09:08 AM)",
            "istTime": ist_str
        }
    # 09:15 = 555 mins, 15:30 = 930 mins
    elif 555 <= time_minutes < 930:
        return {
            "status": "OPEN",
            "message": "Market Open (Closes at 03:30 PM)",
            "istTime": ist_str
        }
    else:
        return {
            "status": "CLOSED",
            "message": "Market Closed (Opens Mon-Fri at 09:15 AM)",
            "istTime": ist_str
        }


def calculate_price_delta_pct(current_price: float, snapshot_price: float) -> float:
    """Calculates percentage price change from baseline snapshot."""
    if snapshot_price <= 0:
        return 0.0
    return ((current_price - snapshot_price) / snapshot_price) * 100.0


def calculate_absolute_change(current_price: float, snapshot_price: float) -> float:
    """Calculates absolute rupee change from baseline snapshot."""
    return current_price - snapshot_price


def calculate_volume_multiplier(current_volume: int, avg_volume_20d: float) -> float:
    """Calculates the ratio of current volume against 20-day historical average."""
    if avg_volume_20d <= 0:
        return 1.0
    return current_volume / avg_volume_20d


def calculate_volatility_adjusted_movement(price_delta_pct: float, typical_volatility_pct: float) -> float:
    """Calculates movement normalized by the stock's typical daily volatility."""
    safe_vol = max(typical_volatility_pct, 0.25)
    return abs(price_delta_pct) / safe_vol


def calculate_opening_gap_pct(today_open: float, previous_close: float) -> float:
    """Calculates opening gap percentage relative to previous close."""
    if previous_close <= 0:
        return 0.0
    return ((today_open - previous_close) / previous_close) * 100.0


def calculate_attention_score(
    price_delta_pct: float,
    volume_multiplier: float,
    volatility_adjusted_movement: float
) -> Dict[str, Any]:
    """
    Deterministic Attention Score Algorithm (0-100):
    - 40% Price movement: Evaluates magnitude of price deviation (scales to max 40 pts at ~4% delta)
    - 30% Volume anomaly: Evaluates volume surge (scales to max 30 pts at ~3.0x 20D avg)
    - 30% Volatility-adjusted movement: Evaluates move vs standard deviation (scales to max 30 pts at 3x typical volatility)
    """
    abs_delta = abs(price_delta_pct)
    
    # 1. Price movement score (0-40 points)
    # A 4.0% or greater move gets full 40 points
    price_score = min(40.0, (abs_delta / 4.0) * 40.0)

    # 2. Volume anomaly score (0-30 points)
    # Baseline normal volume is 1.0x (0 pts), 3.0x or greater gets full 30 pts
    if volume_multiplier > 1.0:
        vol_score = min(30.0, ((volume_multiplier - 1.0) / 2.0) * 30.0)
    else:
        vol_score = 0.0

    # 3. Volatility-adjusted score (0-30 points)
    # 3x standard volatility gets full 30 pts
    vola_score = min(30.0, (volatility_adjusted_movement / 3.0) * 30.0)

    total_raw = price_score + vol_score + vola_score
    total_score = max(0, min(100, int(round(total_raw))))

    # Categories:
    # 70-100 = SIGNIFICANT
    # 40-69 = WORTH CHECKING
    # 0-39 = QUIET
    if total_score >= 70:
        category = "SIGNIFICANT"
    elif total_score >= 40:
        category = "WORTH CHECKING"
    else:
        category = "QUIET"

    return {
        "score": total_score,
        "category": category,
        "price_contribution": round(price_score, 1),
        "volume_contribution": round(vol_score, 1),
        "volatility_contribution": round(vola_score, 1)
    }


def generate_explainability(
    price_delta_pct: float,
    volume_multiplier: float,
    volatility_adjusted_movement: float,
    opening_gap_pct: float,
    attention_score: int,
    attention_category: str
) -> Dict[str, str]:
    """
    Generates explainability metadata explaining the SIGNAL (not fabricating unverified causes).
    """
    abs_delta = abs(price_delta_pct)

    if attention_category == "SIGNIFICANT":
        if abs_delta >= 2.5 and volume_multiplier >= 1.8:
            primary_signal = "UNUSUAL PRICE + VOLUME SURGE"
            explanation = "This stock has broken out with strong directional momentum accompanied by heavy trading volume compared to its 20-day baseline."
        elif volatility_adjusted_movement >= 2.2:
            primary_signal = "VOLATILITY EXPANSION"
            explanation = "This stock has exceeded 2x its typical daily volatility band since baseline, signaling elevated market conviction."
        elif volume_multiplier >= 2.5:
            primary_signal = "INSTITUTIONAL VOLUME SPIKE"
            explanation = "Extremely high trading volume turnover relative to historical average, indicating heightened market interest."
        else:
            primary_signal = "SIGNIFICANT PRICE EXTENSION"
            explanation = "Substantial price departure from baseline snapshot that warrants immediate attention."

    elif attention_category == "WORTH CHECKING":
        if abs(opening_gap_pct) >= 1.2:
            primary_signal = "NOTABLE OPENING GAP"
            direction = "upward" if opening_gap_pct > 0 else "downward"
            explanation = f"Stock opened with a {direction} gap of {abs(opening_gap_pct):.1f}%, indicating overnight repricing."
        elif volume_multiplier >= 1.5:
            primary_signal = "ABOVE-AVERAGE VOLUME ACCUMULATION"
            explanation = "Trading volume is elevated above the 20-day normal baseline while maintaining moderate price trajectory."
        elif abs_delta >= 1.5:
            primary_signal = "MODERATE PRICE DRIFT"
            explanation = "Stock is trending beyond quiet baseline limits with steady participant activity."
        else:
            primary_signal = "ACTIVITY WORTH MONITORING"
            explanation = "Emerging price or volume dynamics slightly above historical median."

    else:  # QUIET
        primary_signal = "STABLE / QUIET BASELINE"
        explanation = "Price and volume are tracking within typical historical limits with minimal baseline deviation."

    return {
        "primarySignal": primary_signal,
        "plainEnglishExplanation": explanation
    }


def compute_stock_analytics(
    quote: MarketQuote,
    snapshot_price: Optional[float] = None,
    snapshot_timestamp: Optional[str] = None
) -> StockAnalytics:
    """
    Computes complete stock analytics by comparing current quote against baseline snapshot.
    If snapshot_price is None or <= 0, snapshot_price defaults to current price (baseline initialization).
    """
    effective_snapshot_price = snapshot_price if (snapshot_price is not None and snapshot_price > 0) else quote.price

    price_delta_pct = calculate_price_delta_pct(quote.price, effective_snapshot_price)
    absolute_change = calculate_absolute_change(quote.price, effective_snapshot_price)
    volume_multiplier = calculate_volume_multiplier(quote.volume, quote.avgVolume20D)
    volatility_adjusted = calculate_volatility_adjusted_movement(price_delta_pct, quote.historicalVolatility)
    opening_gap_pct = calculate_opening_gap_pct(quote.open, quote.previousClose)
    
    # Day change is current vs previous close
    day_change_pct = ((quote.price - quote.previousClose) / quote.previousClose * 100.0) if quote.previousClose > 0 else 0.0

    score_data = calculate_attention_score(price_delta_pct, volume_multiplier, volatility_adjusted)
    
    explain = generate_explainability(
        price_delta_pct,
        volume_multiplier,
        volatility_adjusted,
        opening_gap_pct,
        score_data["score"],
        score_data["category"]
    )

    why_breakdown = WhyBreakdown(
        priceScoreWeight=40.0,
        volumeScoreWeight=30.0,
        volatilityScoreWeight=30.0,
        priceContribution=score_data["price_contribution"],
        volumeContribution=score_data["volume_contribution"],
        volatilityContribution=score_data["volatility_contribution"],
        primarySignal=explain["primarySignal"],
        plainEnglishExplanation=explain["plainEnglishExplanation"]
    )

    details = {
        "sector": quote.sector or "Equity",
        "marketCap": quote.marketCap,
        "fiftyTwoWeekHigh": quote.fiftyTwoWeekHigh,
        "fiftyTwoWeekLow": quote.fiftyTwoWeekLow,
        "open": quote.open,
        "high": quote.high,
        "low": quote.low,
        "previousClose": quote.previousClose,
        "exchange": quote.exchange or "NSE"
    }

    return StockAnalytics(
        symbol=quote.symbol,
        companyName=quote.companyName,
        currentPrice=round(quote.price, 2),
        snapshotPrice=round(effective_snapshot_price, 2),
        priceDeltaPct=round(price_delta_pct, 2),
        absoluteChange=round(absolute_change, 2),
        volume=quote.volume,
        avgVolume20D=round(quote.avgVolume20D, 0),
        volumeMultiplier=round(volume_multiplier, 2),
        volatilityAdjustedMovement=round(volatility_adjusted, 2),
        openingGapPct=round(opening_gap_pct, 2),
        dayChangePct=round(day_change_pct, 2),
        attentionScore=score_data["score"],
        attentionCategory=score_data["category"],
        whyBreakdown=why_breakdown,
        snapshotTimestamp=snapshot_timestamp,
        quoteTimestamp=quote.timestamp,
        source=quote.source,
        isStale=quote.isStale,
        lastUpdatedSecondsAgo=quote.lastUpdatedSecondsAgo,
        sparkline=quote.sparkline,
        details=details
    )


def build_watchlist_summary(
    analytics_list: List[StockAnalytics],
    last_checked_timestamp: Optional[str] = None
) -> WatchlistSummary:
    """Builds the hero summary statistics from the analyzed stocks list."""
    total = len(analytics_list)
    significant = sum(1 for s in analytics_list if s.attentionCategory == "SIGNIFICANT")
    worth_checking = sum(1 for s in analytics_list if s.attentionCategory == "WORTH CHECKING")
    quiet = sum(1 for s in analytics_list if s.attentionCategory == "QUIET")
    
    # Meaningful change if price changed by >= 0.25% or category is not quiet
    changed = sum(1 for s in analytics_list if abs(s.priceDeltaPct) >= 0.25 or s.attentionCategory != "QUIET")

    has_meaningful = (significant > 0 or worth_checking > 0)
    
    if total == 0:
        summary_text = "Your watchlist is quiet. Add stocks to start seeing what changed."
    elif significant > 0:
        summary_text = f"Your watchlist changed in {changed} meaningful ways ({significant} requiring immediate attention)."
    elif worth_checking > 0:
        summary_text = f"Your watchlist changed in {changed} moderate ways with {worth_checking} worth checking."
    else:
        summary_text = "Nothing needs your attention right now."

    return WatchlistSummary(
        totalCount=total,
        changedCount=changed,
        significantCount=significant,
        worthCheckingCount=worth_checking,
        quietCount=quiet,
        lastCheckedTimestamp=last_checked_timestamp,
        hasMeaningfulChanges=has_meaningful,
        summaryText=summary_text
    )


def build_market_pulse(analytics_list: List[StockAnalytics]) -> MarketPulseSummary:
    """Builds the compact Market Pulse strip from real watchlist / market data."""
    status_info = get_indian_market_status()

    top_mover = None
    largest_volume = None
    highest_attention = None

    if analytics_list:
        # Top mover by absolute priceDeltaPct
        sorted_by_move = sorted(analytics_list, key=lambda x: abs(x.priceDeltaPct), reverse=True)
        if sorted_by_move:
            tm = sorted_by_move[0]
            top_mover = {
                "symbol": tm.symbol,
                "changePct": tm.priceDeltaPct,
                "price": tm.currentPrice
            }

        # Largest volume anomaly by volumeMultiplier
        sorted_by_vol = sorted(analytics_list, key=lambda x: x.volumeMultiplier, reverse=True)
        if sorted_by_vol:
            lv = sorted_by_vol[0]
            largest_volume = {
                "symbol": lv.symbol,
                "multiplier": lv.volumeMultiplier,
                "volume": lv.volume
            }

        # Highest attention score
        sorted_by_att = sorted(analytics_list, key=lambda x: x.attentionScore, reverse=True)
        if sorted_by_att:
            ha = sorted_by_att[0]
            highest_attention = {
                "symbol": ha.symbol,
                "score": ha.attentionScore,
                "category": ha.attentionCategory
            }

    return MarketPulseSummary(
        marketStatus=status_info["status"],
        marketStatusMessage=status_info["message"],
        istTime=status_info["istTime"],
        topMover=top_mover,
        largestVolumeAnomaly=largest_volume,
        highestAttention=highest_attention
    )
