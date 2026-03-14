from fastapi import APIRouter, Depends
from app.schemas.comment_schema import CommentCreate, CommentResponse
from app.services.comment_service import CommentService
from app.middleware.auth_middleware import get_current_user

router = APIRouter(prefix="/api/comments", tags=["Comments"])

@router.post("/", response_model=dict)
async def add_comment(comment_data: CommentCreate, current_user: dict = Depends(get_current_user)):
    comment = await CommentService.add_comment(comment_data.model_dump(), current_user)
    return {"success": True, "message": "Comment added", "data": comment}

@router.get("/event/{event_id}")
async def get_event_comments(event_id: str):
    comments = await CommentService.get_event_comments(event_id)
    return {"success": True, "message": "Comments retrieved", "data": comments}

@router.delete("/{comment_id}")
async def delete_comment(comment_id: str, current_user: dict = Depends(get_current_user)):
    result = await CommentService.delete_comment(comment_id, current_user)
    return {"success": True, "message": "Comment deleted", "data": result}
