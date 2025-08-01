from fastapi import APIRouter, Header, HTTPException, Query
from utils.test_data import get_test_data, update_test_data

router = APIRouter(prefix="/api", tags=["metric"])

# --- METRIC ---
@router.get("/metric/unic")
def get_metric_unic(platform: str = Query(...), uid: str = Query(...)):
    return {"status": "ok", "metric": "recorded"} 