import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ScanTask(SQLModel, table=True):
    """
    Represents a single code review scan request in the database.
    This class doubles as both a Pydantic data validator and a SQLAlchemy table.
    """

    # Primary Key: A unique ID safely returned to the user instantly
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    
    filename: str = Field(index=True) 
    
    # The SHA-256 fingerprint of the uploaded file. 
    # index=True makes searching for cache hits lightning fast.
    file_hash: str = Field(index=True)
    
    # State tracking: "PENDING", "COMPLETED", or "FAILED"
    status: str = Field(default="PENDING")
    
    # Stores the LLM JSON evaluation once finished. Nullable (Optional) initially.
    results_json: Optional[str] = Field(default=None)
    
    # Timestamp for enforcing the 24-hour Time-To-Live (TTL) requirement
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))