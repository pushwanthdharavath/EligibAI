from tavily import TavilyClient
from typing import List, Dict, Any, Optional
import os
from datetime import datetime
from urllib.parse import urlparse

class TavilySearchService:
    """Service for searching scholarships using Tavily API."""
    
    def __init__(self):
        self.api_key = os.getenv("TAVILY_API_KEY", "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")
        self.client = TavilyClient(api_key=self.api_key)
        
        # Focus on official government scholarship sources
        self.official_domains = [
            "scholarships.gov.in",  # National Scholarship Portal
            "telanganaepass.cgg.gov.in",  # Telangana ePASS
            "jnanabhumi.ap.gov.in",  # Andhra Pradesh Jnanabhumi
            "jnanabhumiexams.apcfss.in",  # Andhra Pradesh Exams
            "epass.apcfss.in",  # Andhra Pradesh ePASS
            "www.aicte-india.org",  # AICTE
            "www.ugc.ac.in",  # UGC
            "www.myscheme.gov.in",  # myScheme
            "www.education.gov.in",  # Ministry of Education
            "www.socialjustice.gov.in"  # Ministry of Social Justice
        ]
    
    def search_scholarships(
        self, 
        query: str, 
        profile: Optional[Dict[str, Any]] = None,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Search for scholarships using Tavily, prioritizing official sources.
        
        Args:
            query: Search query (e.g., "B.Tech scholarships for SC students in Telangana")
            profile: Optional user profile for context
            max_results: Maximum number of results to return
            
        Returns:
            List of scholarship search results with URLs and metadata
        """
        try:
            # Build enhanced query with profile context
            enhanced_query = self._build_enhanced_query(query, profile)
            print(f"[TAVILY SEARCH] Query: {enhanced_query}")
            print(f"[TAVILY SEARCH] Max results requested: {max_results}")
            
            # Search with Tavily without domain restrictions (government portals have poor SEO)
            search_result = self.client.search(
                query=enhanced_query,
                search_depth="advanced",
                max_results=max_results * 4,  # Get more results to filter
                include_raw_content=False,
                days=90  # Search recent results from last 90 days
            )
            
            print(f"[TAVILY SEARCH] Raw results from Tavily: {len(search_result.get('results', []))}")
            
            results = []
            official_results = []
            reliable_results = []
            
            for result in search_result.get("results", []):
                url = result.get("url", "")
                
                # Skip GitHub and code repositories - they don't contain scholarship info
                if "github.com" in url or "gitlab.com" in url or "bitbucket.org" in url:
                    continue
                
                is_official = self._is_official_domain(url)
                
                scholarship_result = {
                    "title": result.get("title"),
                    "url": url,
                    "snippet": result.get("content"),
                    "source": self._identify_source(url),
                    "is_official": is_official,
                    "score": result.get("score", 0),
                    "published_date": result.get("published_date"),
                    "searched_at": datetime.now().isoformat()
                }
                
                if is_official:
                    official_results.append(scholarship_result)
                else:
                    reliable_results.append(scholarship_result)
            
            print(f"[TAVILY SEARCH] Raw Tavily results: {len(search_result.get('results', []))} total")
            print(f"[TAVILY SEARCH] Filtered: {len(official_results)} official, {len(reliable_results)} reliable")
            print(f"[TAVILY SEARCH] Final results returned: {len(results)}")
            
            # Prioritize official results, then add reliable ones if needed
            results = official_results
            if len(results) < max_results and reliable_results:
                results.extend(reliable_results[:max_results - len(results)])
            
            # Limit to max_results
            results = results[:max_results]
            
            if not results:
                print(f"No results found for query: {query}")
            else:
                print(f"Found {len(results)} results ({len(official_results)} official, {len(reliable_results) - len(official_results)} reliable)")
                print(f"Websites fetched: {[r.get('url', 'unknown') for r in results]}")
            
            return results
            
        except Exception as e:
            print(f"Tavily search error: {e}")
            return []
    
    def _build_enhanced_query(self, query: str, profile: Optional[Dict[str, Any]]) -> str:
        """Build enhanced search query with profile context."""
        if not profile:
            return query
        
        # Add relevant profile information to query
        context_parts = [query]
        
        if profile.get("state"):
            context_parts.append(f"{profile['state']} state")
        
        if profile.get("category"):
            context_parts.append(f"{profile['category']} category")
        
        if profile.get("course"):
            context_parts.append(f"{profile['course']} course")
        
        if profile.get("yearOfStudy"):
            context_parts.append(f"{profile['yearOfStudy']}")
        
        enhanced_query = " ".join(context_parts)
        return enhanced_query
    
    def _is_official_domain(self, url: str) -> bool:
        """Check if URL belongs to an official government domain."""
        for domain in self.official_domains:
            if domain in url:
                return True
        return False
    
    def _identify_source(self, url: str) -> str:
        """Identify which source a URL belongs to."""
        # Check official domains first
        for domain in self.official_domains:
            if domain in url:
                return domain.replace("www.", "").replace(".gov.in", "").replace(".org", "")
        
        # Handle common non-official but reliable sources
        if "buddy4study.com" in url:
            return "Buddy4Study"
        elif "collegedunia.com" in url:
            return "CollegeDunia"
        elif "scholarships360.com" in url:
            return "Scholarships360"
        elif "vidyavision.com" in url:
            return "Vidyavision"
        elif "wemakescholars.com" in url:
            return "WeMakeScholars"
        elif "iare.ac.in" in url:
            return "IARE"
        elif "saitm.ac.in" in url:
            return "SAITM"
        else:
            # Extract domain name as fallback
            try:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc.replace("www.", "")
                # Return the main domain part
                return domain.split(".")[0].capitalize()
            except:
                return "Other Source"
    
    def search_by_source(
        self, 
        source: str, 
        query: str, 
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search a specific official source for scholarships.
        
        Args:
            source: Source name (e.g., "NSP", "ePASS", "AICTE")
            query: Search query
            max_results: Maximum results
            
        Returns:
            Results from specific source
        """
        try:
            # Map source names to domains
            source_domains = {
                "NSP": "scholarships.gov.in",
                "ePASS": "telanganaepass.cgg.gov.in",
                "AICTE": "www.aicte-india.org",
                "UGC": "www.ugc.ac.in",
                "myScheme": "www.myscheme.gov.in"
            }
            
            domain = source_domains.get(source)
            if not domain:
                return []
            
            search_result = self.client.search(
                query=query,
                search_depth="advanced",
                max_results=max_results,
                include_domains=[domain],
                days=30
            )
            
            results = []
            for result in search_result.get("results", []):
                results.append({
                    "title": result.get("title"),
                    "url": result.get("url"),
                    "snippet": result.get("content"),
                    "source": source,
                    "score": result.get("score", 0),
                    "searched_at": datetime.now().isoformat()
                })
            
            return results
            
        except Exception as e:
            print(f"Source-specific search error: {e}")
            return []