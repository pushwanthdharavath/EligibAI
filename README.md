# EligibAI - AI-Powered Scholarship Discovery System

**Tagline:** Your eligibility. Your opportunities.

## 📋 Overview

EligibAI is an AI-powered scholarship discovery and eligibility assistant designed primarily for Indian college students. The system uses real-time web search (Tavily) to discover relevant scholarships from government portals and reliable sources, then presents results with clear eligibility information and direct application links.

**Current Architecture:** Real-time Web Search → Backend Processing → Frontend Display

**Removed Components:** RAG/Qdrant, QLoRA fine-tuning, LangGraph orchestration (simplified to direct API endpoints)

---

## 🏗️ System Architecture

### Current Simplified Architecture

```
USER (Browser)
    │
    ▼
Next.js Frontend (React + TypeScript + Tailwind)
    │
    ▼ POST /api/tavily/orchestrate
FastAPI Backend (Python)
    │
    ├── Tavily Search Service
    │   ├── Query Enhancement (adds state, category, course context)
    │   ├── Domain Filtering (official vs reliable sources)
    │   └── Result Categorization
    │
    ├── Quality Filters
    │   ├── Navigation menu removal
    │   ├── Markdown/table syntax removal
    │   ├── Old date filtering (pre-2026)
    │   ├── Low-quality domain blocking
    │   └── Garbage pattern detection
    │
    └── Response Transformation
        ├── Raw Tavily results
        ├── Metadata enrichment
        └── JSON response
    │
    ▼
Frontend Display
    ├── Source badges (Official/Reliable)
    ├── Scholarship cards
    ├── Portal disclaimer
    └── Apply buttons
```

### Data Flow

1. **User Input:** Student fills profile (state, category, course, income, etc.)
2. **Query Construction:** Backend enhances query with profile context
3. **Tavily Search:** Real-time web search for scholarships
4. **Quality Filtering:** Removes garbage, navigation, old content
5. **Response:** Clean, current scholarship results
6. **Display:** Frontend shows results with source badges and apply links

---

## 🛠️ Technology Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.3.5 | React framework with App Router |
| **React** | Latest | UI library |
| **TypeScript** | Latest | Type safety |
| **Tailwind CSS** | Latest | Styling |
| **Lucide React** | Latest | Icons |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.9+ | Backend language |
| **FastAPI** | Latest | Web framework |
| **Uvicorn** | Latest | ASGI server |
| **Pydantic** | v2 | Data validation |
| **pydantic-settings** | Latest | Configuration management |

### External APIs

| Service | Purpose |
|---------|---------|
| **Tavily Search** | Real-time web search for scholarships |
| **Tavily Extract** | Content extraction from URLs (currently unused) |

### Database

| Technology | Status | Purpose |
|------------|--------|---------|
| **PostgreSQL** | Optional | Scholarship persistence (currently disabled) |
| **SQLAlchemy** | Available | ORM (available but not actively used) |

### Development Tools

| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Local development orchestration |
| **Git** | Version control |

---

## 📁 Project Structure

