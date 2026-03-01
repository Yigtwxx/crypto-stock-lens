"""
Asset Detail Service
Fetches detailed information about crypto and stock assets from real APIs.
- Crypto: CoinGecko /coins/{id} API
- Stocks: Yahoo Finance v8 API
"""
import httpx
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from services.cache import home_cache

# Cache duration: 5 minutes
DETAIL_CACHE_DURATION = 300


def _raw_val(obj) -> float:
    """Extract raw value from Yahoo Finance quoteSummary format: {raw: 123, fmt: '$123'}"""
    if obj is None:
        return 0
    if isinstance(obj, dict):
        return obj.get("raw", 0) or 0
    return float(obj) if obj else 0

# ==========================================
# CoinGecko symbol → ID mapping (top coins)
# CoinGecko API requires coin ID, not ticker symbol
# ==========================================
COINGECKO_IDS: Dict[str, str] = {
    "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin", "SOL": "solana",
    "XRP": "ripple", "ADA": "cardano", "DOGE": "dogecoin", "AVAX": "avalanche-2",
    "LINK": "chainlink", "DOT": "polkadot", "MATIC": "matic-network", "POL": "matic-network",
    "SHIB": "shiba-inu", "TRX": "tron", "UNI": "uniswap", "ATOM": "cosmos",
    "LTC": "litecoin", "ETC": "ethereum-classic", "XLM": "stellar", "BCH": "bitcoin-cash",
    "NEAR": "near", "APT": "aptos", "FIL": "filecoin", "ARB": "arbitrum",
    "OP": "optimism", "VET": "vechain", "ALGO": "algorand", "AAVE": "aave",
    "FTM": "fantom", "SAND": "the-sandbox", "MANA": "decentraland", "AXS": "axie-infinity",
    "THETA": "theta-token", "EGLD": "elrond-erd-2", "XTZ": "tezos", "EOS": "eos",
    "FLOW": "flow", "CHZ": "chiliz", "GALA": "gala", "CRV": "curve-dao-token",
    "LDO": "lido-dao", "IMX": "immutable-x", "RENDER": "render-token", "RNDR": "render-token",
    "INJ": "injective-protocol", "SUI": "sui", "SEI": "sei-network", "TIA": "celestia",
    "PEPE": "pepe", "WIF": "dogwifcoin", "BONK": "bonk", "FLOKI": "floki",
    "FET": "fetch-ai", "GRT": "the-graph", "STX": "blockstack", "MKR": "maker",
    "RUNE": "thorchain", "WLD": "worldcoin-wld", "TAO": "bittensor", "JUP": "jupiter-exchange-solana",
    "STRK": "starknet", "NOT": "notcoin", "TON": "the-open-network",
    "JASMY": "jasmycoin", "HBAR": "hedera-hashgraph", "ICP": "internet-computer",
    "KAS": "kaspa", "ENS": "ethereum-name-service", "PYTH": "pyth-network",
    "ORDI": "ordi", "BLUR": "blur", "MASK": "mask-network", "APE": "apecoin",
    "CAKE": "pancakeswap-token", "SNX": "havven", "COMP": "compound-governance-token",
    "CRO": "crypto-com-chain", "QNT": "quant-network", "KAVA": "kava",
    "ZEC": "zcash", "MINA": "mina-protocol", "NEO": "neo", "XMR": "monero",
    "IOTA": "iota", "ZIL": "zilliqa", "DASH": "dash",
    "1INCH": "1inch", "SUSHI": "sushi", "YFI": "yearn-finance",
    "BAT": "basic-attention-token", "LUNC": "terra-luna", "GMT": "stepn",
    "CFX": "conflux-token", "DYDX": "dydx", "OCEAN": "ocean-protocol",
    "SSV": "ssv-network", "RPL": "rocket-pool", "ONDO": "ondo-finance",
    "ENA": "ethena", "W": "wormhole", "PENDLE": "pendle",
}


