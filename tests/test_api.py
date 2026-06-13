import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool 
from app.main import app
from app.api.dependencies import get_llm_client, get_db_manager
from app.db.manager import DatabaseManager

# --- 1. MOCK THE DATABASE ---
# Create an isolated SQLite database entirely in RAM
# 2. UPDATE THIS ENGINE CONFIGURATION:
test_engine = create_engine(
    "sqlite://", 
    connect_args={"check_same_thread": False}, # Disable SQLite's thread lock
    poolclass=StaticPool # Ensure all threads share the exact same in-memory database
)

def override_get_db_manager():
    SQLModel.metadata.create_all(test_engine) # Auto-create tables in RAM
    with Session(test_engine) as session:
        yield DatabaseManager(session)

app.dependency_overrides[get_db_manager] = override_get_db_manager

# --- 2. MOCK THE LLM ---
class MockLLMClient:
    def __init__(self, should_pass: bool = True):
        self.should_pass = should_pass

    def review_code(self, code_snippet: str):
        return {
            "All variables have meaningful names": self.should_pass,
            "Docstring of function reflects the actual code's logic": self.should_pass
        }

def override_get_llm_client_pass(): return MockLLMClient(should_pass=True)
def override_get_llm_client_fail(): return MockLLMClient(should_pass=False)

# --- 3. TEST CLIENT FIXTURE ---
# Using the "with" context manager automatically triggers FastAPI's startup/shutdown events
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

# --- 4. THE TESTS ---

def test_no_file_uploaded(client):
    response = client.post("/scan")
    assert response.status_code == 422

def test_non_python_file(client):
    files = {"file": ("document.txt", b"Hello world", "text/plain")}
    response = client.post("/scan", files=files)
    assert response.status_code == 400

def test_good_python_file(client):
    app.dependency_overrides[get_llm_client] = override_get_llm_client_pass
    
    files = {"file": ("good_code.py", b"def foo(): pass", "text/plain")}
    post_response = client.post("/scan", files=files)
    
    assert post_response.status_code == 202
    scan_id = post_response.json()["scan_id"]
    
    get_response = client.get(f"/results/{scan_id}")
    assert get_response.status_code == 200
    assert get_response.json()["results"]["All variables have meaningful names"] is True
    
    # Cleanup override
    app.dependency_overrides.pop(get_llm_client, None)

def test_bad_python_file(client):
    app.dependency_overrides[get_llm_client] = override_get_llm_client_fail
    
    files = {"file": ("bad_code.py", b"def x(): a=1", "text/plain")}
    post_response = client.post("/scan", files=files)
    scan_id = post_response.json()["scan_id"]
    
    get_response = client.get(f"/results/{scan_id}")
    assert get_response.json()["results"]["All variables have meaningful names"] is False
    
    # Cleanup override
    app.dependency_overrides.pop(get_llm_client, None)