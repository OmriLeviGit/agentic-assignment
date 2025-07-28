import os
import google.generativeai as genai
from dotenv import load_dotenv, find_dotenv
from .llm_interface import LLMInterface


class GeminiLLM(LLMInterface):
    """Gemini LLM implementation."""

    def __init__(self, model_name: str = 'gemini-1.5-flash'):
        load_dotenv(find_dotenv())
        api_key = os.getenv('GEMINI_API_KEY')

        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def query(self, prompt: str) -> str:
        """Query the Gemini API."""
        try:
            response = self.model.generate_content(prompt)
            return response.candidates[0].content.parts[0].text
        except Exception as e:
            raise RuntimeError(f"Error querying Gemini: {e}")

    def is_available(self) -> bool:
        """Check if Gemini API is available."""
        try:
            # Simple test query
            self.model.generate_content("Hello")
            return True
        except:
            return False