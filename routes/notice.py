from fastapi import APIRouter, Header, HTTPException
from utils.test_data import get_test_data, update_test_data

router = APIRouter(prefix="/api", tags=["notice"])

# --- NOTICE ---
@router.get("/notice/all")
def get_notice_all(token: str = Header(...)):
    return {"notice": get_test_data("notice", [])} 