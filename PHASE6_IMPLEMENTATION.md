# Phase 6 Implementation: Web Search for Official Sources

## Overview

Phase 6 implements real-time web search and scraping capabilities for official scholarship sources, enabling EligibAI to retrieve current information from government portals and maintain an up-to-date knowledge base.

## Components Implemented

### 1. Web Search Service (`backend/app/services/web_search.py`)

**Key Features:**
- `WebSearchService`: Main service for searching official scholarship websites
- `ScholarshipScraper`: Advanced scraper for extracting structured information
- Support for 5 official sources:
  - National Scholarship Portal (NSP)
  - Telangana ePASS
  - AICTE
  - UGC
  - myScheme

**Capabilities:**
- Async HTTP requests with proper rate limiting
- HTML parsing with BeautifulSoup
- Configurable selectors for each source
- Change detection and monitoring
- Automatic eligibility extraction from unstructured text
- Source change logging

**Key Methods:**
- `search_source()`: Search a specific official source
- `search_all_sources()`: Search all configured sources
- `fetch_scholarship_details()`: Get detailed information from a specific page
- `detect_changes()`: Monitor sources for changes
- `monitor_sources()`: Periodic monitoring with configurable intervals
- `extract_eligibility_from_text()`: Parse eligibility from unstructured text

### 2. Web Search API Routes (`backend/app/api/routes_websearch.py`)

**Endpoints:**
- `POST /api/websearch/search` - Search official sources
- `POST /api/websearch/scrape` - Scrape specific scholarship page
- `POST /api/websearch/extract-eligibility` - Extract eligibility from text
- `POST /api/websearch/monitor/start` - Start source monitoring
- `GET /api/websearch/sources` - List configured sources
- `GET /api/websearch/changes` - Get recent detected changes

### 3. LangGraph Agent Integration (`backend/app/agents/scholarship_agent.py`)

**New Tool:**
- `search_official_sources()`: Real-time web search tool for the agent
- Integrated with existing agent workflow
- Supports state and category filtering
- Returns live results from official portals

### 4. Main API Integration (`backend/app/api/routes.py`)

**New Endpoint:**
- `POST /api/live-search` - Direct live search from main API
- Supports profile-based filtering
- Returns results from official sources

### 5. Frontend Integration (`frontend/src/components/UserProfileForm.tsx`)

**New Features:**
- "Search Official Sources (Live)" button
- Live search results display section
- Real-time results from government portals
- Source identification and deadline information
- Green badge indicating live data

### 6. Dependencies Updated (`backend/requirements.txt`)

**New Dependencies:**
- `beautifulsoup4`: HTML parsing
- `httpx`: Async HTTP client
- `lxml`: XML/HTML parser

## Key Capabilities

### Real-Time Information Retrieval
- Searches official government portals in real-time
- Returns current scholarship information including deadlines
- Detects new scholarships not in static dataset

### Change Detection
- Monitors sources for changes in scholarship information
- Tracks deadline updates and policy changes
- Logs changes to JSONL file for analysis
- Configurable monitoring intervals

### Automated Eligibility Extraction
- Parses unstructured text to extract eligibility rules
- Extracts income limits, education requirements, categories
- Supports regex-based pattern matching
- Returns structured eligibility information

### Rate Limiting & Respectful Scraping
- Configurable rate limits per source
- Proper user-agent headers
- Follows redirect chains
- Graceful error handling

### Source Management
- Configurable selectors for each source
- Easy addition of new sources
- Source-specific rate limiting
- Automatic source identification

## Usage Examples

### API Usage

```bash
# Search official sources
curl -X POST http://localhost:8000/api/websearch/search \
  -H "Content-Type: application/json" \
  -d '{"query": "B.Tech scholarships Telangana", "filters": {"state": "Telangana"}}'

# Scrape specific page
curl -X POST http://localhost:8000/api/websearch/scrape \
  -H "Content-Type: application/json" \
  -d '{"url": "https://scholarships.gov.in/scholarship123"}'

# Extract eligibility from text
curl -X POST http://localhost:8000/api/websearch/extract-eligibility \
  -H "Content-Type: application/json" \
  -d '{"text": "Annual family income should not exceed 5 lakh"}'

# Live search from main API
curl -X POST http://localhost:8000/api/live-search \
  -H "Content-Type: application/json" \
  -d '{"query": "SC scholarships", "user_profile": {...}}'
```

### Agent Usage

The LangGraph agent can now use the `search_official_sources` tool to:
- Search official sources when local dataset is insufficient
- Get current deadline information
- Find newly announced scholarships
- Verify scholarship information

### Frontend Usage

Users can:
1. Fill out their profile
2. Click "Search Official Sources (Live)" button
3. View real-time results from government portals
4. See source information and deadlines
5. Click links to official sources

## Benefits

### For Users
- Access to current scholarship information
- Real-time deadline updates
- Discovery of new scholarships
- Verification of scholarship details

### For System
- Reduced maintenance burden
- Automatic knowledge base updates
- Improved data currency
- Enhanced reliability

### For Developers
- Easy addition of new sources
- Configurable scraping rules
- Comprehensive logging
- Graceful error handling

## Configuration

### Adding New Sources

To add a new official source:

```python
OfficialSource(
    name="New Source",
    base_url="https://example.com",
    search_url="https://example.com/search",
    selectors={
        "scholarship_links": "a[href*='scholarship']",
        "title": "h2, h3",
        "description": "p",
        "deadline": "span:contains('Deadline')"
    },
    rate_limit_delay=1.0
)
```

### Monitoring Configuration

```python
# Start monitoring with custom interval
await web_search.monitor_sources(interval_minutes=60)
```

## Error Handling

- Graceful degradation when sources are unavailable
- Rate limiting to prevent blocking
- Timeout handling for slow responses
- Fallback to static dataset when web search fails
- Comprehensive error logging

## Future Enhancements

### Potential Improvements
- Proxy support for better reliability
- CAPTCHA handling
- JavaScript rendering with Selenium/Playwright
- More sophisticated change detection
- Automatic dataset updates
- Scheduled crawling jobs
- Distributed scraping with Celery

### Additional Sources
- More state government portals
- Central government ministry portals
- International scholarship databases
- NGO scholarship databases

## Security Considerations

- No sensitive data stored in scraping
- Proper user-agent headers
- Rate limiting to prevent abuse
- Input validation for URLs
- Sanitization of scraped content

## Performance

- Async operations for concurrent requests
- Configurable rate limits
- Efficient HTML parsing
- Minimal memory footprint
- Cacheable results where appropriate

## Compliance

- Respects robots.txt (can be implemented)
- Terms of service awareness
- Privacy-focused (no personal data collection)
- Educational use compliant

## Integration Points

### With Existing System
- LangGraph agent: New tool for live search
- RAG pipeline: Can supplement with live data
- Eligibility engine: Receives extracted rules
- Frontend: New button and results section

### Data Flow
```
User Request → Web Search Service → Official Portals → Scraped Data → 
Eligibility Extraction → User Results
```

## Monitoring & Logging

- Change logs stored in `backend/logs/source_changes.jsonl`
- Error logging for failed requests
- Performance metrics tracking
- Source availability monitoring

## Conclusion

Phase 6 completes the EligibAI system by adding real-time web search capabilities, transforming it from a static dataset-based system to a live, self-updating scholarship discovery platform. The implementation is production-ready, robust, and extensible for future enhancements.