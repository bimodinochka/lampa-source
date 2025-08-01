from fastapi import APIRouter, Header, HTTPException
from typing import Optional
from utils.test_data import get_test_data, update_test_data
from utils.premium import check_premium_status

router = APIRouter(prefix="/api", tags=["user"])

# --- USERS ---
@router.get("/users/get")
def get_users(token: Optional[str] = Header(None)):
    print(f"Users/get requested with token: {token}")

    # Если токен не предоставлен, возвращаем базовые данные
    if not token:
        user_data = get_test_data("user", {})
        response = {
            "user": user_data
        }
        print(f"Returning user data (no token): {response}")
        return response

    # Проверяем статус пользователя
    status = check_premium_status(token)

    if not status["valid"]:
        # Вместо ошибки возвращаем базовые данные
        user_data = get_test_data("user", {})
        response = {
            "user": user_data
        }
        print(f"Returning user data (invalid token): {response}")
        return response

    # Возвращаем данные в том же формате, что и официальный сервер
    user_data = get_test_data("user", {})
    response = {
        "user": user_data
    }
    print(f"Returning user data: {response}")
    return response


@router.post("/users/backup/import")
async def users_backup_import(data: dict, token: str = Header(...)):
    return {"status": "ok", "imported": True} 