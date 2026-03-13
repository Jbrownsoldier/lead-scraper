import re
import time
from typing import Dict, Any
from duckduckgo_search import DDGS

class EnrichmentModule:
    def __init__(self):
        self.email_regex = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        self.social_platforms = ['facebook.com', 'linkedin.com', 'instagram.com', 'twitter.com', 'x.com', 'yelp.com']

    def enrich_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a lead dictionary and uses DuckDuckGo to search for emails and social links.
        Decision-maker specific searching has been removed.
        """
        business_name = lead.get("business_name", "")
        address = lead.get("address", "")
        
        # Initialize default values
        lead["emails"] = ""
        lead["social_links"] = ""
        
        if not business_name or business_name == "Unknown":
            return lead
            
        print(f"  [~] Scrubbing social records for: {business_name}...")
        
        emails = set()
        socials = set()

        # Search for general business context (socials/contact)
        query = f'"{business_name}" {address} contact facebook instagram linkedin'
        
        def process_results(results_list):
            nonlocal emails, socials
            for r in results_list:
                text_blob = r.get('body', '') + ' ' + r.get('href', '')
                href = r.get('href', '').lower()
                
                # 1. Extract emails via Regex
                found_emails = re.findall(self.email_regex, text_blob)
                for e in found_emails:
                    if not any(e.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']):
                        emails.add(e.lower())
                        
                # 2. Extract socials from URLs
                if any(sp in href for sp in self.social_platforms):
                    if len(href.split('/')) > 3: 
                        socials.add(href)

        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=5))
                process_results(results)
                                
            # Respect rate limits for DuckDuckGo
            time.sleep(2.0)
                            
        except Exception as e:
             print(f"  [!] Enrichment slowed down for {business_name} due to rate limits.")
            
        lead["emails"] = ", ".join(emails) if emails else ""
        
        # Prevent duplicating the main website as a social link
        website_url = lead.get("website", "")
        if website_url:
            social_list = list(socials)
            social_list = [s for s in social_list if s.lower().rstrip('/') != website_url.lower().rstrip('/')]
            lead["social_links"] = ", ".join(social_list)
        else:
            lead["social_links"] = ", ".join(socials) if socials else ""
            
        return lead
