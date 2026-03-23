# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
##### CHANGED FROM HERE 
# backend/main.py

import asyncio
import sys

# fix for Windows Playwright async compatibility
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

###### CHANGED UPTO HERE     

from fastapi import FastAPI

from routes.url_routes import router as url_router

try:
    from routes.visual_routes import router as visual_router
except ImportError:
    visual_router = None

try:
    from routes.payment_routes import router as payment_router
except ImportError:
    payment_router = None

try:
    from routes.scan_routes import router as scan_router
except ImportError:
    scan_router = None

app = FastAPI(title="CampusShield API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("generated", exist_ok=True)
app.mount("/generated", StaticFiles(directory="generated"), name="generated")

app.include_router(url_router, prefix="/api")

if visual_router:
    app.include_router(visual_router, prefix="/api")
if payment_router:
    app.include_router(payment_router, prefix="/api")
if scan_router:
    app.include_router(scan_router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "CampusShield backend running"}
