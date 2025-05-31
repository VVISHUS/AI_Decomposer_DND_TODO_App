import os
import csv
import json
import re
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai
from anthropic import Anthropic

MASTER_PROMPT = """You are a productivity assistant. Your job is to break any user-defined goal into clear, practical subtasks and steps.
Return the output as a valid pure JSON object with the format:
{
  "Subtask1": {
    "title": "1. Subtask Title",
    "steps": [
      "First task",
      "Second task"
    ]
  },
  "Subtask2": {
    "title": "2. Another Title",
    "steps": [
      "First task",
      "Second task"
    ]
  }
}
Do NOT include any text or Markdown formatting like ```json. Only return valid JSON."""
SUCCESS_LOG = "utils/query_success_log.csv"
ERROR_LOG = "utils/query_error_log.csv"


class TaskDecomposer:
    def __init__(self, temperature=0.7):
        self.temperature = temperature
        self._ensure_log_files_exist()

    def _ensure_log_files_exist(self):
        for filename, headers in [(SUCCESS_LOG, ["timestamp", "model", "query", "response"]),
                                 (ERROR_LOG, ["timestamp", "model", "query", "error"])]:
            if not os.path.exists(filename):
                with open(filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)

    def _parse_json_response(self, text: str) -> dict:
        try:
            data = json.loads(text.strip())
            if isinstance(data, dict):
                return data
            else:
                raise ValueError("Parsed object is not a dictionary")
        except json.JSONDecodeError:
            try:
                json_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(1))
                    if isinstance(data, dict):
                        return data
                    else:
                        raise ValueError("Extracted JSON is not a dictionary")
                else:
                    raise ValueError("No JSON block found in response")
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"JSON parsing failed: {str(e)}",
                    "raw_output": text
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}",
                "raw_output": text
            }
    def _log_success(self, model: str, query: str, response: dict):
        """Log successful API calls."""
        with open(SUCCESS_LOG, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), model, query, json.dumps(response)])

    def _log_error(self, model: str, query: str, error: str):
        """Log failed API calls."""
        with open(ERROR_LOG, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().isoformat(), model, query, str(error)])

    # def _validate_response(self, response: dict) -> bool:
    #     """Validate the structure of the decomposed tasks."""
    #     if not isinstance(response, dict):
    #         return False
    #     return all(
    #         isinstance(subtask, dict) and 
    #         "title" in subtask and 
    #         "steps" in subtask and 
    #         isinstance(subtask["steps"], dict)
    #         for subtask in response.values()
    #     )

    def decompose_with_openai(self, query: str) -> dict:
        """Decompose task using OpenAI."""
        try:
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY environment variable not set")

            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": MASTER_PROMPT},
                    {"role": "user", "content": query}
                ],
                temperature=self.temperature,
#                max_tokens=500,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            parsed = self._parse_json_response(content)
            print(f"parsed:\n{parsed}")
            if "error" in parsed:
                raise ValueError(parsed["error"])     
                
            return parsed
            
        except Exception as e:
            self._log_error("openai", query, str(e))
            raise

    def decompose_with_gemini(self, query: str) -> dict:
        """Decompose task using Gemini."""
        try:
            if not os.getenv("GEMINI_API_KEY"):
                raise ValueError("GEMINI_API_KEY environment variable not set")

            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(
                [MASTER_PROMPT, query],
                generation_config=genai.types.GenerationConfig(
                    temperature=self.temperature,
#                    max_output_tokens=500
                )
            )
            content = response.text
            print(content)
            parsed = self._parse_json_response(content)
            
            if "error" in parsed:
                raise ValueError(parsed["error"])
                
            return parsed
            
        except Exception as e:
            self._log_error("gemini", query, str(e))
            raise

    def decompose_with_anthropic(self, query: str) -> dict:
        """Decompose task using Anthropic."""
        try:
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")

            client = Anthropic()
            response = client.messages.create(
                model="claude-3-opus-20240229",
#                max_tokens=500,
                temperature=self.temperature,
                system=MASTER_PROMPT,
                messages=[{"role": "user", "content": query}]
            )
            content = response.content[0].text
            parsed = self._parse_json_response(content)
            
            if "error" in parsed:
                raise ValueError(parsed["error"])
                
            return parsed
            
        except Exception as e:
            self._log_error("anthropic", query, str(e))
            raise

    def answer(self, model: str, query: str) -> dict:
        try:
            model = model.lower()
            if model == "openai":
                result = self.decompose_with_openai(query)
            elif model == "gemini":
                result = self.decompose_with_gemini(query)
            elif model == "anthropic":
                result = self.decompose_with_anthropic(query)
            else:
                raise ValueError(f"Unsupported model: {model}")

            self._log_success(model, query, result)
            return {
                "status": "success",
                "data": result
            }
            
        except Exception as e:
            self._log_error(model, query, str(e))
            return {
                "status": "error",
                "message": str(e),
                "raw_output": getattr(e, "raw_output", None)
            }
        
payload = {
    "model": "gemini",  # or "gemini" or "anthropic"
    "query": "I want to build a portfolio website. What steps should I follow?"
}

# handler=TaskDecomposer()
# result=handler.answer(**payload)

# print(result)