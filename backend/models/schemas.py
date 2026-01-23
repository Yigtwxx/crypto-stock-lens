"""Pydantic models for API request/response schemas."""
from pydantic import BaseModel
from typing import Optional
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


class SentimentAnalysis(BaseModel):
    """Schema for sentiment analysis results."""
    sentiment: str  # "bullish", "bearish", "neutral"
    confidence: float  # 0.0 to 1.0
    reasoning: str
    historical_context: str
    prediction_hash: Optional[str] = None
    tx_hash: Optional[str] = None


class NewsResponse(BaseModel):
    """Schema for news list response."""
    items: list[NewsItem]
    total: int
