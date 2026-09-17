from typing import Dict, Any, Optional
from datetime import datetime
import re
import html


class MockLLMExtractionService:
    """Mock LLM extraction service for testing without API keys."""
    
    def _clean_html(self, content: str) -> str:
        """Remove HTML tags and artifacts from content."""
        # Remove HTML tags
        content = re.sub(r'<[^>]+>', ' ', content)
        # Remove HTML entities
        content = html.unescape(content)
        # Remove common markdown image syntax
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
        # Remove markdown links but keep text
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
        # Remove base64 images
        content = re.sub(r'data:image/[a-z]+;base64,[A-Za-z0-9+/=]+', '', content)
        # Remove URLs in parentheses
        content = re.sub(r'\(https?://[^\s)]+\)', '', content)
        # Remove markdown tables
        content = re.sub(r'\|.*?\|', '', content)
        content = re.sub(r'---+', '', content)
        # Remove navigation menus and common web artifacts
        content = re.sub(r'(Education Loan|Blog|Contact Us|More|Careers|Services|University Express|LoanFlix|Nyra)', '', content)
        content = re.sub(r'(Filter Scholarships|SORT BY|Date Posted|Date posted|Deadline|Popularity)', '', content)
        # Remove "s * " navigation artifacts
        content = re.sub(r'\bs\s*\*\s*', '', content)
        # Remove "s, " navigation artifacts
        content = re.sub(r'\bs,\s*', '', content)
        # Remove webpage metadata sections
        content = re.sub(r'(Also Check|FAQs|Ques\.|Updated|months ago|Content Curator|Top Colleges|Fee Structure|Salary for Freshers|Specializations|Tabulated below)', '', content, flags=re.IGNORECASE)
        # Remove scholarship list headers
        content = re.sub(r'(List of|Incoming|Special Financial Assistance|Saksham|Swanath|Post Matric|Merit Cum Means|Annual Sahara)', '', content, flags=re.IGNORECASE)
        # Remove bullet points of scholarship names (not actual scholarship details)
        content = re.sub(r'\*\s*[A-Z][a-zA-Z\s]+(?:Scholarship|Scheme|Grant)', '', content)
        # Remove general text about scholarships
        content = re.sub(r'(Scholarship for.*?Students|Students can apply|Applicable for students|Eligible students|wtf is this)', '', content, flags=re.IGNORECASE)
        # Remove steps to apply, top colleges, etc.
        content = re.sub(r'(Steps to Apply|Top Colleges|Waqar Niyazi|Content Curator)', '', content, flags=re.IGNORECASE)
        # Remove INR fee tables
        content = re.sub(r'INR\s+\d+\s*[Lk]+', '', content)
        # Remove table-like structures with college names
        content = re.sub(r'(Tabulated below|Below is|fee details of top)', '', content, flags=re.IGNORECASE)
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        # Remove repeated words
        content = re.sub(r'\b(\w+)\s+\1\b', r'\1', content)
        return content.strip()
    
    def extract_scholarship(
        self,
        content: str,
        source_url: str,
        source_domain: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Mock extraction that uses regex patterns to extract structured data.
        This is a fallback when no LLM API key is available.
        """
        try:
            # Clean HTML from content
            content = self._clean_html(content)
            
            # Limit content length for mock extraction to avoid performance issues
            max_content_length = 50000
            if len(content) > max_content_length:
                content = content[:max_content_length]
                print(f"Content truncated to {max_content_length} characters for mock extraction")
            
            # Extract scholarship name - try URL-based name first
            scholarship_name = self._extract_scholarship_name_from_url(source_url)
            if not scholarship_name:
                scholarship_name = self._extract_scholarship_name(content)
            
            scholarship_data = {
                "scholarship_name": scholarship_name,
                "provider": self._extract_provider(content, source_url),
                "state": self._extract_state(content),
                "category": self._extract_category(content),
                "course": self._extract_course(content),
                "income_limit": self._extract_income(content),
                "benefits": self._extract_benefits(content),
                "deadline": self._extract_deadline(content),
                "source_url": source_url,
                "source_domain": source_domain,
                "extraction_timestamp": datetime.now().isoformat(),
                "evidence_snippets": self._extract_evidence(content),
                "extraction_confidence": "medium",
                "missing_fields": []
            }
            
            # Identify missing fields
            missing = []
            for key, value in scholarship_data.items():
                if value is None and key not in ["source_domain", "evidence_snippets", "missing_fields"]:
                    missing.append(key)
            scholarship_data["missing_fields"] = missing if missing else None
            
            return {
                "success": True,
                "scholarship": scholarship_data,
                "extraction_metadata": {
                    "content_length": len(content),
                    "content_word_count": len(content.split()),
                    "extraction_time": datetime.now().isoformat(),
                    "model_used": "mock_regex_extractor",
                    "note": "This is a mock extraction using regex patterns. For production, configure an OpenAI API key."
                }
            }
            
        except Exception as e:
            print(f"Mock extraction error: {e}")
            return {
                "success": False,
                "error": str(e),
                "scholarship": None
            }
    
    def _extract_scholarship_name_from_url(self, source_url: str) -> Optional[str]:
        """Extract scholarship name from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(source_url)
        
        # Check for specific scholarship indicators in URL
        if 'scholarship' in parsed.path.lower():
            parts = parsed.path.split('/')
            for part in parts:
                if part and len(part) > 5 and 'scholarship' in part.lower():
                    return part.replace('-', ' ').replace('_', ' ').title()
        
        # Check for scheme names
        if 'scheme' in parsed.path.lower():
            parts = parsed.path.split('/')
            for part in parts:
                if part and len(part) > 5 and 'scheme' in part.lower():
                    return part.replace('-', ' ').replace('_', ' ').title()
        
        return None
    
    def _extract_scholarship_name(self, content: str) -> Optional[str]:
        """Extract scholarship name using patterns."""
        # Very lenient - skip only code repositories
        skip_phrases = [
            'github.com',
            'gitlab.com',
            'bitbucket.org',
            'repository',
            'pull request',
            'issue',
            'fork',
            'star',
            'code'
        ]
        
        for phrase in skip_phrases:
            if re.search(phrase, content, re.IGNORECASE):
                return None  # Skip extraction for code repositories
        
        patterns = [
            r'(?:Scholarship|Scheme|Fellowship|Grant)\s*(?:for|of|:)?\s*([^.]{5,100}?)(?:\.|for|under|is|The)',
            r'([A-Z][^.]{5,100}?(?:Scholarship|Scheme|Fellowship|Grant)[^.]{0,50}?)(?:\.|is|The)',
            r'(Post(?:-|\s)?Matric)\s*(?:Scholarship|Scheme)[^.]{5,100}?',
            r'(Pre(?:-|\s)?Matric)\s*(?:Scholarship|Scheme)[^.]{5,100}?',
            r'(Merit(?:-|\s)?Cum(?:-|\s)?Means)[^.]{5,100}?',
            r'(Central(?:-|\s)?Sector)[^.]{5,100}?',
            r'(State(?:-|\s)?Government)[^.]{5,100}?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                name = match.group(0).strip()
                # Clean up common artifacts
                name = re.sub(r'\s+', ' ', name)
                name = re.sub(r'^\W+|\W+$', '', name)
                # Remove administrative phrases
                name = re.sub(r'(guidelines|scheme of|top class|education|2018|2019|2020|2021|2022|2023|2024|2025|2026)', '', name, flags=re.IGNORECASE)
                name = name.strip()
                # Reject obvious form fields
                if re.search(r'\[x\]', name) or re.search(r'\d+\s*-\s*\d+', name) or re.search(r'»', name):
                    continue
                # Very lenient length check
                if len(name) > 5 and len(name) < 150:
                    return name
        
        # Try to find any capitalized phrase with scholarship-related words
        sentences = content.split('.')
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['scholarship', 'scheme', 'fellowship', 'grant', 'benefit', 'assistance']):
                # Extract first 8-15 words as name
                words = sentence.strip().split()
                if len(words) >= 3 and len(words) <= 15:
                    candidate = ' '.join(words[:8])
                    if len(candidate) > 10 and len(candidate) < 100:
                        return candidate
        
        # Last resort: return a generic name
        return "Government Scholarship Scheme"
    
    def _extract_provider(self, content: str, source_url: str) -> Optional[str]:
        """Extract provider/organization."""
        from urllib.parse import urlparse
        
        # First try to extract from content
        patterns = [
            r'(Government of Telangana|Government of India|Government of Andhra Pradesh|Government of Karnataka)',
            r'(Ministry of [^.]+?)(?:\.|and)',
            r'(Department of [^.]+?)(?:\.|and)',
            r'(AICTE|UGC|NSP)\s+(?:Government|Council|Portal)',
            r'(Telangana ePASS|National Scholarship Portal|Karnataka SSP)',
            r'(State Government|Central Government)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                provider = match.group(0).strip()
                # Truncate incomplete sentences
                if provider.endswith(' and'):
                    provider = provider[:-4].strip()
                if len(provider) > 5 and len(provider) < 100:
                    return provider
        
        # Fallback to domain-based provider
        parsed = urlparse(source_url)
        domain = parsed.netloc.replace('www.', '')
        
        # Map domains to provider names
        domain_providers = {
            'scholarships.gov.in': 'National Scholarship Portal',
            'buddy4study.com': 'Buddy4Study',
            'collegedunia.com': 'CollegeDunia',
            'vidhyaa.in': 'Vidhyaa',
            'nitk.ac.in': 'NITK',
            'rnsit.ac.in': 'RNSIT',
            'sevasindhukarnataka.com': 'Seva Sindhu Karnataka',
        }
        
        for key, value in domain_providers.items():
            if key in domain:
                return value
        
        # Default to Government of India if no provider found
        return "Government of India"
    
    def _extract_state(self, content: str) -> Optional[str]:
        """Extract state information."""
        states = ['Telangana', 'Andhra Pradesh', 'Karnataka', 'Tamil Nadu', 'Maharashtra', 'Delhi', 'India', 'Kerala', 'Madhya Pradesh', 'Punjab', 'Haryana', 'Bihar', 'Odisha', 'Gujarat', 'Rajasthan', 'Uttar Pradesh', 'West Bengal']
        
        # Check for state mentions
        for state in states:
            if state.lower() in content.lower():
                return state
        
        # Default to India if no state found
        return "India"
    
    def _extract_category(self, content: str) -> Optional[list]:
        """Extract category information."""
        categories = []
        category_keywords = ['SC', 'ST', 'OBC', 'BC', 'EBC', 'General', 'Minority', 'Disabled', 'Physically Challenged', 'Differently Abled']
        
        for cat in category_keywords:
            if cat.upper() in content.upper():
                categories.append(cat)
        
        return categories if categories else None
    
    def _extract_course(self, content: str) -> Optional[list]:
        """Extract course information."""
        courses = []
        course_keywords = ['B.Tech', 'B.E.', 'M.Tech', 'B.Sc', 'M.Sc', 'MBA', 'Diploma', 'Engineering', 'Graduate', 'Postgraduate']
        
        for course in course_keywords:
            if course in content:
                courses.append(course)
        
        return courses if courses else None
    
    def _extract_income(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract income limit."""
        patterns = [
            r'(?:income|salary)\s*(?:should|must|less than|below|up to)?\s*(?:be|of)?\s*(?:INR|Rs\.?|₹)?\s*([\d,]+)\s*(?:per annum|annually|p\.a\.)?',
            r'(?:INR|Rs\.?|₹)\s*([\d,]+)\s*(?:per annum|annually|p\.a\.|L|Lakhs)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    amount = int(amount_str)
                    # Convert to lakhs if amount is in lakhs
                    if 'L' in content.upper() or 'Lakhs' in content:
                        amount = amount * 100000
                    # Sanity check: reject unrealistically high values
                    if amount > 10000000:  # More than 1 crore is suspicious
                        return None
                    return {"max": amount, "unit": "INR per annum"}
                except:
                    pass
        
        return None
    
    def _extract_benefits(self, content: str) -> Optional[str]:
        """Extract benefits information."""
        patterns = [
            r'(?:benefit|amount|scholarship amount|financial assistance|coverage|support)[^.]{10,200}?(?:\.|$)',
            r'(?:reimbursement|allowance|grant|stipend|funding)[^.]{10,200}?(?:\.|$)',
            r'(?:INR|Rs\.?|₹)\s*[\d,]+\s*(?:per annum|annually|p\.a\.|L|Lakhs)[^.]{0,100}',
            r'(?:up to|maximum of|eligible for)[^.]{10,200}?(?:\.|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                benefit = match.group(0).strip()
                # Clean up
                benefit = re.sub(r'\s+', ' ', benefit)
                # Truncate very long administrative text
                if len(benefit) > 150:
                    benefit = benefit[:150] + "..."
                # Filter out fragments
                if len(benefit) > 20 and not benefit.lower().startswith('and') and not benefit.lower().startswith('or'):
                    return benefit
        
        return "Financial assistance for education"
    
    def _extract_deadline(self, content: str) -> Optional[str]:
        """Extract deadline information."""
        patterns = [
            r'(?:deadline|last date|due date|application date)[^.]{5,100}?(?:\.|$)',
            r'(?:Always Open|Rolling|Open throughout|No deadline)',
            r'(?:\d{1,2}(?:st|nd|rd|th)?\s*(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[^.]{0,50})',
            r'(?:\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                deadline = match.group(0).strip()
                # Clean up
                deadline = re.sub(r'\s+', ' ', deadline)
                # Truncate very long administrative text
                if len(deadline) > 80:
                    deadline = deadline[:80] + "..."
                # Filter out fragments
                if len(deadline) > 8 and not deadline.lower().startswith('and') and not deadline.lower().startswith('or'):
                    return deadline
        
        return "Visit official portal for deadline"
    
    def _extract_evidence(self, content: str) -> Optional[list]:
        """Extract key evidence snippets."""
        snippets = []
        sentences = content.split('.')
        
        # Look for sentences with key information
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in ['eligible', 'benefit', 'deadline', 'apply', 'scholarship']):
                clean = sentence.strip()
                if len(clean) > 20 and len(clean) < 300:
                    snippets.append(clean)
                    if len(snippets) >= 3:
                        break
        
        return snippets if snippets else None
