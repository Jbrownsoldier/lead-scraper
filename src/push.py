import os
import sys
import pandas as pd
import asyncio
import aiohttp
from dotenv import load_dotenv

# Configuration
INSTANTLY_CAMPAIGN_ID = "aabd2b29-0087-4e87-bb8f-b0695082f8de" # Website Campaign

async def push_to_instantly(leads: list, api_key: str):
    """Pushes leads to the Instantly campaign via V2 API."""
    url = f"https://api.instantly.ai/v2/campaigns/{INSTANTLY_CAMPAIGN_ID}/leads"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    formatted_leads = []
    for lead in leads:
        # Handle cases where lead is a dict from Pandas
        email = lead.get("email")
        if not email or pd.isna(email):
            continue

        formatted_leads.append({
            "email": email,
            "first_name": "there",
            "last_name": "",
            "company_name": lead.get("business_name", ""),
            "website": lead.get("website", ""),
            "custom_variables": {
                "icebreaker": lead.get("icebreaker", ""),
                "personalizedemailcontent": lead.get("personalizedemailcontent", ""),
                "phone": lead.get("phone", ""),
                "full_address": lead.get("address", ""),
                "website_status": lead.get("website_status", "")
            }
        })

    if not formatted_leads:
        print("[!] No validleads to push.")
        return

    payload = {
        "leads": formatted_leads,
        "skip_if_in_campaign": True
    }

    print(f"[*] Pushing {len(formatted_leads)} verified leads to Instantly...")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status in [200, 201, 202]:
                print("[+] Successfully pushed leads to Instantly!")
                return await resp.json()
            else:
                text = await resp.text()
                print(f"[!] Error pushing to Instantly: {resp.status} - {text}")
                return None

async def main():
    if len(sys.argv) < 2:
        print("Usage: python src/push.py [path_to_verified_csv]")
        return

    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"[!] File not found: {csv_path}")
        return

    load_dotenv()
    instantly_key = os.getenv("INSTANTLY_API_KEY")
    if not instantly_key:
        print("[!] INSTANTLY_API_KEY not found in .env")
        return

    print(f"[*] Loading leads from {csv_path}...")
    try:
        # Load the CSV
        df = pd.read_csv(csv_path)
        
        # If the user filtered by status on Lumrid, they might have a status column.
        # But for simplicity, we push everything in the file they provide.
        leads_list = df.to_dict('records')
        
        await push_to_instantly(leads_list, instantly_key)
        
    except Exception as e:
        print(f"[!] Error processing CSV: {e}")

if __name__ == "__main__":
    asyncio.run(main())
