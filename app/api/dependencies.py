from fastapi import Depends
from sqlmodel import Session

from app.db.database import get_session
from app.db.manager import DatabaseManager
from app.services.llm_provider import OllamaClient
from app.services.orchestrator import ScanOrchestrator


def get_db_manager(session: Session = Depends(get_session)) -> DatabaseManager:
    """
    Injects a fresh, safe database session into the DatabaseManager.
    """
    return DatabaseManager(session=session)


def get_llm_client() -> OllamaClient:
    """
    Instantiates the Ollama Client. 
    (In a more advanced setup, this could return an abstract LLMProvider interface).
    """
    return OllamaClient()


def get_orchestrator(
    db_manager: DatabaseManager = Depends(get_db_manager),
    llm_client: OllamaClient = Depends(get_llm_client),
) -> ScanOrchestrator:
    """
    The ultimate dependency. Assembles the Database and the LLM client, 
    and hands them safely to the Orchestrator.
    """
    return ScanOrchestrator(db_manager=db_manager, llm_client=llm_client)