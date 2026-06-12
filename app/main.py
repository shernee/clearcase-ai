from fastapi import FastAPI, HTTPException, Form, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional, Union
import httpx
import os
import base64
import fitz  # PyMuPDF
from PIL import Image
import io
import json

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

class NoticeRequest(BaseModel):
    notice_text: Optional[str] = Field(None, max_length=50000, description="Immigration notice text")
    
    @validator('notice_text')
    def validate_notice_text(cls, v):
        if v and not v.strip():
            raise ValueError('Notice text cannot be empty or whitespace only')
        return v.strip() if v else None

class ExplanationResponse(BaseModel):
    what_happened: str
    what_they_need: List[str]
    attorney_items: List[str]
    deadline: Optional[str]
    notice_type: str

class OpenRouterMessage(BaseModel):
    role: str
    content: Union[str, List[Dict[str, Any]]]

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

async def process_pdf(file_content: bytes) -> str:
    doc = fitz.open(stream=file_content, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text.strip()

async def process_image(file_content: bytes, filename: str) -> str:
    return base64.b64encode(file_content).decode('utf-8')

@app.post("/explain", response_model=ExplanationResponse)
async def explain_notice(
    notice_text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
) -> ExplanationResponse:
    try:
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            raise HTTPException(status_code=500, detail="OpenRouter API key not configured")
        
        # Process input - prefer file over text
        content_text = ""
        is_image = False
        base64_image = None
        
        if file:
            if not file.filename:
                raise HTTPException(status_code=400, detail="File must have a filename")
            
            file_content = await file.read()
            file_ext = file.filename.lower().split('.')[-1]
            
            if file_ext == 'pdf':
                content_text = await process_pdf(file_content)
                if not content_text.strip():
                    raise HTTPException(status_code=400, detail="No text found in PDF")
            elif file_ext in ['jpg', 'jpeg', 'png']:
                base64_image = await process_image(file_content, file.filename)
                is_image = True
            else:
                raise HTTPException(status_code=400, detail="Unsupported file type. Use JPG, PNG, or PDF")
        elif notice_text:
            content_text = notice_text.strip()
        else:
            raise HTTPException(status_code=400, detail="Must provide either text or file")
        
        # Load prompt from file
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompt.txt')
        with open(prompt_path, 'r') as f:
            base_prompt = f.read().strip()
        
        # Create message content based on input type
        if is_image:
            message_content = [
                {"type": "text", "text": base_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
            ]
            model = "anthropic/claude-3-haiku"
        else:
            message_content = f"{base_prompt}\n\nImmigration Notice:\n{content_text}"
            model = "anthropic/claude-3-haiku"
        
        openrouter_request = OpenRouterRequest(
            model=model,
            messages=[OpenRouterMessage(role="user", content=message_content)]
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
            
            # Handle both string and list content types
            content = llm_response.choices[0].message.content
            if isinstance(content, list):
                # Extract text from vision API response
                content_str = ""
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        content_str += item.get("text", "")
                content = content_str
            
            try:
                parsed_response = json.loads(content)
                return ExplanationResponse(**parsed_response)
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Invalid response format from LLM")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)