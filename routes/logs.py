from fastapi import APIRouter, Header, HTTPException
from utils.test_data import get_test_data, update_test_data

router = APIRouter(prefix="/api", tags=["logs"])

# --- LOGS ---
@router.post("/lampa/logs/write")
async def write_log(log: dict, token: str = Header(...)):
    logs = get_test_data("logs", [])
    logs.append(log)
    update_test_data("logs", logs)
    return {"status": "ok"} 