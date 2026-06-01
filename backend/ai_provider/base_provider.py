from abc import ABC, abstractmethod
import json
from typing import Type, TypeVar
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)

class BaseAIProvider(ABC):
    
    @abstractmethod
    def generate_text(self, prompt: str, system_instruction: str = None) -> str:
        """
        Generate a raw text response from the model.
        """
        pass

    def generate_json(self, prompt: str, response_model: Type[T], system_instruction: str = None) -> T:
        """
        Generates a structured JSON response matching the given Pydantic model.
        Falls back to raw text parsing and Pydantic schema validation.
        """
        schema_info = json.dumps(response_model.model_json_schema(), indent=2)
        json_instruction = (
            f"\n\n[SYSTEM]: You MUST respond strictly in valid JSON format matching this JSON schema:\n"
            f"{schema_info}\n"
            f"Do not include any markdown wrappers (like ```json ... ```) or conversational preamble. "
            f"Start your response with '{{' and end with '}}'. Ensure all JSON keys and string values are properly escaped."
        )
        
        full_prompt = prompt + json_instruction
        raw_response = self.generate_text(full_prompt, system_instruction)
        
        # Clean up markdown block indicators if any are generated
        cleaned = raw_response.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        
        cleaned = cleaned.strip()

        try:
            parsed_json = json.loads(cleaned)
            return response_model.model_validate(parsed_json)
        except Exception as e:
            # Fallback if something like a list got returned inside another structure, or clean parsing failed
            # Try to find the first '{' and last '}'
            start_idx = cleaned.find("{")
            end_idx = cleaned.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                try:
                    substring_json = cleaned[start_idx:end_idx+1]
                    parsed_json = json.loads(substring_json)
                    return response_model.model_validate(parsed_json)
                except Exception as sub_e:
                    pass
            raise ValueError(
                f"Failed to parse and validate Pydantic model {response_model.__name__} from LLM response.\n"
                f"Validation Error: {str(e)}\n"
                f"Raw Response: {raw_response}"
            )
