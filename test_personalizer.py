import os
import asyncio
import sys

# Add src to path
sys.path.append(os.getcwd())

from src.personalizer import Personalizer
from dotenv import load_dotenv

async def test_personalizer():
    load_dotenv()
    p = Personalizer()
    
    lead = {
        "business_name": "Manchester Removals",
        "address": "Manchester, UK",
        "website": "http://example.com",
        "website_status": "Redesign Opportunity",
        "audit_issues": ["No SSL", "No Mobile Viewport"]
    }
    
    print("Personalizing lead...")
    result = await p.research_and_personalize(lead)
    print("\n--- RESULTS ---")
    print(f"Icebreaker: {result.get('icebreaker')}")
    print(f"Content: {result.get('personalizedemailcontent')}")
    print(f"CEO Name: {result.get('ceo_name')}")

if __name__ == "__main__":
    asyncio.run(test_personalizer())
