"""
Verification script for LLM-based Symbol Detection.
Test cases cover:
1. Explicit Regex patterns (Fast Path)
2. LLM Detection (Smart Path)
3. Fallback logic
"""
import sys
import os
import asyncio
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.symbol_detection_service import detect_symbol_smart
from services.ollama_service import check_ollama_health

async def run_verification():
    print("🔍 Starting Symbol Detection Verification...\n")
    
    # Check if Ollama is available
    is_ollama_up = await check_ollama_health()
    if is_ollama_up:
        print("✅ Ollama is ONLINE")
    else:
        print("⚠️  Ollama is OFFLINE - LLM tests might fail or be skipped")
    
    print("\n--- TEST CASE 1: Explicit Pattern (Fast Path) ---")
    text1 = "Bitcoin ($BTC) surges to new highs!"
    print(f"Input: '{text1}'")
    start = time.time()
    res1 = await detect_symbol_smart(text1, title="Crypto Update", asset_type="crypto")
    duration = time.time() - start
    print(f"Result: {res1}")
    print(f"Time: {duration:.4f}s")
    if "BTC" in str(res1) and duration < 0.1:
        print("✅ SUCCESS: Fast path used")
    else:
        print("❌ FAILURE: Fast path missed or too slow")
        
    print("\n--- TEST CASE 2: No Explicit Pattern (LLM Path) ---")
    text2 = "Apple announced new vision pro features today."
    print(f"Input: '{text2}'")
    start = time.time()
    res2 = await detect_symbol_smart(text2, title="Tech News", asset_type="stock")
    duration = time.time() - start
    print(f"Result: {res2}")
    print(f"Time: {duration:.4f}s")
    
    if "AAPL" in str(res2):
        print("✅ SUCCESS: Correct symbol detected")
        if duration > 0.5:
            print("   (Likely used LLM as expected)")
    else:
        print(f"❌ FAILURE: Expected AAPL, got {res2}")

    print("\n--- TEST CASE 3: Ambiguous/Complex (LLM Path) ---")
    text3 = "The social media giant Meta Platforms is facing new regulations in EU."
    print(f"Input: '{text3}'")
    res3 = await detect_symbol_smart(text3, title="Regulation Update", asset_type="stock")
    print(f"Result: {res3}")
    
    if "META" in str(res3):
        print("✅ SUCCESS: Correct symbol detected")
    else:
        print(f"❌ FAILURE: Expected META, got {res3}")

    print("\n--- TEST CASE 4: Crypto Fallback/List ---")
    text4 = "Pepe coin is trending again."
    print(f"Input: '{text4}'")
    res4 = await detect_symbol_smart(text4, title="Meme Coins", asset_type="crypto")
    print(f"Result: {res4}")
    
    if "PEPE" in str(res4):
         print("✅ SUCCESS: Correct symbol detected (could be LLM or List)")
    else:
         print(f"❌ FAILURE: Expected PEPE, got {res4}")

if __name__ == "__main__":
    asyncio.run(run_verification())
