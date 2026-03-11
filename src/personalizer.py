import os
import random
from typing import Dict, Any

class Personalizer:
    def __init__(self):
        # We can add an AI client here later if needed
        self.openai_key = os.getenv("OPENAI_API_KEY")

    def generate_icebreaker(self, lead: Dict[str, Any]) -> str:
        """
        Generates a personalized icebreaker based on the lead's website status.
        Uses a heuristic-based approach by default.
        """
        business_name = lead.get("business_name", "your team")
        status = lead.get("website_status", "")
        notes = lead.get("validation_notes", "").lower()
        ceo = lead.get("ceo_name", "")

        name_part = f"Hi {ceo.split()[0]}, " if ceo else "Hi there, "
        
        # 1. No Website
        if status == "No Website":
            options = [
                f"{name_part}I noticed {business_name} doesn't have a website listed on Google yet. Are you currently taking all your bookings manually?",
                f"{name_part}I was looking for {business_name} online and couldn't find a dedicated site. Is that something you're looking to build this year?",
                f"{name_part}Quick question: Is {business_name} primarily focused on word-of-mouth right now, or have you just not gotten around to the website yet?"
            ]
            return random.choice(options)

        # 2. Social-Only
        if status == "Social-Only":
            options = [
                f"{name_part}I saw {business_name} is currently using social media as your main 'hub.' Have you considered how much more trust a professional domain would add?",
                f"{name_part}Love the work you guys are doing on social! I noticed you don't have a standalone site for {business_name} yet—any plans for that?",
                f"{name_part}I found your profile while searching for local pros. Do you find that just using social media captures enough of the Dallas market for {business_name}?"
            ]
            return random.choice(options)

        # 3. Broken Website
        if status == "Broken":
            if "timeout" in notes or "connection" in notes:
                return f"{name_part}I tried visiting the {business_name} site but it seems to be having some server connection issues today. Just wanted to give you a heads up!"
            if "404" in notes:
                return f"{name_part}I noticed the link to {business_name} on Google is currently leading to a 404 error page. Might be costing you some leads!"
            return f"{name_part}I noticed the website for {business_name} seems to be down or inactive at the moment. Are you currently doing an update?"

        # 4. Parked Domain
        if status == "Parked Domain":
            return f"{name_part}I saw that the {business_name} domain is currently parked. Are you planning on launching the full site soon, or is that a project for later?"

        return f"{name_part}I was checking out {business_name} and wanted to reach out regarding your current digital presence in the local market."
