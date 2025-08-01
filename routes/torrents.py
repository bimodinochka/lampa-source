from fastapi import APIRouter, Header, HTTPException
from utils.test_data import get_test_data, update_test_data
from utils.premium import check_premium_status

router = APIRouter(prefix="/api", tags=["torrents"])

# --- TORRENTS ---
@router.get("/torrents/all")
def get_torrents(token: str = Header(...)):
    # Проверяем премиум статус для торрентов
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for torrents")

    return {"torrents": get_test_data("torrents", [])}


@router.post("/torrents/add")
async def add_torrent(torrent: dict, token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for torrents")

    torrents = get_test_data("torrents", [])
    torrents.append(torrent)
    update_test_data("torrents", torrents)
    return {"status": "ok", "torrent": torrent}


@router.post("/torrents/remove")
async def remove_torrent(torrent_id: str, token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for torrents")

    torrents = get_test_data("torrents", [])
    torrents = [t for t in torrents if t.get("id") != torrent_id]
    update_test_data("torrents", torrents)
    return {"status": "ok", "removed": True} 