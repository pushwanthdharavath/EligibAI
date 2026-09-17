from typing import Optional, Dict, Any
import json
from datetime import datetime
from app.models.scholarship_extraction import ScholarshipExtraction
from app.core.config import settings
from google import genai
import os


class GeminiExtractionService:
    """Service for extracting structured scholarship data using Google Gemini."""
    
    def __init__(self):
        # Check if we have a valid Gemini API key
        self.has_api_key = (
            settings.GEMINI_API_KEY and 
            settings.GEMINI_API_KEY != "your_gemini_api_key_here" and
            "your_" not in settings.GEMINI_API_KEY and
            len(settings.GEMINI_API_KEY) > 10
        )
        
        print(f"Gemini API key check: has_api_key={self.has_api_key}, key_length={len(settings.GEMINI_API_KEY) if settings.GEMINI_API_KEY else 0}")
        
        if self.has_api_key:
            try:
                # Pass API key directly to the client
                self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
                print("Gemini extraction service initialized successfully with API key")
            except Exception as e:
                print(f"Failed to initialize Gemini client: {e}")
                import traceback
                traceback.print_exc()
                self.has_api_key = False
        
        if not self.has_api_key:
            # Use mock service as fallback
            from app.services.llm_extraction_mock import MockLLMExtractionService
            self.mock_service = MockLLMExtractionService()
            print("Warning: No valid Gemini API key found. Using mock extraction service.")
        else:
            # Initialize mock service as fallback
            from app.services.llm_extraction_mock import MockLLMExtractionService
            self.mock_service = MockLLMExtractionService()
            print("Gemini service initialized with fallback to mock service")
    
    def extract_scholarship(
        self,
        content: str,
        source_url: str,
        source_domain: Optional[str] = None,
        skip_gemini: bool = False  # Add flag to skip Gemini
    ) -> Dict[str, Any]:
        """
        Extract structured scholarship information from unstructured content using Gemini.
        
        Args:
            content: Extracted text content from Tavily
            source_url: Original source URL
            source_domain: Source domain name
            skip_gemini: If True, skip Gemini and use mock directly
            
        Returns:
            Structured scholarship data
        """
        # Skip Gemini if flag is set or no API key
        if skip_gemini or not self.has_api_key:
            print("Using mock extraction service (Gemini skipped or no API key)")
            return self.mock_service.extract_scholarship(content, source_url, source_domain)
        
        print(f"Attempting Gemini extraction with model gemini-3.6-flash, content length: {len(content)}")
        
        try:
            # Limit content length to avoid exceeding token limits
            max_content_length = 100000
            if len(content) > max_content_length:
                content = content[:max_content_length]
                print(f"Content truncated to {max_content_length} characters for Gemini extraction")
            
            # Build the extraction prompt
            prompt = self._build_extraction_prompt(content, source_url)
            
            # Generate response using new API with Chat
            chat = self.client.chats.create(model="gemini-3.6-flash")
            response = chat.send_message(prompt)
            
            # Parse the response
            response_text = response.text
            
            # Try to extract JSON from the response
            try:
                scholarship_data = json.loads(response_text)
                
                # Add metadata
                scholarship_data["source_url"] = source_url
                scholarship_data["source_domain"] = source_domain
                scholarship_data["extraction_timestamp"] = datetime.now().isoformat()
                scholarship_data["extraction_confidence"] = "high"
                
                # Identify missing fields
                missing = []
                for key, value in scholarship_data.items():
                    if value is None and key not in ["source_domain", "evidence_snippets", "missing_fields"]:
                        missing.append(key)
                scholarship_data["missing_fields"] = missing if missing else None
                
                print(f"Gemini extraction successful! Extracted scholarship: {scholarship_data.get('scholarship_name', 'unknown')}")
                return {
                    "success": True,
                    "scholarship": scholarship_data,
                    "extraction_metadata": {
                        "content_length": len(content),
                        "content_word_count": len(content.split()),
                        "extraction_time": datetime.now().isoformat(),
                        "model_used": "gemini-3.6-flash",
                        "note": "Extracted using Google Gemini API"
                    }
                }
                
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON from Gemini response: {e}")
                print(f"Response text: {response_text[:500]}")
                # Fallback to mock extraction
                print("Falling back to mock extraction due to JSON parse error")
                return self.mock_service.extract_scholarship(content, source_url, source_domain)
                
        except Exception as e:
            print(f"Gemini extraction error: {e}")
            # Fallback to mock extraction
            print("Falling back to mock extraction due to error")
            return self.mock_service.extract_scholarship(content, source_url, source_domain)
    
    def _build_extraction_prompt(self, content: str, source_url: str) -> str:
        """Build the extraction prompt for Gemini."""
        prompt = f"""
You are a scholarship information extraction expert. Extract structured scholarship information from the following content.

Content:
{content}

Source URL: {source_url}

Extract the following fields and return ONLY a valid JSON object (no markdown, no explanations):
{{
    "scholarship_name": "Name of the scholarship",
    "provider": "Organization/government body providing the scholarship",
    "state": "State if applicable, or null if national",
    "category": ["List of eligible categories like SC, ST, OBC, General, etc."],
    "course": ["List of eligible courses like B.Tech, B.Sc, MBA, etc."],
    "education_level": ["Undergraduate", "Postgraduate", etc. if specified],
    "year_of_study": ["1st Year", "2nd Year", etc. if specified"],
    "age_limit": {{"min": 18, "max": 25}} if age limits specified, or null,
    "gender": "Male/Female/Any if specified, or null",
    "income_limit": {{"max": 500000, "unit": "INR per annum"}} if income limit specified, or null,
    "disability_required": true/false if disability is required, or null,
    "benefits": "Description of benefits/amount",
    "deadline": "Application deadline if specified",
    "source_url": "{source_url}",
    "source_domain": "Domain name of source",
    "evidence_snippets": ["3-4 key sentences from the content that provide evidence"],
    "extraction_confidence": "high/medium/low"
}}

If a field is not mentioned in the content, set it to null. Return ONLY the JSON object, nothing else.
"""
        return prompt