```
eligiblAI/
├── frontend/                          # Next.js frontend application
│   ├── src/
│   │   ├── app/                      # Next.js app router
│   │   │   ├── layout.tsx            # Root layout
│   │   │   ├── page.tsx              # Home page
│   │   │   └── globals.css           # Global styles
│   │   └── components/
│   │       └── UserProfileForm.tsx   # Main form component
│   ├── public/                       # Static assets
│   ├── .eslintrc.json                # ESLint config
│   ├── .prettierrc                   # Prettier config
│   ├── tailwind.config.ts            # Tailwind config
│   ├── tsconfig.json                 # TypeScript config
│   ├── next.config.js                # Next.js config
│   ├── package.json                  # Dependencies
│   └── Dockerfile                    # Frontend Dockerfile
│
├── backend/                          # FastAPI backend application
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app entry point
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   └── config.py             # Configuration (API keys, settings)
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── scholarship.py        # Scholarship data models
│   │   │   ├── eligibility.py        # Eligibility models
│   │   │   ├── database.py           # Database models
│   │   │   └── scholarship_extraction.py  # Extraction models
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── tavily_search.py      # Tavily search service
│   │   │   ├── tavily_extract.py     # Tavily extract service
│   │   │   ├── llm_extraction.py     # LLM extraction (mock mode)
│   │   │   ├── llm_extraction_mock.py    # Mock extraction fallback
│   │   │   ├── llm_extraction_gemini.py   # Gemini extraction (inactive)
│   │   │   ├── eligibility_engine_v2.py   # Eligibility engine (inactive)
│   │   │   └── database.py          # Database service (inactive)
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── scholarship_agent.py     # LangGraph agent (inactive)
│   │   │   └── scholarship_orchestrator.py  # Orchestrator (inactive)
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── routes.py              # Main routes
│   │       ├── routes_tavily.py      # Tavily endpoints (ACTIVE)
│   │       ├── routes_finetuning.py  # Fine-tuning endpoints (inactive)
│   │       ├── routes_evaluation.py   # Evaluation endpoints (inactive)
│   │       └── routes_websearch.py    # Web search endpoints (inactive)
│   ├── data/
│   │   └── scholarships.json          # Static scholarship data (unused)
│   ├── main.py                       # Uvicorn entry point
│   ├── requirements.txt               # Python dependencies
│   ├── .env                          # Environment variables
│   ├── .env.example                  # Environment template
│   └── Dockerfile                    # Backend Dockerfile
│
├── aws/terraform/                    # AWS infrastructure (planned)
│   ├── main.tf                       # Terraform config
│   ├── variables.tf                  # Variables
│   ├── outputs.tf                    # Outputs
│   ├── backend-task-definition.json  # ECS task def
│   ├── frontend-task-definition.json # ECS task def
│   └── deploy.sh                     # Deployment script
│
├── nginx/                            # Nginx configuration (planned)
│   └── nginx.conf                    # Reverse proxy config
│
├── docker-compose.yml                # Development Docker Compose
├── docker-compose.prod.yml           # Production Docker Compose
│
├── .dockerignore                     # Docker ignore patterns
├── .gitignore                        # Git ignore patterns
├── DEPLOYMENT.md                     # Deployment guide
├── README.md                         # This file
└── AGENTS.md                         # Development guidelines
```

---

## 🔑 Key Components

### 1. Tavily Search Service (`backend/app/services/tavily_search.py`)

**Purpose:** Real-time web search for scholarships

**Key Features:**
- Query enhancement with profile context (state, category, course)
- Official domain filtering (scholarships.gov.in, ePASS portals, etc.)
- Result categorization (official vs reliable sources)
- Configurable result limits

**Official Domains:**
- scholarships.gov.in (National Scholarship Portal)
- telanganaepass.cgg.gov.in (Telangana ePASS)
- jnanabhumi.ap.gov.in (Andhra Pradesh JnanaBhumi)
- www.aicte-india.org (AICTE)
- www.ugc.ac.in (UGC)
- www.myscheme.gov.in (myScheme)
- www.education.gov.in (Ministry of Education)
- www.socialjustice.gov.in (Social Justice Ministry)

**API Endpoint:**
```python
def search_scholarships(query: str, profile: dict, max_results: int)
```

### 2. Quality Filters (`backend/app/api/routes_tavily.py`)

**Purpose:** Remove low-quality and irrelevant results

**Filter Categories:**

1. **Navigation Menu Removal:**
   - "Menu", "About Us", "Contact Us", "Site Map"
   - "Dashboard Login", "RTI Manual", "Privacy Policy"
   - "Copyright", "All rights reserved"

2. **Markdown/Table Syntax Removal:**
   - `##`, `###`, `#`, `|`, `---`
   - "Also Check", "FAQs", "Ques", "Ans"
   - "[PDF]" labels

3. **Image/Garbage Removal:**
   - "Image 1:", "Image 2:", etc.
   - "OTR registration", "One Time Registration"
   - URL paths: "/en/", "/fresh/", "/public/"

