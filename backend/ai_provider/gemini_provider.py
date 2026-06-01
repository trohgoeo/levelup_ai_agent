import os
import google.generativeai as genai
from backend.ai_provider.base_provider import BaseAIProvider

class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key: str = None, model: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model = model
        
    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        if not self.api_key:
            raise ValueError("Gemini API key is missing or not configured.")
        
        genai.configure(api_key=self.api_key)
        
        # Pass system instruction directly in the GenerativeModel initiation if available
        model = genai.GenerativeModel(
            model_name=self.model,
            system_instruction=system_instruction
        )
        
        # Call the content generator with low temperature
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.2}
        )
        
        return response.text
