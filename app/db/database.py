from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

# The local SQLite file that will be created in your project root
sqlite_file_name = "scans.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# The engine is the core interface to the database.
# check_same_thread=False is strictly required for FastAPI and SQLite to work together.
engine = create_engine(
    sqlite_url, 
    connect_args={"check_same_thread": False}, 
    echo=False
)


def create_db_and_tables() -> None:
    """
    Reads all SQLModel classes (like ScanTask) and generates the actual 
    tables in the SQLite database file if they don't already exist.
    """
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """
    A FastAPI dependency function. 
    It safely opens a database connection when a request starts,
    and guarantees the connection closes when the request finishes.
    """
    with Session(engine) as session:
        yield session