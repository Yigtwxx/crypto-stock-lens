"""
Liquidation Router
Handles liquidation heatmap, history, levels, and market candles.
"""
from fastapi import APIRouter
from services.liquidation_service import liquidation_service

router = APIRouter()


@router.get("/api/liquidations/heatmap")
async def get_liquidation_heatmap():
    """
    Get live liquidation heatmap data.
    Aggregated from real-time Binance WebSocket stream.
    """
    return await liquidation_service.get_heatmap_data()


@router.get("/api/liquidations/history/{symbol}")
async def get_liquidation_history(symbol: str):
    """
    Get all stored liquidation history for a specific symbol.
    Start building your heat profile from this data.
    """
    return await liquidation_service.get_liquidation_history(symbol)


@router.get("/api/liquidations/levels/{symbol}")
async def get_liquidation_levels(
    symbol: str,
    price_min: float,
    price_max: float,
    num_bins: int = 100,
    leverage: int = 50
):
    """
    Get cumulative liquidation levels grouped by price bins.
    For Coinglass-style heatmap visualization.
    """
    return await liquidation_service.get_liquidation_levels(
        symbol=symbol,
        price_min=price_min,
        price_max=price_max,
        num_bins=num_bins,
        leverage=leverage
    )


@router.get("/api/market/candles/{symbol}")
async def get_market_candles(symbol: str, interval: str = "1h"):
    """
    Get OHLCV candles for chart backfilling.
    Default: 1h interval, 1 week limit.
    """
    return await liquidation_service.fetch_candles(symbol, interval)
