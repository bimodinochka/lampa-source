from fastapi import APIRouter, Header, HTTPException, Request
from utils.test_data import get_test_data, update_test_data
from utils.premium import check_premium_status

router = APIRouter(prefix="/api", tags=["notifications"])

# --- NOTIFICATIONS ---
@router.get("/notifications/all")
def get_notifications(token: str = Header(...)):
    # Проверяем премиум статус для уведомлений
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for notifications")

    return {
        "secuses": True,
        "notifications": get_test_data("notifications", [])
    }


@router.post("/notifications/add")
async def add_notification(request: Request, token: str = Header(...)):
    # Проверяем премиум статус для уведомлений
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for notifications")

    try:
        # Получаем данные из формы
        form_data = await request.form()
        voice = form_data.get("voice", "")
        data_str = form_data.get("data", "{}")
        episode = form_data.get("episode", "")
        season = form_data.get("season", "")

        # Парсим JSON из строки data
        import json
        try:
            data = json.loads(data_str)
        except:
            data = {}

        # Создаем новое уведомление
        import time
        new_notification = {
            "id": int(time.time() * 1000),  # Генерируем уникальный ID
            "cid": 148608,
            "voice": voice,
            "card_id": str(data.get("id", "")),
            "card": json.dumps(data),  # Сохраняем полные данные как JSON строку
            "status": 1,
            "time": int(time.time() * 1000),
            "time_update": int(time.time() * 1000),
            "episode": int(episode) if episode.isdigit() else 0,
            "season": int(season) if season.isdigit() else 0,
            "profile": 153918
        }

        notifications = get_test_data("notifications", [])
        notifications.append(new_notification)
        update_test_data("notifications", notifications)

        return {"secuses": True}
    except Exception as e:
        print(f"Error in add_notification: {e}")
        return {"secuses": True} 