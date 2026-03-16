from fastapi import APIRouter, Depends
from app.database.connection import get_database
from app.schemas.category_schema import CategoryCreate
from app.models.category_model import CategoryModel
from app.middleware.role_middleware import require_admin
from bson import ObjectId

router = APIRouter(prefix="/api/categories", tags=["Categories"])

@router.get("")
async def get_categories():
    db = get_database()
    try:
        categories = await db["categories"].find().to_list(100)
        for cat in categories:
            cat["id"] = str(cat.pop("_id"))
            # Get count of events in this category
            count = await db["events"].count_documents({"category": {"$regex": f"^{cat['name']}$", "$options": "i"}})
            cat["eventCount"] = count
        return {"success": True, "message": "Categories retrieved", "data": categories}
    except Exception as e:
        import logging
        logging.error(f"Error fetching categories: {e}")
        return {"success": True, "message": "Currently unavailable", "data": []}

@router.post("", dependencies=[Depends(require_admin)])
async def create_category(cat_data: CategoryCreate):
    db = get_database()
    new_cat = CategoryModel(**cat_data.model_dump())
    res = await db["categories"].insert_one(new_cat.model_dump(by_alias=True, exclude_none=True))
    created = await db["categories"].find_one({"_id": res.inserted_id})
    created["id"] = str(created.pop("_id"))
    return {"success": True, "message": "Category created", "data": created}

@router.delete("/{category_id}", dependencies=[Depends(require_admin)])
async def delete_category(category_id: str):
    db = get_database()
    try:
        res = await db["categories"].delete_one({"_id": ObjectId(category_id)})
        if res.deleted_count == 0:
            return {"success": False, "message": "Category not found"}
        return {"success": True, "message": "Category deleted"}
    except:
        return {"success": False, "message": "Invalid ID"}
@router.put("/{category_id}", dependencies=[Depends(require_admin)])
async def update_category(category_id: str, cat_data: CategoryCreate):
    db = get_database()
    try:
        res = await db["categories"].update_one(
            {"_id": ObjectId(category_id)},
            {"$set": cat_data.model_dump()}
        )
        if res.matched_count == 0:
            return {"success": False, "message": "Category not found"}
        
        updated = await db["categories"].find_one({"_id": ObjectId(category_id)})
        updated["id"] = str(updated.pop("_id"))
        return {"success": True, "message": "Category updated", "data": updated}
    except:
        return {"success": False, "message": "Invalid ID or update failed"}
