import logging
from app.main import app

# Explicitly expose app for uvicorn main:app
# This solves the "Could not import module 'main'" error
# when Render attempts to run uvicorn main:app from the backend/ directory

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
