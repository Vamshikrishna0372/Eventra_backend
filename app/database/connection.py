import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Robust .env loading
cwd = os.getcwd()
env_paths = [
    os.path.join(cwd, ".env"),
    os.path.join(cwd, "backend", ".env"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
]

for path in env_paths:
    if os.path.exists(path):
        load_dotenv(path)
        break

# Prioritize MONGODB_URL from Atlas
MONGO_URI = os.getenv("MONGODB_URL") or os.getenv("MONGO_URI") or "mongodb://localhost:27017"
DATABASE_NAME = os.getenv("DATABASE_NAME", "eventra")

logger = logging.getLogger("eventra.database")

# Initialize client as None
client = None
db = None
is_connected = False

def get_database():
    global client, db
    if client is None:
        try:
            # Mask password for logging
            masked_uri = MONGO_URI
            if "@" in masked_uri:
                parts = masked_uri.split("@")
                proto_auth = parts[0]
                host_params = parts[1]
                if ":" in proto_auth:
                    proto, auth = proto_auth.split("://")
                    if ":" in auth:
                        user, _pw = auth.split(":")
                        masked_uri = f"{proto}://{user}:****@{host_params}"
            
            logger.info(f"Connecting to MongoDB with URI: {masked_uri}")
            
            # Use a longer timeout for SRV resolution to prevent DNS flakes
            client = AsyncIOMotorClient(MONGO_URI, serverSelectionTimeoutMS=5000, connectTimeoutMS=10000)
            db = client[DATABASE_NAME]
            logger.info(f"MongoDB Client initialized for Database: {DATABASE_NAME}")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB Client: {e}")
            if "DNS" in str(e):
                logger.error("HINT: Your MongoDB Atlas hostname might be incorrect or DNS is blocked. Check cluster identifier in .env")
            return None
    return db

async def verify_connection():
    global is_connected
    database = get_database()
    if database is None:
        is_connected = False
        return False
    try:
        # The ping command is cheap and does not require auth.
        await database.command("ping")
        logger.info("MongoDB connected successfully")
        is_connected = True
        return True
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        is_connected = False
        return False
