from typing import Dict, Any

class Scorer:
    def score_lead(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates a Confidence Score based on data presence and validation status.
        Modifies the lead dictionary in-place to add 'confidence_score'.
        """
        score = 0
        
        # 1. Base criteria for a good lead
        if lead.get("phone"):
            score += 3
        if lead.get("address") and lead.get("address") != "Unknown":
            score += 2
        
        # 2. Maps status
        maps_status = lead.get("maps_status", "")
        if maps_status == "OPERATIONAL":
            score += 2
        elif maps_status in ("CLOSED_TEMPORARILY", "CLOSED_PERMANENTLY"):
            score -= 5 # Massive penalty for closed businesses
            
        # 3. Website status weighting
        web_status = lead.get("website_status", "")
        if web_status == "No Website":
            score += 3 # Prime target
        elif web_status == "Social-Only":
            score += 3 # Prime target (active but needs a real site)
        elif web_status == "Parked Domain":
            score += 2 # Good target, but might just be squatting
        elif web_status == "Broken":
            score += 1 # Okay target, but could indicate business closure
            
        # Assign High/Medium/Low based on accumulated score
        has_enrichment = bool(lead.get("emails") or lead.get("ceo_name"))
        
        if score >= 8 and has_enrichment:
            lead["confidence_score"] = "High"
        elif score >= 5:
            lead["confidence_score"] = "Medium"
        else:
            lead["confidence_score"] = "Low"
            
        return lead
