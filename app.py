from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
from utils.utils import TaskDecomposer
from fastapi import HTTPException



app=FastAPI(title="LLM Task Decomposer API")

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

handler = TaskDecomposer()

@app.post("/decompose")
async def get_task_breakdown(request: QueryRequest):
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Empty query")
            
        return handler.answer(request.model, request.query)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError:
        raise HTTPException(status_code=504, detail="LLM timeout")
    except Exception:
        raise HTTPException(status_code=500)

# if __name__ == "__main__":
#     uvicorn.run("app:app",host="0.0.0.0",port=5000)