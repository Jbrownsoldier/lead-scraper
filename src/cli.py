import argparse
import asyncio
import os
import sys
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

async def run_scraper(query: str, max_results: int, output_file: str, skip_enrichment: bool = False):
    # 1. Load Environment Variables
    load_dotenv()
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    
    if not api_key:
        print("[!] ERROR: GOOGLE_PLACES_API_KEY not found in .env file.")
        print("[!] Please add it and try again.")
        sys.exit(1)

    # 1.5 Setup Scraped-Leads directory
    output_dir = "Scraped-Leads"
    os.makedirs(output_dir, exist_ok=True)
    
    # Ensure output_file goes into the directory if not specifically path'd
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
            print(f"[*] Deduped {original_count - len(new_leads_chunk)} leads in this chunk that were already processed previously.")
            
        if not new_leads_chunk:
            continue
            
        print(f"\n--- Phase 2: Validating Websites and Scoring ({len(new_leads_chunk)} leads) ---")
        async with aiohttp.ClientSession() as session:
            tasks = [validator.validate_website(lead, session) for lead in new_leads_chunk]
            validated_chunk = await asyncio.gather(*tasks)
            
        actionable_chunk = [
            lead for lead in validated_chunk 
            if lead.get("website_status") and "FILTER OUT" not in lead.get("website_status")
        ]
        
        if actionable_chunk:
            target_leads.extend(actionable_chunk)
            print(f"[*] Found {len(actionable_chunk)} actionable leads in this chunk. Total actionable so far: {len(target_leads)} / {max_results}")
        else:
            print(f"[*] No actionable leads in this chunk.")
            
        if len(target_leads) >= max_results:
            print(f"\n[*] Reached goal of {max_results} actionable leads. Stopping API calls to save money.")
            target_leads = target_leads[:max_results]
            break

    if not target_leads:
        print("\n[!] No actionable leads found after filtering valid websites. Exiting.")
        cost = discovery.api_calls * 0.032
        print(f"\n--- Run Summary ---")
        print(f"[*] API Calls Made: {discovery.api_calls}")
        print(f"[*] Estimated Google Places API Cost: ${cost:.3f} USD\n")
        return
        
    print(f"\n--- Phase 3: Scoring and Enriching ({len(target_leads)} refined leads) ---")
    
    if skip_enrichment:
        print("[*] Skipping Enrichment phase as requested.")
        for i, lead in enumerate(target_leads):
            target_leads[i] = scorer.score_lead(lead)
    else:
        # We apply synchronous enrichment and scoring, then generate icebreaker
        for i, lead in enumerate(target_leads):
            target_leads[i] = enricher.enrich_lead(lead)
            target_leads[i] = scorer.score_lead(target_leads[i])
            target_leads[i]["icebreaker"] = personalizer.generate_icebreaker(target_leads[i])
        
    print("[*] Enrichment, Scoring, and Personalization complete.")

    # 6. Step 5: Export to CSV
    print(f"\n--- Phase 4: Exporting Results ---")
    
    exporter.export_to_csv(target_leads, filename=output_file)
    cost = discovery.api_calls * 0.032
    print(f"\n--- Run Summary ---")
    print(f"[*] API Calls Made: {discovery.api_calls}")
    print(f"[*] Estimated Google Places API Cost: ${cost:.3f} USD")
    print("\n[+] Process finished successfully!\n")

def main():
    parser = argparse.ArgumentParser(description="Local Script-Based Lead Scraper for B2B Prospecting.")
    parser.add_argument(
        "-q", "--query", 
        type=str, 
        required=True, 
        help="Search query for Google Places (e.g., 'Landscapers in Orlando, FL')"
    )
    parser.add_argument(
        "-m", "--max-results", 
        type=int, 
        default=50, 
        help="Maximum number of leads to fetch (default: 50)"
    )
    parser.add_argument(
        "-o", "--output", 
        type=str, 
        default="leads_output.csv", 
        help="Output CSV filename (will be saved in Scraped-Leads/ folder) (default: leads_output.csv)"
    )
    parser.add_argument(
        "--skip-enrichment",
        action="store_true",
        help="Skip the DuckDuckGo enrichment phase for faster execution."
    )

    args = parser.parse_args()

    # Run the async core
    try:
        asyncio.run(run_scraper(query=args.query, max_results=args.max_results, output_file=args.output, skip_enrichment=args.skip_enrichment))
    except KeyboardInterrupt:
        print("\n[!] Process interrupted by user.")
        sys.exit(0)

if __name__ == "__main__":
    main()
