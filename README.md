# EligibAI - AI-Powered Scholarship Discovery System

**Tagline:** Your eligibility. Your opportunities.

## 📋 Overview

EligibAI is an AI-powered scholarship discovery and eligibility assistant designed primarily for Indian college students. The system uses real-time web search (Tavily) to discover relevant scholarships from government portals and reliable sources, then uses LLM-based extraction and eligibility checking to filter results based on the student's profile.

**Current Architecture:** Real-time Web Search → Tavily Extract → LLM Extraction → Eligibility Checking → Frontend Display

**Active Components:** Tavily Search, Tavily Extract, Gemini/OpenAI LLM, Eligibility Engine, LangGraph Orchestration

---

## 🏗️ System Architecture

### Current Full Pipeline Architecture

```
USER (Browser)
    │
    ▼
Next.js Frontend (React + TypeScript + Tailwind)
    │
    ▼ POST /api/tavily/orchestrate
FastAPI Backend (Python)
    │
    ├── LangGraph Orchestration
    │   ├── Query Analysis
    │   ├── Tavily Search
    │   ├── Tavily Extract
    │   ├── LLM Extraction (Gemini/OpenAI)
    │   ├── Eligibility Checking
    │   └── Evidence Generation
    │
    └── Response Transformation
        ├── Structured scholarship data
        ├── Field-by-field eligibility comparison
        └── JSON response
    │
    ▼
Frontend Display
    ├── Source badges (Official/Reliable)
    ├── Scholarship cards with eligibility status
    ├── Field-by-field comparison
    └── Apply buttons
```

### Data Flow

1. **User Input:** Student fills profile (state, category, course, income, etc.)
2. **Query Construction:** Backend enhances query with profile context
3. **Tavily Search:** Real-time web search for scholarships
4. **Tavily Extract:** Extracts full page content from scholarship URLs
5. **LLM Extraction:** Gemini/OpenAI extracts structured scholarship data (name, eligibility criteria, benefits, deadlines)
6. **Eligibility Checking:** Engine compares user profile against scholarship requirements
7. **Evidence Generation:** Generates field-by-field comparison with MATCH/MISMATCH/NOT_SPECIFIED status
8. **Display:** Frontend shows results with eligibility status and apply links

---

## 🛠️ Technology Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.3.5 | React framework with App Router |
| **React** | 19.2.8 | UI library |
| **TypeScript** | Latest | Type safety |
| **Tailwind CSS** | v4 | Styling |
| **Lucide React** | Latest | Icons |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.9+ | Backend language |
| **FastAPI** | Latest | Web framework |
| **Uvicorn** | Latest | ASGI server |
| **Pydantic** | v2 | Data validation |
| **pydantic-settings** | Latest | Configuration management |
| **LangChain** | Latest | LLM framework |
| **LangGraph** | Latest | Orchestration framework |

### External APIs

| Service | Purpose |
|---------|---------|
| **Tavily Search** | Real-time web search for scholarships |
| **Tavily Extract** | Content extraction from URLs |
| **Google Gemini** | LLM for structured data extraction (primary) |
| **OpenAI** | LLM fallback for extraction (secondary) |

### Database

