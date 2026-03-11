# Local B2B Lead Scraper & Validator

A highly-targeted local lead generation script built in Python. This automation relies on the Google Places API (NEW) to discover real local businesses, asynchronously filters out any business that already has a functional website, and enriches the remaining prospects with social links, emails, and CEO names using DuckDuckGo.

## Features
- **Discovery Engine:** Uses `places:searchText` via the official Google Places API to legally and reliably pull local business names, addresses, and phone numbers.
- **Async Validation Engine:** Uses `aiohttp` to simultaneously ping website URLs. Automatically discards businesses with working websites (`HTTP 200 OK`). 
- **Target Identification:** Exclusively targets businesses with:
  - No website
  - Broken websites (DNS errors, timeouts, `HTTP 403 Forbidden`)
  - Social-Only presence (Redirects to Facebook, Instagram, LinkedIn, etc.)
  - Parked Domains ("This domain is parked", "buy this domain on GoDaddy")
- **Confidence Scoring:** Grades prospect data completeness (High / Medium / Low). 
- **Enrichment Module:** Uses `duckduckgo-search` to scrub public records for the CEO/Owner's name, public `name@domain.com` emails via regex, and social links.
- **CSV Export:** Safely exports all clean, verified leads to a structured CSV.

## Setup Requirements

1. **Clone the repository and CD into it**
2. **Set up the virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Configure Environment Variables:**
   Create a `.env` file in the root directory and add your Google Places API Key:
   ```env
   GOOGLE_PLACES_API_KEY="your_api_key_here"
   ```

## Usage

Run the CLI via terminal:
```bash
./venv/bin/python src/cli.py -q "Roofers in Dallas, TX" -m 50 -o dallas_roofers.csv
```

**Arguments:**
- `-q` or `--query`: The search string for Google Places.
- `-m` or `--max-results`: Maximum leads to fetch from Google (Default: 50).
- `-o` or `--output`: The filename to dump the exported CSV results into.
- `--skip-enrichment`: Optional flag to skip DuckDuckGo extraction for faster bulk processing.

## Project Architecture
- `src/cli.py`: The command loop and progress UI.
- `src/discovery.py`: Google Places API integration.
- `src/validator.py`: The `aiohttp` and `BeautifulSoup4` URL testing engine.
- `src/scorer.py`: The confidence grading logic.
- `src/enrichment.py`: DuckDuckGo scraping for owners, emails, and social links.
- `src/exporter.py`: Outputs the final Pandas DataFrame to CSV.
