from fastapi import APIRouter, Header, HTTPException, Query, Request
from typing import Optional
from utils.test_data import get_test_data, update_test_data
from utils.tmdb import handle_tmdb_request

router = APIRouter(prefix="/api", tags=["collections"])

# --- COLLECTIONS ---
@router.get("/collections/list")
def get_collections(category: Optional[str] = None, token: Optional[str] = Header(None)):
    collections = get_test_data("collections", [])
    if category:
        collections = [c for c in collections if c.get("category") == category]
    return {"results": collections}


@router.get("/collections/liked")
def get_collections_liked(token: str = Header(...)):
    """Get liked collections"""
    return {"results": get_test_data("collections_liked", [])}


@router.get("/collections/view/{url}")
def get_collections_view(url: str, page: int = Query(1), token: str = Header(...)):
    """Get collection view by URL"""
    key = f"{url}_{page}"
    collections_view = get_test_data("collections_view", {})
    if key not in collections_view:
        collections_view[key] = {
            "page": page,
            "results": [
                {"id": 1, "title": f"Collection Item {page}-1", "type": "movie"},
                {"id": 2, "title": f"Collection Item {page}-2", "type": "tv"}
            ],
            "total_pages": 3
        }
        update_test_data("collections_view", collections_view)
    return collections_view[key]


@router.get("/collections/{collection_id}")
async def collections_handler(collection_id: str, request: Request):
    """Handle collections requests"""
    try:
        # Получаем коллекцию из TMDB
        tmdb_path = f"collection/{collection_id}"
        tmdb_params = {}
        
        result = await handle_tmdb_request(tmdb_path, tmdb_params, request)
        
        if "error" in result:
            return {
                "page": 1,
                "results": [],
                "total_pages": 1,
                "total_results": 0
            }
        else:
            return result
            
    except Exception as e:
        return {
            "page": 1,
            "results": [],
            "total_pages": 1,
            "total_results": 0
        } 