import os
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    MarketQuote,
    StockAnalytics,
    WatchlistChangesResponse,
    AddWatchlistRequest,
    WatchlistActionResponse,
    SearchResultItem,
    UserProfile
)
from app.auth import get_current_user
from app.storage import storage_service
from app.nse_service import nse_service
from app.analytics import (
    get_indian_market_status,
    compute_stock_analytics,
    build_watchlist_summary,
    build_market_pulse
)

app = FastAPI(
    title="GrowwPulse API",
    description="Smart Change-First Market Watchlist Backend for Indian Equities",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", summary="Health Check")
async def health_check():
    market_info = get_indian_market_status()
    return {
        "status": "healthy",
        "service": "GrowwPulse Backend",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market": market_info
    }


@app.get("/api/market-status", summary="Get Indian Market Hours Status")
async def get_market_status():
    return get_indian_market_status()


@app.get("/api/watchlist", summary="Get User Watchlist Symbols")
async def get_watchlist(user: UserProfile = Depends(get_current_user)):
    symbols = await storage_service.get_watchlist(user.id)
    return {"symbols": symbols, "count": len(symbols)}


@app.post("/api/watchlist", response_model=WatchlistActionResponse, summary="Add Stock to Watchlist")
async def add_stock(
    request: AddWatchlistRequest,
    user: UserProfile = Depends(get_current_user)
):
    clean_sym = request.symbol.strip().upper().replace(".NS", "")
    if not clean_sym:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock symbol cannot be empty."
        )

    # 1. Validate real market quote exists
    try:
        quote = await nse_service.get_quote(clean_sym)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not validate symbol '{clean_sym}' with real market data: {str(e)}"
        )

    # 2. Add to watchlist
    await storage_service.add_to_watchlist(user.id, clean_sym)

    # 3. Save baseline snapshot if not already present
    existing_snapshot = await storage_service.get_snapshot(user.id, clean_sym)
    if not existing_snapshot:
        await storage_service.save_snapshot(
            user_id=user.id,
            symbol=clean_sym,
            price=quote.price,
            volume=quote.volume
        )

    return WatchlistActionResponse(
        success=True,
        message=f"Added {clean_sym} to your watchlist.",
        symbol=clean_sym,
        data={
            "price": quote.price,
            "companyName": quote.companyName,
            "source": quote.source
        }
    )


@app.delete("/api/watchlist/{symbol}", response_model=WatchlistActionResponse, summary="Remove Stock from Watchlist")
async def remove_stock(
    symbol: str,
    user: UserProfile = Depends(get_current_user)
):
    clean_sym = symbol.strip().upper().replace(".NS", "")
    removed = await storage_service.remove_from_watchlist(user.id, clean_sym)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Symbol '{clean_sym}' was not found in your watchlist."
        )

    return WatchlistActionResponse(
        success=True,
        message=f"Removed {clean_sym} from your watchlist.",
        symbol=clean_sym
    )


@app.get("/api/watchlist/quotes", response_model=List[MarketQuote], summary="Get Raw Quotes for Watchlist")
async def get_watchlist_quotes(user: UserProfile = Depends(get_current_user)):
    symbols = await storage_service.get_watchlist(user.id)
    if not symbols:
        return []
    quotes = await nse_service.get_quotes_batch(symbols)
    return quotes


@app.get("/api/watchlist/changes", response_model=WatchlistChangesResponse, summary="Get Watchlist Changes & Attention Analytics")
async def get_watchlist_changes(user: UserProfile = Depends(get_current_user)):
    symbols = await storage_service.get_watchlist(user.id)
    if not symbols:
        empty_summary = build_watchlist_summary([])
        empty_pulse = build_market_pulse([])
        return WatchlistChangesResponse(
            summary=empty_summary,
            pulse=empty_pulse,
            stocks=[]
        )

    # 1. Fetch user baseline snapshots
    snapshots = await storage_service.get_all_snapshots(user.id)

    # 2. Fetch live market quotes for all symbols concurrently
    quotes = await nse_service.get_quotes_batch(symbols)

    # 3. Compute analytics per stock
    analytics_list: List[StockAnalytics] = []
    latest_snapshot_ts: Optional[str] = None

    for quote in quotes:
        snap = snapshots.get(quote.symbol)
        if snap is None:
            # First time seeing this quote: initialize snapshot baseline
            await storage_service.save_snapshot(
                user_id=user.id,
                symbol=quote.symbol,
                price=quote.price,
                volume=quote.volume
            )
            snap_price = quote.price
            snap_ts = quote.timestamp
        else:
            snap_price = snap.get("price", quote.price)
            snap_ts = snap.get("timestamp")

        if snap_ts and (latest_snapshot_ts is None or snap_ts > latest_snapshot_ts):
            latest_snapshot_ts = snap_ts

        analytics = compute_stock_analytics(
            quote=quote,
            snapshot_price=snap_price,
            snapshot_timestamp=snap_ts
        )
        analytics_list.append(analytics)

    # 4. Sort by attentionScore descending by default
    analytics_list.sort(key=lambda s: s.attentionScore, reverse=True)

    # 5. Build summary & market pulse
    summary = build_watchlist_summary(analytics_list, last_checked_timestamp=latest_snapshot_ts)
    pulse = build_market_pulse(analytics_list)

    return WatchlistChangesResponse(
        summary=summary,
        pulse=pulse,
        stocks=analytics_list
    )


@app.post("/api/watchlist/mark-seen", response_model=WatchlistChangesResponse, summary="Mark Current Market State as New Baseline")
async def mark_current_as_seen(user: UserProfile = Depends(get_current_user)):
    """
    Updates the baseline snapshot for all symbols in the user's watchlist to current market prices.
    After this call, changes relative to baseline will be reset to ~0%.
    """
    symbols = await storage_service.get_watchlist(user.id)
    if not symbols:
        empty_summary = build_watchlist_summary([])
        empty_pulse = build_market_pulse([])
        return WatchlistChangesResponse(
            summary=empty_summary,
            pulse=empty_pulse,
            stocks=[]
        )

    # 1. Fetch current quotes
    quotes = await nse_service.get_quotes_batch(symbols)

    # 2. Update all baseline snapshots
    await storage_service.update_all_snapshots_to_current(user.id, quotes)

    # 3. Re-fetch changes with updated baseline
    return await get_watchlist_changes(user=user)


@app.get("/api/quote/{symbol}", response_model=StockAnalytics, summary="Get Single Stock Analytics")
async def get_single_quote(symbol: str, user: UserProfile = Depends(get_current_user)):
    clean_sym = symbol.strip().upper().replace(".NS", "")
    try:
        quote = await nse_service.get_quote(clean_sym)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Quote not found for '{clean_sym}': {str(e)}"
        )

    snap = await storage_service.get_snapshot(user.id, clean_sym)
    snap_price = snap.get("price") if snap else quote.price
    snap_ts = snap.get("timestamp") if snap else quote.timestamp

    return compute_stock_analytics(
        quote=quote,
        snapshot_price=snap_price,
        snapshot_timestamp=snap_ts
    )


@app.get("/api/search", response_model=List[SearchResultItem], summary="Search NSE Equities (Query param or all)")
async def search_stocks_all(q: Optional[str] = ""):
    return nse_service.search_symbols(q or "")


@app.get("/api/search/{query}", response_model=List[SearchResultItem], summary="Search NSE Equities (Path param)")
async def search_stocks_path(query: str):
    return nse_service.search_symbols(query)

