from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class ScholarshipDB(Base):
    """PostgreSQL model for structured scholarship data."""
    
    __tablename__ = "scholarships"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    scholarship_name = Column(String(500), nullable=False, index=True)
    provider = Column(String(500), nullable=True, index=True)
    
    # Eligibility - Demographics
    state = Column(String(100), nullable=True, index=True)
    district = Column(JSON, nullable=True)  # List of districts
    category = Column(JSON, nullable=True)  # List of categories: SC, ST, OBC, etc.
    gender = Column(String(50), nullable=True)
    age_limit = Column(JSON, nullable=True)  # {'min': 18, 'max': 30}
    
    # Eligibility - Education
    course = Column(JSON, nullable=True)  # List of courses
    education_level = Column(JSON, nullable=True)  # List of levels
    year_of_study = Column(JSON, nullable=True)  # List of years
    academic_requirements = Column(Text, nullable=True)
    
    # Eligibility - Financial
    income_limit = Column(JSON, nullable=True)  # {'max': 200000, 'unit': 'INR per annum'}
    
    # Eligibility - Other
    disability_required = Column(Boolean, nullable=True)
    institution_requirements = Column(Text, nullable=True)
    single_child = Column(Boolean, nullable=True)
    
    # Benefits
    benefits = Column(Text, nullable=True)
    amount = Column(String(200), nullable=True)
    
    # Application Information
    deadline = Column(String(100), nullable=True, index=True)
    application_url = Column(String(1000), nullable=True)
    application_process = Column(Text, nullable=True)
    required_documents = Column(JSON, nullable=True)  # List of documents
    
    # Source Information
    source_url = Column(String(1000), nullable=False, unique=True, index=True)
    source_domain = Column(String(500), nullable=True, index=True)
    
    # Metadata
    extraction_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    last_verified = Column(DateTime, nullable=True)
    extraction_confidence = Column(String(50), nullable=True)  # high, medium, low
    missing_fields = Column(JSON, nullable=True)  # List of missing fields
    evidence_snippets = Column(JSON, nullable=True)  # List of evidence snippets
    
    # Additional metadata
    raw_metadata = Column(JSON, nullable=True)  # Store any additional extraction metadata
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_scholarship_state_category', 'state', 'category'),
        Index('idx_scholarship_course', 'course'),
        Index('idx_scholarship_deadline', 'deadline'),
        Index('idx_scholarship_confidence', 'extraction_confidence'),
    )


class ExtractionLog(Base):
    """Log of extraction operations for tracking and debugging."""
    
    __tablename__ = "extraction_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String(1000), nullable=False, index=True)
    extraction_method = Column(String(50), nullable=False)  # 'llm', 'mock', 'manual'
    extraction_timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    success = Column(Boolean, nullable=False)
    error_message = Column(Text, nullable=True)
    extraction_metadata = Column(JSON, nullable=True)
    content_length = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)  # For LLM extractions


class ScholarshipContent(Base):
    """Store raw extracted content for reference and future re-extraction."""
    
    __tablename__ = "scholarship_content"
    
    id = Column(Integer, primary_key=True, index=True)
    scholarship_id = Column(Integer, ForeignKey('scholarships.id'), nullable=True, index=True)
    source_url = Column(String(1000), nullable=False, unique=True, index=True)
    
    # Raw content
    raw_content = Column(Text, nullable=True)
    markdown_content = Column(Text, nullable=True)
    content_type = Column(String(50), nullable=True)  # 'PDF', 'Webpage', 'Document'
    
    # Content metadata
    word_count = Column(Integer, nullable=True)
    extracted_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationship
    scholarship = relationship("ScholarshipDB", backref="content_records")
