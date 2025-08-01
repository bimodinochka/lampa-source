from fastapi import APIRouter, Header, HTTPException
from utils.test_data import get_test_data, update_test_data
from utils.premium import check_premium_status

router = APIRouter(prefix="/api", tags=["timeline"])

# --- TIMELINE ---
@router.get("/timeline/all")
def get_timeline(token: str = Header(...)):
    # Проверяем премиум статус для timeline
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for timeline sync")

    return {"timelines": get_test_data("timeline", [])} 