from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from utils.test_data import get_test_data, update_test_data

router = APIRouter(prefix="/api", tags=["plugins"])

# --- PLUGINS ---
@router.get("/plugins/blacklist")
def get_plugins_blacklist(token: str = Header(None)):
    return get_test_data("plugins_blacklist", [])


@router.get("/plugins/all")
def get_plugins_all(token: str = Header(...)):
    return {
        "secuses": True,
        "plugins": get_test_data("plugins", [])
    }


@router.get("/extensions/list")
def get_extensions_list(token: str = Header(...)):
    return {
        "secuses": True,
        "results": get_test_data("extensions", [])
    }


@router.post("/extensions/status")
async def extensions_status(data: dict, token: str = Header(...)):
    return {"status": "ok"}


@router.post("/plugins/status")
async def plugins_status(data: dict, token: str = Header(...)):
    return {"status": "ok"} 