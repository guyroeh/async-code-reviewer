import pytest
import asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app

# @pytest.mark.asyncio tells pytest this is an asynchronous test
@pytest.mark.asyncio
async def test_system_max_capacity():
    """
    Fires 6 requests at the exact same time entirely in-memory.
    Expects exactly five 202 (Accepted) and one 503 (Service Unavailable).
    """
    
    async def send_upload_request(worker_id: int):
        """Sends a single POST request using the in-memory ASGI transport."""
        # ASGITransport bypasses the network port and talks directly to FastAPI
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            files = {"file": (f"test_load_{worker_id}.py", b"print('hello')", "text/plain")}
            response = await client.post("/scan", files=files)
            return response.status_code

    # 1. Prepare 6 asynchronous tasks
    tasks = [send_upload_request(i) for i in range(6)]
    
    # 2. Fire them all simultaneously and wait for the results
    status_codes = await asyncio.gather(*tasks)

    # 3. Count the results
    success_count = status_codes.count(202)
    rejection_count = status_codes.count(503)

    # 4. Assert the architectural rules held up
    assert success_count == 5, f"Expected 5 successes, got {success_count}"
    assert rejection_count == 1, f"Expected 1 rejection, got {rejection_count}"