from pydantic import BaseModel, Field

class CommentCreate(BaseModel):
    eventId: str
    text: str = Field(..., min_length=1, max_length=1000)

class CommentResponse(BaseModel):
    id: str
    eventId: str
    userId: str
    userName: str
    userPicture: str
    text: str
    createdAt: str
