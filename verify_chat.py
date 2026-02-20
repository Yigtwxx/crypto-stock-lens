import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from services.chat_service import chat_with_oracle

async def test_chat():
    print("--- TEST 1: Stock Query (NVDA) ---")
    response_stock = await chat_with_oracle("Analyze NVDA")
    print(f"Sources: {response_stock.get('sources')}")
    print(f"Detected Symbol: {response_stock.get('detected_symbol')}")
    # We can't easily see the internal context without logging, but sources should be 'Piyasa Verileri' not 'Teknik Analiz' if it worked
    
    print("\n--- TEST 2: Crypto Query (BTC) ---")
    response_crypto = await chat_with_oracle("Analyze BTC")
    print(f"Sources: {response_crypto.get('sources')}")
    print(f"Detected Symbol: {response_crypto.get('detected_symbol')}")

    print("\n--- TEST 3: General Stock Query (NASDAQ) ---")
    response_general = await chat_with_oracle("How is NASDAQ performing?")
    print(f"Sources: {response_general.get('sources')}")

if __name__ == "__main__":
    try:
        asyncio.run(test_chat())
    except Exception as e:
        print(f"Test failed: {e}")
