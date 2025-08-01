from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from utils.test_data import get_test_data, update_test_data

router = APIRouter(prefix="/api", tags=["discussions"])

# --- DISCUSSIONS ---
@router.get("/discuss/get/{method_id}/{page}/{lang}")
def get_discuss(method_id: str, page: int, lang: str, token: Optional[str] = Header(None)):
    key = f"{method_id}_{page}_{lang}"
    return get_test_data("discuss", {}).get(key, {"result": [], "total": 0, "total_pages": 1})


@router.post("/discuss/add")
async def add_discuss(comment: dict, token: str = Header(...)):
    key = f"{comment.get('method_id', 'unknown')}_1_{comment.get('lang', 'ru')}"
    discuss = get_test_data("discuss", {})
    if key not in discuss:
        discuss[key] = {"result": [], "total": 0, "total_pages": 1}
    discuss[key]["result"].append(comment)
    discuss[key]["total"] += 1
    update_test_data("discuss", discuss)
    return {"status": "ok", "comment": comment}


@router.post("/discuss/voite")
async def voite_discuss(data: dict, token: str = Header(...)):
    return {"status": "ok", "voted": True} 