4. **Date Filtering:**
   - Blocks 2020, 2021, 2022, 2023, 2024, 2025
   - Only shows 2026 results

5. **Low-Quality Domain Blocking:**
   - rssing.com, noticebard.com, theglobalscholarship.org
   - quora.com, shiksha.com, collegedunia.com
   - manabadi.co.in, saitm.ac.in

6. **Scholarship Content Validation:**
   - Must contain scholarship-related keywords
   - Minimum length requirements
   - No obvious garbage patterns

### 3. Simplified Orchestration Endpoint (`backend/app/api/routes_tavily.py`)

**Endpoint:** `POST /api/tavily/orchestrate`

**Request Body:**
```json
{
  "query": "find all the scholarships im eligible for",
  "profile": {
    "state": "Karnataka",
    "category": "SC",
    "course": "B.Tech",
    "year": "1st Year",
    "annualIncome": 6000000
  },
  "max_results": 20
}
```

**Response:**
```json
{
  "success": true,
  "query": "find all the scholarships im eligible for",
  "results": [
    {
      "scholarship_name": "Post-Matric Scholarship",
      "provider": "National Scholarship Portal",
      "benefits": "Financial assistance for education...",
      "deadline": "Visit source for deadline",
      "source_url": "https://scholarships.gov.in/...",
      "is_official": true,
      "eligibility": {
        "overall_status": "NEEDS_MORE_INFORMATION",
        "explanation": "Visit source for eligibility details"
      }
    }
  ],
  "pipeline_summary": {
    "search_results": 20,
    "extraction_skipped": true,
    "using_raw_search": true
  }
}
```

### 4. Frontend Profile Form (`frontend/src/components/UserProfileForm.tsx`)

**Features:**
- Student profile input (personal, education, financial)
- Real-time search with loading progress bar (0-100%)
- Quality filtering on frontend
- Source badge display (Official/Reliable)
- Portal availability disclaimer
- Clean card-based UI

**Key Components:**
- Form state management with React hooks
- Loading animation with progress bar
- API integration with FastAPI backend
- Responsive design with Tailwind CSS
- Garbage pattern filtering (frontend layer)

---

## 🔄 Data Pipeline

### Complete Pipeline Flow

```
1. USER INPUT
   ├── State: Karnataka/Telangana/Andhra Pradesh/etc.
   ├── Category: SC/ST/OBC/General/EWS
   ├── Course: B.Tech/B.Sc/B.Com/MBA/etc.
   ├── Year: 1st/2nd/3rd/4th/5th Year
   ├── Income: Annual family income
   └── Disability: Yes/No

2. QUERY ENHANCEMENT
   ├── Append state to query
   ├── Append category to query
   ├── Append course to query
   └── Append year to query
   Example: "Karnataka state SC category B.Tech course 1st Year"

3. TAVILY SEARCH
   ├── API call to Tavily Search
   ├── Multiplier: max_results * 4 (for breadth)
   ├── Raw results: 40-80 results
   └── Return titles, snippets, URLs, sources

4. QUALITY FILTERING (Backend)
   ├── Remove navigation menu text
   ├── Remove markdown/table syntax
   ├── Remove image references
   ├── Remove old dates (pre-2026)
   ├── Block low-quality domains
   ├── Validate scholarship content
   └── Final results: 5-20 scholarships

5. RESPONSE TRANSFORMATION
   ├── Add metadata (official/reliable)
   ├── Structure JSON response
   └── Return to frontend

6. FRONTEND FILTERING
   ├── Additional garbage pattern checks
   ├── Length validation
   └── Display preparation

7. UI DISPLAY
   ├── Source badges
   ├── Scholarship cards
   ├── Portal disclaimer
   └── Apply buttons
```

---

## 🚀 API Endpoints

### Active Endpoints

#### `/api/tavily/orchestrate` (POST)
**Purpose:** Main search endpoint

