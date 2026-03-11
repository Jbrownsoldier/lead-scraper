# Lead Finder Improvements

The following features have been identified as high-impact improvements for the next phase of development for the B2B Lead Scraper system.

## 1. The "LinkedIn Sleuth" Upgrade (Free & High Value)
**The Problem:** Right now, our DuckDuckGo enrichment module is decent, but it's essentially just doing a blind Google search for "CEO" and hoping their name appears in the tiny snippet of text under the search result. It often returns blank.
**The Fix:** Upgrade the enrichment module to specifically target LinkedIn. Configure the script to search `site:linkedin.com/in/ "Company Name" (Owner OR CEO OR Founder)` and parse the exact name of the first profile that pops up. This drastically increases the success rate of finding the actual decision-maker's name.

## 2. Multi-City Automation "The Regional Sweep" (Free & High Volume)
**The Problem:** Currently, the system requires manual execution for one city/query at a time (e.g., `"Roofers in Dallas"`, wait, `"Roofers in Austin"`, wait).
**The Fix:** Add a "Batch Mode" feature. Allow the script to ingest a text file containing a list of search queries or locations (e.g., 50 Texas cities). The script will automatically loop through every city, perform discovery, validation, and enrichment, and stitch them all together into one massive, master CSV file.

## 3. Integrated Email Verification Hunter (Low Cost & Enterprise Grade)
**The Problem:** The current script uses Regular Expressions to scrape public emails off DuckDuckGo. This means we only find emails if the owner happened to post their email publicly on a forum or Facebook page, completely missing hidden professional business emails.
**The Fix:** Integrate the API of a professional B2B data provider like **Hunter.io** or **Apollo.io**. Once the script identifies a company with a broken website, it automatically pings the API with the company name to return the verified corporate email address of the CEO. *(Note: To conserve budget, this expensive API call should strictly be triggered only on the final, highly-vetted "Broken/No Website" leads).*