| Technology | Status | Purpose |
|------------|--------|---------|
| **PostgreSQL** | Optional | Scholarship persistence (currently disabled) |
| **SQLAlchemy** | Available | ORM (available but not actively used) |
| **Redis** | Available | Caching (available but not actively used) |

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
│   │   │   ├── llm_extraction.py     # LLM extraction service (orchestrator)
│   │   │   ├── llm_extraction_mock.py    # Mock extraction fallback
│   │   │   ├── llm_extraction_gemini.py   # Gemini extraction
│   │   │   ├── eligibility_engine_v2.py   # Eligibility engine (ACTIVE)
│   │   │   └── database.py          # Database service (inactive)
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── scholarship_agent.py     # LangGraph agent
│   │   │   └── scholarship_orchestrator.py  # LangGraph orchestrator (ACTIVE)
│   │   └── api/
│   │       ├── __init__.py
│   │       ├── routes.py              # Main routes
│   │       └── routes_tavily.py      # Tavily endpoints (ACTIVE)
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
├── EC2_DEPLOYMENT_FIXES.md           # EC2 deployment guide
│
├── .dockerignore                     # Docker ignore patterns
├── .gitignore                        # Git ignore patterns
├── DEPLOYMENT.md                     # Deployment guide
├── README.md                         # This file
└── AGENTS.md                         # Development guidelines
```

---

## 🔑 Key Components

### 1. LangGraph Orchestrator (`backend/app/agents/scholarship_orchestrator.py`)

**Purpose:** Manages the complete scholarship discovery pipeline

**Pipeline Stages:**
1. Query Analysis - Enhances query with profile context
2. Tavily Search - Finds scholarship URLs
3. Tavily Extract - Extracts full page content
4. LLM Extraction - Uses Gemini/OpenAI to extract structured data
5. Database Storage - Saves scholarships (optional, currently disabled)
6. Eligibility Checking - Compares user profile against requirements
7. Evidence Generation - Generates field-by-field comparison

**Fallback Chain:**
- Gemini (primary) → OpenAI (secondary) → Mock (last resort)

### 2. Tavily Search Service (`backend/app/services/tavily_search.py`)

**Purpose:** Real-time web search for scholarships

**Key Features:**
- Query enhancement with profile context (state, category, course)
- Domain filtering (excludes social media, dictionaries, encyclopedias)
- Official domain prioritization (scholarships.gov.in, ePASS portals, etc.)
- Result categorization (official vs reliable sources)

**Excluded Domains:**
- Social media: facebook.com, instagram.com, youtube.com, twitter.com, x.com, tiktok.com, linkedin.com
- Dictionaries: merriam-webster.com, wiktionary.org
- Encyclopedias: wikipedia.org, wikivoyage.org, britannica.com
- Other: findagrave.com, salemgastro.com, cityofsalem.net

**Official Domains:**
- scholarships.gov.in (National Scholarship Portal)
- telanganaepass.cgg.gov.in (Telangana ePASS)
- jnanabhumi.ap.gov.in (Andhra Pradesh JnanaBhumi)
- www.aicte-india.org (AICTE)
- www.ugc.ac.in (UGC)
- www.myscheme.gov.in (myScheme)
- www.education.gov.in (Ministry of Education)
- www.socialjustice.gov.in (Social Justice Ministry)

### 3. LLM Extraction Service (`backend/app/services/llm_extraction.py`)

**Purpose:** Extract structured scholarship data using LLM

**Providers:**
1. **Gemini (Primary):** Google Gemini API (gemini-3.6-flash)
2. **OpenAI (Secondary):** GPT-4o-mini if Gemini unavailable
3. **Mock (Fallback):** Regex-based extraction when LLMs unavailable

**Extracted Fields:**
- Scholarship name
- Provider
- State
- Category (SC, ST, OBC, General, etc.)
- Course (B.Tech, B.Sc, MBA, etc.)
- Income limit (min/max)
- Benefits
- Deadline
- Eligibility criteria
- Evidence snippets

### 4. Eligibility Engine v2 (`backend/app/services/eligibility_engine_v2.py`)

**Purpose:** Compare user profile against scholarship requirements

**Comparisons:**
- Education (course, level)
- Income (against limits)
- Category (SC, ST, OBC, General, etc.)
- State (state residency)
- Age (age limits)
- Gender (male/female/other)
- Disability (disability required)
- Year of study

**Status Types:**
- **MATCH:** User meets requirement
- **MISMATCH:** User does not meet requirement
- **NOT_SPECIFIED:** Requirement not specified in scholarship

**Overall Eligibility:**
- **ELIGIBLE:** All requirements match
- **POTENTIALLY_ELIGIBLE:** Some requirements not specified
- **NOT_ELIGIBLE:** One or more requirements mismatch
- **NEEDS_MORE_INFORMATION:** Insufficient information

### 5. API Endpoint (`backend/app/api/routes_tavily.py`)

**Endpoint:** `POST /api/tavily/orchestrate`

**Request Body:**
```json
{
  "query": "Telangana ST B.Tech scholarship eligibility application",
  "profile": {
    "state": "Telangana",
    "category": "ST",
    "course": "B.Tech",
    "yearOfStudy": "1st Year",
    "annualFamilyIncome": "100000",
    "disabilityStatus": "No"
  },
  "max_results": 20
}
```

**Response:**
```json
{
  "success": true,
  "query": "Telangana ST B.Tech scholarship eligibility application",
  "results": [
    {
      "scholarship_name": "Post-Matric Scholarship for SC Students",
      "provider": "National Scholarship Portal",
      "benefits": "Financial assistance for education...",
      "deadline": "Visit source for deadline",
      "source_url": "https://scholarships.gov.in/...",
      "eligibility": {
        "overall_status": "NOT_ELIGIBLE",
        "explanation": "Not eligible due to 1 mismatching requirement(s)",
        "field_comparisons": [
          {
            "field": "category",
            "status": "MISMATCH",
            "reason": "Category mismatch. Required: SC, Your category: ST"
          }
        ]
      }
    }
  ],
  "pipeline_summary": {
    "search_results": 20,
    "extraction_skipped": false,
    "using_raw_search": false
  }
}
```

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

2. QUERY ANALYSIS
   ├── Parse user query
   ├── Add profile context
   └── Generate search keywords

3. TAVILY SEARCH
   ├── API call to Tavily Search
   ├── Multiplier: max_results * 4 (for breadth)
   ├── Domain filtering (exclude social media, dictionaries)
   ├── Raw results: 20-80 results
   └── Return titles, snippets, URLs, sources

4. TAVILY EXTRACT
   ├── Extract full page content from URLs
   ├── Limit to top 5-10 results
   └── Return structured content

5. LLM EXTRACTION
   ├── Use Gemini (primary) or OpenAI (secondary)
   ├── Extract structured data:
   │   ├── Scholarship name
   │   ├── Provider
   │   ├── Eligibility criteria (category, state, income, course, etc.)
   │   ├── Benefits
   │   ├── Deadline
   │   └── Evidence snippets
   └── Fallback to mock if LLM unavailable

6. ELIGIBILITY CHECKING
   ├── Compare user profile against scholarship requirements
   ├── Field-by-field comparison
   ├── Determine overall status (ELIGIBLE/NOT_ELIGIBLE/POTENTIALLY_ELIGIBLE)
   └── Generate explanation

7. EVIDENCE GENERATION
   ├── Combine scholarship data with eligibility results
   ├── Add source badges
   └── Return structured response

8. FRONTEND DISPLAY
   ├── Source badges (Official/Reliable)
   ├── Scholarship cards with eligibility status
   ├── Field-by-field comparison
   ├── Matching/Mismatching conditions
   └── Apply buttons
```

