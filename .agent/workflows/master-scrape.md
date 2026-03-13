---
description: Automated Lead Scraping & Outreach Pipeline (Hands-Off)
---
// turbo-all

This workflow handles the high-volume scraping and personalization process without requiring manual approvals for each step.

1. **Clean Workspace**
   - Reset the deduplicator to ensure fresh leads for this session.
   ```bash
   rm -f Scraped-Leads/seen_leads.json
   ```

2. **Run Master Scrape (UK Hubs)**
   - Run a batch for three major UK hubs in parallel-ready mode.
   ```bash
   venv/bin/python3 src/cli.py -q "house removals London" -m 100 -o movers_london_master.csv
   venv/bin/python3 src/cli.py -q "house removals Manchester" -m 100 -o movers_manchester_master.csv
   venv/bin/python3 src/cli.py -q "house removals Birmingham" -m 100 -o movers_birmingham_master.csv
   ```

3. **Consolidate Results**
   ```bash
   cat Scraped-Leads/movers_london_master.csv Scraped-Leads/movers_manchester_master.csv Scraped-Leads/movers_birmingham_master.csv > Scraped-Leads/master_outreach_list.csv
   ```

4. **Next Steps (User Action)**
   - Upload `Scraped-Leads/master_outreach_list.csv` to Lumrid for email verification.
   - Once verified, use `python3 src/push.py` to send to Instantly.
