import os
import pandas as pd
from typing import List, Dict, Any

class Exporter:
    def export_to_csv(self, leads: List[Dict[str, Any]], filename: str = "leads.csv"):
        """
        Exports the finalized leads to a CSV file. Appends if file exists.
        """
        if not leads:
            print("[!] No actionable leads found to export.")
            return

        df = pd.DataFrame(leads)
        
        # Reorder columns for better readability if they exist
        expected_columns = [
            "business_name", 
            "ceo_name",
            "emails",
            "confidence_score",
            "website_status",
            "phone", 
            "address", 
            "website", 
            "social_links",
            "maps_status",
            "validation_notes"
        ]
        
        # Only keep columns that actually exist in the dataframe
        cols = [col for col in expected_columns if col in df.columns]
        
        df = df[cols]
        # Append if exists, otherwise write new with header
        file_exists = os.path.isfile(filename)
        df.to_csv(filename, mode='a', index=False, header=not file_exists)
        print(f"[*] Successfully exported {len(leads)} leads to {filename} (Appended)")
