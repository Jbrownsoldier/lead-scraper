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
            "first_name": "there",
            "last_name": "",
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

async def run_discovery(query: str, max_results: int, output_file: str):
    """Step 1: Discover, Validate, and Enrich leads for external verification."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print("[!] ERROR: GOOGLE_PLACES_API_KEY not found.")
        return

    output_dir = "Scraped-Leads"
    os.makedirs(output_dir, exist_ok=True)
    if not os.path.dirname(output_file):
        output_file = os.path.join(output_dir, output_file)

    discovery = GooglePlacesDiscovery(api_key)
    validator = Validator()
    scorer = Scorer()
    enricher = EnrichmentModule()
    exporter = Exporter()
    deduplicator = Deduplicator(storage_file=os.path.join(output_dir, "seen_leads.json"))
    
    print(f"\n--- Step 1: Discovering & Validating Leads for '{query}' ---")
    
    final_leads = []
    async for raw_leads_chunk in discovery.fetch_leads_generator(query):
        new_leads_chunk = deduplicator.filter_and_record_new_leads(raw_leads_chunk)
        
        if not new_leads_chunk:
            continue
            
        print(f"[*] Validating {len(new_leads_chunk)} leads...")
        async with aiohttp.ClientSession() as session:
            tasks = [validator.validate_website(lead, session) for lead in new_leads_chunk]
            validated_chunk = await asyncio.gather(*tasks)
            
        # 1. Enrichment (Parallel 3 at a time)
        print(f"[*] Enriching {len(validated_chunk)} leads...")
        semaphore = asyncio.Semaphore(3)
        async def enrich_and_score(lead):
            async with semaphore:
                enriched = await asyncio.to_thread(enricher.enrich_lead, lead)
                return scorer.score_lead(enriched)

        enriched_chunk = await asyncio.gather(*(enrich_and_score(l) for l in validated_chunk))
        final_leads.extend(enriched_chunk)
        
        print(f"[+] Total Leads gathered: {len(final_leads)} / {max_results}")
        if len(final_leads) >= max_results:
            final_leads = final_leads[:max_results]
            break

    exporter.export_to_csv(final_leads, filename=output_file)
    print(f"\n[!] STEP 1 COMPLETE: '{output_file}' ready for Anymailfinder.")

async def run_personalization(input_file: str, output_file: str):
    """Step 2: Take Anymailfinder-verified CSV and add AI Personalization."""
    if not os.path.exists(input_file):
        print(f"[!] Input file not found: {input_file}")
        return

    load_dotenv()
    df = pd.read_csv(input_file)
    leads = df.to_dict('records')
    
    personalizer = Personalizer()
    exporter = Exporter()
    
    print(f"\n--- Step 2: AI Personalization ({len(leads)} leads) ---")
    
    processed_leads = []
    batch_size = 1
    batches = [leads[i:i + batch_size] for i in range(0, len(leads), batch_size)]
    
    for i, batch in enumerate(batches):
        if i > 0:
            await asyncio.sleep(15) # Safe pacing for free tier
        
        print(f"[*] Batch {i+1}/{len(batches)}: Researching {len(batch)} leads...")
        personalized_batch = await personalizer.research_and_personalize_batch(batch)
        processed_leads.extend(personalized_batch)
        
        # Periodic saving
        if (i + 1) % 10 == 0:
            exporter.export_to_csv(processed_leads, filename=output_file)
            print(f"    [v] Progress saved ({i+1}/{len(batches)} leads)")
    
    exporter.export_to_csv(processed_leads, filename=output_file)
    print(f"\n[!] STEP 2 COMPLETE: '{output_file}' personalized and ready for Instantly!")

async def run_raw_discovery(niche: str, cities: list, max_per_city: int, output_file: str):
    """Step 1 (Raw): High-speed discovery bypassing all audits/enrichment."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        print("[!] ERROR: GOOGLE_PLACES_API_KEY not found.")
        return

    output_dir = "Scraped-Leads"
    os.makedirs(output_dir, exist_ok=True)
    if not os.path.dirname(output_file):
        output_file = os.path.join(output_dir, output_file)

    discovery = GooglePlacesDiscovery(api_key)
    exporter = Exporter()
    deduplicator = Deduplicator(storage_file=os.path.join(output_dir, "seen_leads_raw.json"))
    
    print(f"\n--- Raw Mode: Gathering Fast Leads for '{niche}' across {len(cities)} cities ---")
    
    all_leads = []
    
    async def process_city(city):
        city_leads = []
        query = f"{niche} in {city}"
        print(f"[*] Searching: {query}...")
        async for chunk in discovery.fetch_leads_generator(query):
            new_leads = deduplicator.filter_and_record_new_leads(chunk)
            city_leads.extend(new_leads)
            if len(city_leads) >= max_per_city:
                break
        return city_leads

    # Process all cities in parallel
    results = await asyncio.gather(*(process_city(city) for city in cities))
    for res in results:
        all_leads.extend(res)

    print(f"\n[+] Total Raw Leads gathered: {len(all_leads)}")
    exporter.export_to_csv(all_leads, filename=output_file)
    print(f"[!] Exported to: {output_file}")

def main():
    parser = argparse.ArgumentParser(description="AI-Powered Lead Scraper 2.0")
    parser.add_argument("mode", choices=["discovery", "personalize", "raw"], help="discovery, personalize, or raw")
    parser.add_argument("-q", "--query", type=str, help="Search query (Discovery mode)")
    parser.add_argument("-n", "--niche", type=str, help="Niche (Raw mode)")
    parser.add_argument("-c", "--cities", type=str, help="Comma-separated cities (Raw mode)")
    parser.add_argument("-m", "--max-results", type=int, default=10, help="Max results or max per city")
    parser.add_argument("-i", "--input", type=str, help="Input CSV (Personalize mode)")
    parser.add_argument("-o", "--output", type=str, default="leads_output.csv")

    args = parser.parse_args()

    if args.mode == "discovery":
        if not args.query:
            print("[!] --query is required for discovery mode.")
            return
        asyncio.run(run_discovery(query=args.query, max_results=args.max_results, output_file=args.output))
    elif args.mode == "personalize":
        if not args.input:
            print("[!] --input (CSV from Anymailfinder) is required for personalize mode.")
            return
        asyncio.run(run_personalization(input_file=args.input, output_file=args.output))
    elif args.mode == "raw":
        if not args.niche or not args.cities:
            print("[!] --niche and --cities required for raw mode.")
            return
        cities_list = [c.strip() for c in args.cities.split(",")]
        asyncio.run(run_raw_discovery(niche=args.niche, cities=cities_list, max_per_city=args.max_results, output_file=args.output))

if __name__ == "__main__":
    import pandas as pd
    main()
