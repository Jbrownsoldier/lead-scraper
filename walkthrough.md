# Lead Scraper Walkthrough

This guide will show you how to use the local lead scraping script simply and effectively.

## Step 1: Open Your Terminal
To run the scraper, you need to open your computer's terminal and navigate to the folder where the project lives.
```bash
cd "/Users/jamalbrown/Desktop/JBrown AI Solutions/Coding/lead-scraper"
```

## Step 2: Run the Command
You can trigger the scraper by running a single command. 
**Example Command:**
```bash
./venv/bin/python src/cli.py -q "Plumbers in Tampa FL" -m 50 -o tampa_plumbers.csv
```

## Step 3: Where are my leads?
Your scientific results are saved as **.csv** files directly inside the `lead-scraper` folder. 
- Look for files ending in `.csv` (e.g., `tampa_plumbers.csv`, `my_leads.csv`).
- You can open these with Excel or Google Sheets.

## Step 4: What is `seen_leads.json`?
This file acts as the **"Memory"** of your scraper.
- It stores a unique code for every business it has ever found.
- **Why?** So you never pay for the same lead twice. If you run a search tomorrow that finds the same business, the script will say "I've seen this one before!" and skip it automatically.
- **Do not delete this file** unless you want the scraper to forget everything and start fresh.

---

## Pro Tip: Fast Mode
If you want to pull leads lightning fast without searching for CEO names or emails, add `--skip-enrichment` to your command:
```bash
./venv/bin/python src/cli.py -q "Roofers" -m 100 -o fast_leads.csv --skip-enrichment
```
