class AgentError(Exception):
    """Base exception for all agent-related errors."""
    pass

class APIKeyError(AgentError):
    """Raised when the API key is missing or invalid."""
    pass

class MemoryFileError(AgentError):
    """Raised when the memory/retrieval save file is missing, corrupted, or incompatible."""
    pass