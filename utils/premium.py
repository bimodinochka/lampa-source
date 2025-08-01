import time
from utils.test_data import get_test_data

# --- CONFIG ---
PREMIUM_EXPIRY = 1761683315507  # Реальная дата окончания премиума

# --- PREMIUM CHECK FUNCTION ---
def check_premium_status(token: str) -> dict:
    """Check if user has premium status based on token"""
    print(f"check_premium_status: checking token={token}")

    # Проверяем, есть ли устройство с таким токеном
    device = None
    for dev in get_test_data("devices", []):
        if dev["token"] == token:
            device = dev
            break

    print(f"check_premium_status: found device={device}")

    if not device:
        print(f"check_premium_status: device not found for token={token}")
        return {"valid": False, "premium": False, "message": "Invalid token"}

    # Проверяем премиум статус (время окончания подписки)
    current_time = int(time.time())
    premium_expiry = PREMIUM_EXPIRY

    is_premium = current_time < premium_expiry

    result = {
        "valid": True,
        "premium": is_premium,
        "premium_expiry": premium_expiry,
        "current_time": current_time,
        "device": device
    }

    print(f"check_premium_status: result={result}")
    return result 