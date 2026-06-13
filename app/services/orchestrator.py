import json
import uuid
import logging

from app.core.hashing import generate_file_hash
from app.db.manager import DatabaseManager
from app.services.llm_provider import OllamaClient

logger = logging.getLogger(__name__)

class ScanOrchestrator:
    """
    Coordinates the high-level workflow of the code review process.
    Acts as the bridge between the API, the Database, and the LLM.
    """

    def __init__(self, db_manager: DatabaseManager, llm_client: OllamaClient) -> None:
        # Dependency Injection: We pass the initialized tools in, 
        # keeping this class loosely coupled and highly testable.
        self.db = db_manager
        self.llm = llm_client

    def execute_scan(self, scan_id: uuid.UUID, code_content: str) -> None:
        """
        The main pipeline executed as a background task.
        Flow: Hash File -> Check Cache -> Call LLM (if miss) -> Update DB.
        """
        try:
            # Step 1: Generate the unique fingerprint for the file
            file_hash = generate_file_hash(code_content)
            logger.info(f"Scan {scan_id}: Generated hash {file_hash}")

            # Step 2: Check the database for a cache hit to save compute
            cached_results = self.db.find_cached_results(file_hash)

            if cached_results:
                logger.info(f"Scan {scan_id}: Cache HIT. Reusing previous results.")
                self.db.update_scan_status(
                    scan_id=scan_id, 
                    status="COMPLETED", 
                    results_json=cached_results
                )
                return

            # Step 3: Cache miss. Send the code to the LLM engine.
            logger.info(f"Scan {scan_id}: Cache MISS. Sending to LLM.")
            review_results_dict = self.llm.review_code(code_content)

            # Step 4: Serialize results to a JSON string and save to the database
            results_json_str = json.dumps(review_results_dict)
            self.db.update_scan_status(
                scan_id=scan_id, 
                status="COMPLETED", 
                results_json=results_json_str,
                file_hash=file_hash  # Ensure the hash is saved so future scans can use it
            )

        except Exception as e:
            # Step 5: Safety Net. If the LLM crashes or DB locks, fail gracefully.
            logger.error(f"Scan {scan_id}: Failed with error - {e}")
            
            # We MUST update the status to FAILED, otherwise the user's 
            # API request will poll for "PENDING" forever.
            error_payload = json.dumps({"error": "Internal system failure during scan."})
            self.db.update_scan_status(
                scan_id=scan_id, 
                status="FAILED", 
                results_json=error_payload
            )