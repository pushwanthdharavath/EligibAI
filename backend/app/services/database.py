from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

from app.core.config import settings
from app.models.database import Base, ScholarshipDB, ExtractionLog, ScholarshipContent


class DatabaseService:
    """Service for PostgreSQL database operations."""
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.available = False
        
        try:
            self.engine = create_engine(
                settings.DATABASE_URL,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            self.available = True
        except Exception as e:
            print(f"Database not available: {e}")
            self.available = False
    
    def create_tables(self):
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            print("Database tables created successfully")
            return True
        except Exception as e:
            print(f"Error creating tables: {e}")
            return False
    
    def get_session(self) -> Session:
        """Get a database session."""
        if not self.available:
            raise Exception("Database not available")
        return self.SessionLocal()
    
    def _check_available(self) -> bool:
        """Check if database is available."""
        return self.available
    
    def save_scholarship(
        self,
        scholarship_data: Dict[str, Any],
        raw_content: Optional[str] = None,
        content_type: Optional[str] = None,
        extraction_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[int]:
        """
        Save a scholarship to the database.
        
        Args:
            scholarship_data: Structured scholarship data from extraction
            raw_content: Raw extracted content (optional)
            content_type: Type of content (PDF, Webpage, etc.)
            extraction_metadata: Extraction metadata
            
        Returns:
            Scholarship ID if successful, None otherwise
        """
        if not self._check_available():
            print("Database not available - skipping save")
            return None
            
        session = self.get_session()
        try:
            # Check if scholarship already exists by source_url
            existing = session.query(ScholarshipDB).filter(
                ScholarshipDB.source_url == scholarship_data.get("source_url")
            ).first()
            
            if existing:
                # Update existing record
                for key, value in scholarship_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                existing.updated_at = datetime.utcnow()
                existing.last_verified = datetime.utcnow()
                scholarship_id = existing.id
            else:
                # Create new record
                db_scholarship = ScholarshipDB(
                    scholarship_name=scholarship_data.get("scholarship_name"),
                    provider=scholarship_data.get("provider"),
                    state=scholarship_data.get("state"),
                    district=scholarship_data.get("district"),
                    category=scholarship_data.get("category"),
                    gender=scholarship_data.get("gender"),
                    age_limit=scholarship_data.get("age_limit"),
                    course=scholarship_data.get("course"),
                    education_level=scholarship_data.get("education_level"),
                    year_of_study=scholarship_data.get("year_of_study"),
                    academic_requirements=scholarship_data.get("academic_requirements"),
                    income_limit=scholarship_data.get("income_limit"),
                    disability_required=scholarship_data.get("disability_required"),
                    institution_requirements=scholarship_data.get("institution_requirements"),
                    single_child=scholarship_data.get("single_child"),
                    benefits=scholarship_data.get("benefits"),
                    amount=scholarship_data.get("amount"),
                    deadline=scholarship_data.get("deadline"),
                    application_url=scholarship_data.get("application_url"),
                    application_process=scholarship_data.get("application_process"),
                    required_documents=scholarship_data.get("required_documents"),
                    source_url=scholarship_data.get("source_url"),
                    source_domain=scholarship_data.get("source_domain"),
                    extraction_timestamp=scholarship_data.get("extraction_timestamp"),
                    extraction_confidence=scholarship_data.get("extraction_confidence"),
                    missing_fields=scholarship_data.get("missing_fields"),
                    evidence_snippets=scholarship_data.get("evidence_snippets"),
                    raw_metadata=extraction_metadata
                )
                session.add(db_scholarship)
                session.flush()
                scholarship_id = db_scholarship.id
            
            # Save raw content if provided
            if raw_content:
                content_record = ScholarshipContent(
                    scholarship_id=scholarship_id,
                    source_url=scholarship_data.get("source_url"),
                    raw_content=raw_content,
                    content_type=content_type,
                    word_count=len(raw_content.split()) if raw_content else 0
                )
                session.add(content_record)
            
            session.commit()
            return scholarship_id
            
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error saving scholarship: {e}")
            return None
        finally:
            session.close()
    
    def get_scholarship_by_id(self, scholarship_id: int) -> Optional[Dict[str, Any]]:
        """Get a scholarship by ID."""
        if not self._check_available():
            return None
        session = self.get_session()
        try:
            scholarship = session.query(ScholarshipDB).filter(
                ScholarshipDB.id == scholarship_id
            ).first()
            
            if scholarship:
                return self._scholarship_to_dict(scholarship)
            return None
        finally:
            session.close()
    
    def get_scholarship_by_url(self, source_url: str) -> Optional[Dict[str, Any]]:
        """Get a scholarship by source URL."""
        if not self._check_available():
            return None
        session = self.get_session()
        try:
            scholarship = session.query(ScholarshipDB).filter(
                ScholarshipDB.source_url == source_url
            ).first()
            
            if scholarship:
                return self._scholarship_to_dict(scholarship)
            return None
        finally:
            session.close()
    
    def search_scholarships(
        self,
        state: Optional[str] = None,
        category: Optional[List[str]] = None,
        course: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search scholarships with filters.
        
        Args:
            state: Filter by state
            category: Filter by category (list)
            course: Filter by course (list)
            limit: Maximum number of results
            
        Returns:
            List of scholarship dictionaries
        """
        if not self._check_available():
            return []
        session = self.get_session()
        try:
            query = session.query(ScholarshipDB)
            
            if state:
                query = query.filter(ScholarshipDB.state == state)
            
            if category:
                # Filter if scholarship has any of the specified categories
                query = query.filter(ScholarshipDB.category.op('@>')(category))
            
            if course:
                # Filter if scholarship has any of the specified courses
                query = query.filter(ScholarshipDB.course.op('@>')(course))
            
            scholarships = query.order_by(ScholarshipDB.created_at.desc()).limit(limit).all()
            
            return [self._scholarship_to_dict(s) for s in scholarships]
        finally:
            session.close()
    
    def get_all_scholarships(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all scholarships with optional limit."""
        if not self._check_available():
            return []
        session = self.get_session()
        try:
            scholarships = session.query(ScholarshipDB).order_by(
                ScholarshipDB.created_at.desc()
            ).limit(limit).all()
            
            return [self._scholarship_to_dict(s) for s in scholarships]
        finally:
            session.close()
    
    def log_extraction(
        self,
        source_url: str,
        extraction_method: str,
        success: bool,
        error_message: Optional[str] = None,
        extraction_metadata: Optional[Dict[str, Any]] = None,
        content_length: Optional[int] = None,
        tokens_used: Optional[int] = None
    ):
        """Log an extraction operation."""
        if not self._check_available():
            return
        session = self.get_session()
        try:
            log = ExtractionLog(
                source_url=source_url,
                extraction_method=extraction_method,
                extraction_timestamp=datetime.utcnow(),
                success=success,
                error_message=error_message,
                extraction_metadata=extraction_metadata,
                content_length=content_length,
                tokens_used=tokens_used
            )
            session.add(log)
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            print(f"Error logging extraction: {e}")
        finally:
            session.close()
    
    def get_raw_content(self, source_url: str) -> Optional[str]:
        """Get raw content for a scholarship URL."""
        if not self._check_available():
            return None
        session = self.get_session()
        try:
            content = session.query(ScholarshipContent).filter(
                ScholarshipContent.source_url == source_url
            ).first()
            
            if content:
                return content.raw_content
            return None
        finally:
            session.close()
    
    def _scholarship_to_dict(self, scholarship: ScholarshipDB) -> Dict[str, Any]:
        """Convert SQLAlchemy model to dictionary."""
        return {
            "id": scholarship.id,
            "scholarship_name": scholarship.scholarship_name,
            "provider": scholarship.provider,
            "state": scholarship.state,
            "district": scholarship.district,
            "category": scholarship.category,
            "gender": scholarship.gender,
            "age_limit": scholarship.age_limit,
            "course": scholarship.course,
            "education_level": scholarship.education_level,
            "year_of_study": scholarship.year_of_study,
            "academic_requirements": scholarship.academic_requirements,
            "income_limit": scholarship.income_limit,
            "disability_required": scholarship.disability_required,
            "institution_requirements": scholarship.institution_requirements,
            "single_child": scholarship.single_child,
            "benefits": scholarship.benefits,
            "amount": scholarship.amount,
            "deadline": scholarship.deadline,
            "application_url": scholarship.application_url,
            "application_process": scholarship.application_process,
            "required_documents": scholarship.required_documents,
            "source_url": scholarship.source_url,
            "source_domain": scholarship.source_domain,
            "extraction_timestamp": scholarship.extraction_timestamp.isoformat() if scholarship.extraction_timestamp else None,
            "last_verified": scholarship.last_verified.isoformat() if scholarship.last_verified else None,
            "extraction_confidence": scholarship.extraction_confidence,
            "missing_fields": scholarship.missing_fields,
            "evidence_snippets": scholarship.evidence_snippets,
            "created_at": scholarship.created_at.isoformat() if scholarship.created_at else None,
            "updated_at": scholarship.updated_at.isoformat() if scholarship.updated_at else None
        }
    
    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            session = self.get_session()
            session.execute(text("SELECT 1"))
            session.close()
            return True
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False


# Global database service instance
db_service = DatabaseService()
