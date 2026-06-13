import asyncio
import json
import uuid
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, status
from app.core.hashing import generate_file_hash
from app.api.dependencies import get_db_manager, get_orchestrator
from app.core.config import settings
from app.db.manager import DatabaseManager
from app.services.orchestrator import ScanOrchestrator

# Create the router component
router = APIRouter()

# Global variable to hold our concurrency lock
scan_semaphore: Optional[asyncio.Semaphore] = None

def get_semaphore() -> asyncio.Semaphore:
    """
    Lazily initializes the Semaphore. We do this because asyncio objects 
    must be created inside the active event loop (which starts when the server boots).
    """
    global scan_semaphore
    if scan_semaphore is None:
        scan_semaphore = asyncio.Semaphore(settings.max_concurrent_scans)
    return scan_semaphore


async def protected_background_scan(
    scan_id: uuid.UUID, 
    code_content: str, 
    orchestrator: ScanOrchestrator
) -> None:
    """
    A wrapper for the orchestrator that enforces the 5-scan limit during execution.
    """
    semaphore = get_semaphore()
    async with semaphore:
        # We use asyncio.to_thread so the synchronous LLM call doesn't block 
        # the main server loop while waiting for Ollama to finish.
        await asyncio.to_thread(orchestrator.execute_scan, scan_id, code_content)


def validate_python_file(file: UploadFile) -> None:
    """
    Ensures the uploaded file is a valid Python script and does not exceed the size limit.
    Raises an HTTP 400 or 413 error if validation fails.
    """
    if not file.filename or not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only .py files are supported.")

    if file.size and file.size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File is too large. Maximum allowed size is {settings.max_file_size_bytes / 1024} KB."
        )

def enforce_system_capacity() -> None:
    """
    Checks if the system has available capacity to process a new scan.
    Raises an HTTP 503 error if the semaphore is locked.
    """
    if get_semaphore().locked():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="System is currently at maximum capacity. Please try again later.",
        )

@router.post("/scan", status_code=status.HTTP_202_ACCEPTED)
async def submit_scan(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db_manager: DatabaseManager = Depends(get_db_manager),
    orchestrator: ScanOrchestrator = Depends(get_orchestrator),
) -> dict:
    """
    Endpoint to upload a file and start the asynchronous code review.
    """
    # 1. Validation & Capacity Checks
    validate_python_file(file)
    enforce_system_capacity()

    # 2. Read File Content
    code_bytes = await file.read()
    code_content = code_bytes.decode("utf-8")
    
    # 3. Setup Task Identifiers
    filename = file.filename
    scan_id = uuid.uuid4()
    file_hash = generate_file_hash(code_content)
    
    # 4. Save to Database
    db_manager.create_pending_scan(
        scan_id=scan_id, 
        filename=filename, 
        file_hash=file_hash
    )

    # 5. Dispatch Background Task
    background_tasks.add_task(
        protected_background_scan, 
        scan_id=scan_id, 
        code_content=code_content, 
        orchestrator=orchestrator
    )

    # 6. Return Receipt
    return {
        "filename": filename,
        "scan_id": str(scan_id), 
        "status": "PENDING"
    }

@router.get("/results/{scan_id}", status_code=status.HTTP_200_OK)
def get_scan_results(
    scan_id: uuid.UUID,
    db_manager: DatabaseManager = Depends(get_db_manager),
) -> dict:
    """
    Endpoint for users to poll the status of their requested scan.
    """
    task = db_manager.get_scan(scan_id)

    if not task:
        raise HTTPException(status_code=404, detail="Scan not found or has expired.")

    # If still working, just return the status
    if task.status != "COMPLETED":
        return {"scan_id": str(task.id), "status": task.status}

    # If finished, deserialize the JSON string back into a dictionary
    parsed_results = json.loads(task.results_json) if task.results_json else {}

    return {
        "scan_id": str(task.id),
        "status": task.status,
        "results": parsed_results
    }

@router.get("/results/file/{filename}", status_code=status.HTTP_200_OK)
def get_scan_results_by_filename(
    filename: str,
    db_manager: DatabaseManager = Depends(get_db_manager),
) -> dict:
    """
    Fetch the most recent code review results using just the name of the file.
    """
    task = db_manager.get_latest_scan_by_filename(filename)

    if not task:
        raise HTTPException(
            status_code=404, 
            detail=f"No scans found for a file named '{filename}'."
        )

    if task.status != "COMPLETED":
        return {
            "filename": task.filename,
            "scan_id": task.id, 
            "status": task.status
        }

    parsed_results = json.loads(task.results_json) if task.results_json else {}

    return {
        "filename": task.filename,
        "scan_id": task.id,
        "status": task.status,
        "results": parsed_results
    }