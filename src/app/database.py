"""
Database Module

SQLAlchemy-based database for storing deepfake detection job metadata and results.
Uses SQLite for simplicity and portability.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create base class for models
Base = declarative_base()


class AnalysisJob(Base):
    """
    Database model for deepfake detection analysis jobs.
    
    Tracks job lifecycle from upload through processing to completion.
    """
    __tablename__ = 'analysis_jobs'
    
    # Primary key
    job_id = Column(String(36), primary_key=True)  # UUID format
    
    # File metadata
    filename = Column(String(255), nullable=False)
    file_size_mb = Column(Float, nullable=False)
    
    # Timestamps
    upload_timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    completion_timestamp = Column(DateTime, nullable=True)
    
    # Status tracking
    status = Column(String(20), nullable=False, default='queued')
    # Possible values: 'queued', 'processing', 'completed', 'failed'
    
    # Analysis results (null until completed)
    verdict = Column(String(10), nullable=True)  # 'Real' or 'Fake'
    confidence = Column(Float, nullable=True)  # 0-100
    probability = Column(Float, nullable=True)  # 0-1
    
    # Performance metrics
    processing_time_seconds = Column(Float, nullable=True)
    
    # Error handling
    error_message = Column(String(500), nullable=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model instance to dictionary for JSON serialization.
        
        Returns:
            Dictionary representation of the job
        """
        return {
            'job_id': self.job_id,
            'filename': self.filename,
            'file_size_mb': round(self.file_size_mb, 2),
            'upload_timestamp': self.upload_timestamp.isoformat() if self.upload_timestamp else None,
            'completion_timestamp': self.completion_timestamp.isoformat() if self.completion_timestamp else None,
            'status': self.status,
            'verdict': self.verdict,
            'confidence': round(self.confidence, 2) if self.confidence else None,
            'probability': round(self.probability, 4) if self.probability else None,
            'processing_time_seconds': round(self.processing_time_seconds, 2) if self.processing_time_seconds else None,
            'error_message': self.error_message
        }


