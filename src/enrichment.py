from duckduckgo_search import DDGS
import re
from typing import Dict, Any
import time

class EnrichmentModule:
    def __init__(self):
        self.email_regex = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
        self.social_platforms = ['facebook.com', 'linkedin.com', 'instagram.com', 'twitter.com', 'x.com', 'yelp.com']

    def enrich_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes a lead dictionary and uses DuckDuckGo to search for emails, social links, and CEO/Owner names.
        Modifies the dictionary in-place and returns it.
        """
        business_name = lead.get("business_name", "")
        address = lead.get("address", "")
        
        # Initialize default values
        lead["emails"] = ""
        lead["social_links"] = ""
        lead["ceo_name"] = ""
        
        # Small sanity check to ensure we have a measurable business
        if not business_name or business_name == "Unknown":
            return lead
            
        print(f"  [~] Scrubbing public records for: {business_name}...")
        
        query = f'"{business_name}" {address} owner OR ceo OR founder email'
        
        emails = set()
        socials = set()
        ceo_name = "Not Found"
        
        def process_results(results_list):
            nonlocal ceo_name, emails, socials
            for r in results_list:
                text_blob = r.get('body', '') + ' ' + r.get('href', '')
                title = r.get('title', '')
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
                        
                # 3. Simple CEO/Owner heuristic from LinkedIn titles
                if 'linkedin.com' in href and ('owner' in title.lower() or 'ceo' in title.lower() or 'founder' in title.lower()):
                    parts = title.split('-')
                    if len(parts) > 1:
                        potential_name = parts[0].strip()
                        if potential_name.lower() not in business_name.lower():
                            ceo_name = potential_name

        try:
            with DDGS() as ddgs:
                # Basic search for general info
                results = list(ddgs.text(query, max_results=5))
                
                # Targeted linkedin search
                linkedin_query = f'"{business_name}" {address} CEO OR Owner site:linkedin.com'
                li_results = list(ddgs.text(linkedin_query, max_results=2))
                results.extend(li_results)
                
                process_results(results)

                # Fallback query if no emails or name found
                if (not emails or ceo_name == "Not Found") and len(address.split()) > 2:
                    fallback_query = f'"{business_name}" owner OR ceo email'
                    fallback_results = list(ddgs.text(fallback_query, max_results=3))
                    process_results(fallback_results)
                                
            # Respect rate limits for DuckDuckGo free tier
            time.sleep(3.0)
                            
        except Exception as e:
            print(f"  [!] Enrichment failed for {business_name} due to active limit blocks.")
            
        lead["emails"] = ", ".join(emails) if emails else ""
        
        # Prevent duplicating the main website as a social link
        website_url = lead.get("website", "")
        if website_url:
            socials = {s for s in socials if s.lower() != website_url.lower()}
            
        lead["social_links"] = ", ".join(socials) if socials else ""
        lead["ceo_name"] = ceo_name if ceo_name != "Not Found" else ""
        
        return lead
