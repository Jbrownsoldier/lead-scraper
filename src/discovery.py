import os
import sys
import aiohttp
import asyncio
from typing import List, Dict, Any

class GooglePlacesDiscovery:
    def __init__(self, api_key: str):
        self.api_key = api_key
        # Using the New Places API (Text Search)
        self.text_search_url = "https://places.googleapis.com/v1/places:searchText"

    async def _fetch_page(self, session: aiohttp.ClientSession, query: str, page_token: str = None) -> Dict[str, Any]:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.businessStatus,nextPageToken"
        }
        
        payload = {
            "textQuery": query,
            "pageSize": 20 # Max 20 results per page for Text Search
        }
        
        if page_token:
            payload["pageToken"] = page_token

        async with session.post(self.text_search_url, headers=headers, json=payload) as response:
            if response.status != 200:
                print(f"Error fetching data from Google Places: {response.status}")
                text = await response.text()
                print(f"Details: {text}")
                return {}
            
            return await response.json()

    async def search_leads(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Searches Google Places API for leads matching the query.
        Handles pagination up to max_results.
        """
        if not self.api_key:
            print("Error: GOOGLE_PLACES_API_KEY is not set.")
            sys.exit(1)

        print(f"[*] Discovering leads for query: '{query}'...")
        all_places = []
        page_token = None
        
        async with aiohttp.ClientSession() as session:
            while len(all_places) < max_results:
                data = await self._fetch_page(session, query, page_token)
                
                places = data.get("places", [])
                if not places:
                    break
                    
                for place in places:
                    # Map new API fields to manageable dictionary
                    lead = {
                        "business_name": place.get("displayName", {}).get("text", "Unknown"),
                        "address": place.get("formattedAddress", "Unknown"),
                        "phone": place.get("nationalPhoneNumber", ""),
                        "website": place.get("websiteUri", ""),
                        "maps_status": place.get("businessStatus", "UNKNOWN")
                    }
                    all_places.append(lead)
                    
                    if len(all_places) >= max_results:
                        break
                
                page_token = data.get("nextPageToken")
                if not page_token:
                    break # No more pages
                    
                # Small delay to respect API rate limits
                await asyncio.sleep(1)

        print(f"[*] Discovery complete. Found {len(all_places)} initial records.")
        return all_places

# Quick test execution block
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
    if not API_KEY:
        print("Please set GOOGLE_PLACES_API_KEY in your .env file to run this test.")
        sys.exit(1)
        
    async def test():
        discovery = GooglePlacesDiscovery(API_KEY)
        results = await discovery.search_leads("plumbers in austin tx", max_results=5)
        for r in results:
            print(r)
            
    asyncio.run(test())
