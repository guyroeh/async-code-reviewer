import hashlib


def generate_file_hash(content: str) -> str:
    """
    Generates a SHA-256 hash for the given file content.

    This acts as a unique fingerprint for the code. If two files have
    the exact same content, they will produce the exact same hash,
    allowing us to reuse previous scan results and save LLM compute time.

    Args:
        content (str): The raw text content of the uploaded Python file.

    Returns:
        str: A 64-character hexadecimal string representing the hash.
    """
    # hashlib requires bytes, so we must encode the standard Python string
    content_bytes = content.encode("utf-8")
    
    # Create the SHA-256 hash object
    hash_object = hashlib.sha256(content_bytes)
    
    # Return the readable 64-character hexadecimal string
    return hash_object.hexdigest()