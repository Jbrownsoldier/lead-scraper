import argparse
import asyncio
import os
import sys
import json
import logging
from dotenv import load_dotenv

# Import modules
from discovery import GooglePlacesDiscovery
from validator import Validator
from scorer import Scorer
from exporter import Exporter
from enrichment import EnrichmentModule
from deduplicator import Deduplicator
from personalizer import Personalizer

import aiohttp

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
        formatted_leads.append({
            "email": lead.get("email", ""),
            "first_name": lead.get("ceo_name", "").split()[0] if lead.get("ceo_name") else "there",
            "last_name": lead.get("ceo_name", "").split()[-1] if lead.get("ceo_name") and len(lead.get("ceo_name").split()) > 1 else "",
            "company_name": lead.get("business_name", ""),
            "website": lead.get("website", ""),
            "custom_variables": {
                "icebreaker": lead.get("icebreaker", ""),
                "phone": lead.get("phone", ""),
                "full_address": lead.get("address", ""),
                "website_status": lead.get("website_status", "")
            }
        })

    payload = {
        "leads": formatted_leads,
        "skip_if_in_campaign": True
    }

    print(f"[*] Pushing {len(formatted_leads)} leads to Instantly Campaign...")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as resp:
            if resp.status in [200, 201, 202]:
                print("[+] Successfully pushed leads to Instantly!")
                return await resp.json()
            else:
                text = await resp.text()
                print(f"[!] Error pushing to Instantly: {resp.status} - {text}")
                return None

async def run_scraper(query: str, max_results: int, output_file: str, skip_enrichment: bool = False):
    # 1. Load Environment Variables
    load_dotenv()
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    instantly_key = os.getenv("INSTANTLY_API_KEY")
    
    if not api_key:
        print("[!] ERROR: GOOGLE_PLACES_API_KEY not found in .env file.")
        sys.exit(1)

    # 1.5 Setup Scraped-Leads directory
    output_dir = "Scraped-Leads"
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.dirname(output_file):
        output_file = os.path.join(output_dir, output_file)

    # 2. Initialize Engines
    discovery = GooglePlacesDiscovery(api_key)
    validator = Validator()
    scorer = Scorer()
    enricher = EnrichmentModule()
    personalizer = Personalizer()
    exporter = Exporter()
    
    # 3. Step 1: Discover Leads
    print(f"\n--- Phase 1: Discovering Leads for '{query}' ---")
    
    target_leads = []
    deduplicator = Deduplicator(storage_file=os.path.join(output_dir, "seen_leads.json"))
    
    async for raw_leads_chunk in discovery.fetch_leads_generator(query):
        original_count = len(raw_leads_chunk)
        new_leads_chunk = deduplicator.filter_and_record_new_leads(raw_leads_chunk)
        
        if len(new_leads_chunk) < original_count:
            print(f"[*] Deduped {original_count - len(new_leads_chunk)} leads in this chunk.")
            
        if not new_leads_chunk:
            continue
            
        print(f"\n--- Phase 2: Validating Websites ({len(new_leads_chunk)} leads) ---")
        async with aiohttp.ClientSession() as session:
            tasks = [validator.validate_website(lead, session) for lead in new_leads_chunk]
            validated_chunk = await asyncio.gather(*tasks)
            
        actionable_chunk = [
            lead for lead in validated_chunk 
            if lead.get("website_status") and "FILTER OUT" not in lead.get("website_status")
        ]
        
        if actionable_chunk:
            target_leads.extend(actionable_chunk)
            print(f"[*] Found {len(actionable_chunk)} actionable leads. Total: {len(target_leads)} / {max_results}")
        else:
            print(f"[*] No actionable leads in this chunk.")
            
        if len(target_leads) >= max_results:
            target_leads = target_leads[:max_results]
            break

    if not target_leads:
        print("\n[!] No actionable leads found. Exiting.")
        return
        
    print(f"\n--- Phase 3: AI Research & Personalization ({len(target_leads)} leads) ---")
    
    processed_leads = []
    for lead in target_leads:
        # Scoring and Enrichment (Original)
        enriched = enricher.enrich_lead(lead)
        scored = scorer.score_lead(enriched)
        
        # New Gemini AI Personalization
        print(f"[*] Researching {scored.get('business_name')}...")
        personalized = await personalizer.research_and_personalize(scored)
        processed_leads.append(personalized)
        
    print("[*] AI Personalization complete.")

    # 6. Step 5: Export to CSV
    print(f"\n--- Phase 4: Exporting Results ---")
    exporter.export_to_csv(processed_leads, filename=output_file)
    
    print(f"\n[!] NEXT STEP: Upload '{output_file}' to Lumrid for free verification.")
    print(f"[!] Once verified, download the 'Good/Risky' CSV and run: python src/push.py [filename]")

    cost = discovery.api_calls * 0.032
    print(f"\n--- Run Summary ---")
    print(f"[*] API Calls Made: {discovery.api_calls}")
    print(f"[*] Estimated Google Places API Cost: ${cost:.3f} USD")
    print("\n[+] Scraper finished successfully!\n")

def main():
    parser = argparse.ArgumentParser(description="AI-Powered Lead Scraper and Automated Outreach.")
    parser.add_argument("-q", "--query", type=str, required=True)
    parser.add_argument("-m", "--max-results", type=int, default=10)
    parser.add_argument("-o", "--output", type=str, default="leads_output.csv")
    parser.add_argument("--skip-enrichment", action="store_true")

    args = parser.parse_args()

    try:
        asyncio.run(run_scraper(query=args.query, max_results=args.max_results, output_file=args.output, skip_enrichment=args.skip_enrichment))
    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    main()
