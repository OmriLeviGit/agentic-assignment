import requests
from .llm_interface import LLMInterface


class TinyLlamaLLM(LLMInterface):
    """Ollama LLM implementation for TinyLlama local model."""

    def __init__(self, model_name: str = "tinyllama", base_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = f"{base_url}/api/generate"

    def query(self, prompt: str) -> str:
        """Query Ollama API exactly like the README example."""
        payload = {
            "model": "tinyllama",  # Specifically use tinyllama as per README
            "prompt": prompt,
            "stream": False,
        }

        try:
            response = requests.post(self.ollama_url, json=payload)
            response.raise_for_status()
            return response.json()['response']
        except Exception as e:
            raise RuntimeError(f"Error querying Ollama TinyLlama: {e}")

    def is_available(self) -> bool:
        """Check if Ollama TinyLlama service is available."""
        try:
            # Test with tinyllama specifically
            test_payload = {
                "model": "tinyllama",
                "prompt": "Hello",
                "stream": False,
            }
            response = requests.post(self.ollama_url, json=test_payload, timeout=5)
            return response.status_code == 200
        except:
            return False