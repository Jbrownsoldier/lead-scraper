import os
import pandas as pd
from typing import List, Dict, Any

class Exporter:
    def export_to_csv(self, leads: List[Dict[str, Any]], filename: str = "leads.csv"):
        """
        Exports the finalized leads to CSV file(s). 
        Splits into multiple files if the count exceeds 1000 (Lumrid limit).
        """
        if not leads:
            print("[!] No actionable leads found to export.")
            return

        # Split leads into chunks of 1000
        chunk_size = 1000
        chunks = [leads[i:i + chunk_size] for i in range(0, len(leads), chunk_size)]

        for i, chunk in enumerate(chunks):
            df = pd.DataFrame(chunk)
            
            # Reorder columns for better readability if they exist
            expected_columns = [
                "person_name",
                "email",
                "business_name", 
                "icebreaker",
                "email_body",
                "website_status",
                "phone", 
                "address", 
                "website", 
                "confidence_score",
                "validation_notes",
                "maps_status"
            ]
            
            cols = [col for col in expected_columns if col in df.columns]
            df = df[cols]
            
            # If multiple chunks, add suffix
            if len(chunks) > 1:
                name, ext = os.path.splitext(filename)
                chunk_filename = f"{name}_part{i+1}{ext}"
            else:
                chunk_filename = filename

            # We write new files (overwrite) for each run to ensure proper chunking
            df.to_csv(chunk_filename, index=False)
            print(f"[*] Successfully exported {len(chunk)} leads to {chunk_filename}")
