from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from utils.test_data import get_test_data, update_test_data

router = APIRouter(prefix="/api", tags=["reactions"])

# --- REACTIONS ---
@router.get("/reactions/get/{method_id}")
def get_reactions(method_id: str, token: Optional[str] = Header(None)):
    return get_test_data("reactions", {}).get(method_id, {"result": []})


@router.post("/reactions/add/{method_id}/{type}")
async def add_reaction(method_id: str, type: str, reaction: dict, token: str = Header(...)):
    reactions = get_test_data("reactions", {})
    if method_id not in reactions:
        reactions[method_id] = {"result": []}
    reactions[method_id]["result"].append({"type": type, **reaction})
    update_test_data("reactions", reactions)
    return {"status": "ok"} 