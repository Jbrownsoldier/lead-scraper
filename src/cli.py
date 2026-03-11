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

import aiohttp

async def run_scraper(query: str, max_results: int, output_file: str, skip_enrichment: bool = False):
    # 1. Load Environment Variables
    load_dotenv()
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    
    if not api_key:
        print("[!] ERROR: GOOGLE_PLACES_API_KEY not found in .env file.")
        print("[!] Please add it and try again.")
        sys.exit(1)

    # 2. Initialize Engines
    discovery = GooglePlacesDiscovery(api_key)
    validator = Validator()
    scorer = Scorer()
    enricher = EnrichmentModule()
    exporter = Exporter()

    # 3. Step 1: Discover Leads
    print(f"\n--- Phase 1: Discovering Leads for '{query}' ---")
    raw_leads = await discovery.search_leads(query, max_results=max_results)
    
    if not raw_leads:
        print("[!] No leads found. Exiting.")
        return

    # 3.5 Deduplication
    deduplicator = Deduplicator(storage_file="seen_leads.json")
    original_count = len(raw_leads)
    raw_leads = deduplicator.filter_and_record_new_leads(raw_leads)
    
    if len(raw_leads) < original_count:
        print(f"[*] Deduped {original_count - len(raw_leads)} leads that were already processed previously.")

    if not raw_leads:
        print("[!] All discovered leads have been previously processed. No new leads found. Exiting.")
        return

    # 4. Step 2 & 3: Validate Websites and Score
    print(f"\n--- Phase 2: Validating Websites and Scoring ({len(raw_leads)} leads) ---")
    
    async with aiohttp.ClientSession() as session:
        # Create validation tasks
        tasks = [validator.validate_website(lead, session) for lead in raw_leads]
        
        # Run validations concurrently
        validated_leads = await asyncio.gather(*tasks)
        
    print("[*] Validation complete.")

    # 5. Step 4: Filter strictly before enrichment (saves time and requests)
    # We only want to enrich businesses that are actually good leads (no real website)
    target_leads = [
        lead for lead in validated_leads 
        if lead.get("website_status") and "FILTER OUT" not in lead.get("website_status")
    ]
    
    if not target_leads:
        print("\n[!] No actionable leads found after filtering valid websites. Exiting.")
        return
        
    print(f"\n--- Phase 3: Scoring and Enriching ({len(target_leads)} refined leads) ---")
    
    if skip_enrichment:
        print("[*] Skipping Enrichment phase as requested.")
        for i, lead in enumerate(target_leads):
            target_leads[i] = scorer.score_lead(lead)
    else:
        # We apply scoring and then synchronous enrichment (to prevent DuckDuckGo rate limiting)
        for i, lead in enumerate(target_leads):
            target_leads[i] = scorer.score_lead(lead)
            target_leads[i] = enricher.enrich_lead(target_leads[i])
        
    print("[*] Enrichment and Scoring complete.")

    # 6. Step 5: Export to CSV
    print(f"\n--- Phase 4: Exporting Results ---")
    
    exporter.export_to_csv(target_leads, filename=output_file)
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
        help="Output CSV filename (default: leads_output.csv)"
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
