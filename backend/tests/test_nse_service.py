import time
import pytest
from app.models import MarketQuote
from app.nse_service import NSEMarketDataService, CacheItem


@pytest.mark.asyncio
async def test_normalization_and_real_quote_fetch():
    service = NSEMarketDataService()
    # Fetch real quote for TCS
    quote = await service.get_quote("TCS")
    
    assert quote.symbol == "TCS"
    assert quote.price > 0
    assert quote.volume >= 0
    assert quote.avgVolume20D > 0
    assert quote.historicalVolatility > 0
    assert quote.source.startswith("LIVE")
    assert quote.isStale is False
    assert quote.companyName is not None


@pytest.mark.asyncio
async def test_cache_hit_and_expiry():
    service = NSEMarketDataService()
    
    # 1. First fetch loads into cache
    q1 = await service.get_quote("INFY")
    assert q1.symbol == "INFY"
    
    # 2. Immediate second fetch should be cache hit
    q2 = await service.get_quote("INFY")
    assert q2.symbol == "INFY"
    assert q2.isStale is False
    
    # 3. Simulate cache expiry
    service._cache["INFY"].cached_at = time.time() - 30
    q3 = await service.get_quote("INFY")
    assert q3.symbol == "INFY"
    # Now fresh again
    assert service._cache["INFY"].cached_at > time.time() - 5


@pytest.mark.asyncio
async def test_stale_fallback_when_providers_fail(monkeypatch):
    service = NSEMarketDataService()
    
    # Seed cache with a valid quote
    cached_quote = MarketQuote(
        symbol="RELIANCE",
        companyName="Reliance Industries Ltd",
        price=1400.0,
        previousClose=1390.0,
        open=1395.0,
        high=1410.0,
        low=1390.0,
        volume=5000000,
        avgVolume20D=4500000.0,
        historicalVolatility=1.8,
        timestamp="2026-09-04T08:00:00Z",
        source="LIVE • NSE"
    )
    service._cache["RELIANCE"] = CacheItem(quote=cached_quote, cached_at=time.time() - 60)

    # Monkeypatch providers to simulate network outage
    monkeypatch.setattr(service, "_fetch_from_nse", lambda s: None)
    monkeypatch.setattr(service, "_fetch_from_yfinance_rest", lambda s: None)

    # Fetch should return stale quote instead of failing
    q_stale = await service.get_quote("RELIANCE")
    assert q_stale.symbol == "RELIANCE"
    assert q_stale.isStale is True
    assert "STALE" in q_stale.source
    assert q_stale.lastUpdatedSecondsAgo >= 60


def test_symbol_search():
    service = NSEMarketDataService()
    results = service.search_symbols("TATA")
    assert len(results) > 0
    symbols = [r.symbol for r in results]
    assert "TATAMOTORS" in symbols or "TATASTEEL" in symbols
