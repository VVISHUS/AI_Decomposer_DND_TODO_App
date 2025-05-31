import os
import csv
import json
import re
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai
from anthropic import Anthropic
import requests
MODELS = {
    "llama-3.3_70B": "meta-llama/Llama-3.3-70B-Instruct",
    "llama-3.1_8B": "meta-llama/Meta-Llama-3.1-8B-Instruct",
    "hermes-3_70B": "NousResearch/Hermes-3-Llama-3.1-70B",
    "qwq_32B": "Qwen/QwQ-32B-Preview",
    "deepseek-v3": "deepseek-ai/DeepSeek-V3",
    "qwq_32B_alt": "Qwen/QwQ-32B",
    "deepseek-v3_0324": "deepseek-ai/DeepSeek-V3-0324",
    "deepseek-r1": "deepseek-ai/DeepSeek-R1",
    "qwen2.5-coder_32B": "Qwen/Qwen2.5-Coder-32B-Instruct",
    "llama-3.2_3B": "meta-llama/Llama-3.2-3B-Instruct",
    "qwen2.5_72B": "Qwen/Qwen2.5-72B-Instruct",
    "llama-3_70B": "meta-llama/Meta-Llama-3-70B-Instruct",
    "llama-3.1_405B": "meta-llama/Meta-Llama-3.1-405B-Instruct",
    "llama-3.1_70B": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "gemini-1.5-flash": "gemini",
    "openAI":"openai", 
    "anthropic":"anthropic"
}

# print(MODELS.keys())
# print(f"{"llama-3_70B" in MODELS.keys()}")
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
            # parsed = self._parse_json_response(content)
            # if "error" in parsed:
            #     raise ValueError(parsed["error"])     
                
            return content
            
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
            # print(content)
            # parsed = self._parse_json_response(content)
            
            # if "error" in parsed:
            #     raise ValueError(parsed["error"])
                
            return content
            
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
            # parsed = self._parse_json_response(content)
            
            # if "error" in parsed:
            #     raise ValueError(parsed["error"])
                
            return content
            
        except Exception as e:
            self._log_error("anthropic", query, str(e))
            raise
    def decompose_with_hyperbolic_models(self, model:str,query:str)->dict:
        URL = "https://api.hyperbolic.xyz/v1/chat/completions"
        HEADERS = {
                "Content-Type": "application/json",
                # "Authorization": f"Bearer {os.getenv("HYPERBOLIC")}"
                "Authorization": f"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ2YWliczE3MTdAZ21haWwuY29tIiwiaWF0IjoxNzQ0NDkyNTg0fQ.s3kVhBY0sTEaQyaeHt_3cDS1Rw7TFMjiOvkS8veql6Y"
            }
        data = {
            "messages": [
                    {"role": "system", "content": MASTER_PROMPT},
                    {"role": "user", "content": query}
                ],
                "model":model,
                "temperature":self.temperature
         }
        try:
            response = requests.post(URL, headers=HEADERS, json=data)
            response.raise_for_status()
            result = response.json()
            answer = result['choices'][0]['message']['content']
            return answer
        except Exception as e:
            self._log_error(model, query, str(e))
            raise

    def answer(self, model: str, query: str) -> dict:
        try:
            um_model=MODELS[model]
            result=None
            if um_model == "openai":
                result = self.decompose_with_openai(query=query)
            elif um_model == "gemini":
                result = self.decompose_with_gemini(query=query)
            elif um_model == "anthropic":
                result = self.decompose_with_anthropic(query=query)
            elif model in MODELS.keys():
                result= self.decompose_with_hyperbolic_models(model=MODELS[model],query=query)
            else:
                raise ValueError(f"Unsupported model: {model}")
            
            print(f"result:\n {result}\n")
            fresult=self._parse_json_response(result)
            print(f"final result:\n {fresult}")
            if "error" in fresult:
                raise ValueError(fresult["error"])
            
            self._log_success(model, query, fresult)

            return {
                "status": "success",
                "data": fresult
            }
            
        except Exception as e:
            self._log_error(model, query, str(e))
            return {
                "status": "error",
                "message": str(e),
                "raw_output": getattr(e, "raw_output", None)
            }
        
# payload = {
#     "model": "llama-3_70B",  # or "gemini" or "anthropic"
#     "query": "I want to build a portfolio website. What steps should I follow?"
# }

# handler=TaskDecomposer()
# result=handler.answer(**payload)

# print(result)