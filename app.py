from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from utils.utils import GetResponse

app=FastAPI(title="LLM Task Decomposer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],  # Your React app's origin
    allow_credentials=True,
    allow_methods=["*"],  # Or specify ["POST", "GET", etc.]
    allow_headers=["*"],
)
class QueryRequest(BaseModel):
    model:str ="gemini"
    query:str

@app.post("/decompose")
def get_task_breakdown(request:QueryRequest):
    handler=GetResponse()
    result=handler.answer(request.model,request.query)
    return result

if __name__ == "__main__":
    config = uvicorn.Config("app:app", port=5000, log_level="info")
    server = uvicorn.Server(config)
    server.run()