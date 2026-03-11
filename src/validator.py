import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Dict, Any

class Validator:
    def __init__(self):
        # A common set of terms used by domain registrars for parked domains
        self.parked_keywords = [
            "domain is parked",
            "buy this domain",
            "this domain is for sale",
            "site under construction",
            "godaddy.com",
            "hughesnet",
            "dns resolution error"
        ]

        # Common social media domains
        self.social_domains = [
            "facebook.com",
            "instagram.com",
            "linkedin.com",
            "twitter.com",
            "x.com",
            "yelp.com"
        ]

    async def validate_website(self, lead: Dict[str, Any], session: aiohttp.ClientSession) -> Dict[str, Any]:
        """
        Validates the website URL asynchronously.
        Modifies the lead dictionary in-place to add 'website_status' and 'validation_notes'.
        """
        url = lead.get("website")
        
        # 1. No Website
        if not url:
            lead["website_status"] = "No Website"
            lead["validation_notes"] = "No URL provided by Google."
            return lead

        # 2. Social-Only Presence
        if any(domain in url.lower() for domain in self.social_domains):
            lead["website_status"] = "Social-Only"
            lead["validation_notes"] = "URL points to a social media profile."
            return lead

        # 3. Test the Real Website
        try:
            # Setup a browser-like user agent to avoid bot-blocks
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            
            # Using a short timeout (10 seconds)
            async with session.get(url, headers=headers, timeout=10, allow_redirects=True, ssl=False) as response:
                final_url = str(response.url).lower()
                
                # Check for redirects to social media
                if any(domain in final_url for domain in self.social_domains):
                    lead["website_status"] = "Social-Only"
                    lead["validation_notes"] = f"Redirected to social profile: {final_url}"
                    return lead

                if response.status >= 400:
                    lead["website_status"] = "Broken"
                    lead["validation_notes"] = f"HTTP Error {response.status}"
                    return lead

                # Check for parked domains by reading HTML
                html = await response.text()
                soup = BeautifulSoup(html, "html.parser")
                text_content = soup.get_text().lower()

                if any(kw in text_content for kw in self.parked_keywords):
                    lead["website_status"] = "Parked Domain"
                    lead["validation_notes"] = "HTML content suggests a parked or under-construction domain."
                    return lead

                # If all checks pass, it's a real website
                lead["website_status"] = "Real Website (FILTER OUT)"
                lead["validation_notes"] = "Site appears functional and active."
                return lead

        except asyncio.TimeoutError:
            lead["website_status"] = "Broken"
            lead["validation_notes"] = "Connection timed out."
            return lead
        except aiohttp.ClientError as e:
            lead["website_status"] = "Broken"
            lead["validation_notes"] = f"Client Error: {str(e)}"
            return lead
        except Exception as e:
            lead["website_status"] = "Broken"
            lead["validation_notes"] = f"Unexpected Error: {str(e)}"
            return lead

# Quick test execution block
if __name__ == "__main__":
    async def test():
        validator = Validator()
        async with aiohttp.ClientSession() as session:
            test_leads = [
                {"business_name": "No Site LLC", "website": None},
                {"business_name": "Facebook Plumber", "website": "https://facebook.com/myplumbingbiz"},
                {"business_name": "Broken Site Inc", "website": "https://this-site-definitely-does-not-exist-123.com"},
                {"business_name": "Google", "website": "https://google.com"}
            ]
            
            tasks = [validator.validate_website(lead, session) for lead in test_leads]
            results = await asyncio.gather(*tasks)
            
            for r in results:
                print(f"[{r['business_name']}] -> {r['website_status']}: {r['validation_notes']}")

    asyncio.run(test())
