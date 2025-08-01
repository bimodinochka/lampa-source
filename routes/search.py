from fastapi import APIRouter, Header, HTTPException
from utils.test_data import get_test_data, update_test_data
from utils.premium import check_premium_status

router = APIRouter(prefix="/api", tags=["search"])

# --- SEARCH HISTORY ---
@router.get("/search/history")
def get_search_history(token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    return {"history": get_test_data("search_history", [])}


@router.post("/search/history/add")
async def add_search_history(query: str, token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    history = get_test_data("search_history", [])
    if query not in history:
        history.insert(0, query)
        history = history[:50]  # Ограничиваем 50 элементами
        update_test_data("search_history", history)
    
    return {"status": "ok"}


@router.post("/search/history/clear")
async def clear_search_history(token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    update_test_data("search_history", [])
    return {"status": "ok", "cleared": True} 