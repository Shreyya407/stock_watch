from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MarketQuote(BaseModel):
    symbol: str
    companyName: str
    price: float
    previousClose: float
    open: float
    high: float
    low: float
    volume: int
    avgVolume20D: float
    historicalVolatility: float
    timestamp: str
    source: str
    isStale: bool = False
    lastUpdatedSecondsAgo: int = 0
    sparkline: Optional[List[float]] = None
    fiftyTwoWeekHigh: Optional[float] = None
    fiftyTwoWeekLow: Optional[float] = None
    marketCap: Optional[float] = None
    sector: Optional[str] = None
    exchange: Optional[str] = "NSE"


class WhyBreakdown(BaseModel):
    priceScoreWeight: float = 40.0
    volumeScoreWeight: float = 30.0
    volatilityScoreWeight: float = 30.0
    priceContribution: float
    volumeContribution: float
    volatilityContribution: float
    primarySignal: str
    plainEnglishExplanation: str


class StockAnalytics(BaseModel):
    symbol: str
    companyName: str
    currentPrice: float
    snapshotPrice: float
    priceDeltaPct: float
    absoluteChange: float
    volume: int
    avgVolume20D: float
    volumeMultiplier: float
    volatilityAdjustedMovement: float
    openingGapPct: float
    dayChangePct: float
    attentionScore: int
    attentionCategory: str  # SIGNIFICANT, WORTH CHECKING, QUIET
    whyBreakdown: WhyBreakdown
    snapshotTimestamp: Optional[str] = None
    quoteTimestamp: str
    source: str
    isStale: bool = False
    lastUpdatedSecondsAgo: int = 0
    sparkline: Optional[List[float]] = None
    details: Optional[Dict[str, Any]] = None


class WatchlistSummary(BaseModel):
    totalCount: int
    changedCount: int
    significantCount: int
    worthCheckingCount: int
    quietCount: int
    lastCheckedTimestamp: Optional[str] = None
    hasMeaningfulChanges: bool
    summaryText: str


class MarketPulseSummary(BaseModel):
    marketStatus: str  # OPEN, CLOSED, PRE_MARKET
    marketStatusMessage: str
    istTime: str
    topMover: Optional[Dict[str, Any]] = None
    largestVolumeAnomaly: Optional[Dict[str, Any]] = None
    highestAttention: Optional[Dict[str, Any]] = None


class WatchlistChangesResponse(BaseModel):
    summary: WatchlistSummary
    pulse: MarketPulseSummary
    stocks: List[StockAnalytics]


class AddWatchlistRequest(BaseModel):
    symbol: str


class WatchlistActionResponse(BaseModel):
    success: bool
    message: str
    symbol: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class SearchResultItem(BaseModel):
    symbol: str
    name: str
    exchange: str = "NSE"
    sector: Optional[str] = None


class UserProfile(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None


class AuthLoginRequest(BaseModel):
    email: str
    password: str


class AuthRegisterRequest(BaseModel):
    name: Optional[str] = None
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user: UserProfile
    message: str = "Success"

