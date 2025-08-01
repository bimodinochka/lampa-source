from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from utils.test_data import get_test_data, update_test_data

router = APIRouter(prefix="/api", tags=["trailers"])

# --- TRAILERS ---
@router.get("/trailers/short/trailers/{type}")
def get_trailers(type: str, token: Optional[str] = Header(None)):
    return get_test_data("trailers", {}).get(type, {"results": []})


@router.get("/trailers/get/trailers/{type}/{page}")
def get_trailers_with_page(type: str, page: int, token: str = Header(...)):
    """Get trailers with pagination"""
    return {
        "secuses": True,
        "page": page,
        "total_pages": 22,
        "results": get_test_data("trailers", {}).get(f"{type}_{page}", [])
    } 