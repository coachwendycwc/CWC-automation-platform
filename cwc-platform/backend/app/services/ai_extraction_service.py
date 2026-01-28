"""
AI Extraction Service - Uses Claude API to extract invoice data from transcripts.
"""
import os
import json
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

import httpx

from app.config import get_settings

settings = get_settings()


class AIExtractionService:
    """Service for extracting invoice data from call transcripts using Claude AI."""

    def __init__(self):
        self.api_key = settings.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-5-sonnet-20241022"
        self._pricing_rules: str | None = None

    def is_configured(self) -> bool:
        """Check if the service is configured with an API key."""
        return bool(self.api_key)

    def _load_pricing_rules(self) -> str:
        """Load the pricing rules document."""
        if self._pricing_rules:
            return self._pricing_rules

        # Try to load from docs folder
        possible_paths = [
            Path(__file__).parent.parent.parent.parent / "docs" / "cwc-pricing-rules.md",
            Path(__file__).parent.parent.parent / "docs" / "cwc-pricing-rules.md",
            Path("/Users/rafaelrodriguez/GitHub/CWC-automation platform/cwc-platform/docs/cwc-pricing-rules.md"),
        ]

        for path in possible_paths:
            if path.exists():
                self._pricing_rules = path.read_text()
                return self._pricing_rules

        # Fallback to embedded pricing info
        self._pricing_rules = """
## CWC Pricing Reference

### Executive Coaching
- Executive Leadership Coaching Program: $9,900 (12 sessions over 6 months, $1,650/month)
- Leadership Clarity Session: $697 (single 90-minute session)
- Executive Coaching Lab: $997 ($100/month for 10 months, group format)

### Consulting
- Hourly: $350/hour
- Project-based: Starting at $5,000

### Discovery Calls
- Free (30-45 minutes)

### Not Offered
- Life Coaching
- DEI Workshops
- Keynote Speaking
"""
        return self._pricing_rules

    def _build_extraction_prompt(self, transcript: str, meeting_title: str | None, attendees: list | None) -> str:
        """Build the prompt for extraction."""
        pricing_rules = self._load_pricing_rules()

        attendee_info = ""
        if attendees:
            attendee_info = "\n".join([
                f"- {a.get('name', 'Unknown')} ({a.get('email', 'no email')})"
                for a in attendees
            ])
        else:
            attendee_info = "No attendee information available"

        return f"""You are an AI assistant helping extract invoice-relevant information from coaching call transcripts.

## Pricing Rules Reference
{pricing_rules}

## Call Information
Meeting Title: {meeting_title or 'Not provided'}
Attendees:
{attendee_info}

## Transcript
{transcript[:15000]}  # Limit transcript length

## Your Task
Analyze this transcript and extract information needed to create an invoice. Return a JSON object with the following structure:

{{
  "is_billable": true/false,  // Is this a billable engagement vs discovery/free call?
  "client_name": "string",    // Full name of the client
  "client_email": "string or null",  // Email if mentioned
  "organization_name": "string or null",  // Company if mentioned
  "service_type": "executive_coaching" | "consulting" | "group_coaching" | "discovery" | "other",
  "package_name": "string or null",  // e.g., "Executive Leadership Coaching Program"
  "price": number or null,    // Price discussed or from pricing rules
  "payment_terms": "string or null",  // e.g., "monthly", "paid in full"
  "num_sessions": number or null,  // Number of sessions if applicable
  "duration_months": number or null,  // Duration in months if applicable
  "start_date": "YYYY-MM-DD or null",  // Start date if discussed
  "special_requests": ["string"],  // Any customizations or special requests
  "key_topics": ["string"],  // Main topics discussed
  "next_steps": ["string"],  // Action items mentioned
  "trigger_phrases": ["string"],  // Phrases that helped identify service type
  "notes": "string"  // Any additional context
}}

## Confidence Scores
Also provide confidence scores (0-100) for key fields:
{{
  "confidence": {{
    "client_name": 0-100,
    "service_type": 0-100,
    "package_name": 0-100,
    "price": 0-100
  }}
}}

Return ONLY valid JSON with both objects nested under a root object with keys "extraction" and "confidence".
If this appears to be a discovery/intro call with no commitment, set is_billable to false.
"""

    async def extract_from_transcript(
        self,
        transcript: str,
        meeting_title: str | None = None,
        attendees: list | None = None,
    ) -> dict:
        """
        Extract invoice data from a transcript using Claude AI.

        Returns:
            dict with 'extraction', 'confidence', and 'raw_response' keys
        """
        if not self.is_configured():
            return {
                "error": "AI extraction not configured. Set ANTHROPIC_API_KEY.",
                "extraction": None,
                "confidence": None,
            }

        prompt = self._build_extraction_prompt(transcript, meeting_title, attendees)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "max_tokens": 2000,
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                    },
                )

                if response.status_code != 200:
                    return {
                        "error": f"Claude API error: {response.status_code} - {response.text}",
                        "extraction": None,
                        "confidence": None,
                    }

                result = response.json()
                content = result.get("content", [{}])[0].get("text", "")

                # Parse JSON from response
                parsed = self._parse_json_response(content)
                if parsed:
                    return {
                        "extraction": parsed.get("extraction", {}),
                        "confidence": parsed.get("confidence", {}),
                        "raw_response": content,
                    }
                else:
                    return {
                        "error": "Failed to parse AI response as JSON",
                        "extraction": None,
                        "confidence": None,
                        "raw_response": content,
                    }

        except Exception as e:
            return {
                "error": f"Extraction failed: {str(e)}",
                "extraction": None,
                "confidence": None,
            }

    def _parse_json_response(self, content: str) -> dict | None:
        """Parse JSON from Claude's response, handling markdown code blocks."""
        # Try direct parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract from markdown code block
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find JSON object in the text
        json_match = re.search(r"\{[\s\S]*\}", content)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def build_invoice_line_items(self, extraction: dict) -> list[dict]:
        """Build invoice line items from extracted data."""
        if not extraction or not extraction.get("is_billable"):
            return []

        line_items = []
        service_type = extraction.get("service_type", "other")
        package_name = extraction.get("package_name", "")
        price = extraction.get("price")

        if service_type == "executive_coaching":
            if "Leadership Coaching Program" in (package_name or ""):
                line_items.append({
                    "description": f"Executive Leadership Coaching Program\n12 sessions over 6 months\nIncludes: DiSC Assessment, Positive Intelligence Test",
                    "quantity": 1,
                    "unit_price": price or 9900,
                    "service_type": "coaching",
                })
            elif "Clarity" in (package_name or ""):
                line_items.append({
                    "description": "Leadership Clarity Session\nSingle 90-minute deep-dive session",
                    "quantity": 1,
                    "unit_price": price or 697,
                    "service_type": "coaching",
                })
            elif "Lab" in (package_name or ""):
                line_items.append({
                    "description": "Executive Coaching Lab - Group Program\n10-month program",
                    "quantity": 1,
                    "unit_price": price or 997,
                    "service_type": "coaching",
                })
            else:
                # Generic coaching
                line_items.append({
                    "description": f"Executive Coaching - {package_name or 'Custom Package'}",
                    "quantity": 1,
                    "unit_price": price or 0,
                    "service_type": "coaching",
                })

        elif service_type == "consulting":
            num_hours = extraction.get("num_sessions") or 1
            line_items.append({
                "description": f"Consulting Services\n{extraction.get('notes', '')}".strip(),
                "quantity": num_hours,
                "unit_price": price or 350,
                "service_type": "consulting",
            })

        elif service_type == "group_coaching":
            line_items.append({
                "description": "Executive Coaching Lab - Group Program\n10-month program",
                "quantity": 1,
                "unit_price": price or 997,
                "service_type": "coaching",
            })

        else:
            # Generic service
            if price:
                line_items.append({
                    "description": extraction.get("notes", "Professional Services"),
                    "quantity": 1,
                    "unit_price": price,
                    "service_type": "other",
                })

        return line_items


# Singleton instance
ai_extraction_service = AIExtractionService()