**Request:**
```json
{
  "query": "scholarships for SC B.Tech students in Karnataka",
  "profile": {
    "state": "Karnataka",
    "category": "SC",
    "course": "B.Tech",
    "year": "1st Year",
    "annualIncome": 6000000
  },
  "max_results": 20
}
```

**Response:**
```json
{
  "success": true,
  "query": "scholarships for SC B.Tech students in Karnataka",
  "results": [...],
  "pipeline_summary": {
    "search_results": 20,
    "extraction_skipped": true,
    "using_raw_search": true
  }
}
```

#### `/api/tavily/test-search` (POST)
**Purpose:** Test Tavily search directly

#### `/api/tavily/test-extraction` (POST)
**Purpose:** Test extraction (currently inactive)

### Inactive Endpoints (Architecture Simplified)

The following endpoints exist in codebase but are not actively used:

- `/api/eligibility` - Eligibility checking (static dataset, inactive)
- `/api/search` - RAG search (RAG removed, inactive)
- `/api/agent` - LangGraph agent (simplified, inactive)
- `/api/finetuning/*` - QLoRA fine-tuning (removed, inactive)
- `/api/evaluation/*` - RAGAS evaluation (removed, inactive)
- `/api/websearch/*` - Web search endpoints (consolidated into Tavily, inactive)

---

## 🔧 Configuration

### Environment Variables (`.env`)

```bash
# Tavily API
TAVILY_API_KEY=your_tavily_api_key_here

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Database (Optional - currently disabled)
DATABASE_URL=postgresql://user:password@localhost:5432/eligibai

# LLM APIs (Optional - currently using mock mode)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Frontend
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend Configuration (`backend/app/core/config.py`)

```python
class Settings(BaseSettings):
    tavily_api_key: str
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    database_url: Optional[str] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
```

---

## 📦 Dependencies

### Backend (`requirements.txt`)

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-multipart>=0.0.6
tavily-python>=0.3.0
sqlalchemy>=2.0.0
psycopg2-binary>=2.9.0
langchain>=0.1.0
langgraph>=0.0.0
```

### Frontend (`package.json`)

```json
{
  "dependencies": {
    "next": "16.3.5",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.3.0",
    "lucide-react": "^0.300.0"
  }
}
```

---

## 🚀 Setup Instructions

### Prerequisites

- Node.js (v18 or higher)
- Python (v3.9 or higher)
- Tavily API key

### Local Development Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env and add your TAVILY_API_KEY

# Run backend
python main.py
```

Backend will run on: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

Frontend will run on: `http://localhost:3000`

### Docker Setup

