import os
import json
import logging
import re
from typing import Dict, Any, Optional
from google import genai
from google.genai import types
from datetime import datetime

class Personalizer:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            try:
                # Use the new Google GenAI SDK
                self.client = genai.Client(api_key=self.api_key)
                self.model_name = "gemini-2.0-flash"
            except Exception as e:
                logging.error(f"GenAI Init Error: {e}")
                self.client = None
        else:
            self.client = None

    async def research_and_personalize_batch(self, leads: list) -> list:
        """
        Researches and personalizes a batch of leads (recommended size: 1 for free tier) in ONE Gemini call.
        """
        if not self.client or not leads:
            for l in leads: l["icebreaker"] = self._generate_fallback_icebreaker(l)
            return leads

        # Helper to get first name properly
        def get_first_name(lead):
            raw_name = lead.get("person_name") or lead.get("first_name") or lead.get("Name") or lead.get("name") or "there"
            if not isinstance(raw_name, str): raw_name = "there"
            return raw_name.split()[0] if raw_name.strip() else "there"

        # Prepare a condensed summary for the batch
        batch_info = []
        for i, lead in enumerate(leads):
            first_name = get_first_name(lead)
            issues = lead.get('audit_issues', [])
            issues_str = ', '.join(issues) if isinstance(issues, list) else str(issues)
            
            summary = (
                f"Business {i+1}: {lead.get('business_name')} | "
                f"URL: {lead.get('website')} | "
                f"Status: {lead.get('website_status')} | "
                f"Issues Found: {issues_str} | "
                f"Contact Name: {first_name}"
            )
            batch_info.append(summary)

        prompt = f"""
        Write a hyper-personalized outreach email for these {len(leads)} physiotherapy businesses.
        
        DATA:
        {chr(10).join(batch_info)}

        INSTRUCTIONS:
        1. Write a unique ICEBREAKER (1 sentence). 
           - Match their niche (PT/Rehab). Mention something specific from their business/website.
           - START with "Hi [First Name]," followed by a newline.
        2. Write the TRANSITION & OFFER. 
           - You MUST include this specific context based on 'Status':
             - If Status mentions 'Needs Redesign' or 'Issues Found': Mention that the current site has technical gaps (like bad mobile view or missing SSL) and say: "I actually went ahead and built a modern version of your site to show you what's possible."
             - If Status is 'Operational': Acknowledge their site is good but say you've seen competitors ranking higher and built an 'SEO-optimized version' to show them how to win more patients. Say: "I actually went ahead and built a modern, SEO-optimized version of your site to show you what's possible."
        3. ALWAYS end this section with this EXACT text (The CTA):
           "Would you be open to a quick 15-min call this week so I can walk you through it? Or, if it’s easier, I can send over the website. Either way, I think you’ll see how much extra leads this modern website will get you.\n\nBest, Jay"

        STRICT RULES:
        - NEVER repeat the instructions like "If Status is...". Just write the final email text.
        - NO DASH CHARACTERS (-).
        - Use a casual, expert, but spontaneous tone.

        FORMAT YOUR RESPONSE LIKE THIS FOR EACH:
        B_ID: [Business Name]
        ICEBREAKER: [The Hi Name + Icebreaker]
        EMAIL_BODY: [The Transition + Offer + CTA]
        """

        max_retries = 3
        retry_delay = 20
        
        for attempt in range(max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt
                )
                
                resp_text = response.text
                
                # Map results back to leads using regex for better parsing
                blocks = re.split(r'B_ID:', resp_text)
                for block in blocks[1:]: # Skip first empty split
                    lines = [l.strip() for l in block.split('\n') if l.strip()]
                    biz_name_part = lines[0].lower()
                    
                    # Find matching lead
                    current_lead = next((l for l in leads if l.get("business_name","").lower() in biz_name_part or biz_name_part in l.get("business_name","").lower()), None)
                    
                    if current_lead:
                        for l in block.split('\n'):
                            if l.strip().startswith('ICEBREAKER:'):
                                current_lead["icebreaker"] = l.replace('ICEBREAKER:', '').strip()
                            elif l.strip().startswith('EMAIL_BODY:'):
                                current_lead["email_body"] = l.replace('EMAIL_BODY:', '').strip()
                
                # Success, break retry loop
                break

            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    logging.warning(f"Rate limited (429). Retrying in {retry_delay}s... (Attempt {attempt + 1})")
                    import time
                    time.sleep(retry_delay)
                else:
                    logging.error(f"GenAI Batch Error: {e}")
                    for lead in leads:
                        if not lead.get("icebreaker"):
                            lead["icebreaker"] = self._generate_fallback_icebreaker(lead)
                    break
        
        return leads

    async def research_and_personalize(self, lead: Dict[str, Any]) -> Dict[str, Any]:
        """
        Single lead fallback (calls batch logic with a list of 1)
        """
        results = await self.research_and_personalize_batch([lead])
        return results[0]

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
        
        return f"{name_part}I was checking out {business_name} and wanted to reach out regarding your digital presence."
