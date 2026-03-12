# AI-Powered Lead Scraper & Outreach Machine

A professional-grade, automated lead generation and outreach system. This tool discovers local businesses with poor or missing digital presences, uses Gemini AI (grounded in Google Search) to research their owners, and prepares hyper-personalized outreach campaigns.

## 🔄 The 3-Step Success Workflow

### 1. Scrape & AI Personalize
**Command:** `python src/cli.py -q "Business Type in City" -m 100`
- **Discovery:** Finds leads via Google Places API (optimized cost using Field Masking).
- **Validation:** Filters out businesses that already have working websites.
- **AI Research:** Gemini 1.5 Flash looks up the Owner/CEO on LinkedIn/Google.
- **AI Copywriting:** Generates two tags:
    - `{{icebreaker}}`: Spartan, casual opening relating to the owner's interests or business.
    - `{{personalizedemailcontent}}`: A pitch explaining their website issue and offering your pre-built solution.
- **Auto-Splitting:** If results exceed 1,000 leads, it splits the CSV into "Parts" for Lumrid compatibility.

### 2. Verify (Manual & Free)
**Action:** Upload your generated CSV to [Lumrid](https://app.lumrid.com/account).
- This ensures you only email **verified** addresses, protecting your domain's health.
- Download the "Clean/Safe" result CSV.

### 3. Push to Instantly
**Command:** `python src/push.py [path_to_verified_csv]`
- Uploads only the verified leads directly into your **"Website Campaign"** on Instantly.
- Automatically maps your AI personlization tags.

---

## 🛠️ Setup

1. **Environment:**
   ```bash
   pip install -r requirements.txt
   ```
2. **API Keys (.env):**
   ```env
   GOOGLE_PLACES_API_KEY="your_key"
   INSTANTLY_API_KEY="your_key"
   GEMINI_API_KEY="your_key"
   ```

## 💰 Cost Tracking (per 1,000 leads)
- **Google Places:** ~$4.60 USD (utilizing the $200 monthly credit).
- **Gemini AI:** $0.00 (within free tier of 1,500 requests/day).
- **Verification:** $0.00 (via Lumrid free tier).

## 📁 Key Files
- `src/cli.py`: Main orchestration & AI research.
- `src/personalizer.py`: Gemini system prompts & personalization logic.
- `src/push.py`: Instantly API uploader.
- `src/exporter.py`: Smart CSV chunking logic.
- `src/discovery.py`: Cost-optimized Google Places implementation.
- `Scraped-Leads/`: Where all your target lists are saved.
