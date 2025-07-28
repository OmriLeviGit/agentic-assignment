from abc import ABC, abstractmethod
from typing import Optional, Dict, Any


class LLMInterface(ABC):
    """Abstract interface for LLM providers."""

    @abstractmethod
    def query(self, prompt: str) -> str:
        """Send a prompt to the LLM and return the response."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the LLM service is available."""
        pass