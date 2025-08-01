from fastapi import APIRouter, Header, HTTPException
from utils.test_data import get_test_data, update_test_data
from utils.premium import check_premium_status

router = APIRouter(prefix="/api", tags=["account"])

# --- ACCOUNT STATUS ---
@router.get("/account/status")
def get_account_status(token: str = Header(...)):
    """Get account status in format expected by Lampa"""
    status = check_premium_status(token)

    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")

    # Возвращаем данные в том же формате, что и официальный сервер
    account_data = get_test_data("account", {})
    return {
        "secuses": True,
        "email": account_data.get("email", "igor.tonin@inbox.ru"),
        "id": account_data.get("id", 148608),
        "token": token,
        "profile": account_data.get("profile", {
            "id": 153918,
            "cid": 148608,
            "name": "Общий",
            "main": 1,
            "icon": "l_1"
        })
    } 