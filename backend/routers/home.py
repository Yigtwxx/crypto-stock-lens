"""
Home Router
Handles Home page widget endpoints: funding rates, liquidations, on-chain data, macro calendar, whale trades.
"""
from fastapi import APIRouter
from services.home_service import fetch_funding_rates, fetch_liquidations, fetch_onchain_data, fetch_macro_calendar
from services.onchain_service import fetch_whale_trades

router = APIRouter()


@router.get("/api/home/funding-rates")
async def get_funding_rates():
    """Get real-time funding rates from Binance Futures."""
    return await fetch_funding_rates()


@router.get("/api/home/liquidations")
async def get_liquidations():
    """Get recent large liquidations from Binance Futures."""
    return await fetch_liquidations()


@router.get("/api/home/onchain")
async def get_onchain_data():
    """Get on-chain stats."""
    return await fetch_onchain_data()


@router.get("/api/home/macro-calendar")
async def get_macro_calendar():
    """Get US Economic Calendar (ForexFactory)."""
    return await fetch_macro_calendar()


@router.get("/api/onchain/whales")
async def get_whale_trades():
    """Get on-chain whale trade activity from Binance."""
    return await fetch_whale_trades()
