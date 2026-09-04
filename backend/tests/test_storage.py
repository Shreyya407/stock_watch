import pytest
from app.storage import StorageService
from app.models import MarketQuote


@pytest.mark.asyncio
async def test_watchlist_crud_and_user_isolation():
    storage = StorageService()
    user_a = "user-test-aaa"
    user_b = "user-test-bbb"

    # Add stocks to user A
    await storage.add_to_watchlist(user_a, "TCS")
    await storage.add_to_watchlist(user_a, "INFY")

    # Add stocks to user B
    await storage.add_to_watchlist(user_b, "RELIANCE")

    list_a = await storage.get_watchlist(user_a)
    list_b = await storage.get_watchlist(user_b)

    assert "TCS" in list_a
    assert "INFY" in list_a
    assert "RELIANCE" not in list_a

    assert "RELIANCE" in list_b
    assert "TCS" not in list_b

    # Remove from user A
    await storage.remove_from_watchlist(user_a, "TCS")
    updated_a = await storage.get_watchlist(user_a)
    assert "TCS" not in updated_a


@pytest.mark.asyncio
async def test_baseline_snapshot_persistence():
    storage = StorageService()
    user = "user-snapshot-test"

    # Save initial baseline snapshot
    await storage.save_snapshot(user, "TCS", price=3000.0, volume=1500000, timestamp="2026-09-01T10:00:00Z")

    snap = await storage.get_snapshot(user, "TCS")
    assert snap is not None
    assert snap["price"] == 3000.0
    assert snap["volume"] == 1500000
    assert snap["timestamp"] == "2026-09-01T10:00:00Z"


@pytest.mark.asyncio
async def test_mark_seen_updates_baseline_snapshots():
    storage = StorageService()
    user = "user-mark-seen-test"

    # Initial baseline
    await storage.save_snapshot(user, "HDFCBANK", price=1600.0, volume=5000000, timestamp="2026-09-01T09:15:00Z")

    # Simulate updated quote
    new_quote = MarketQuote(
        symbol="HDFCBANK",
        companyName="HDFC Bank Ltd",
        price=1650.0,
        previousClose=1620.0,
        open=1625.0,
        high=1660.0,
        low=1620.0,
        volume=6200000,
        avgVolume20D=5000000.0,
        historicalVolatility=1.4,
        timestamp="2026-09-04T12:00:00Z",
        source="LIVE • NSE"
    )

    # Trigger update on mark seen
    await storage.update_all_snapshots_to_current(user, [new_quote])

    updated_snap = await storage.get_snapshot(user, "HDFCBANK")
    assert updated_snap is not None
    assert updated_snap["price"] == 1650.0
    assert updated_snap["volume"] == 6200000
    assert updated_snap["timestamp"] != "2026-09-01T09:15:00Z"
