"""Pydantic models for API request/response schemas."""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class NewsItem(BaseModel):
    """Schema for a news item."""
    id: str
    title: str
    summary: str
    source: str
    published_at: datetime
    symbol: str
    asset_type: str  # "stock" or "crypto"
    url: Optional[str] = None


class AnalysisRequest(BaseModel):
    """Schema for requesting AI analysis of a news item."""
    news_id: str
    current_price: Optional[float] = None  # Current market price for technical analysis


class TechnicalSignals(BaseModel):
    rsi_signal: Optional[str] = "Neutral"
    support_levels: List[str] = []
    resistance_levels: List[str] = []
    target_price: Optional[str] = None

class SentimentAnalysis(BaseModel):
    """Schema for sentiment analysis results."""
    sentiment: str  # "bullish", "bearish", "neutral"
    confidence: float  # 0.0 to 1.0
    reasoning: str
    historical_context: str
    technical_signals: Optional[TechnicalSignals] = None
    prediction_hash: Optional[str] = None
    tx_hash: Optional[str] = None


class NewsResponse(BaseModel):
    """Schema for news list response."""
    items: List[NewsItem]
    total: int


class FearGreedHistory(BaseModel):
    """Schema for Fear & Greed historical data point."""
    value: int
    classification: str
    date: str


class FearGreedData(BaseModel):
    """Schema for Fear & Greed Index response."""
    value: int  # 0-100
    classification: str  # "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"
    timestamp: str
    history: List[FearGreedHistory] = []


class CoinData(BaseModel):
    """Schema for individual coin data."""
    symbol: str
    name: str = ""
    logo: str = ""
    price: float
    change_24h: float
    volume_24h: float
    high_24h: float
    low_24h: float
    market_cap: float = 0
    market_cap_rank: int = 0


class MarketOverview(BaseModel):
    """Schema for market overview response."""
    coins: List[CoinData]
    total_volume_24h: float
    total_market_cap: float
    btc_dominance: float
    eth_dominance: float = 0
    active_cryptocurrencies: int
    timestamp: str
