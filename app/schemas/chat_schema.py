from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's message to the AI assistant")

class ChatResponse(BaseModel):
    reply: str = Field(..., description="The AI assistant's generated response")
