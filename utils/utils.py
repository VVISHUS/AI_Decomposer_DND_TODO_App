import os
import csv
import json
import re
from datetime import datetime
from openai import OpenAI
import google.generativeai as genai
from anthropic import Anthropic

MASTER_PROMPT = (
    """You are a productivity assistant. Your job is to break any user-defined goal into clear, practical subtasks and steps. "
    Return the output as a **valid pure JSON** object with the format:\n"
    {\n
      (1)Subtask1-> Subtask Title: {\n
        step1: First task,\n
        step2: Second task\n
      },\n
      (2)Subtask2-> Another Title: {\n
        "step1": "First task,\n
        "step2": "Second task"\n'
      }\n"
    }\n"
    Do NOT include any text or Markdown formatting like ```json. Only return valid JSON."""
)

SUCCESS_LOG = "query_success_log.csv"
ERROR_LOG = "query_error_log.csv"


class GetResponse:
    def __init__(self, temp=0.7, prompt=""):
        self.temp = temp
        self.prompt = prompt

    def _parse_json_response(self,text:str)->dict:
        try:
            # Remove Markdown-style code block wrappers if present
            json_str_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
            if json_str_match:
                json_str = json_str_match.group(1)
            else:
                # Assume the entire output might be JSON already
                json_str = text.strip()

            return json.loads(json_str)
        except Exception as e:
            return {"error": "No JSON found in model output", "raw_output": text}


    def _log_success(self, model, query, raw_output):
        exists = os.path.exists(SUCCESS_LOG)
        with open(SUCCESS_LOG, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not exists:
                writer.writerow(["timestamp", "model", "query", "raw_output"])
            writer.writerow([datetime.now().isoformat(), model, query, json.dumps(raw_output, ensure_ascii=False)])

    def _log_error(self, model, query, error):
        exists = os.path.exists(ERROR_LOG)
        with open(ERROR_LOG, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not exists:
                writer.writerow(["timestamp", "model", "query", "error"])
            writer.writerow([datetime.now().isoformat(), model, query, str(error)])


    def openai_response(self, query):
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": MASTER_PROMPT},
                    {"role": "user", "content": query}
                ],
                temperature=self.temp,
                max_tokens=500
            )
            raw = response.choices[0].message.content
            # parsed = self._parse_json_response(raw)
            # self._log_success("openai", query, parsed)
            return raw
        except Exception as e:
            self._log_error("openai", query, e)
            return {"error": str(e)}

    def gemini_response(self, query):
        try:
            genai.configure(api_key="AIzaSyDqcK7STmBNmXtPkcKmifpIbAZH4-UU_7o")
            # genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content([MASTER_PROMPT, query])
            raw = response.text
            print(raw)
            # parsed = self._parse_json_response(raw)
            # self._log_success("gemini", query, parsed)
            return raw
        except Exception as e:
            self._log_error("gemini", query, e)
            return {"error": str(e)}

    def anthropic_response(self, query):
        try:
            client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            response = client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=500,
                temperature=self.temp,
                messages=[{"role": "user", "content": f"{MASTER_PROMPT}\n\n{query}"}]
            )
            raw = response.content[0].text
            # parsed = self._parse_json_response(raw)
            # self._log_success("anthropic", query, parsed)
            return raw
        except Exception as e:
            self._log_error("anthropic", query, e)
            return {"error": str(e)}

    def answer(self, model: str, query: str = "") -> dict:
        self.prompt = query
        raw_res=None
        if model.lower() == "openai":
            raw_res= self.openai_response(query)
        elif model.lower() == "gemini":
            raw_res= self.gemini_response(query)
        elif model.lower() == "anthropic":
            raw_res= self.anthropic_response(query)
        else:
            error_msg = f"Unsupported model name: {model}. Choose from ['openai', 'gemini', 'anthropic']."
            self._log_error(model, query, error_msg)
            return {"error": error_msg}
        parsed = self._parse_json_response(raw_res)
        self._log_success("openai", query, parsed)
        return parsed
    
# Example Usage 
# if __name__ == "__main__":
#     llm = GetResponse(temp=0.7)
#     query = "I want to build a portfolio website. What are the steps I should take?"

#     print("🔷 OpenAI:")
#     print(json.dumps(llm.answer("openai", query), indent=2))

#     print("\n🔶 Gemini:")
#     print(json.dumps(llm.answer("gemini", query), indent=2))

#     print("\n🟡 Claude (Anthropic):")
#     print(json.dumps(llm.answer("anthropic", query), indent=2))