---

## 🚀 API Endpoints

### Active Endpoints

#### `/api/tavily/orchestrate` (POST)
**Purpose:** Main orchestration endpoint with full pipeline

**Request:**
```json
{
  "query": "scholarships for SC B.Tech students in Karnataka",
  "profile": {
    "state": "Karnataka",
    "category": "SC",
    "course": "B.Tech",
    "yearOfStudy": "1st Year",
    "annualFamilyIncome": "600000"
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
    "extraction_skipped": false,
    "using_raw_search": false
  }
}
```

#### `/api/tavily/test-search` (POST)
**Purpose:** Test Tavily search directly

#### `/api/tavily/test-extraction` (POST)
**Purpose:** Test LLM extraction directly

#### `/health` (GET)
**Purpose:** Health check endpoint

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

# LLM APIs
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
google-genai>=0.1.0
openai>=1.0.0
```

### Frontend (`package.json`)

```json
{
  "dependencies": {
    "next": "16.3.5",
    "react": "^19.2.8",
    "react-dom": "^19.2.8",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.3.0",
    "lucide-react": "^0.300.0"
  }
}
```

---

## 🚀 Setup Instructions

### Prerequisites

- Node.js (v20 or higher)
- Python (v3.9 or higher)
- Tavily API key
- Gemini API key (recommended) or OpenAI API key

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

# Edit .env and add your API keys:
# TAVILY_API_KEY=your_tavily_api_key
# GEMINI_API_KEY=your_gemini_api_key

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
   - Domain filtering (excludes social media, dictionaries)

2. **LLM-Based Extraction**
   - Gemini (primary) or OpenAI (secondary) for structured data extraction
   - Extracts eligibility criteria, benefits, deadlines
   - Evidence snippets for verification
   - Mock fallback when LLMs unavailable

3. **Eligibility Checking**
   - Field-by-field comparison (category, state, income, course, etc.)
   - MATCH/MISMATCH/NOT_SPECIFIED status for each field
   - Overall eligibility status (ELIGIBLE/NOT_ELIGIBLE/POTENTIALLY_ELIGIBLE)
   - Detailed explanations

4. **LangGraph Orchestration**
   - Complete pipeline management
   - Sequential workflow
   - Error handling and fallbacks
   - State management

5. **User-Friendly UI**
   - Clean card-based design
   - Loading progress bar (0-100%)
   - Source badge display (Official/Reliable)
   - Field-by-field comparison display
   - Portal availability disclaimer
   - Direct apply buttons

6. **Profile-Based Search**
   - State-specific results
   - Category-specific results
   - Course-specific results
   - Income-based context

### Known Limitations

- **Gemini Free Tier:** 20 requests/day limit (can be upgraded)
- **Mock Extraction:** Less accurate when LLMs unavailable
- **No Database Persistence:** Scholarships not saved (PostgreSQL optional)
- **No Caching:** Repeated searches make fresh API calls
- **Single API Dependency:** Relies on Tavily Search

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
2. **Indiascholarships** - Scholarship directory

---

## 🔐 Security Considerations

### Current Security Measures

- API keys stored in environment variables
- CORS configured (all origins for development)
- Input validation with Pydantic
- Error handling without exposing sensitive data

### Production Security Recommendations

- Use environment-specific API keys
- Restrict CORS to specific origins
- Add rate limiting
- Implement authentication/authorization
- Use HTTPS with SSL certificates
- Regularly rotate API keys
- Monitor API usage and costs

---

## 🚀 Deployment

### Local Development

- Frontend: Next.js dev server on port 3000
- Backend: Uvicorn on port 8000

### Docker Deployment

- Frontend: Docker container on port 3000
- Backend: Docker container on port 8000

### AWS EC2 Deployment

See `EC2_DEPLOYMENT_FIXES.md` for detailed deployment instructions.

**Current EC2 Setup:**
- Instance: t3.micro (Amazon Linux 2023)
- Public IP: 13.62.229.119
- Frontend: Docker container (port 3000)
- Backend: Direct Python execution (port 8000)
- EBS Volume: 8GB

---

## 📝 Troubleshooting

### Common Issues

1. **Gemini 429 Error (Quota Exceeded)**
   - Free tier: 20 requests/day limit
   - Solution: Wait for quota reset or upgrade to paid plan
   - Fallback: System uses mock extraction

2. **Frontend Shows "Failed to Fetch"**
   - Check if backend is running
   - Check CORS configuration
   - Verify API URL

3. **No Results Returned**
   - Check Tavily API key
   - Check search query
   - Verify domain filtering

4. **Eligibility Not Matching**
   - Mock extraction limitations (use real LLM)
   - Check profile data accuracy
   - Verify extraction quality

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
   - Eligibility status (ELIGIBLE/NOT_ELIGIBLE/POTENTIALLY_ELIGIBLE)
   - Field-by-field comparison
   - Apply button

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License.

---

## 📞 Support

For issues or questions, please open an issue on GitHub.

---

## 🙏 Acknowledgments

- Tavily API for web search
- Google Gemini for LLM extraction
- OpenAI for LLM fallback
- Next.js team for the framework
- FastAPI team for the framework
