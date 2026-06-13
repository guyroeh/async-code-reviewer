import json
import requests
from typing import Dict, Any

from app.core.config import settings
from app.prompts.templates import VARIABLE_CHECK_PROMPT, DOCSTRING_CHECK_PROMPT


class OllamaClient:
    """
    Handles communication with the local Ollama LLM instance.
    Abstracts away the HTTP requests and JSON parsing.
    """

    def __init__(self) -> None:
        self.url = settings.llm_provider_url
        self.model = settings.llm_model_name
        self.timeout = settings.llm_timeout_seconds

    def _call_model(self, prompt: str, code: str) -> Dict[str, Any]:
        """
        Internal helper method to send the request to Ollama and parse the JSON.
        """
        payload = {
            "model": self.model,
            "prompt": f"{prompt}\n\nCode to review:\n```python\n{code}\n```",
            "format": "json",  # Forces Ollama to strictly return a JSON structure
            "stream": False,
            "options": {
                "temperature": 0.0  # 0.0 makes the model deterministic, not creative
            }
        }

        try:
            response = requests.post(self.url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            # Extract the string response from Ollama's payload
            raw_result = response.json().get("response", "{}")
            
            # Convert that string back into a Python dictionary
            return json.loads(raw_result)
            
        except (requests.RequestException, json.JSONDecodeError) as e:
            # If the model crashes, times out, or returns garbage, fail safely
            print(f"LLM Connection Error: {e}")
            return {"rule_passed": False, "explanation": "System error during LLM evaluation."}

    def review_code(self, code_snippet: str) -> Dict[str, bool]:
        """
        Executes both predefined singular checks against the provided code.
        
        Returns a dictionary tracking the TRUE/FALSE adherence for each rule.
        """
        # Run Rule 1
        var_result = self._call_model(VARIABLE_CHECK_PROMPT, code_snippet)
        
        # Run Rule 2
        doc_result = self._call_model(DOCSTRING_CHECK_PROMPT, code_snippet)

        # Map the results to the specific rules required by the assignment
        return {
            "All variables have meaningful names": var_result.get("rule_passed", False),
            "Docstring of function reflects the actual code's logic": doc_result.get("rule_passed", False)
        }