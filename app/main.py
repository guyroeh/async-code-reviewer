from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router as api_router
from app.core.config import settings
from app.db.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan Manager.
    Code before the 'yield' runs exactly once when the server boots up.
    Code after the 'yield' runs when the server shuts down.
    """
    # 1. Initialize the SQLite database and create tables if they don't exist
    create_db_and_tables()
    
    # 2. Yield control back to FastAPI so it can start accepting web traffic
    yield


# Initialize the main application instance
# Initialize the main application instance with custom UI parameters
app = FastAPI(
    title="🔍 AI Code Reviewer",
    description=(
        "Welcome to the Automated Code Review Platform. Upload any Python file (.py) "
        "to instantly analyze its variables and docstring integrity using local LLM intelligence."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",  # Changes the documentation page from /docs to the main home page!
    redoc_url=None, # Disables the alternative Redoc documentation to keep things simple
    swagger_ui_parameters={
        "defaultModelsExpandDepth": -1,  # Hides the confusing "Schemas" section at the bottom
        "docExpansion": "list",         # Keeps the endpoints cleanly listed
    }
)

# Plug in the router containing our POST and GET endpoints
app.include_router(api_router)

