from fastapi import APIRouter, Depends
from app.database.connection import get_database
from app.schemas.category_schema import CategoryCreate
from app.models.category_model import CategoryModel
from app.middleware.role_middleware import require_admin
from bson import ObjectId

router = APIRouter(prefix="/api/categories", tags=["Categories"])

@router.get("/")
async def get_categories():
    db = get_database()
    categories = await db["categories"].find().to_list(100)
    for cat in categories:
        cat["id"] = str(cat.pop("_id"))
    return {"success": True, "message": "Categories retrieved", "data": categories}

@router.post("/", dependencies=[Depends(require_admin)])
async def create_category(cat_data: CategoryCreate):
    db = get_database()
    new_cat = CategoryModel(**cat_data.model_dump())
    res = await db["categories"].insert_one(new_cat.model_dump(by_alias=True, exclude_none=True))
    created = await db["categories"].find_one({"_id": res.inserted_id})
    created["id"] = str(created.pop("_id"))
    return {"success": True, "message": "Category created", "data": created}