```bash
# Start all services
docker-compose up -d

# Access applications
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

---

## 🎯 Key Features

### Current Features

1. **Real-Time Web Search**
   - Tavily API for live scholarship discovery
   - Query enhancement with profile context
   - Multi-source search (government portals + reliable aggregators)

2. **Quality Filtering**
   - Navigation menu removal
   - Markdown/table syntax removal
   - Old date filtering (pre-2026)
   - Low-quality domain blocking
   - Garbage pattern detection

3. **Source Classification**
   - Official government portals (green badge)
   - Reliable aggregators (blue badge)
   - Clear visual distinction

4. **User-Friendly UI**
   - Clean card-based design
   - Loading progress bar (0-100%)
   - Portal availability disclaimer
   - Direct apply buttons

5. **Profile-Based Search**
   - State-specific results
   - Category-specific results
   - Course-specific results
   - Income-based context

### Removed Features (Architecture Simplified)

- ❌ RAG with Qdrant vector database
- ❌ QLoRA fine-tuning
- ❌ LangGraph orchestration
- ❌ Eligibility rule engine (static dataset)
- ❌ LLM extraction (currently using mock mode)
- ❌ Database persistence (PostgreSQL disabled)
- ❌ Change detection and monitoring
- ❌ Evaluation framework (RAGAS)

---

## 📊 Official Sources

### Government Portals (Official Sources)

1. **National Scholarship Portal (NSP)**
   - URL: scholarships.gov.in
   - Central government scholarships
   - SC/ST/OBC/Minority scholarships

2. **Telangana ePASS**
   - URL: telanganaepass.cgg.gov.in
   - Telangana state scholarships
   - Fee reimbursement

3. **Andhra Pradesh JnanaBhumi**
   - URL: jnanabhumi.ap.gov.in
   - AP state scholarships
   - RTF/MTF schemes

4. **AICTE**
   - URL: www.aicte-india.org
   - Technical education scholarships
   - Pragati, Saksham, etc.

5. **UGC**
   - URL: www.ugc.ac.in
   - Higher education scholarships
   - Research fellowships

6. **myScheme**
   - URL: www.myscheme.gov.in
   - Government scheme portal
   - All government schemes

7. **Ministry of Education**
   - URL: www.education.gov.in
   - Central ministry scholarships

8. **Ministry of Social Justice**
   - URL: www.socialjustice.gov.in
   - SC/ST/OBC scholarships

### Reliable Aggregators (Non-Official)

1. **Buddy4Study** - Scholarship information platform
2. **Propelld** - Education financing platform
3. **Indiascholarships** - Scholarship directory

---

## 🔍 Quality Filter Details

### Backend Filters (Python)

**File:** `backend/app/api/routes_tavily.py`

**Navigation Keywords:**
```python
navigation_keywords = [
    "Menu", "About Us", "Contact Us", "Site Map", "RTI Manual",
    "Dashboard Login", "Login", "logo", "A+;)", "A;)", "A-;)",
    "Schemes & Policies", "Awards", "Link", "Footer", "Privacy Policy",
    "Terms of Service", "Copyright", "All rights reserved",
    "Rising-2047", "tg rising", "ts logo", "Official Login",
    "Dashboard", "RSSing", "chan-", "all_p2",
    "Image 1:", "Image 2:", "Image 3:", "Image 4:", "Image 5:",
    "Image", "OTR registration", "One Time Registration",
    "/en/", "/fresh/", "/public/", "/scheme", "0-", "-0",
    "##", "###", "#", "|", "---", "Also Check", "FAQs", "Ques", "Ans",
    "[PDF]", "Scheme Guidelines of Scheme", "General Overview",
    "Salary for Freshers", "Steps to Apply", "Top"
]
```

**Low-Quality Domains:**
```python
low_quality_domains = [
    "rssing.com", "noticebard.com", "theglobalscholarship.org", "quora.com",
    "shiksha.com", "collegedunia.com", "manabadi.co.in", "saitm.ac.in"
]
```

**Old Years:**
```python
old_years = ["2020", "2021", "2022", "2023", "2024", "2025"]
```

**Scholarship Keywords:**
```python
scholarship_keywords = [
    "scholarship", "grant", "fellowship", "financial aid",
    "reimbursement", "fee", "eligible", "eligibility",
    "income", "students", "education"
]
```

### Frontend Filters (TypeScript)

**File:** `frontend/src/components/UserProfileForm.tsx`

**Garbage Patterns:**
```typescript
const garbagePatterns = [
  "image 1:", "image 2:", "image 3:", "image 4:", "image 5:",
  "otr registration", "one time registration",
  "/en/", "/fresh/", "/public/", "/scheme",
  "0-", "-0", "may 17, 2022", "2022", "2023", "2024", "2025"
];
```

---

## 🎨 UI Components

### UserProfileForm Component

**Key Sections:**

1. **Header**
   - Logo and title
   - Clean design

2. **Profile Form**
   - Personal Information (name, age, gender)
   - State selection
   - Category selection
   - Education (course, year)
   - Financial (income, disability)
   - Search query input

3. **Search Button**
   - Loading progress bar (0-100%)
   - Animated transition
   - Disabled during search

4. **Results Section**
   - Stats (Scholarships Found, Data Freshness)
   - Informational note
   - Portal disclaimer (orange warning)
   - Scholarship cards

5. **Scholarship Card**
   - Source badge (Official/Reliable)
   - Scholarship title
   - Description/benefits
   - Apply button

---

## 📝 Interview Preparation Topics

### Architecture & Design

1. **Why simplify from RAG to Tavily-only?**
   - RAG complexity vs reliability
   - Real-time data freshness
   - Maintenance overhead
   - User experience focus

2. **Why multiple filtering layers?**
   - Defense in depth
   - Backend filters (Python) for server-side quality
   - Frontend filters (TypeScript) for user experience
   - Network bandwidth optimization

3. **Why remove LangGraph orchestration?**
   - Complexity vs value
   - Direct API endpoints simpler
   - Easier debugging
   - Faster response times

### Technical Implementation

1. **Tavily Search Integration**
   - API authentication
   - Query enhancement strategies
   - Rate limiting considerations
   - Error handling

2. **Quality Filtering Strategies**
   - Pattern matching
   - Domain blacklisting
   - Date validation
   - Content validation

3. **Frontend State Management**
   - React hooks (useState, useEffect)
   - Form handling
   - Loading states
   - Error handling

### Scalability Considerations

1. **Current Limitations**
   - No database persistence
   - No caching
   - Single API dependency (Tavily)
   - No load balancing

2. **Future Improvements**
   - Redis caching for queries
   - PostgreSQL for history
   - Rate limiting
   - Load balancing with Nginx
   - CDN for static assets

### API Design

1. **RESTful Principles**
   - POST for search (query in body)
   - JSON request/response
   - Clear error messages
   - Structured responses

2. **Error Handling**
   - Try-catch blocks
   - Graceful degradation
   - User-friendly error messages
   - Logging for debugging

---

## 🔐 Security Considerations

### Current Security Measures

1. **API Key Management**
   - Environment variables
   - .env files not committed
   - .env.example provided

2. **CORS Configuration**
   - Frontend-backend communication
   - Allowed origins configured

3. **Input Validation**
   - Pydantic models for backend
   - TypeScript types for frontend
   - Length limits on inputs

### Future Security Improvements

1. **API Rate Limiting**
   - Prevent abuse
   - Protect Tavily quota

2. **Authentication**
   - User accounts
   - JWT tokens
   - Protected routes

3. **HTTPS**
   - SSL certificates
   - Secure communication

---

## 📈 Performance Optimization

### Current Optimizations

1. **Frontend**
   - React fast refresh
   - Tailwind CSS (JIT)
   - Lazy loading components

2. **Backend**
   - Async/await for I/O
   - Connection pooling (if DB used)
   - Efficient filtering

### Future Optimizations

1. **Caching**
   - Redis for common queries
   - Browser caching
   - CDN for static assets

2. **Database**
   - Query optimization
   - Indexing
   - Connection pooling

3. **API**
   - Response compression
   - Pagination
   - Batch requests

---

## 🧪 Testing

### Manual Testing Checklist

1. **Frontend**
   - Form submission
   - Loading animation
   - Results display
   - Responsive design

2. **Backend**
   - API endpoint response
   - Quality filtering
   - Error handling
   - Logging

3. **Integration**
   - Frontend-backend communication
   - Tavily API integration
   - End-to-end flow

### Future Testing

1. **Unit Tests**
   - Jest for frontend
   - Pytest for backend

2. **Integration Tests**
   - API testing
   - End-to-end testing

3. **E2E Tests**
   - Playwright or Cypress
   - User flow testing

---

## 🚢 Deployment

### Current Deployment

- Local development with Docker Compose
- Manual backend and frontend startup

### Production Deployment (Planned)

1. **AWS Infrastructure**
   - ECS for container orchestration
   - RDS for PostgreSQL (if needed)
   - ALB for load balancing
   - Route 53 for DNS

2. **CI/CD Pipeline**
   - GitHub Actions
   - Automated testing
   - Automated deployment

3. **Monitoring**
   - CloudWatch for logs
   - Application performance monitoring
   - Error tracking

---

## 📚 Learning Resources

### Technologies Used

1. **Next.js**
   - Documentation: nextjs.org/docs
   - App Router: nextjs.org/docs/app

2. **FastAPI**
   - Documentation: fastapi.tiangolo.com
   - Tutorial: fastapi.tiangolo.com/tutorial

3. **Tavily**
   - Documentation: docs.tavily.com
   - API Reference: docs.tavily.com/docs/api

4. **Tailwind CSS**
   - Documentation: tailwindcss.com/docs
   - Cheatsheet: tailwindcss.com/docs/installation

---

## 🤝 Contributing

### Development Guidelines

1. **Code Style**
   - Prettier for frontend
   - Black for backend
   - Type hints for Python
   - TypeScript for frontend

2. **Commit Messages**
   - Conventional commits
   - Clear descriptions
   - Reference issues

3. **Code Review**
   - Peer review required
   - Automated tests pass
   - Documentation updated

---

## 📄 License

MIT License

---

## 📞 Contact

For questions or support, please refer to the project repository.

---

## 🎓 Interview Questions & Answers

### Q1: Why did you choose Tavily over building a custom web scraper?

**Answer:** Tavily provides:
- Reliable web search API
- Built-in content extraction
- Rate limiting and error handling
- Reduced development time
- Better result quality than custom scrapers
- API-based approach is more maintainable

### Q2: How do you handle government portal downtime?

**Answer:** 
- Added disclaimer in UI about portal availability
- Multiple sources (not single point of failure)
- Error handling with user-friendly messages
- Suggest users try again later or visit directly

### Q3: Why remove RAG and Qdrant?

**Answer:**
- Complexity vs value: RAG added complexity without clear benefit
- Real-time search: Tavily provides current data without RAG
- Maintenance: Simplified architecture easier to maintain
- User experience: Faster response times, simpler pipeline

### Q4: How do you ensure result quality?

**Answer:**
- Multi-layer filtering (backend + frontend)
- Navigation menu removal
- Markdown/table syntax removal
- Old date filtering
- Low-quality domain blocking
- Scholarship content validation

### Q5: What are the scalability challenges?

**Answer:**
- Single API dependency (Tavily)
- No caching layer
- No database persistence
- No load balancing
- Solutions: Redis caching, PostgreSQL, Nginx load balancer

### Q6: How do you handle API rate limits?

**Answer:**
- Currently not implemented (Tavily has generous limits)
- Future: Redis-based rate limiting
- User accounts with quotas
- Queue system for heavy loads

### Q7: Why TypeScript for frontend?

**Answer:**
- Type safety
- Better IDE support
- Catch errors at compile time
- Self-documenting code
- Better refactoring

### Q8: Why Pydantic v2 for backend?

**Answer:**
- Data validation
- Automatic schema generation
- Fast performance
- Type hints
- API documentation (FastAPI integration)

### Q9: How do you handle state management in frontend?

**Answer:**
- React hooks (useState, useEffect)
- Local component state
- No global state (not needed for current scope)
- Future: Redux/Zustand if complexity grows

### Q10: What are the security considerations?

**Answer:**
- API keys in environment variables
- CORS configuration
- Input validation (Pydantic, TypeScript)
- Future: Authentication, rate limiting, HTTPS

---

## 🎯 Key Takeaways for Interviews

1. **Architecture Decision Making**
   - Simplified architecture for maintainability
   - Real-time data over cached data
   - User experience over complex features

2. **Technical Implementation**
   - Quality filtering strategies
   - API integration best practices
   - Error handling patterns

3. **Problem Solving**
   - Garbage content removal
   - Date validation
   - Domain blocking

4. **Future Improvements**
   - Caching layer
   - Database persistence
   - Load balancing
   - Authentication

5. **Trade-offs**
   - RAG removed for simplicity
   - Mock extraction for reliability
   - Multiple filtering layers for quality

---

**Last Updated:** 2026
**Version:** 2.0 (Simplified Architecture)
**Status:** Production Ready (Local Development)
