# Lead Scraper Walkthrough

This guide will show you how to use the local lead scraping script simply and effectively.

## Step 1: Open Your Terminal
To run the scraper, you need to open your computer's terminal and navigate to the folder where the project lives.
```bash
cd "/Users/jamalbrown/Desktop/JBrown AI Solutions/Coding/Lead Scraper "
```

## Step 2: Run the Command
You can trigger the scraper by running a single command. The script requires three pieces of information:
1. `-q` : The search query (What do you want to search for? Example: "Roofers in Dallas, TX")
2. `-m` : The maximum number of local businesses to pull from Google (Example: 20)
3. `-o` : The name of the CSV file you want to save the good leads into (Example: leads.csv)

**Example Command:**
```bash
./venv/bin/python src/cli.py -q "Plumbers in Tampa FL" -m 50 -o tampa_plumbers.csv
```

## Step 3: Wait a Few Seconds
The script will now automate the following:
1. Ask Google Maps to find the top businesses matching your query.
2. Find every single website URL from those businesses.
3. Visit all those websites at the exact same time.
4. Delete any business from your list that has a perfectly functional, real website.
5. Take the remaining businesses (the ones with broken sites, parked domains, or Facebook-only pages) and search DuckDuckGo for their CEO's name, public email addresses, and social media links.

## Step 4: Open Your Leads
When the terminal says `[+] Process finished successfully!`, a new CSV file will appear in the folder. Open this spreadsheet in Excel or Google Sheets. 

You now have a clean list of hyper-targeted local B2B prospects who definitively need digital help!