async def _resolve_coingecko_id(symbol: str) -> Optional[str]:
    """Resolve a crypto symbol to its CoinGecko ID."""
    symbol_upper = symbol.upper()
    if symbol_upper in COINGECKO_IDS:
        return COINGECKO_IDS[symbol_upper]
    
    # Fallback: search CoinGecko API
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/search",
                params={"query": symbol_upper}
            )
            if resp.status_code == 200:
                data = resp.json()
                coins = data.get("coins", [])
                for coin in coins:
                    if coin.get("symbol", "").upper() == symbol_upper:
                        return coin.get("id")
    except Exception:
        pass
    
    # Last resort: try lowercase symbol as ID
    return symbol.lower()


async def fetch_crypto_detail(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed crypto asset information from CoinGecko.
    Returns: description, categories, links, market data, ATH/ATL, supply info.
    """
    cache_key = f"asset_detail_crypto_{symbol.upper()}"
    cached = home_cache.get(cache_key)
    if cached is not None:
        return cached
    
    coin_id = await _resolve_coingecko_id(symbol)
    if not coin_id:
        return None
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"https://api.coingecko.com/api/v3/coins/{coin_id}",
                params={
                    "localization": "false",
                    "tickers": "false",
                    "market_data": "true",
                    "community_data": "true",
                    "developer_data": "true",
                    "sparkline": "false"
                }
            )
            
            if resp.status_code != 200:
                print(f"CoinGecko detail API returned {resp.status_code} for {coin_id}")
                return None
            
            data = resp.json()
            md = data.get("market_data", {})
            
            # Extract description (first 500 chars, strip HTML)
            import re
            desc_raw = data.get("description", {}).get("en", "")
            desc_clean = re.sub(r'<[^>]+>', '', desc_raw)
            description = desc_clean[:1500].strip()
            if len(desc_clean) > 1500:
                description += "..."
            
            # Build links
            links = {}
            links_data = data.get("links", {})
            if links_data.get("homepage") and links_data["homepage"][0]:
                links["website"] = links_data["homepage"][0]
            if links_data.get("blockchain_site") and links_data["blockchain_site"][0]:
                links["explorer"] = links_data["blockchain_site"][0]
            if links_data.get("subreddit_url"):
                links["reddit"] = links_data["subreddit_url"]
            if links_data.get("repos_url", {}).get("github") and links_data["repos_url"]["github"][0]:
                links["github"] = links_data["repos_url"]["github"][0]
            twitter = links_data.get("twitter_screen_name", "")
            if twitter:
                links["twitter"] = f"https://twitter.com/{twitter}"
            
            result = {
                "type": "crypto",
                "symbol": symbol.upper(),
                "name": data.get("name", symbol),
                "logo": data.get("image", {}).get("large", ""),
                "description": description,
                "categories": data.get("categories", [])[:5],
                "genesis_date": data.get("genesis_date"),
                "hashing_algorithm": data.get("hashing_algorithm"),
                "links": links,
                
                # Market data
                "market_cap_rank": data.get("market_cap_rank", 0),
                "price": md.get("current_price", {}).get("usd", 0),
                "market_cap": md.get("market_cap", {}).get("usd", 0),
                "fully_diluted_valuation": md.get("fully_diluted_valuation", {}).get("usd", 0),
                "total_volume": md.get("total_volume", {}).get("usd", 0),
                "change_24h": md.get("price_change_percentage_24h", 0) or 0,
                "change_7d": md.get("price_change_percentage_7d", 0) or 0,
                "change_30d": md.get("price_change_percentage_30d", 0) or 0,
                "change_1y": md.get("price_change_percentage_1y", 0) or 0,
                
                # ATH / ATL
                "ath": md.get("ath", {}).get("usd", 0),
                "ath_change_percentage": md.get("ath_change_percentage", {}).get("usd", 0),
                "ath_date": md.get("ath_date", {}).get("usd", ""),
                "atl": md.get("atl", {}).get("usd", 0),
                "atl_change_percentage": md.get("atl_change_percentage", {}).get("usd", 0),
                "atl_date": md.get("atl_date", {}).get("usd", ""),
                
                # Supply
                "circulating_supply": md.get("circulating_supply", 0),
                "total_supply": md.get("total_supply", 0),
                "max_supply": md.get("max_supply"),
                
                # High / Low
                "high_24h": md.get("high_24h", {}).get("usd", 0),
                "low_24h": md.get("low_24h", {}).get("usd", 0),
                
                # Community data
                "twitter_followers": data.get("community_data", {}).get("twitter_followers", 0) or 0,
                "reddit_subscribers": data.get("community_data", {}).get("reddit_subscribers", 0) or 0,
                "telegram_channel_user_count": data.get("community_data", {}).get("telegram_channel_user_count", 0) or 0,
                
                # Developer data
                "github_stars": data.get("developer_data", {}).get("stars", 0) or 0,
                "github_forks": data.get("developer_data", {}).get("forks", 0) or 0,
                "github_subscribers": data.get("developer_data", {}).get("subscribers", 0) or 0,
                "github_total_issues": data.get("developer_data", {}).get("total_issues", 0) or 0,
                "github_closed_issues": data.get("developer_data", {}).get("closed_issues", 0) or 0,
                "github_pull_requests_merged": data.get("developer_data", {}).get("pull_requests_merged", 0) or 0,
                "commit_count_4_weeks": data.get("developer_data", {}).get("commit_count_4_weeks", 0) or 0,
                
                # Sentiment
                "sentiment_votes_up_percentage": data.get("sentiment_votes_up_percentage", 0) or 0,
                "sentiment_votes_down_percentage": data.get("sentiment_votes_down_percentage", 0) or 0,
                "watchlist_portfolio_users": data.get("watchlist_portfolio_users", 0) or 0,
                
                "timestamp": datetime.now().isoformat()
            }
            
            home_cache.set(cache_key, result, DETAIL_CACHE_DURATION)
            return result
    
    except Exception as e:
        print(f"Error fetching crypto detail for {symbol}: {e}")
        return None


async def fetch_stock_detail(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch detailed stock information from Yahoo Finance.
    Returns: company info, sector, financials, 52-week data.
    """
    cache_key = f"asset_detail_stock_{symbol.upper()}"
    cached = home_cache.get(cache_key)
    if cached is not None:
        return cached
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Accept": "application/json"
            }
            
            # Fetch chart data for price info
            chart_resp = await client.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=5d",
                headers=headers
            )
            
            meta = {}
            if chart_resp.status_code == 200:
                chart_data = chart_resp.json()
                results = chart_data.get("chart", {}).get("result", [])
                if results:
                    meta = results[0].get("meta", {})
            
            price = meta.get("regularMarketPrice", 0) or 0
            prev_close = meta.get("chartPreviousClose", 0) or meta.get("previousClose", 0) or price
            change_24h = ((price - prev_close) / prev_close * 100) if prev_close and price else 0
            
            # Try yfinance for detailed info (description, sector, employees, etc.)
            description = ""
            sector = ""
            industry = ""
            employees = 0
            website = ""
            country = ""
            pe_ratio = 0
            dividend_yield = 0
            year_high = meta.get("fiftyTwoWeekHigh", 0) or 0
            year_low = meta.get("fiftyTwoWeekLow", 0) or 0
            market_cap = 0
            volume = meta.get("regularMarketVolume", 0) or 0
            
            # Defaults for financial data (populated by yfinance if available)
            revenue = 0
            net_income = 0
            earnings_per_share = 0
            forward_eps = 0
            forward_pe = 0
            profit_margin = 0
            operating_margin = 0
            beta = 0
            book_value = 0
            price_to_book = 0
            target_high = 0
            target_low = 0
            target_mean = 0
            recommendation = ""
            avg_50 = 0
            avg_200 = 0
            free_cash_flow = 0
            debt_to_equity = 0
            return_on_equity = 0
            
            try:
                # Direct Yahoo Finance quoteSummary API (no yfinance dependency)
                modules = "assetProfile,financialData,defaultKeyStatistics,summaryDetail"
                summary_url = f"https://query1.finance.yahoo.com/v10/finance/quoteSummary/{symbol}?modules={modules}"
                summary_resp = await client.get(summary_url, headers=headers)
                
                if summary_resp.status_code == 200:
                    summary_data = summary_resp.json()
                    result_data = summary_data.get("quoteSummary", {}).get("result", [])
                    
                    if result_data:
                        modules_data = result_data[0]
                        
                        # Asset Profile
                        profile = modules_data.get("assetProfile", {})
                        description = profile.get("longBusinessSummary", "") or ""
                        if len(description) > 1500:
                            description = description[:1500].strip() + "..."
                        sector = profile.get("sector", "") or ""
                        industry = profile.get("industry", "") or ""
                        employees = profile.get("fullTimeEmployees", 0) or 0
                        website = profile.get("website", "") or ""
                        country = profile.get("country", "") or ""
                        
                        # Financial Data
                        fin = modules_data.get("financialData", {})
                        revenue = _raw_val(fin.get("totalRevenue"))
                        net_income = _raw_val(fin.get("netIncomeToCommon")) or _raw_val(fin.get("ebitda"))
                        earnings_per_share = _raw_val(fin.get("earningsPerShare")) or 0
                        free_cash_flow = _raw_val(fin.get("freeCashflow"))
                        operating_margin_raw = _raw_val(fin.get("operatingMargins"))
                        if operating_margin_raw:
                            operating_margin = round(operating_margin_raw * 100, 2)
                        profit_margin_raw = _raw_val(fin.get("profitMargins"))
                        if profit_margin_raw:
                            profit_margin = round(profit_margin_raw * 100, 2)
                        roe_raw = _raw_val(fin.get("returnOnEquity"))
                        if roe_raw:
                            return_on_equity = round(roe_raw * 100, 2)
                        debt_to_equity = _raw_val(fin.get("debtToEquity")) or 0
                        target_high = _raw_val(fin.get("targetHighPrice")) or 0
                        target_low = _raw_val(fin.get("targetLowPrice")) or 0
                        target_mean = _raw_val(fin.get("targetMeanPrice")) or 0
                        recommendation = fin.get("recommendationKey", "") or ""
                        current_price_fin = _raw_val(fin.get("currentPrice"))
                        if current_price_fin and not price:
                            price = current_price_fin
                        
                        # Default Key Statistics
                        stats = modules_data.get("defaultKeyStatistics", {})
                        forward_eps = _raw_val(stats.get("forwardEps")) or 0
                        forward_pe = _raw_val(stats.get("forwardPE")) or 0
                        pe_ratio = _raw_val(stats.get("trailingPE")) or _raw_val(stats.get("forwardPE")) or 0
                        beta = _raw_val(stats.get("beta")) or 0
                        book_value = _raw_val(stats.get("bookValue")) or 0
                        price_to_book = _raw_val(stats.get("priceToBook")) or 0
                        enterprise_value = _raw_val(stats.get("enterpriseValue")) or 0
                        if not earnings_per_share:
                            earnings_per_share = _raw_val(stats.get("trailingEps")) or 0
                        shares_outstanding = _raw_val(stats.get("sharesOutstanding")) or 0
                        avg_50 = _raw_val(stats.get("fiftyDayAverage")) or 0
                        avg_200 = _raw_val(stats.get("twoHundredDayAverage")) or 0
                        
                        # Summary Detail  
                        detail = modules_data.get("summaryDetail", {})
                        market_cap = _raw_val(detail.get("marketCap")) or 0
                        if not pe_ratio:
                            pe_ratio = _raw_val(detail.get("trailingPE")) or 0
                        dividend_yield_raw = _raw_val(detail.get("dividendYield"))
                        if dividend_yield_raw:
                            dividend_yield = round(dividend_yield_raw * 100, 2)
                        if not year_high:
                            year_high = _raw_val(detail.get("fiftyTwoWeekHigh")) or 0
                        if not year_low:
                            year_low = _raw_val(detail.get("fiftyTwoWeekLow")) or 0
                        if not avg_50:
                            avg_50 = _raw_val(detail.get("fiftyDayAverage")) or 0
                        if not avg_200:
                            avg_200 = _raw_val(detail.get("twoHundredDayAverage")) or 0
                        if not volume:
                            volume = _raw_val(detail.get("volume")) or 0
                else:
                    print(f"Yahoo quoteSummary returned {summary_resp.status_code} for {symbol}")
            except Exception as e:
                print(f"Yahoo quoteSummary failed for {symbol}: {e}")
            
            # If market_cap still 0, calculate from shares outstanding
            if market_cap == 0:
                shares = meta.get("sharesOutstanding", 0) or 0
                if shares > 0 and price > 0:
                    market_cap = price * shares
            
            # Get stock metadata from our service for name
            from services.stock_market_service import STOCK_METADATA, get_stock_logo
            stock_meta = STOCK_METADATA.get(symbol, {"name": meta.get("longName") or symbol, "sector": "Other"})
            
            result = {
                "type": "stock",
                "symbol": symbol.upper(),
                "name": stock_meta.get("name", symbol),
                "logo": get_stock_logo(symbol),
                "description": description,
                "sector": sector or stock_meta.get("sector", ""),
                "industry": industry,
                "country": country,
                "employees": employees,
                "website": website,
                
                # Market data
                "price": float(price),
                "market_cap": float(market_cap),
                "total_volume": float(volume * price) if price else 0,
                "change_24h": round(float(change_24h), 2),
                "pe_ratio": round(float(pe_ratio), 2) if pe_ratio else None,
                "dividend_yield": dividend_yield if dividend_yield else None,
                
                # 52-Week Data
                "fifty_two_week_high": float(year_high),
                "fifty_two_week_low": float(year_low),
                "high_24h": float(meta.get("regularMarketDayHigh", 0) or 0),
                "low_24h": float(meta.get("regularMarketDayLow", 0) or 0),
                
                "links": {"website": website} if website else {},
                
                # Financials
                "revenue": float(revenue) if revenue else None,
                "net_income": float(net_income) if net_income else None,
                "earnings_per_share": round(float(earnings_per_share), 2) if earnings_per_share else None,
                "forward_eps": round(float(forward_eps), 2) if forward_eps else None,
                "forward_pe": round(float(forward_pe), 2) if forward_pe else None,
                "profit_margin": profit_margin if profit_margin else None,
                "operating_margin": operating_margin if operating_margin else None,
                "beta": round(float(beta), 2) if beta else None,
                "book_value": round(float(book_value), 2) if book_value else None,
                "price_to_book": round(float(price_to_book), 2) if price_to_book else None,
                "free_cash_flow": float(free_cash_flow) if free_cash_flow else None,
                "debt_to_equity": round(float(debt_to_equity), 2) if debt_to_equity else None,
                "return_on_equity": return_on_equity if return_on_equity else None,
                
                # Analyst
                "target_high_price": float(target_high) if target_high else None,
                "target_low_price": float(target_low) if target_low else None,
                "target_mean_price": float(target_mean) if target_mean else None,
                "recommendation": recommendation,
                
                # Moving Averages
                "fifty_day_average": round(float(avg_50), 2) if avg_50 else None,
                "two_hundred_day_average": round(float(avg_200), 2) if avg_200 else None,
                
                "timestamp": datetime.now().isoformat()
            }
            
            home_cache.set(cache_key, result, DETAIL_CACHE_DURATION)
            return result
    
    except Exception as e:
        print(f"Error fetching stock detail for {symbol}: {e}")
        return None


async def fetch_asset_detail(symbol: str, asset_type: str = "crypto") -> Optional[Dict[str, Any]]:
    """
    Main entry point: fetch detailed info for any asset.
    """
    if asset_type == "stock" or asset_type == "nasdaq":
        return await fetch_stock_detail(symbol.upper())
    else:
        return await fetch_crypto_detail(symbol.upper())
