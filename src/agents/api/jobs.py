"""
Job management for async crew execution.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from ..runner import CrewRunner, CrewResult

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    """Represents an async crew job."""
    job_id: str
    topic: str
    language: str
    status: JobStatus
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[CrewResult] = None
    error: Optional[str] = None
    progress: float = 0.0  # 0.0 to 1.0


class JobManager:
    """
    Manages async crew job execution.
    
    Simple in-memory implementation for single-instance deployments.
    For production with multiple instances, use Redis or a database.
    """
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.runner = CrewRunner()
    
    def create_job(self, topic: str, language: str) -> str:
        """
        Create a new job and return its ID.
        
        Args:
            topic: Research topic
            language: Target language
            
        Returns:
            Job ID (UUID)
        """
        job_id = str(uuid.uuid4())
        
        job = Job(
            job_id=job_id,
            topic=topic,
            language=language,
            status=JobStatus.PENDING,
        )
        
        self.jobs[job_id] = job
        logger.info("Created job %s for topic: %s", job_id, topic)
        
        return job_id
    
    async def execute_job(self, job_id: str) -> None:
        """
        Execute a job in the background.
        
        Args:
            job_id: Job ID to execute
        """
        job = self.jobs.get(job_id)
        if not job:
            logger.error("Job %s not found", job_id)
            return
        
        try:
            # Update status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            job.progress = 0.1
            logger.info("Starting job %s", job_id)
            
            # Execute crew in thread pool (CPU-bound work)
            loop = asyncio.get_event_loop()
            
            job.progress = 0.3
            
            # Run crew workflow (this is the slow part)
            result = await loop.run_in_executor(
                None,  # Use default executor
                self.runner.run,
                job.topic,
                job.language,
            )
            
            job.progress = 0.9
            
            # Save outputs
            try:
                saved_paths = self.runner.save_output(result)
                logger.info("Job %s outputs saved: %s", job_id, list(saved_paths.keys()))
            except Exception as e:
                logger.warning("Job %s: Failed to save outputs: %s", job_id, e)
            
            # Mark complete
            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            job.progress = 1.0
            
            logger.info(
                "Job %s completed in %.2f seconds",
                job_id,
                (job.completed_at - job.started_at).total_seconds()
            )
            
        except Exception as e:
            logger.exception("Job %s failed", job_id)
            job.status = JobStatus.FAILED
            job.error = str(e)
            job.completed_at = datetime.now()
            job.progress = 0.0
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    def list_jobs(self, limit: int = 100) -> list[Job]:
        """List recent jobs."""
        jobs = sorted(
            self.jobs.values(),
            key=lambda j: j.created_at,
            reverse=True
        )
        return jobs[:limit]


# Global job manager instance
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """Get or create the global job manager."""
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager