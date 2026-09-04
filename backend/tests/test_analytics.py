import pytest
from app.models import MarketQuote
from app.analytics import (
    calculate_price_delta_pct,
    calculate_absolute_change,
    calculate_volume_multiplier,
    calculate_volatility_adjusted_movement,
    calculate_opening_gap_pct,
    calculate_attention_score,
    generate_explainability,
    compute_stock_analytics,
    build_watchlist_summary,
    build_market_pulse
)


def test_price_delta_and_rupee_change():
    current_price = 3241.20
    snapshot_price = 3121.80

    delta_pct = calculate_price_delta_pct(current_price, snapshot_price)
    abs_change = calculate_absolute_change(current_price, snapshot_price)

    assert round(delta_pct, 2) == 3.82
    assert round(abs_change, 2) == 119.40


def test_volume_multiplier():
    current_vol = 2400000
    avg_20d = 1000000
    multiplier = calculate_volume_multiplier(current_vol, avg_20d)
    assert multiplier == 2.4

    # Handle zero division
    assert calculate_volume_multiplier(100, 0) == 1.0


def test_volatility_adjusted_movement():
    delta_pct = 4.8
    typical_vol = 1.6
    vol_adjusted = calculate_volatility_adjusted_movement(delta_pct, typical_vol)
    assert round(vol_adjusted, 2) == 3.0


def test_opening_gap():
    today_open = 1020.0
    prev_close = 1000.0
    gap = calculate_opening_gap_pct(today_open, prev_close)
    assert round(gap, 2) == 2.0


def test_attention_score_and_categories():
    # 1. Significant scenario (High price + High volume + High volatility)
    res_sig = calculate_attention_score(
        price_delta_pct=4.5,
        volume_multiplier=2.8,
        volatility_adjusted_movement=2.9
    )
    assert res_sig["score"] >= 70
    assert res_sig["category"] == "SIGNIFICANT"

    # 2. Worth checking scenario
    res_worth = calculate_attention_score(
        price_delta_pct=2.0,
        volume_multiplier=1.8,
        volatility_adjusted_movement=1.4
    )
    assert 40 <= res_worth["score"] <= 69
    assert res_worth["category"] == "WORTH CHECKING"

    # 3. Quiet scenario (Minimal move)
    res_quiet = calculate_attention_score(
        price_delta_pct=0.2,
        volume_multiplier=1.0,
        volatility_adjusted_movement=0.2
    )
    assert res_quiet["score"] < 40
    assert res_quiet["category"] == "QUIET"


def test_explainability_generation():
    explain_sig = generate_explainability(
        price_delta_pct=3.5,
        volume_multiplier=2.2,
        volatility_adjusted_movement=2.5,
        opening_gap_pct=1.0,
        attention_score=82,
        attention_category="SIGNIFICANT"
    )
    assert "UNUSUAL" in explain_sig["primarySignal"] or "VOLATILITY" in explain_sig["primarySignal"]
    assert len(explain_sig["plainEnglishExplanation"]) > 20

    explain_quiet = generate_explainability(
        price_delta_pct=0.1,
        volume_multiplier=0.9,
        volatility_adjusted_movement=0.1,
        opening_gap_pct=0.0,
        attention_score=15,
        attention_category="QUIET"
    )
    assert explain_quiet["primarySignal"] == "STABLE / QUIET BASELINE"


def test_compute_stock_analytics_end_to_end():
    quote = MarketQuote(
        symbol="TCS",
        companyName="Tata Consultancy Services Ltd",
        price=3241.20,
        previousClose=3121.80,
        open=3150.0,
        high=3260.0,
        low=3140.0,
        volume=2400000,
        avgVolume20D=1000000.0,
        historicalVolatility=1.5,
        timestamp="2026-09-04T09:15:00Z",
        source="LIVE • NSE"
    )

    analytics = compute_stock_analytics(quote, snapshot_price=3121.80, snapshot_timestamp="2026-09-03T15:30:00Z")
    assert analytics.symbol == "TCS"
    assert analytics.priceDeltaPct == 3.82
    assert analytics.absoluteChange == 119.40
    assert analytics.volumeMultiplier == 2.4
    assert analytics.attentionCategory in ("SIGNIFICANT", "WORTH CHECKING")
    assert analytics.whyBreakdown.primarySignal is not None
    assert analytics.whyBreakdown.priceScoreWeight == 40.0
    assert analytics.whyBreakdown.volumeScoreWeight == 30.0
    assert analytics.whyBreakdown.volatilityScoreWeight == 30.0


def test_build_watchlist_summary_and_pulse():
    quote1 = MarketQuote(
        symbol="TCS", companyName="TCS", price=3200.0, previousClose=3000.0,
        open=3050.0, high=3220.0, low=3040.0, volume=2000000, avgVolume20D=1000000.0,
        historicalVolatility=1.5, timestamp="2026-09-04T09:15:00Z", source="LIVE • NSE"
    )
    quote2 = MarketQuote(
        symbol="INFY", companyName="Infosys", price=1500.0, previousClose=1500.0,
        open=1500.0, high=1505.0, low=1495.0, volume=500000, avgVolume20D=500000.0,
        historicalVolatility=1.2, timestamp="2026-09-04T09:15:00Z", source="LIVE • YAHOO FINANCE"
    )

    a1 = compute_stock_analytics(quote1, snapshot_price=3000.0)
    a2 = compute_stock_analytics(quote2, snapshot_price=1500.0)

    summary = build_watchlist_summary([a1, a2], last_checked_timestamp="2026-09-03T10:00:00Z")
    assert summary.totalCount == 2
    assert summary.changedCount >= 1

    pulse = build_market_pulse([a1, a2])
    assert pulse.marketStatus in ("OPEN", "CLOSED", "PRE_MARKET")
    assert pulse.topMover is not None
    assert pulse.topMover["symbol"] == "TCS"
