import os
import uuid
import pytest
from unittest.mock import patch
from fastapi import HTTPException
from app.storage import StorageService, DatabaseUnavailableException, get_supabase_client
from app.models import MarketQuote


@pytest.fixture
def supabase_test_user():
    """Creates a real test user in Supabase auth for isolated integration tests, then cleans up."""
    client = get_supabase_client()
    if not client:
        pytest.skip("Supabase client not configured")
    
    unique_email = f"test_store_{uuid.uuid4().hex[:8]}@growwpulse.test"
    user_res = client.auth.admin.create_user({
        "email": unique_email,
        "password": "password123!",
        "email_confirm": True,
        "user_metadata": {"name": "Test Trader"}
    })
    user_id = str(user_res.user.id)
    yield user_id

    # Teardown: delete user (cascades to watchlists, snapshots, profiles)
    try:
        client.auth.admin.delete_user(user_id)
    except Exception:
        pass


@pytest.mark.asyncio
async def test_real_supabase_watchlist_crud_and_user_isolation(supabase_test_user):
    storage = StorageService()
    user_a = supabase_test_user

    # Create a second user to test strict isolation
    client = get_supabase_client()
    u2_res = client.auth.admin.create_user({
        "email": f"test_store_b_{uuid.uuid4().hex[:8]}@growwpulse.test",
        "password": "password123!",
        "email_confirm": True
    })
    user_b = str(u2_res.user.id)

    try:
        # Add stocks to user A
        await storage.add_to_watchlist(user_a, "TCS")
        await storage.add_to_watchlist(user_a, "INFY")

        # Add stocks to user B
        await storage.add_to_watchlist(user_b, "RELIANCE")

        list_a = await storage.get_watchlist(user_a)
        list_b = await storage.get_watchlist(user_b)

        # Verify User A has TCS & INFY, but NOT RELIANCE
        assert "TCS" in list_a
        assert "INFY" in list_a
        assert "RELIANCE" not in list_a

        # Verify User B has RELIANCE, but NOT TCS/INFY
        assert "RELIANCE" in list_b
        assert "TCS" not in list_b
        assert "INFY" not in list_b

        # Remove from user A
        await storage.remove_from_watchlist(user_a, "TCS")
        updated_a = await storage.get_watchlist(user_a)
        assert "TCS" not in updated_a
        assert "INFY" in updated_a

    finally:
        try:
            client.auth.admin.delete_user(user_b)
        except Exception:
            pass


@pytest.mark.asyncio
async def test_real_supabase_snapshot_persistence_and_mark_seen(supabase_test_user):
    storage = StorageService()
    user = supabase_test_user

    # 1. Save initial baseline snapshot
    await storage.save_snapshot(user, "TCS", price=3000.0, volume=1500000, timestamp="2026-09-01T10:00:00Z")

    snap = await storage.get_snapshot(user, "TCS")
    assert snap is not None
    assert snap["price"] == 3000.0
    assert snap["volume"] == 1500000

    # 2. Update baseline on Mark Seen
    new_quote = MarketQuote(
        symbol="TCS",
        companyName="Tata Consultancy Services Ltd",
        price=3200.0,
        previousClose=3100.0,
        open=3150.0,
        high=3220.0,
        low=3140.0,
        volume=2500000,
        avgVolume20D=2000000.0,
        historicalVolatility=1.2,
        timestamp="2026-09-04T14:00:00Z",
        source="LIVE • NSE"
    )

    await storage.update_all_snapshots_to_current(user, [new_quote])

    updated_snap = await storage.get_snapshot(user, "TCS")
    assert updated_snap is not None
    assert updated_snap["price"] == 3200.0
    assert updated_snap["volume"] == 2500000


@pytest.mark.asyncio
async def test_real_supabase_profiles_persistence(supabase_test_user):
    storage = StorageService()
    user_id = supabase_test_user

    # Save user preferences in public.profiles table
    await storage.save_user_profile(user_id, {
        "attention_threshold": 48,
        "default_sort": "volume",
        "theme": "dark"
    })

    profile = await storage.get_user_profile(user_id)
    assert profile is not None
    assert profile.get("id") == user_id
    assert profile.get("attention_threshold") == 48
    assert profile.get("default_sort") == "volume"


@pytest.mark.asyncio
async def test_database_failure_does_not_silently_fallback():
    """
    CRITICAL ARCHITECTURE REQUIREMENT:
    When Supabase is unavailable or fails, storage operations MUST raise
    HTTP 503 database_unavailable and NEVER silently fall back to fake in-memory persistence.
    """
    storage = StorageService()

    # Simulate Supabase client being None (disconnected / outage)
    with patch.object(storage, "_get_client", side_effect=DatabaseUnavailableException("Database is offline")):
        
        # 1. get_watchlist must fail with 503
        with pytest.raises(HTTPException) as exc_info:
            await storage.get_watchlist("any-user-id")
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail.get("error") == "database_unavailable"

        # 2. add_to_watchlist must fail with 503
        with pytest.raises(HTTPException) as exc_info:
            await storage.add_to_watchlist("any-user-id", "TCS")
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail.get("error") == "database_unavailable"

        # 3. save_snapshot must fail with 503
        with pytest.raises(HTTPException) as exc_info:
            await storage.save_snapshot("any-user-id", "TCS", 3000.0, 1000000)
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail.get("error") == "database_unavailable"

        # 4. get_all_snapshots must fail with 503
        with pytest.raises(HTTPException) as exc_info:
            await storage.get_all_snapshots("any-user-id")
        assert exc_info.value.status_code == 503
        assert exc_info.value.detail.get("error") == "database_unavailable"
