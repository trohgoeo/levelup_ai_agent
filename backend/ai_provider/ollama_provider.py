import requests
import json
from backend.ai_provider.base_provider import BaseAIProvider

class OllamaProvider(BaseAIProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip('/')
        self.model = model

    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        url = f"{self.base_url}/api/chat"
        
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.2
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result["message"]["content"]
        except requests.exceptions.RequestException as e:
            raise ConnectionError(
                f"Failed to communicate with Ollama local API at {self.base_url}. "
                f"Please verify Ollama is active (`ollama serve` or run the Ollama application) "
                f"and ensure you have pulled the model using `ollama pull {self.model}`.\n"
                f"Details: {str(e)}"
            )
