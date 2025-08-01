from fastapi import APIRouter, Header, HTTPException, Query
from typing import Optional
from utils.test_data import get_test_data, update_test_data
from utils.premium import check_premium_status

router = APIRouter(prefix="/api", tags=["bookmarks"])

# --- BOOKMARKS ---
@router.get("/bookmarks/all")
def get_bookmarks(token: str = Header(...), category: Optional[str] = Query(None)):
    # Проверяем премиум статус для синхронизации закладок
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for bookmarks sync")

    # Добавляем поддержку категорий
    bookmarks = get_test_data("bookmarks", [])
    
    if category:
        bookmarks = [b for b in bookmarks if b.get("category") == category]
    
    return {"bookmarks": bookmarks}


@router.get("/bookmarks/categories")
def get_bookmark_categories(token: str = Header(...)):
    # Новый эндпоинт для получения категорий
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for bookmarks sync")

    return {
        "categories": ["book", "like", "wath", "viewed", "scheduled", "continued", "thrown"]
    }


@router.post("/bookmarks/add")
async def add_bookmark(bookmark: dict, token: str = Header(...)):
    # Проверяем премиум статус для синхронизации закладок
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for bookmarks sync")

    bookmarks = get_test_data("bookmarks", [])
    bookmarks.append(bookmark)
    update_test_data("bookmarks", bookmarks)
    return {"status": "ok", "bookmark": bookmark}


@router.post("/bookmarks/clear")
async def clear_bookmarks(data: dict, token: str = Header(...)):
    return {"status": "ok", "cleared": True} 