from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from utils.utils import TaskDecomposer


app=FastAPI(title="LLM Task Decomposer API")

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="LLM Task Decomposer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "https://ai-decomposer-dnd-todo-app.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    model:str ="gemini"
    query:str

@app.post("/decompose")
def get_task_breakdown(request:QueryRequest):
    handler=TaskDecomposer()
    result=handler.answer(request.model,request.query)
    return result


# if __name__ == "__main__":
#     uvicorn.run("app:app",host="0.0.0.0",port=5000)