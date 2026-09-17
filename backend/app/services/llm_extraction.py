from openai import OpenAI
from typing import Optional, Dict, Any
import json
from datetime import datetime
from app.models.scholarship_extraction import ScholarshipExtraction
from app.core.config import settings


class LLMExtractionService:
    """Service for extracting structured scholarship data using LLM."""
    
    def __init__(self, force_mock: bool = False):
        # Force mock extraction if flag is set (to avoid quota issues)
        self.force_mock = force_mock
        
        # Check if we have a valid Gemini API key (preferred)
        gemini_key = settings.GEMINI_API_KEY
        self.use_gemini = (
            not force_mock and  # Don't use Gemini if forced to mock
            gemini_key and 
            gemini_key != "your_gemini_api_key_here" and
            "your_" not in gemini_key and
            len(gemini_key) > 10
        )
        
        print(f"LLMExtractionService init: force_mock={force_mock}, use_gemini={self.use_gemini}, key_exists={bool(gemini_key)}, key_length={len(gemini_key) if gemini_key else 0}")
        
        if self.use_gemini:
            try:
                from app.services.llm_extraction_gemini import GeminiExtractionService
                self.gemini_service = GeminiExtractionService()
                print(f"Using Gemini for LLM extraction (has_api_key={self.gemini_service.has_api_key})")
            except Exception as e:
                print(f"Failed to initialize Gemini service: {e}")
                import traceback
                traceback.print_exc()
                self.use_gemini = False
        
        # Fallback to OpenAI if Gemini not available AND not forced to mock
        if not self.use_gemini and not self.force_mock:
            self.has_openai_key = (
                settings.OPENAI_API_KEY and 
                settings.OPENAI_API_KEY != "your_openai_api_key_here" and
                "your_" not in settings.OPENAI_API_KEY and
                "sk-" in settings.OPENAI_API_KEY  # Valid OpenAI keys start with sk-
            )
            
            if self.has_openai_key:
                try:
                    self.client = OpenAI(
                        api_key=settings.OPENAI_API_KEY,
                        base_url=settings.OPENAI_BASE_URL if hasattr(settings, 'OPENAI_BASE_URL') else None
                    )
                    self.model = settings.MODEL_NAME if hasattr(settings, 'MODEL_NAME') else "gpt-4o-mini"
                    print("Using OpenAI for LLM extraction")
                except Exception as e:
                    print(f"Failed to initialize OpenAI client: {e}")
                    self.has_openai_key = False
            else:
                self.has_openai_key = False
        else:
            self.has_openai_key = False
        
        # Final fallback to mock service
        if not self.use_gemini and not self.has_openai_key:
            from app.services.llm_extraction_mock import MockLLMExtractionService
            self.mock_service = MockLLMExtractionService()
            print("Warning: No valid LLM API key found. Using mock extraction service.")
        else:
            # Initialize mock service as fallback in case LLM fails
            from app.services.llm_extraction_mock import MockLLMExtractionService
            self.mock_service = MockLLMExtractionService()
            if self.force_mock:
                print("FORCE MOCK MODE: Using mock extraction service exclusively")
            else:
                print("Gemini service initialized with fallback to mock service")
    
    def extract_scholarship(
        self,
        content: str,
        source_url: str,
        source_domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured scholarship information from unstructured content.
        
        Args:
            content: Extracted text content from Tavily
            source_url: Original source URL
            source_domain: Source domain (optional)
            
        Returns:
            Dictionary with extracted scholarship data and metadata
        """
        # If forced to use mock, skip all LLM attempts
        if self.force_mock:
            print("Force mock mode enabled - using mock extraction directly")
            return self.mock_service.extract_scholarship(content, source_url, source_domain)
        
        # Try Gemini first (preferred)
        if self.use_gemini:
            try:
                print("Using Gemini extraction service")
                result = self.gemini_service.extract_scholarship(content, source_url, source_domain)
                if result.get("extraction_metadata", {}).get("model_used") == "gemini-3.6-flash":
                    print("Real Gemini extraction successful")
                return result
            except Exception as e:
                print(f"Gemini extraction error: {e}")
                print("Falling back to OpenAI or mock extraction")
        
        # Try OpenAI if Gemini not available
        if self.has_openai_key:
            try:
                extraction_prompt = self._build_extraction_prompt(content, source_url)
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": self._get_system_prompt()
                        },
                        {
                            "role": "user",
                            "content": extraction_prompt
                        }
                    ],
                    temperature=0.1,  # Low temperature for consistent extraction
                    response_format={"type": "json_object"}
                )
                
                extracted_json = json.loads(response.choices[0].message.content)
                
                # Validate and structure the extraction
                scholarship_data = self._process_extraction(extracted_json, source_url, source_domain)
                
                return {
                    "success": True,
                    "scholarship": scholarship_data,
                    "extraction_metadata": {
                        "content_length": len(content),
                        "content_word_count": len(content.split()),
                        "extraction_time": datetime.now().isoformat(),
                        "model_used": self.model,
                        "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else None
                    }
                }
                
            except Exception as e:
                print(f"OpenAI extraction error: {e}")
                # Fallback to mock if OpenAI fails
                print("Falling back to mock extraction service")
        
        # Final fallback to mock service
        return self.mock_service.extract_scholarship(content, source_url, source_domain)
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for LLM extraction."""
        return """You are an expert at extracting structured scholarship information from unstructured text. Your task is to carefully analyze the provided scholarship content and extract specific fields.

IMPORTANT RULES:
1. ONLY extract information that is EXPLICITLY stated in the text
2. If a field is not mentioned, leave it as null or omit it - DO NOT guess or hallucinate
3. Preserve exact wording when possible, especially for scholarship names and benefits
4. Be conservative with confidence - if information is unclear, mark it as missing
5. Extract the actual source URL as provided
6. Identify key evidence snippets that support your extraction
7. Separate explicit requirements from general information

EXTRACTION FIELDS TO FOCUS ON:
- Scholarship name and provider
- Eligibility criteria (state, category, income, education, age, gender, disability)
- Benefits and amount
- Deadline and application process
- Required documents
- Source URL (use the one provided in the input)

RESPONSE FORMAT:
Return a JSON object with the extracted scholarship information using the standard schema. Include an "evidence_snippets" array with 2-3 key quotes from the text that support your extraction, and a "missing_fields" array listing important information that could not be found."""
    
    def _build_extraction_prompt(self, content: str, source_url: str) -> str:
        """Build the extraction prompt."""
        return f"""Extract structured scholarship information from the following content.

SOURCE URL: {source_url}

CONTENT:
{content}

Please extract all available scholarship information following the schema. Be thorough but conservative - only extract what is explicitly stated."""
    
    def _process_extraction(
        self,
        extracted_json: Dict[str, Any],
        source_url: str,
        source_domain: Optional[str]
    ) -> Dict[str, Any]:
        """Process and validate the LLM extraction."""
        
        # Ensure source URL is set
        extracted_json["source_url"] = source_url
        if source_domain:
            extracted_json["source_domain"] = source_domain
        
        # Set extraction timestamp
        extracted_json["extraction_timestamp"] = datetime.now().isoformat()
        
        # Identify missing fields
        missing_fields = []
        important_fields = [
            "scholarship_name", "provider", "state", "category", "course",
            "income_limit", "benefits", "deadline"
        ]
        
        for field in important_fields:
            if field not in extracted_json or extracted_json[field] is None:
                missing_fields.append(field)
        
        extracted_json["missing_fields"] = missing_fields if missing_fields else None
        
        # Validate income limit format
        if "income_limit" in extracted_json and extracted_json["income_limit"]:
            if isinstance(extracted_json["income_limit"], str):
                # Try to parse string income limit
                try:
                    extracted_json["income_limit"] = {
                        "description": extracted_json["income_limit"]
                    }
                except:
                    pass
        
        # Validate age limit format
        if "age_limit" in extracted_json and extracted_json["age_limit"]:
            if isinstance(extracted_json["age_limit"], str):
                # Try to parse string age limit
                try:
                    extracted_json["age_limit"] = {
                        "description": extracted_json["age_limit"]
                    }
                except:
                    pass
        
        # Set default confidence based on missing fields
        if len(missing_fields) <= 2:
            extracted_json["extraction_confidence"] = "high"
        elif len(missing_fields) <= 4:
            extracted_json["extraction_confidence"] = "medium"
        else:
            extracted_json["extraction_confidence"] = "low"
        
        return extracted_json
    
    def extract_batch(
        self,
        extractions: list[tuple[str, str, Optional[str]]]
    ) -> list[Dict[str, Any]]:
        """
        Extract scholarships from multiple content sources.
        
        Args:
            extractions: List of (content, source_url, source_domain) tuples
            
        Returns:
            List of extraction results
        """
        results = []
        for content, url, domain in extractions:
            result = self.extract_scholarship(content, url, domain)
            results.append(result)
        return results
