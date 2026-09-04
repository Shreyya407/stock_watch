import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY", "")

# Initialize Supabase client if credentials available
supabase_client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client, Client
        supabase_client: Optional[Client] = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Warning: Could not initialize Supabase client: {e}. Falling back to local storage.")
        supabase_client = None


class LocalStorageEngine:
    """In-memory resilient fallback engine when Supabase credentials are not provided."""

    def __init__(self):
        # user_id -> set of symbols
        self._watchlists: Dict[str, List[str]] = {}
        # user_id -> { symbol -> { "price": float, "volume": int, "timestamp": str } }
        self._snapshots: Dict[str, Dict[str, Dict[str, Any]]] = {}

        # Default initial stocks for the demo user
        demo_id = "00000000-0000-0000-0000-000000000001"
        self._watchlists[demo_id] = ["TCS", "RELIANCE", "INFY", "TATAMOTORS", "HDFCBANK"]
        # Set slightly offset baseline for initial demo so changes are visible immediately
        yesterday_iso = datetime.now(timezone.utc).isoformat()
        self._snapshots[demo_id] = {
            "TCS": {"price": 2280.0, "volume": 1200000, "timestamp": yesterday_iso},
            "RELIANCE": {"price": 1390.0, "volume": 5500000, "timestamp": yesterday_iso},
            "INFY": {"price": 1460.0, "volume": 3200000, "timestamp": yesterday_iso},
            "TATAMOTORS": {"price": 680.0, "volume": 8500000, "timestamp": yesterday_iso},
            "HDFCBANK": {"price": 1720.0, "volume": 9000000, "timestamp": yesterday_iso},
        }

    def get_watchlist(self, user_id: str) -> List[str]:
        return list(self._watchlists.get(user_id, []))

    def add_to_watchlist(self, user_id: str, symbol: str) -> bool:
        clean_sym = symbol.strip().upper()
        if user_id not in self._watchlists:
            self._watchlists[user_id] = []
        if clean_sym not in self._watchlists[user_id]:
            self._watchlists[user_id].append(clean_sym)
            return True
        return False

    def remove_from_watchlist(self, user_id: str, symbol: str) -> bool:
        clean_sym = symbol.strip().upper()
        if user_id in self._watchlists and clean_sym in self._watchlists[user_id]:
            self._watchlists[user_id].remove(clean_sym)
            if user_id in self._snapshots and clean_sym in self._snapshots[user_id]:
                del self._snapshots[user_id][clean_sym]
            return True
        return False

    def get_snapshot(self, user_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        clean_sym = symbol.strip().upper()
        return self._snapshots.get(user_id, {}).get(clean_sym)

    def get_all_snapshots(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        return self._snapshots.get(user_id, {})

    def save_snapshot(self, user_id: str, symbol: str, price: float, volume: int, timestamp: Optional[str] = None) -> bool:
        clean_sym = symbol.strip().upper()
        if user_id not in self._snapshots:
            self._snapshots[user_id] = {}
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        self._snapshots[user_id][clean_sym] = {
            "price": float(price),
            "volume": int(volume),
            "timestamp": ts
        }
        return True


_local_store = LocalStorageEngine()


class StorageService:
    """
    Storage Service bridging Supabase PostgreSQL tables and local fallback engine.
    Ensures baseline persistence and user isolation.
    """

    async def get_watchlist(self, user_id: str) -> List[str]:
        if supabase_client:
            try:
                res = supabase_client.table("watchlists").select("symbol").eq("user_id", user_id).execute()
                if res.data:
                    return [r["symbol"] for r in res.data]
                return []
            except Exception as e:
                print(f"Supabase get_watchlist error: {e}. Falling back to local.")
        return _local_store.get_watchlist(user_id)

    async def add_to_watchlist(self, user_id: str, symbol: str) -> bool:
        clean_sym = symbol.strip().upper()
        if supabase_client:
            try:
                supabase_client.table("watchlists").upsert({
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "symbol": clean_sym,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }, on_conflict="user_id,symbol").execute()
                return True
            except Exception as e:
                print(f"Supabase add_to_watchlist error: {e}. Falling back to local.")
        return _local_store.add_to_watchlist(user_id, clean_sym)

    async def remove_from_watchlist(self, user_id: str, symbol: str) -> bool:
        clean_sym = symbol.strip().upper()
        if supabase_client:
            try:
                supabase_client.table("watchlists").delete().eq("user_id", user_id).eq("symbol", clean_sym).execute()
                supabase_client.table("snapshots").delete().eq("user_id", user_id).eq("symbol", clean_sym).execute()
                return True
            except Exception as e:
                print(f"Supabase remove_from_watchlist error: {e}. Falling back to local.")
        return _local_store.remove_from_watchlist(user_id, clean_sym)

    async def get_snapshot(self, user_id: str, symbol: str) -> Optional[Dict[str, Any]]:
        clean_sym = symbol.strip().upper()
        if supabase_client:
            try:
                res = supabase_client.table("snapshots").select("*").eq("user_id", user_id).eq("symbol", clean_sym).execute()
                if res.data and len(res.data) > 0:
                    item = res.data[0]
                    return {
                        "price": float(item["price"]),
                        "volume": int(item["volume"]),
                        "timestamp": item.get("timestamp")
                    }
                return None
            except Exception as e:
                print(f"Supabase get_snapshot error: {e}. Falling back to local.")
        return _local_store.get_snapshot(user_id, clean_sym)

    async def get_all_snapshots(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        if supabase_client:
            try:
                res = supabase_client.table("snapshots").select("*").eq("user_id", user_id).execute()
                results = {}
                for item in res.data or []:
                    results[item["symbol"]] = {
                        "price": float(item["price"]),
                        "volume": int(item["volume"]),
                        "timestamp": item.get("timestamp")
                    }
                return results
            except Exception as e:
                print(f"Supabase get_all_snapshots error: {e}. Falling back to local.")
        return _local_store.get_all_snapshots(user_id)

    async def save_snapshot(self, user_id: str, symbol: str, price: float, volume: int, timestamp: Optional[str] = None) -> bool:
        clean_sym = symbol.strip().upper()
        ts = timestamp or datetime.now(timezone.utc).isoformat()
        if supabase_client:
            try:
                supabase_client.table("snapshots").upsert({
                    "id": str(uuid.uuid4()),
                    "user_id": user_id,
                    "symbol": clean_sym,
                    "price": float(price),
                    "volume": int(volume),
                    "timestamp": ts
                }, on_conflict="user_id,symbol").execute()
                return True
            except Exception as e:
                print(f"Supabase save_snapshot error: {e}. Falling back to local.")
        return _local_store.save_snapshot(user_id, clean_sym, price, volume, ts)

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
                timestamp=now_iso
            )
        return True


storage_service = StorageService()
