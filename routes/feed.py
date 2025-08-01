from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from utils.test_data import get_test_data, update_test_data

router = APIRouter(prefix="/api", tags=["feed"])

# --- FEED ---
@router.get("/feed/all")
def get_feed(token: Optional[str] = Header(None)):
    return {"secuses": True, "result": get_test_data("feed", [])} 