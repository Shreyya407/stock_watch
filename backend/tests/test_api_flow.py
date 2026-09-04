import uuid
import pytest
import httpx
from app.main import app
from app.storage import get_supabase_client


@pytest.mark.asyncio
async def test_api_health():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "market" in data
        assert data["service"] == "GrowwPulse Backend"


@pytest.mark.asyncio
async def test_api_search_endpoints():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Search with query parameter
        res1 = await client.get("/api/search?q=TCS")
        assert res1.status_code == 200
        items1 = res1.json()
        assert any(item["symbol"] == "TCS" for item in items1)

        # 2. Search all (empty query)
        res_empty = await client.get("/api/search")
        assert res_empty.status_code == 200
        assert len(res_empty.json()) > 10

        # 3. Search with path parameter
        res_path = await client.get("/api/search/RELIANCE")
        assert res_path.status_code == 200
        assert any(item["symbol"] == "RELIANCE" for item in res_path.json())


@pytest.mark.asyncio
async def test_complete_auth_and_snapshot_lifecycle():
    """
    Test the complete live flow:
    New user -> Register -> Add TCS -> Initial snapshot saved -> Fetch current quote ->
    Calculate change -> Display attention score -> Mark Current as Seen ->
    Update snapshot -> Refresh/Re-fetch -> Snapshot remains persisted.
    """
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        unique_id = uuid.uuid4().hex[:8]
        email = f"trader_e2e_{unique_id}@growwpulse.local"
        password = "password123"
        name = "Smart Trader"

        user_id = None
        try:
            # 1. Register User
            reg_res = await client.post("/api/auth/register", json={
                "email": email,
                "password": password,
                "name": name
            })
            assert reg_res.status_code == 200
            reg_data = reg_res.json()
            token = reg_data["token"]
            user_id = reg_data["user"]["id"]
            assert token is not None
            assert reg_data["user"]["email"] == email

            headers = {"Authorization": f"Bearer {token}"}

            # 2. Verify /api/auth/me returns mapped user profile
            me_res = await client.get("/api/auth/me", headers=headers)
            assert me_res.status_code == 200
            assert me_res.json()["id"] == user_id
            assert me_res.json()["email"] == email

            # 3. Add TCS to Watchlist
            add_res = await client.post("/api/watchlist", json={"symbol": "TCS"}, headers=headers)
            assert add_res.status_code == 200
            assert add_res.json()["success"] is True
            assert add_res.json()["symbol"] == "TCS"

            # 4. Get Watchlist
            wl_res = await client.get("/api/watchlist", headers=headers)
            assert wl_res.status_code == 200
            assert "TCS" in wl_res.json()["symbols"]

            # 5. Fetch Watchlist Changes & Analytics
            changes_res = await client.get("/api/watchlist/changes", headers=headers)
            assert changes_res.status_code == 200
            changes_data = changes_res.json()
            assert "stocks" in changes_data
            assert "summary" in changes_data
            assert "pulse" in changes_data

            tcs_stock = next((s for s in changes_data["stocks"] if s["symbol"] == "TCS"), None)
            assert tcs_stock is not None
            assert tcs_stock["currentPrice"] > 0
            assert "attentionScore" in tcs_stock
            assert tcs_stock["attentionCategory"] in ("SIGNIFICANT", "WORTH CHECKING", "QUIET")
            assert tcs_stock["whyBreakdown"]["primarySignal"] is not None

            # 6. Single Quote endpoint
            quote_res = await client.get("/api/quote/TCS", headers=headers)
            assert quote_res.status_code == 200
            assert quote_res.json()["symbol"] == "TCS"

            # 7. Mark Current as Seen
            seen_res = await client.post("/api/watchlist/mark-seen", headers=headers)
            assert seen_res.status_code == 200
            seen_data = seen_res.json()
            tcs_after_seen = next((s for s in seen_data["stocks"] if s["symbol"] == "TCS"), None)
            assert tcs_after_seen is not None
            # Change delta after mark seen should be near 0
            assert abs(tcs_after_seen["priceDeltaPct"]) < 0.1

            # 8. Simulate Page Refresh / Subsequent Fetch (baseline must remain persisted)
            refresh_res = await client.get("/api/watchlist/changes", headers=headers)
            assert refresh_res.status_code == 200
            refresh_data = refresh_res.json()
            tcs_after_refresh = next((s for s in refresh_data["stocks"] if s["symbol"] == "TCS"), None)
            assert tcs_after_refresh is not None
            assert abs(tcs_after_refresh["priceDeltaPct"]) < 0.1

            # 9. Delete Stock from Watchlist
            del_res = await client.delete("/api/watchlist/TCS", headers=headers)
            assert del_res.status_code == 200
            assert del_res.json()["success"] is True

            # 10. Verify empty watchlist
            wl_res_after = await client.get("/api/watchlist", headers=headers)
            assert "TCS" not in wl_res_after.json()["symbols"]

        finally:
            if user_id:
                supa = get_supabase_client()
                if supa:
                    try:
                        supa.auth.admin.delete_user(user_id)
                    except Exception:
                        pass
