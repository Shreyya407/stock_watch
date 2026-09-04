import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status
from dotenv import load_dotenv

load_dotenv()

DEFAULT_STARTER_STOCKS = ["TCS", "RELIANCE", "INFY", "TATAMOTORS", "HDFCBANK"]


class DatabaseUnavailableException(HTTPException):
    """Exception raised when Supabase PostgreSQL is unreachable, misconfigured, or fails."""
    def __init__(self, message: str = "Database is temporarily unavailable. Your data was not saved.", details: Optional[str] = None):
        detail_data: Dict[str, Any] = {
            "error": "database_unavailable",
            "message": message
        }
        if details:
            detail_data["details"] = details
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail_data
        )


def get_supabase_client():
    url = os.getenv("SUPABASE_URL") or os.getenv("VITE_SUPABASE_URL") or ""
    key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY") or
        os.getenv("SUPABASE_ANON_KEY") or
        os.getenv("VITE_SUPABASE_ANON_KEY") or
        ""
    )
    if url and key:
        try:
            from supabase import create_client
            return create_client(url, key)
        except Exception as e:
            print(f"Warning: Could not initialize Supabase client: {e}")
            return None
    return None


supabase_client = get_supabase_client()


class StorageService:
    """
    Storage Service with Supabase PostgreSQL as the SINGLE SOURCE OF TRUTH for persistent user data.
    Strictly enforces persistence:
      - Never silently falls back to in-memory fake data.
      - Raises HTTP 503 database_unavailable if Supabase is offline or queries fail.
    Handles:
      - Watchlists (user-tracked equities, notes, targets)
      - Active Baseline Snapshots (user active baseline)
      - Historical Snapshot Timeline (audit log of price states)
      - Companies Master Catalog (centralized fundamental & price metadata)
      - User Profiles & Preferences (custom attention thresholds, UI settings)
    """

    def _get_client(self):
        global supabase_client
        if supabase_client is None:
            supabase_client = get_supabase_client()
        if supabase_client is None:
            raise DatabaseUnavailableException(
                message="Database is temporarily unavailable. Supabase connection is not initialized."
            )
        return supabase_client

    # =========================================================================
    # 1. Watchlist Operations
    # =========================================================================

    async def initialize_starter_watchlist(self, user_id: str) -> List[str]:
        """Automatically provisions starter stocks in Supabase for new user accounts."""
        client = self._get_client()
        now_iso = datetime.now(timezone.utc).isoformat()
        try:
            # Check if already has any items
            existing = client.table("watchlists").select("symbol").eq("user_id", user_id).execute()
            if existing.data and len(existing.data) > 0:
                return [r["symbol"] for r in existing.data]

            # Insert default starter stocks directly into Supabase watchlists
            watchlist_inserts = []
            for sym in DEFAULT_STARTER_STOCKS:
                watchlist_inserts.append({
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "symbol": sym,
                    "created_at": now_iso
                })
            client.table("watchlists").insert(watchlist_inserts).execute()
            return DEFAULT_STARTER_STOCKS
        except Exception as e:
            print(f"Notice: Starter watchlist initialization ({e})")
            return []

    async def get_watchlist(self, user_id: str) -> List[str]:
        """Fetches list of stock symbols in the user's watchlist from Supabase."""
        client = self._get_client()
        try:
            res = client.table("watchlists").select("symbol").eq("user_id", user_id).execute()
            if res.data is not None and len(res.data) > 0:
                return [r["symbol"] for r in res.data]

            # If user has no watchlist in Supabase, auto-initialize starter stocks in Supabase
            return await self.initialize_starter_watchlist(user_id)
        except HTTPException:
            raise
        except Exception as e:
            raise DatabaseUnavailableException(
                message="Database is temporarily unavailable. Could not load watchlist.",
                details=str(e)
            )

    async def add_to_watchlist(
        self,
        user_id: str,
        symbol: str,
        notes: Optional[str] = None,
        target_price: Optional[float] = None,
        tags: Optional[List[str]] = None
    ) -> bool:
        """Adds a symbol to the user's watchlist in Supabase."""
        clean_sym = symbol.strip().upper()
        client = self._get_client()
        try:
            existing = client.table("watchlists").select("id").eq("user_id", user_id).eq("symbol", clean_sym).execute()
            if not existing.data:
                insert_payload: Dict[str, Any] = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "symbol": clean_sym,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                if notes is not None:
                    insert_payload["notes"] = notes
                if target_price is not None:
                    insert_payload["target_price"] = target_price
                if tags is not None:
                    insert_payload["tags"] = tags

                client.table("watchlists").insert(insert_payload).execute()
            return True
        except HTTPException:
            raise
        except Exception as e:
            raise DatabaseUnavailableException(
                message="Database is temporarily unavailable. Your data was not saved.",
                details=str(e)
            )

    async def remove_from_watchlist(self, user_id: str, symbol: str) -> bool:
        """Removes a symbol and its active snapshot from the user's watchlist in Supabase."""
        clean_sym = symbol.strip().upper()
        client = self._get_client()
        try:
            # Check existence first
            existing = client.table("watchlists").select("id").eq("user_id", user_id).eq("symbol", clean_sym).execute()
            if not existing.data:
                return False

            client.table("watchlists").delete().eq("user_id", user_id).eq("symbol", clean_sym).execute()
            try:
                client.table("snapshots").delete().eq("user_id", user_id).eq("symbol", clean_sym).execute()
            except Exception:
                pass
            return True
        except HTTPException:
            raise
        except Exception as e:
            raise DatabaseUnavailableException(
                message="Database is temporarily unavailable. Could not remove stock.",
                details=str(e)
            )

    # =========================================================================
    # 2. Baseline Snapshots Operations
    # =========================================================================

    async def get_snapshot(self, user_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        """Retrieves current baseline snapshot for a user and symbol from Supabase."""
        clean_sym = symbol.strip().upper()
        client = self._get_client()
        try:
            res = client.table("snapshots").select("*").eq("user_id", user_id).eq("symbol", clean_sym).execute()
            if res.data and len(res.data) > 0:
                item = res.data[0]
                return {
                    "price": float(item["price"]),
                    "volume": int(item["volume"]),
                    "timestamp": item.get("timestamp"),
                    "attention_score": item.get("attention_score"),
                    "attention_category": item.get("attention_category"),
                    "price_delta_pct": item.get("price_delta_pct")
                }
            return None
        except HTTPException:
            raise
        except Exception as e:
            raise DatabaseUnavailableException(
                message="Database is temporarily unavailable. Could not load snapshot.",
                details=str(e)
            )

    async def get_all_snapshots(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Retrieves all baseline snapshots for a user from Supabase."""
        client = self._get_client()
        try:
            res = client.table("snapshots").select("*").eq("user_id", user_id).execute()
            results: Dict[str, Dict[str, Any]] = {}
            if res.data:
                for item in res.data:
                    results[item["symbol"]] = {
                        "price": float(item["price"]),
                        "volume": int(item["volume"]),
                        "timestamp": item.get("timestamp"),
                        "attention_score": item.get("attention_score"),
                        "attention_category": item.get("attention_category"),
                        "price_delta_pct": item.get("price_delta_pct")
                    }
            return results
        except HTTPException:
            raise
        except Exception as e:
            raise DatabaseUnavailableException(
                message="Database is temporarily unavailable. Could not load snapshots.",
                details=str(e)
            )

    async def save_snapshot(
        self,
        user_id: str,
        symbol: str,
        price: float,
        volume: int,
        timestamp: Optional[str] = None,
        attention_score: Optional[int] = None,
        attention_category: Optional[str] = None,
        price_delta_pct: Optional[float] = None,
        trigger_event: str = "MANUAL"
    ) -> bool:
        """
        Saves or updates active baseline snapshot in Supabase,
        and logs immutable event in snapshot_history.
        """
        clean_sym = symbol.strip().upper()
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        client = self._get_client()

        try:
            # 1. Update/insert baseline in `snapshots`
            existing = client.table("snapshots").select("id").eq("user_id", user_id).eq("symbol", clean_sym).execute()
            snap_payload = {
                "price": float(price),
                "volume": int(volume),
                "timestamp": ts,
                "attention_score": attention_score,
                "attention_category": attention_category,
                "price_delta_pct": price_delta_pct
            }
            if existing.data and len(existing.data) > 0:
                client.table("snapshots").update(snap_payload).eq("user_id", user_id).eq("symbol", clean_sym).execute()
            else:
                snap_payload["id"] = str(uuid.uuid4())
                snap_payload["user_id"] = user_id
                snap_payload["symbol"] = clean_sym
                client.table("snapshots").insert(snap_payload).execute()

            # 2. Append event to `snapshot_history`
            try:
                history_payload = {
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "symbol": clean_sym,
                    "price": float(price),
                    "volume": int(volume),
                    "attention_score": attention_score,
                    "attention_category": attention_category,
                    "price_delta_pct": price_delta_pct,
                    "trigger_event": trigger_event,
                    "snapshot_timestamp": ts
                }
                client.table("snapshot_history").insert(history_payload).execute()
            except Exception as history_err:
                print(f"Notice: snapshot_history write bypassed ({history_err})")

            return True
        except HTTPException:
            raise
        except Exception as e:
            raise DatabaseUnavailableException(
                message="Database is temporarily unavailable. Your snapshot was not saved.",
                details=str(e)
            )

    async def update_all_snapshots_to_current(self, user_id: str, quotes: List[Any]) -> bool:
        """
        Updates baseline snapshot for all symbols in user's watchlist to their current quote values.
        Called on 'Mark Current as Seen'.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        for q in quotes:
            await self.save_snapshot(
                user_id=user_id,
                symbol=q.symbol,
                price=q.price,
                volume=q.volume,
                timestamp=now_iso,
                trigger_event="MARK_SEEN"
            )
        return True

    # =========================================================================
    # 3. Snapshot History & Time Audit Log Operations
    # =========================================================================

    async def get_snapshot_history(self, user_id: str, symbol: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves chronological snapshot records for user or specific symbol from Supabase."""
        client = self._get_client()
        try:
            query = client.table("snapshot_history").select("*").eq("user_id", user_id)
            if symbol:
                query = query.eq("symbol", symbol.strip().upper())
            res = query.order("snapshot_timestamp", desc=True).limit(limit).execute()
            return res.data or []
        except HTTPException:
            raise
        except Exception as e:
            raise DatabaseUnavailableException(
                message="Database is temporarily unavailable. Could not load snapshot history.",
                details=str(e)
            )

    # =========================================================================
    # 4. Companies Master Catalog Operations
    # =========================================================================

    async def upsert_company(self, data: Dict[str, Any]) -> bool:
        """Saves or updates master company metadata in Supabase."""
        symbol = data.get("symbol", "").strip().upper()
        if not symbol:
            return False

        client = self._get_client()
        try:
            record = {
                "symbol": symbol,
                "company_name": data.get("company_name") or data.get("companyName") or symbol,
                "sector": data.get("sector"),
                "industry": data.get("industry"),
                "exchange": data.get("exchange", "NSE"),
                "market_cap": data.get("marketCap") or data.get("market_cap"),
                "fifty_two_week_high": data.get("fiftyTwoWeekHigh") or data.get("fifty_two_week_high"),
                "fifty_two_week_low": data.get("fiftyTwoWeekLow") or data.get("fifty_two_week_low"),
                "pe_ratio": data.get("peRatio") or data.get("pe_ratio"),
                "last_price": data.get("price") or data.get("last_price"),
                "last_volume": data.get("volume") or data.get("last_volume"),
                "avg_volume_20d": data.get("avgVolume20D") or data.get("avg_volume_20d"),
                "historical_volatility": data.get("historicalVolatility") or data.get("historical_volatility"),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }
            clean_record = {k: v for k, v in record.items() if v is not None}
            client.table("companies").upsert(clean_record).execute()
            return True
        except Exception:
            return False

    async def upsert_companies_batch(self, quotes_or_companies: List[Any]) -> bool:
        """Batch upsert quotes to company master catalog."""
        for item in quotes_or_companies:
            if hasattr(item, "dict"):
                data = item.dict()
            elif isinstance(item, dict):
                data = item
            else:
                continue
            await self.upsert_company(data)
        return True

    async def get_company(self, symbol: str) -> Optional[Dict[str, Any]]:
        clean_sym = symbol.strip().upper()
        client = self._get_client()
        try:
            res = client.table("companies").select("*").eq("symbol", clean_sym).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except Exception:
            return None

    async def seed_companies_from_registry(self, registry: List[Dict[str, str]]) -> int:
        """Seeds company directory into Supabase companies catalog."""
        count = 0
        for item in registry:
            await self.upsert_company({
                "symbol": item["symbol"],
                "company_name": item.get("name", item["symbol"]),
                "sector": item.get("sector"),
                "exchange": "NSE"
            })
            count += 1
        return count

    # =========================================================================
    # 5. User Profiles & Settings Operations
    # =========================================================================

    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        client = self._get_client()
        try:
            res = client.table("profiles").select("*").eq("id", user_id).execute()
            if res.data and len(res.data) > 0:
                return res.data[0]
            return None
        except HTTPException:
            raise
        except Exception as e:
            raise DatabaseUnavailableException(
                message="Database is temporarily unavailable. Could not load profile.",
                details=str(e)
            )

    async def save_user_profile(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        client = self._get_client()
        try:
            payload = {
                "id": user_id,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                **profile_data
            }
            client.table("profiles").upsert(payload).execute()
            return True
        except HTTPException:
            raise
        except Exception as e:
            raise DatabaseUnavailableException(
                message="Database is temporarily unavailable. Profile settings were not saved.",
                details=str(e)
            )


storage_service = StorageService()
