import os
import random
import logging
from typing import Dict, Any, Optional
import google.generativeai as genai

class Personalizer:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # 1.5 Flash is cost-effective and fast
            # We enable the google_search tool for grounding
            self.model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                tools=[{"google_search_retrieval": {}}]
            )
        else:
            self.model = None

    async def research_and_personalize(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses Gemini to research the decision maker and write a personalized icebreaker.
        """
        if not self.model:
            # Fallback to templates if no API key
            lead["icebreaker"] = self._generate_fallback_icebreaker(lead)
            return lead

        business_name = lead.get("business_name", "your team")
        location = lead.get("location", "")
        status = lead.get("website_status", "")
        website = lead.get("website", "")
        
        # Phase 1: Research the Decision Maker
        research_prompt = f"""
        Research the owner, CEO, or lead decision maker for the business: "{business_name}" in {location}.
        Website lookup: {website}
        
        Please find:
        1. Full Name of the Owner/CEO.
        2. Their LinkedIn profile URL if available.
        3. A direct business or owner email address if publicly listed.
        4. Any specific mentions of their background or current focus.
        
        Search through Google and social media (LinkedIn, Twitter, Facebook) to be as accurate as possible.
        """
        
        try:
            # Research call
            research_response = self.model.generate_content(research_prompt)
            research_text = research_response.text
            
            # Extract email from research if present and not already found
            if not lead.get("emails"):
                found_emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', research_text)
                if found_emails:
                    lead["emails"] = ", ".join(list(set(e.lower() for e in found_emails)))

            # Phase 2: Generate the Icebreaker
            # Extract clean company name from domain if possible
            clean_company = business_name.lower().replace(" ", "")
            if website:
                domain = website.lower().replace("https://", "").replace("http://", "").replace("www.", "").split('/')[0]
                if "." in domain:
                    clean_company = domain.split('.')[0]

            personalization_prompt = f"""
            You are an expert cold outreach specialist.
            
            Context:
            Business Name: {business_name}
            Clean Company Name: {clean_company}
            Website Status: {status}
            Prospect Research:
            {research_text}

            Task 1 (Icebreaker):
            Write a personalized icebreaker for a cold email using the research and company name. 
            - Use company name: {clean_company}
            - Style: Succinct, casual, informal, spartan tone.
            - Relate back to the user (shared interest).
            - End with: "figured i'd reach out" (or similar).
            - ABSOLUTE RULE: NO DASH CHARACTERS EVER (-).

            Task 2 (Personalized Content):
            Write a short follow-up sentence responding to the {status} status.
            - Explain why their current situation (broken/missing site) is a problem for {clean_company}.
            - Mention: "I actually went ahead and built you a new one to show you what's possible."
            - Style: Casual and helpful.
            - ABSOLUTE RULE: NO DASH CHARACTERS EVER (-).

            Response Format:
            ICEBREAKER: [icebreaker text]
            CONTENT: [personalized content text]
            """
            
            # Personalization call
            icebreaker_response = self.model.generate_content(personalization_prompt)
            resp_text = icebreaker_response.text.replace('-', ' ').replace('—', ' ').replace('–', ' ')
            
            # Simple parsing
            icebreaker = ""
            content = ""
            for line in resp_text.split('\n'):
                if line.startswith("ICEBREAKER:"):
                    icebreaker = line.replace("ICEBREAKER:", "").strip().replace('"', '')
                if line.startswith("CONTENT:"):
                    content = line.replace("CONTENT:", "").strip().replace('"', '')

            lead["icebreaker"] = icebreaker
            lead["personalizedemailcontent"] = content
            
            # Extract name if possible
            if "," in lead["icebreaker"] and len(lead["icebreaker"].split(",")[0].split()) <= 3:
                name_candidate = lead["icebreaker"].split(",")[0].replace("Hi", "").replace("hi", "").strip()
                if name_candidate and len(name_candidate) < 20:
                    lead["ceo_name"] = name_candidate

        except Exception as e:
            logging.error(f"Gemini Personalization Error: {e}")
            if not lead.get("icebreaker"):
                lead["icebreaker"] = self._generate_fallback_icebreaker(lead)
        
        return lead

    def _generate_fallback_icebreaker(self, lead: Dict[str, Any]) -> str:
        """Original heuristic-based fallback"""
        business_name = lead.get("business_name", "your team")
        status = lead.get("website_status", "")
        name_part = "Hi there, "
        
        if status == "No Website":
            return f"{name_part}I noticed {business_name} doesn't have a website listed on Google yet. Are you currently taking all your bookings manually?"
        if status == "Social-Only":
            return f"{name_part}Love the work you guys are doing on social! I noticed you don't have a standalone site for {business_name} yet—any plans for that?"
        if status == "Broken":
            return f"{name_part}I noticed the website for {business_name} seems to be down or inactive at the moment. Are you currently doing an update?"
        if status == "Redesign Opportunity":
            return f"{name_part}I was checking out the site for {business_name} and noticed it could use a few updates like mobile optimization and SSL. Are you guys planning on a redesign soon?"
        
        return f"{name_part}I was checking out {business_name} and wanted to reach out regarding your current digital presence."
