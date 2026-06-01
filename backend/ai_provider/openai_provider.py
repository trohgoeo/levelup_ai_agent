import os
from openai import OpenAI
from backend.ai_provider.base_provider import BaseAIProvider

class OpenAIProvider(BaseAIProvider):
    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        
    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        if not self.api_key:
            raise ValueError("OpenAI API key is missing or not configured.")
        
        client = OpenAI(api_key=self.api_key)
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.2
        )
        return response.choices[0].message.content
