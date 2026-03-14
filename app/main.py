from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.routes.auth_routes import router as auth_router
from app.routes.auth_routes import users_router
from app.routes.event_routes import router as event_router
from app.routes.registration_routes import router as registration_router
from app.routes.category_routes import router as category_router
from app.routes.notification_routes import router as notification_router
from app.routes.analytics_routes import router as analytics_router
from app.routes.wishlist_routes import router as wishlist_router
from app.routes.comment_routes import router as comment_routes
from app.routes.settings_routes import router as settings_routes
from app.routes.ticket_routes import router as ticket_router
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.tasks.reminder_tasks import send_event_reminders

scheduler = AsyncIOScheduler()

app = FastAPI(title="Eventra API")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("eventra")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": str(exc.detail), "data": None}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Create a cleaner error message
    error_msgs = []
    for error in errors:
        loc = " -> ".join([str(x) for x in error["loc"][1:]])
        error_msgs.append(f"{loc}: {error['msg']}")
    
    message = "Validation Error: " + ", ".join(error_msgs) if error_msgs else "Invalid request data"
    
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": message, "data": None}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logging.error(f"Internal Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": f"Server Error: {str(exc)}", "data": None}
    )

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(event_router)
app.include_router(registration_router)
app.include_router(category_router)
app.include_router(notification_router)
app.include_router(analytics_router)
app.include_router(wishlist_router)
app.include_router(comment_routes)
app.include_router(settings_routes)
app.include_router(ticket_router)

@app.on_event("startup")
async def startup_db():
    logger.info("Initializing Eventra Database and Services...")
    from app.database.connection import get_database, client
    # Initial setup if required. client is successfully created already.
    # Populate categories if not exists
    db = get_database()
    try:
        # 1. Create Indexes for performance and uniqueness
        await db["users"].create_index("email", unique=True)
        await db["events"].create_index("categoryId")
        await db["registrations"].create_index("userId")
        await db["registrations"].create_index("eventId")
        await db["payments"].create_index("userId")
        await db["wishlists"].create_index([("userId", 1), ("eventId", 1)], unique=True)
        
        # 2. Populate categories if not exists
        count = await db["categories"].count_documents({})
        if count == 0:
            default_categories = [
                {"name": "Technical", "description": "Tech events, Hackathons, Coding"},
                {"name": "Cultural", "description": "Festivals, Music, Dance"},
                {"name": "Sports", "description": "Tournaments, Athletics"},
                {"name": "Workshop", "description": "Hands-on learning sessions"},
                {"name": "Placement", "description": "Seminars, Drives, Career Prep"},
                {"name": "Hackathon", "description": "Intensive coding competitions"}
            ]
            from app.models.category_model import CategoryModel
            for c in default_categories:
                mod = CategoryModel(**c)
                await db["categories"].insert_one(mod.model_dump(by_alias=True, exclude_none=True))
        
        # 3. Populate events if not exists
        event_count = await db["events"].count_documents({})
        if event_count == 0:
            # Re-fetch categories to get real IDs for referencing
            cats = await db["categories"].find().to_list(length=10)
            cat_map = {cat["name"]: str(cat["_id"]) for cat in cats}
            
            sample_events = [
                {
                    "title": "AI & Machine Learning Workshop",
                    "description": "Deep dive into neural networks and data science applications in the modern world.",
                    "date": "2026-04-15",
                    "time": "10:00 AM",
                    "venue": "CSE Seminar Hall",
                    "category": "Technical",
                    "categoryId": cat_map.get("Technical"),
                    "organizerName": "CSE Department",
                    "imageUrl": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&q=80&w=800",
                    "maxParticipants": 100,
                    "registeredCount": 0,
                    "status": "open",
                    "isPaidEvent": False,
                    "price": 0
                },
                {
                    "title": "Web Development Bootcamp",
                    "description": "Learn Full Stack development with React and Node.js in this intensive 3-day bootcamp.",
                    "date": "2026-04-20",
                    "time": "09:00 AM",
                    "venue": "Computer Lab 3",
                    "category": "Technical",
                    "categoryId": cat_map.get("Technical"),
                    "organizerName": "Web Club",
                    "imageUrl": "https://images.unsplash.com/photo-1547658719-da2b51169166?auto=format&fit=crop&q=80&w=800",
                    "maxParticipants": 80,
                    "registeredCount": 0,
                    "status": "open",
                    "isPaidEvent": False,
                    "price": 0
                }
            ]
            from app.models.event_model import EventModel
            for e in sample_events:
                mod = EventModel(**e)
                await db["events"].insert_one(mod.model_dump(by_alias=True, exclude_none=True))

        # 4. Initialize Analytics if empty
        if await db["analytics"].count_documents({}) == 0:
            from app.models.analytics_model import AnalyticsModel
            await db["analytics"].insert_one(AnalyticsModel().model_dump(by_alias=True, exclude_none=True))

        # 5. Initialize Settings if empty
        if await db["settings"].count_documents({}) == 0:
            from app.models.settings_model import SettingsModel
            default_settings = SettingsModel(
                contactEmail="support@eventra.edu",
                supportPhone="+91 9988776655"
            )
            await db["settings"].insert_one(default_settings.model_dump(by_alias=True, exclude_none=True))

    except Exception as e:
        print("Failed system initialization: ", e)

    # Start the scheduler
    try:
        scheduler.add_job(send_event_reminders, 'interval', minutes=60)
        scheduler.start()
        logging.info("Scheduler started successfully")
    except Exception as e:
        logging.error(f"Failed to start scheduler: {e}")

@app.on_event("shutdown")
async def shutdown_scheduler():
    scheduler.shutdown()

@app.get("/")
def read_root():
    return {"success": True, "message": "Welcome to Eventra API"}


