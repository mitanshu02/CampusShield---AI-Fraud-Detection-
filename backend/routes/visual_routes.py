# backend/routes/visual_routes.py

from fastapi import APIRouter
from pydantic import BaseModel
from analyzers.visual_detector import run_visual_detector
import asyncio
from concurrent.futures import ThreadPoolExecutor

router    = APIRouter()
_executor = ThreadPoolExecutor(max_workers=2)

class VisualRequest(BaseModel):
    url: str

@router.post("/analyze-visual")
async def analyze_visual(request: VisualRequest):
    url = request.url.strip()
    if not url.startswith("http://") and \
       not url.startswith("https://"):
        url = "https://" + url

    loop   = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        _executor,
        run_visual_detector,
        url
    )
    return result

# # backend/routes/visual_routes.py

# from fastapi import APIRouter
# from pydantic import BaseModel

# router = APIRouter()

# class VisualRequest(BaseModel):
#     url: str

# @router.post("/analyze-visual")
# async def analyze_visual(request: VisualRequest):
#     return {
#         "visual_similarity": None,
#         "detected_brand":    None,
#         "heatmap_url":       None,
#         "risk":              None,
#         "available":         False,
#         "reason":            "Visual analysis coming soon"
#     }