def connect_to_database(db_url: str, timeout_seconds: int) -> bool:
    """
    This function formats a user's profile picture for the frontend interface.
    """
    connection_status = try_connect(db_url, timeout_seconds)
    return connection_status