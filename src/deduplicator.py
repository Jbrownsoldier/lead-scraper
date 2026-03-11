import json
import os
import hashlib
from typing import Dict, Any, List

class Deduplicator:
    def __init__(self, storage_file: str = "seen_leads.json"):
        self.storage_file = storage_file
        self.seen_hashes = self._load_data()

    def _load_data(self) -> set:
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return set(data)
            except (json.JSONDecodeError, IOError):
                return set()
        return set()

    def _save_data(self):
        with open(self.storage_file, 'w', encoding='utf-8') as f:
            json.dump(list(self.seen_hashes), f)

    def _generate_hash(self, lead: Dict[str, Any]) -> str:
        name = str(lead.get('business_name', '')).strip().lower()
        phone = str(lead.get('phone', '')).strip().lower()
        address = str(lead.get('address', '')).strip().lower()
        
        # Create a unique string based on name, phone, and address
        unique_string = f"{name}|{phone}|{address}"
        return hashlib.md5(unique_string.encode('utf-8')).hexdigest()

    def is_duplicate(self, lead: Dict[str, Any]) -> bool:
        """Returns True if the lead has been seen before."""
        lead_hash = self._generate_hash(lead)
        return lead_hash in self.seen_hashes

    def add_lead(self, lead: Dict[str, Any]):
        """Marks a lead as seen."""
        lead_hash = self._generate_hash(lead)
        self.seen_hashes.add(lead_hash)
        self._save_data()

    def filter_and_record_new_leads(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filters out duplicate leads and records the new ones as seen."""
        new_leads = []
        for lead in leads:
            if not self.is_duplicate(lead):
                new_leads.append(lead)
                self.add_lead(lead)
        return new_leads
