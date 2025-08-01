from fastapi import APIRouter, Header, HTTPException, Query
from typing import Optional
from utils.test_data import get_test_data, update_test_data

router = APIRouter(prefix="/api", tags=["ad"])

# --- AD/ADV/STAT ---
@router.get("/ad/stat")
def ad_stat(platform: str = Query(...), type: str = Query(...), method: str = Query(None), name: str = Query(None)):
    ad_stat = get_test_data("ad_stat", [])
    ad_stat.append({"platform": platform, "type": type, "method": method, "name": name})
    update_test_data("ad_stat", ad_stat)
    return {"status": "ok"}


@router.get("/ad/all")
def ad_all(token: str = Header(None)):
    return get_test_data("ad_all", [])


@router.get("/ad/vast")
def ad_vast(token: str = Header(None)):
    return get_test_data("ad_vast", {})


@router.post("/adv/log")
async def adv_log(data: dict, token: str = Header(None)):
    adv_log = get_test_data("adv_log", [])
    adv_log.append(data)
    update_test_data("adv_log", adv_log)
    return {"status": "ok"}


@router.post("/payment/event_prime")
async def payment_event_prime(data: dict, token: str = Header(None)):
    event_prime = get_test_data("event_prime", [])
    event_prime.append(data)
    update_test_data("event_prime", event_prime)
    return {"status": "ok"} 