class DatabaseManager:
    """
    Manages database connections and operations for TrueSight backend.
    """
    
    def __init__(self, db_path: str = "results/truesight.db"):
        """
        Initialize database manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        
        # Create results directory if it doesn't exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create database engine
        db_url = f"sqlite:///{self.db_path}"
        self.engine = create_engine(db_url, echo=False)
        
        # Create tables if they don't exist
        Base.metadata.create_all(self.engine)
        
        # Create session factory
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        logger.info(f"Database initialized at: {self.db_path}")
    
    def get_session(self) -> Session:
        """
        Create a new database session.
        
        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()
    
    def create_job(
        self,
        job_id: str,
        filename: str,
        file_size_mb: float
    ) -> AnalysisJob:
        """
        Create a new analysis job with 'queued' status.
        
        Args:
            job_id: Unique job identifier (UUID)
            filename: Original video filename
            file_size_mb: File size in megabytes
        
        Returns:
            Created AnalysisJob instance
        """
        session = self.get_session()
        
        try:
            job = AnalysisJob(
                job_id=job_id,
                filename=filename,
                file_size_mb=file_size_mb,
                status='queued',
                upload_timestamp=datetime.utcnow()
            )
            
            session.add(job)
            session.commit()
            session.refresh(job)
            
            logger.info(f"Created job {job_id}: {filename} ({file_size_mb:.2f} MB)")
            return job
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating job: {e}")
            raise
        finally:
            session.close()
    
    def get_job(self, job_id: str) -> Optional[AnalysisJob]:
        """
        Retrieve a job by ID.
        
        Args:
            job_id: Job identifier
        
        Returns:
            AnalysisJob instance or None if not found
        """
        session = self.get_session()
        
        try:
            job = session.query(AnalysisJob).filter_by(job_id=job_id).first()
            return job
        finally:
            session.close()
    
    def update_status(self, job_id: str, status: str) -> bool:
        """
        Update job status.
        
        Args:
            job_id: Job identifier
            status: New status ('queued', 'processing', 'completed', 'failed')
        
        Returns:
            True if updated successfully, False otherwise
        """
        session = self.get_session()
        
        try:
            job = session.query(AnalysisJob).filter_by(job_id=job_id).first()
            
            if job:
                job.status = status
                session.commit()
                logger.info(f"Job {job_id} status updated to: {status}")
                return True
            else:
                logger.warning(f"Job {job_id} not found")
                return False
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating status: {e}")
            return False
        finally:
            session.close()
    
    def save_results(
        self,
        job_id: str,
        verdict: str,
        confidence: float,
        probability: float,
        processing_time_seconds: float
    ) -> bool:
        """
        Save analysis results and mark job as completed.
        
        Args:
            job_id: Job identifier
            verdict: 'Real' or 'Fake'
            confidence: Confidence percentage (0-100)
            probability: Raw probability (0-1)
            processing_time_seconds: Time taken for processing
        
        Returns:
            True if saved successfully, False otherwise
        """
        session = self.get_session()
        
        try:
            job = session.query(AnalysisJob).filter_by(job_id=job_id).first()
            
            if job:
                job.verdict = verdict
                job.confidence = confidence
                job.probability = probability
                job.processing_time_seconds = processing_time_seconds
                job.status = 'completed'
                job.completion_timestamp = datetime.utcnow()
                
                session.commit()
                logger.info(
                    f"Job {job_id} completed: {verdict} "
                    f"(confidence: {confidence:.2f}%, time: {processing_time_seconds:.2f}s)"
                )
                return True
            else:
                logger.warning(f"Job {job_id} not found")
                return False
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving results: {e}")
            return False
        finally:
            session.close()
    
    def set_error(self, job_id: str, error_message: str) -> bool:
        """
        Mark job as failed and save error message.
        
        Args:
            job_id: Job identifier
            error_message: Error description
        
        Returns:
            True if updated successfully, False otherwise
        """
        session = self.get_session()
        
        try:
            job = session.query(AnalysisJob).filter_by(job_id=job_id).first()
            
            if job:
                job.status = 'failed'
                job.error_message = error_message
                job.completion_timestamp = datetime.utcnow()
                
                session.commit()
                logger.error(f"Job {job_id} failed: {error_message}")
                return True
            else:
                logger.warning(f"Job {job_id} not found")
                return False
                
        except Exception as e:
            session.rollback()
            logger.error(f"Error setting error: {e}")
            return False
        finally:
            session.close()
    
    def get_all_jobs(self, limit: int = 50, offset: int = 0) -> List[AnalysisJob]:
        """
        Retrieve all jobs, ordered by upload time (newest first).
        
        Args:
            limit: Maximum number of jobs to return
            offset: Number of jobs to skip (for pagination)
        
        Returns:
            List of AnalysisJob instances
        """
        session = self.get_session()
        
        try:
            jobs = session.query(AnalysisJob)\
                .order_by(AnalysisJob.upload_timestamp.desc())\
                .limit(limit)\
                .offset(offset)\
                .all()
            return jobs
        finally:
            session.close()
    
    def get_jobs_by_status(self, status: str, limit: int = 50) -> List[AnalysisJob]:
        """
        Retrieve jobs with specific status.
        
        Args:
            status: Job status to filter by
            limit: Maximum number of jobs to return
        
        Returns:
            List of AnalysisJob instances
        """
        session = self.get_session()
        
        try:
            jobs = session.query(AnalysisJob)\
                .filter_by(status=status)\
                .order_by(AnalysisJob.upload_timestamp.desc())\
                .limit(limit)\
                .all()
            return jobs
        finally:
            session.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        session = self.get_session()
        
        try:
            total_jobs = session.query(AnalysisJob).count()
            completed_jobs = session.query(AnalysisJob).filter_by(status='completed').count()
            failed_jobs = session.query(AnalysisJob).filter_by(status='failed').count()
            processing_jobs = session.query(AnalysisJob).filter_by(status='processing').count()
            queued_jobs = session.query(AnalysisJob).filter_by(status='queued').count()
            
            # Get verdict distribution for completed jobs
            real_count = session.query(AnalysisJob)\
                .filter_by(status='completed', verdict='Real').count()
            fake_count = session.query(AnalysisJob)\
                .filter_by(status='completed', verdict='Fake').count()
            
            return {
                'total_jobs': total_jobs,
                'completed_jobs': completed_jobs,
                'failed_jobs': failed_jobs,
                'processing_jobs': processing_jobs,
                'queued_jobs': queued_jobs,
                'real_videos': real_count,
                'fake_videos': fake_count
            }
        finally:
            session.close()


# Global database instance
_db_instance = None

def get_database() -> DatabaseManager:
    """
    Get or create global database instance (singleton pattern).
    
    Returns:
        DatabaseManager instance
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseManager()
    return _db_instance
