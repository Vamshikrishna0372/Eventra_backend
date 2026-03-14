from fastapi import HTTPException
from app.database.connection import get_database
from app.models.comment_model import CommentModel
from bson import ObjectId

class CommentService:
    @staticmethod
    async def add_comment(comment_data: dict, current_user: dict):
        db = get_database()
        
        # Add comment
        new_comment = CommentModel(
            eventId=comment_data["eventId"],
            userId=current_user["id"],
            text=comment_data["text"]
        )
        
        res = await db["event_comments"].insert_one(new_comment.model_dump(by_alias=True, exclude_none=True))
        
        # Get full info
        created = await db["event_comments"].find_one({"_id": res.inserted_id})
        
        return {
            "id": str(created["_id"]),
            "eventId": created["eventId"],
            "userId": created["userId"],
            "userName": current_user["name"],
            "userPicture": current_user.get("picture", ""),
            "text": created["text"],
            "createdAt": created["createdAt"].isoformat()
        }

    @staticmethod
    async def get_event_comments(event_id: str):
        db = get_database()
        cursor = db["event_comments"].find({"eventId": event_id}).sort("createdAt", -1).limit(50)
        comments = await cursor.to_list(50)
        
        results = []
        for c in comments:
            user = await db["users"].find_one({"_id": ObjectId(c["userId"])})
            if user:
                results.append({
                    "id": str(c["_id"]),
                    "eventId": c["eventId"],
                    "userId": c["userId"],
                    "userName": user["name"],
                    "userPicture": user.get("profileImage", ""),
                    "text": c["text"],
                    "createdAt": c["createdAt"].isoformat()
                })
        return results

    @staticmethod
    async def delete_comment(comment_id: str, current_user: dict):
        db = get_database()
        comment = await db["event_comments"].find_one({"_id": ObjectId(comment_id)})
        if not comment:
            raise HTTPException(status_code=404, detail="Comment not found")
            
        if comment["userId"] != current_user["id"] and current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Not authorized")
            
        await db["event_comments"].delete_one({"_id": ObjectId(comment_id)})
        return {"message": "Comment deleted successfully"}
