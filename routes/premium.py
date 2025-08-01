from fastapi import APIRouter, Header, HTTPException
import time

from utils.test_data import get_test_data, update_test_data
from utils.premium import check_premium_status, PREMIUM_EXPIRY

router = APIRouter(prefix="/api", tags=["premium"])

# --- PREMIUM STATUS ---
@router.get("/premium/status")
def get_premium_status(token: str = Header(...)):
    """Check premium status of user"""
    status = check_premium_status(token)
    return {
        "valid": status["valid"],
        "premium": status["premium"],
        "premium_expiry": status["premium_expiry"],
        "current_time": status["current_time"],
        "days_remaining": max(0, (status["premium_expiry"] - status["current_time"]) // 86400)
    }


@router.get("/premium/status/debug")
def get_premium_status_debug():
    """Debug endpoint to check premium status without token"""
    return {
        "devices": get_test_data("devices", []),
        "current_time": int(time.time()),
        "premium_expiry": PREMIUM_EXPIRY,
        "is_premium": int(time.time()) < PREMIUM_EXPIRY
    }


@router.get("/premium/check")
def check_premium_endpoint(token: str = Header(...)):
    """Check premium status in simple format"""
    status = check_premium_status(token)

    if not status["valid"]:
        return {"premium": False, "error": "Invalid token"}

    return {
        "premium": status["premium"],
        "expiry": status["premium_expiry"],
        "days_remaining": max(0, (status["premium_expiry"] - status["current_time"]) // 86400)
    }


@router.get("/premium/status/simple")
def get_premium_status_simple():
    """Simple premium status check (no token required)"""
    current_time = int(time.time())
    premium_expiry = PREMIUM_EXPIRY
    is_premium = current_time < premium_expiry

    return {
        "premium": is_premium,
        "premium_value": 1 if is_premium else 0,  # Для совместимости с приложением
        "expiry": premium_expiry,
        "current_time": current_time,
        "days_remaining": max(0, (premium_expiry - current_time) // 86400)
    }


@router.get("/premium/check/app")
def check_premium_for_app():
    """Premium check endpoint specifically for the app"""
    current_time = int(time.time())
    premium_expiry = PREMIUM_EXPIRY
    is_premium = current_time < premium_expiry

    return {
        "status": "ok",
        "premium": is_premium,
        "premium_value": 1 if is_premium else 0,
        "expiry": premium_expiry,
        "current_time": current_time,
        "message": "Premium subscription is active until 2025" if is_premium else "Premium subscription expired"
    } 