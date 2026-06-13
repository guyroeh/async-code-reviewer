import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlmodel import Session, select

from app.core.config import settings
from app.db.models import ScanTask


class DatabaseManager:
    """
    Handles all direct interactions with the SQLite database.
    Implements the 'Lazy Purge' strategy to enforce the 24-hour TTL requirement.
    """

    def __init__(self, session: Session) -> None:
        # Dependency Injection: The database session is passed in,
        # ensuring this class doesn't manage its own risky connections.
        self.session = session

    def _purge_expired_records(self) -> None:
        """
        PRIVATE METHOD: The core of the Lazy Purge strategy.
        Identifies and deletes any ScanTask records older than the TTL limit.
        """
        # Calculate the exact cutoff time in UTC
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=settings.result_ttl_hours)

        # Select all tasks created before the cutoff time
        statement = select(ScanTask).where(ScanTask.created_at < cutoff_time)
        expired_tasks = self.session.exec(statement).all()

        # Delete them and commit the transaction
        for task in expired_tasks:
            self.session.delete(task)
        
        if expired_tasks:
            self.session.commit()

    def create_pending_scan(self, scan_id: uuid.UUID, filename: str, file_hash: str) -> ScanTask:
        """
        Creates the initial placeholder record when a user first uploads a file.
        This allows the user to immediately poll for the 'PENDING' status.
        """
        self._purge_expired_records()
        
        # Save both the short ID and the actual filename
        task = ScanTask(id=scan_id, filename=filename, file_hash=file_hash)
        self.session.add(task)
        self.session.commit()
        self.session.refresh(task)
        return task

    def get_latest_scan_by_filename(self, filename: str) -> Optional[ScanTask]:
        """Retrieves the most recent scan matching a specific filename."""
        self._purge_expired_records()
        
        # Sort by creation time descending to ensure we get the latest attempt
        statement = (
            select(ScanTask)
            .where(ScanTask.filename == filename)
            .order_by(ScanTask.created_at.desc())
        )
        return self.session.exec(statement).first()
    

    def find_cached_results(self, file_hash: str) -> Optional[str]:
        """
        Searches the database for a completed scan matching the file hash.
        """
        self._purge_expired_records()  # Ensure we don't return an expired cache hit

        statement = select(ScanTask).where(
            ScanTask.file_hash == file_hash,
            ScanTask.status == "COMPLETED"
        )
        cached_task = self.session.exec(statement).first()

        if cached_task:
            return cached_task.results_json
        return None

    def update_scan_status(
        self, 
        scan_id: uuid.UUID, 
        status: str, 
        results_json: Optional[str] = None, 
        file_hash: Optional[str] = None
    ) -> None:
        """
        Updates an existing task. Used by the Orchestrator when the LLM finishes.
        """
        task = self.session.get(ScanTask, scan_id)
        if task:
            task.status = status
            if results_json:
                task.results_json = results_json
            if file_hash:
                task.file_hash = file_hash
            
            self.session.add(task)
            self.session.commit()
            
    def get_scan(self, scan_id: uuid.UUID) -> Optional[ScanTask]:
        """
        Retrieves a specific scan. Used by the API to check status.
        """
        self._purge_expired_records()  # Trigger lazy cleanup on reads
        return self.session.get(ScanTask, scan_id)