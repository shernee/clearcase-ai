from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any
import httpx
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

class NoticeRequest(BaseModel):
    notice_text: str = Field(..., min_length=10, max_length=50000, description="Immigration notice text")
    
    @validator('notice_text')
    def validate_notice_text(cls, v):
        if not v.strip():
            raise ValueError('Notice text cannot be empty or whitespace only')
        return v.strip()

class ExplanationResponse(BaseModel):
    explanation: str

class OpenRouterMessage(BaseModel):
    role: str
    content: str

class OpenRouterRequest(BaseModel):
    model: str
    messages: List[OpenRouterMessage]

class OpenRouterChoice(BaseModel):
    message: OpenRouterMessage

class OpenRouterResponse(BaseModel):
    choices: List[OpenRouterChoice]

@app.get("/")
async def read_root():
    return FileResponse("static/index.html")

@app.post("/explain", response_model=ExplanationResponse)
async def explain_notice(request: NoticeRequest) -> ExplanationResponse:
    try:
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
        
        prompt = f"""Please explain this immigration notice in simple, clear language. 
        Break down what it means, what actions (if any) are required, and any important deadlines.
        Make it easy to understand for someone who may not be familiar with immigration terminology.

        Immigration Notice:
        {request.notice_text}"""
        
        openrouter_request = OpenRouterRequest(
            model="anthropic/claude-3-haiku",
            messages=[OpenRouterMessage(role="user", content=prompt)]
        )
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openrouter_api_key}",
                    "Content-Type": "application/json"
                },
                json=openrouter_request.dict()
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Error calling LLM service")
            
            llm_response_data = response.json()
            llm_response = OpenRouterResponse(**llm_response_data)
            explanation = llm_response.choices[0].message.content
            
            return ExplanationResponse(explanation=explanation)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)