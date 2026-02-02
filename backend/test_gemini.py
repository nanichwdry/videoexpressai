import asyncio
import sys
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

print(f"GEMINI_API_KEY loaded: {os.getenv('GEMINI_API_KEY')[:20]}..." if os.getenv('GEMINI_API_KEY') else "GEMINI_API_KEY: NOT FOUND")

sys.path.insert(0, os.path.dirname(__file__))

from utils.gemini_helper import enhance_prompt

async def test():
    result = await enhance_prompt("cat on beach")
    print("\n=== GEMINI TEST ===")
    print(f"Used Gemini: {result.get('used_gemini')}")
    print(f"Original: {result.get('original_prompt')}")
    print(f"Enhanced: {result.get('enhanced_prompt')}")
    if 'error' in result:
        print(f"Error: {result['error']}")

if __name__ == "__main__":
    asyncio.run(test())
