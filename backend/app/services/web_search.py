import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime
import asyncio
from dataclasses import dataclass
import json
from pathlib import Path

@dataclass
class OfficialSource:
    """Configuration for an official scholarship source."""
    name: str
    base_url: str
    search_url: str
    selectors: Dict[str, str]
    requires_pagination: bool = False
    rate_limit_delay: float = 1.0

class WebSearchService:
    """Service for searching and scraping official scholarship websites."""
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0, follow_redirects=True)
        self.sources = self._initialize_sources()
        self.session_cookies = {}
        
    def _initialize_sources(self) -> List[OfficialSource]:
        """Initialize official scholarship sources."""
        return [
            OfficialSource(
                name="National Scholarship Portal",
                base_url="https://scholarships.gov.in",
                search_url="https://scholarships.gov.in/search",
                selectors={
                    "scholarship_links": "a[href*='scholarship'], a[href*='scheme'], a[href*='scheme']",
                    "title": "h2, h3, h4, .scheme-title, .scholarship-title",
                    "description": "p, .description, .scheme-description",
                    "deadline": "span:contains('Deadline'), span:contains('Last Date'), .deadline, .last-date",
                    "eligibility": "div:contains('Eligibility'), .eligibility"
                },
                rate_limit_delay=2.0
            ),
            OfficialSource(
                name="Telangana ePASS",
                base_url="https://telanganaepass.cgg.gov.in",
                search_url="https://telanganaepass.cgg.gov.in/",
                selectors={
                    "scholarship_links": "a[href*='scholarship'], a[href*='postmatric'], a[href*='prematric']",
                    "title": "h2, h3, h4, .scheme-name",
                    "description": "p, .description",
                    "deadline": "span:contains('Last Date'), span:contains('Deadline'), .deadline",
                    "status": "span:contains('Status')"
                },
                rate_limit_delay=1.5
            ),
            OfficialSource(
                name="AICTE",
                base_url="https://www.aicte-india.org",
                search_url="https://www.aicte-india.org/schemes.php",
                selectors={
                    "scheme_links": "a[href*='scheme'], a[href*='scholarship']",
                    "title": "h2, h3, h4, .scheme-title",
                    "description": "p, .description",
                    "deadline": "span:contains('Last Date'), .deadline"
                },
                rate_limit_delay=1.0
            ),
            OfficialSource(
                name="UGC",
                base_url="https://www.ugc.ac.in",
                search_url="https://www.ugc.ac.in/ugc_notices.php",
                selectors={
                    "scholarship_links": "a[href*='scholarship'], a[href*='scheme']",
                    "title": "h2, h3, h4, .notice-title",
                    "description": "p, .description",
                    "deadline": "span:contains('Last Date'), .deadline"
                },
                rate_limit_delay=1.0
            ),
            OfficialSource(
                name="myScheme",
                base_url="https://www.myscheme.gov.in",
                search_url="https://www.myscheme.gov.in/search",
                selectors={
                    "scheme_links": "a[href*='scheme'], a[href*='scholarship']",
                    "title": "h2, h3, h4, .scheme-title",
                    "description": "p, .description",
                    "deadline": "span:contains('Last Date'), .deadline"
                },
                rate_limit_delay=1.0
            )
        ]
    
    async def search_source(
        self, 
        source: OfficialSource, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search a specific official source for scholarships.
        
        Args:
            source: Official source configuration
            query: Search query
            filters: Optional filters (state, category, education)
            
        Returns:
            List of scholarship information found
        """
        try:
            # Rate limiting
            await asyncio.sleep(source.rate_limit_delay)
            
            # Build search URL with query parameters
            search_params = self._build_search_params(query, filters)
            
            response = await self.client.get(
                source.search_url,
                params=search_params,
                headers=self._get_headers(source)
            )
            
            if response.status_code != 200:
                print(f"Error accessing {source.name}: {response.status_code}")
                return []
            
            # Parse HTML response
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract scholarship information
            scholarships = self._extract_scholarships(soup, source)
            
            # If no results from main page, try alternative approaches
            if not scholarships:
                scholarships = await self._alternative_search(source, query, filters)
            
            return scholarships
            
        except Exception as e:
            print(f"Error searching {source.name}: {e}")
            return []
    
    async def _alternative_search(
        self, 
        source: OfficialSource, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Alternative search methods when main search fails."""
        scholarships = []
        
        try:
            # Try common scholarship URL patterns
            common_paths = [
                "/scholarships",
                "/schemes", 
                "/notices",
                "/announcements",
                "/news",
                "/student-welfare",
                "/education"
            ]
            
            for path in common_paths:
                await asyncio.sleep(source.rate_limit_delay)
                
                try:
                    url = f"{source.base_url}{path}"
                    response = await self.client.get(url, headers=self._get_headers(source))
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        page_scholarships = self._extract_scholarships(soup, source)
                        scholarships.extend(page_scholarships)
                        
                        if scholarships:
                            break
                except:
                    continue
                    
        except Exception as e:
            print(f"Alternative search failed for {source.name}: {e}")
        
        return scholarships
    
    def _build_search_params(self, query: str, filters: Optional[Dict[str, Any]]) -> Dict[str, str]:
        """Build search parameters for the source."""
        params = {"q": query}
        
        if filters:
            if filters.get("state"):
                params["state"] = filters["state"]
            if filters.get("category"):
                params["category"] = filters["category"]
            if filters.get("education"):
                params["education"] = filters["education"]
        
        return params
    
    def _get_headers(self, source: OfficialSource) -> Dict[str, str]:
        """Get appropriate headers for the source."""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9"
        }
        return headers
    
    def _extract_scholarships(self, soup: BeautifulSoup, source: OfficialSource) -> List[Dict[str, Any]]:
        """Extract scholarship information from parsed HTML."""
        scholarships = []
        
        # Try to find scholarship links
        scholarship_links = soup.select(source.selectors["scholarship_links"])
        
        for link in scholarship_links:
            href = link.get('href')
            if not href:
                continue
            
            # Get absolute URL
            absolute_url = urljoin(source.base_url, href)
            
            # Filter out generic links
            if self._is_generic_link(absolute_url):
                continue
            
            # Extract basic information from the link or parent elements
            scholarship = {
                "source": source.name,
                "source_url": absolute_url,
                "title": self._extract_text(link),
                "scraped_at": datetime.now().isoformat()
            }
            
            # Try to get more details from the page
            scholarship.update(self._extract_link_details(link, source))
            
            # Only add if we have meaningful content
            if scholarship.get("title") and len(scholarship["title"]) > 5:
                scholarships.append(scholarship)
        
        return scholarships
    
    def _is_generic_link(self, url: str) -> bool:
        """Filter out generic/homepage links."""
        generic_patterns = [
            r'/$',
            r'/home',
            r'/index',
            r'/contact',
            r'/about',
            r'/privacy',
            r'/terms',
            r'/login',
            r'/register',
            r'/dashboard',
            r'/admin',
            r'/search',
            r'#',
            r'mailto:',
            r'tel:',
            r'javascript:'
        ]
        
        for pattern in generic_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        
        # Filter out very short URLs (likely navigation links)
        if len(url) < 30:
            return True
        
        return False
    
    def _extract_text(self, element) -> str:
        """Extract text from an HTML element."""
        if element:
            return element.get_text(strip=True)
        return ""
    
    def _extract_link_details(self, link, source: OfficialSource) -> Dict[str, Any]:
        """Extract additional details from a scholarship link."""
        details = {}
        
        # Look for parent elements that might contain more information
        parent = link.parent
        if parent:
            # Try to find title in nearby headings
            heading = parent.find(source.selectors["title"])
            if heading:
                details["title"] = self._extract_text(heading)
            
            # Try to find description
            description = parent.find(source.selectors["description"])
            if description:
                details["description"] = self._extract_text(description)
            
            # Try to find deadline
            deadline = parent.find(source.selectors["deadline"])
            if deadline:
                details["deadline"] = self._extract_text(deadline)
        
        return details
    
    async def fetch_scholarship_details(self, url: str, source_name: str) -> Dict[str, Any]:
        """
        Fetch detailed information from a specific scholarship page.
        
        Args:
            url: Scholarship page URL
            source_name: Name of the source
            
        Returns:
            Detailed scholarship information
        """
        try:
            source = next((s for s in self.sources if s.name == source_name), None)
            if not source:
                return {}
            
            await asyncio.sleep(source.rate_limit_delay)
            
            response = await self.client.get(url, headers=self._get_headers(source))
            
            if response.status_code != 200:
                return {}
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract detailed information
            details = {
                "source": source_name,
                "source_url": url,
                "title": self._extract_text(soup.find(source.selectors["title"])),
                "description": self._extract_text(soup.find(source.selectors["description"])),
                "deadline": self._extract_text(soup.find(source.selectors["deadline"])),
                "eligibility": self._extract_text(soup.find(source.selectors["eligibility"])),
                "scraped_at": datetime.now().isoformat()
            }
            
            # Extract all text content for further processing
            details["full_text"] = soup.get_text(separator=' ', strip=True)
            
            return details
            
        except Exception as e:
            print(f"Error fetching details from {url}: {e}")
            return {}
    
    async def search_all_sources(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search all official sources for scholarships.
        
        Args:
            query: Search query
            filters: Optional filters
            
        Returns:
            Combined results from all sources
        """
        all_results = []
        
        for source in self.sources:
            results = await self.search_source(source, query, filters)
            all_results.extend(results)
        
        return all_results
    
    async def detect_changes(self, scholarships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect changes in scholarship information by comparing with current data.
        
        Args:
            scholarships: Current scholarship data
            
        Returns:
            List of detected changes
        """
        changes = []
        
        for scholarship in scholarships:
            source_url = scholarship.get("source_url")
            if not source_url:
                continue
            
            source_name = scholarship.get("source")
            
            # Fetch current information from source
            current_details = await self.fetch_scholarship_details(source_url, source_name)
            
            if not current_details:
                continue
            
            # Compare with stored information
            stored_title = scholarship.get("title", "")
            current_title = current_details.get("title", "")
            
            stored_deadline = scholarship.get("deadline", "")
            current_deadline = current_details.get("deadline", "")
            
            if stored_title != current_title or stored_deadline != current_deadline:
                changes.append({
                    "scholarship_id": scholarship.get("id"),
                    "source": source_name,
                    "source_url": source_url,
                    "type": "information_change",
                    "detected_at": datetime.now().isoformat(),
                    "changes": {
                        "title": {"old": stored_title, "new": current_title},
                        "deadline": {"old": stored_deadline, "new": current_deadline}
                    }
                })
        
        return changes
    
    async def monitor_sources(self, interval_minutes: int = 60):
        """
        Periodically monitor sources for changes.
        
        Args:
            interval_minutes: Monitoring interval in minutes
        """
        while True:
            print(f"Monitoring sources for changes (interval: {interval_minutes} minutes)...")
            
            # Monitoring disabled - static dataset removed
            # # Load current scholarships
            # from app.services.scholarship_dataset import ScholarshipDataset
            # dataset = ScholarshipDataset()
            # current_scholarships = dataset.get_all_scholarships()
            # 
            # # Convert to dict format
            # scholarship_dicts = [
            #     {
            #         "id": s.id,
            #         "source_url": s.source_url,
            #         "title": s.scheme_name,
            #         "deadline": s.deadline
            #     }
            #     for s in current_scholarships
            # ]
            # 
            # # Detect changes
            # changes = await self.detect_changes(scholarship_dicts)
            # 
            # if changes:
            #     print(f"Detected {len(changes)} changes:")
            #     for change in changes:
            #         print(f"  - {change['scholarship_id']}: {change['type']}")
            #     
            #     # Save changes to log file
            #     self._log_changes(changes)
            
            print("Monitoring disabled - static dataset removed. Use live web search instead.")
            
            # Wait for next interval
            await asyncio.sleep(interval_minutes * 60)
    
    def _log_changes(self, changes: List[Dict[str, Any]]):
        """Log detected changes to a file."""
        log_path = Path("backend/logs/source_changes.jsonl")
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        existing_changes = []
        if log_path.exists():
            try:
                with open(log_path, 'r') as f:
                    existing_changes = json.load(f)
            except:
                existing_changes = []
        
        # Add new changes
        existing_changes.extend(changes)
        
        # Keep only last 1000 changes
        existing_changes = existing_changes[-1000:]
        
        with open(log_path, 'w') as f:
            json.dump(existing_changes, f, indent=2)
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

class ScholarshipScraper:
    """Advanced scraper for extracting structured scholarship information."""
    
    def __init__(self):
        self.web_search = WebSearchService()
    
    async def scrape_scholarship_page(self, url: str) -> Dict[str, Any]:
        """
        Scrape a scholarship page and extract structured information.
        
        Args:
            url: URL of the scholarship page
            
        Returns:
            Structured scholarship information
        """
        try:
            source = self._identify_source(url)
            if not source:
                return {}
            
            return await self.web_search.fetch_scholarship_details(url, source.name)
            
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return {}
    
    def _identify_source(self, url: str) -> Optional[OfficialSource]:
        """Identify which official source a URL belongs to."""
        for source in self.web_search.sources:
            if source.base_url in url:
                return source
        return None
    
    async def extract_eligibility_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract eligibility information from unstructured text using regex patterns.
        
        Args:
            text: Text content to parse
            
        Returns:
            Extracted eligibility information
        """
        eligibility = {
            "education": [],
            "income_max": None,
            "income_min": None,
            "category": [],
            "age_min": None,
            "age_max": None,
            "gender": None,
            "state": [],
            "year_of_study": []
        }
        
        # Extract income limits
        income_patterns = [
            r"income.*?(\d+,\d+|\d+)\s*lakh",
            r"Rs\.?\s*(\d+,\d+|\d+)\s*lakh",
            r"₹\s*(\d+,\d+|\d+)\s*lakh"
        ]
        
        for pattern in income_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                # Extract numeric value
                for match in matches:
                    # Remove non-numeric characters
                    numeric = re.sub(r'[^\d,]', '', match)
                    if numeric:
                        value = int(numeric.replace(',', ''))
                        # Convert lakhs to actual value (1 lakh = 100,000)
                        if 'lakh' in match.lower():
                            value *= 100000
                        eligibility["income_max"] = value
                        break
        
        # Extract education requirements
        education_keywords = {
            "B.Tech": ["B.Tech", "B.E.", "Bachelor of Technology", "Engineering"],
            "Diploma": ["Diploma", "Polytechnic"],
            "B.Sc": ["B.Sc", "Bachelor of Science"],
            "M.Tech": ["M.Tech", "Master of Technology"],
            "MBA": ["MBA", "Master of Business Administration"]
        }
        
        for education, keywords in education_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    if education not in eligibility["education"]:
                        eligibility["education"].append(education)
                    break
        
        # Extract category requirements
        categories = ["SC", "ST", "OBC", "General", "EWS", "OBC", "General-EWS"]
        for category in categories:
            if category in text:
                eligibility["category"].append(category)
        
        # Extract state requirements
        states = ["Telangana", "Andhra Pradesh", "Karnataka", "Tamil Nadu", "Maharashtra", "Delhi"]
        for state in states:
            if state in text:
                eligibility["state"].append(state)
        
        return eligibility
    
    async def close(self):
        """Close the web search service."""
        await self.web_search.close()