from fastapi import APIRouter, Header, HTTPException, Request
from typing import Optional
from utils.test_data import get_test_data, update_test_data
from utils.premium import check_premium_status

router = APIRouter(prefix="/api", tags=["person"])

# --- PERSON LIST ---
@router.get("/person/list")
def get_person_list(token: Optional[str] = Header(None)):
    # Если токен не предоставлен, возвращаем пустой список
    if not token:
        return {
            "secuses": True,
            "results": []
        }

    # Проверяем премиум статус для списка персон
    status = check_premium_status(token)
    if not status["valid"]:
        # Вместо ошибки возвращаем пустой список
        return {
            "secuses": True,
            "results": []
        }
    if not status["premium"]:
        # Вместо ошибки возвращаем пустой список
        return {
            "secuses": True,
            "results": []
        }

    return {
        "secuses": True,
        "results": get_test_data("person_list", [])
    }


# --- PERSON SUBSCRIBE/UNSUBSCRIBE ---
@router.post("/person/subscribe")
async def subscribe_person(request: Request, token: str = Header(...)):
    # Проверяем премиум статус для подписки на персон
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for person subscriptions")

    try:
        # Получаем данные из формы
        form_data = await request.form()
        person_data = form_data.get("person")

        if person_data:
            # Парсим JSON из строки
            import json
            person = json.loads(person_data)
        else:
            # Попробуем получить из JSON body
            body = await request.json()
            person = body.get("person", {})

        person_subscribes = get_test_data("person_subscribes", [])
        person_subscribes.append(person)
        update_test_data("person_subscribes", person_subscribes)
        return {"secuses": True}
    except Exception as e:
        print(f"Error in subscribe_person: {e}")
        return {"secuses": True}


@router.post("/person/unsubscribe")
async def unsubscribe_person(request: Request, token: str = Header(...)):
    try:
        # Получаем данные из формы
        form_data = await request.form()
        person_data = form_data.get("person")

        if person_data:
            # Парсим JSON из строки
            import json
            person = json.loads(person_data)
        else:
            # Попробуем получить из JSON body
            body = await request.json()
            person = body.get("person", {})

        person_subscribes = get_test_data("person_subscribes", [])
        update_test_data("person_subscribes", [p for p in person_subscribes if p.get("id") != person.get("id")])
        return {"secuses": True}
    except Exception as e:
        print(f"Error in unsubscribe_person: {e}")
        return {"secuses": True} 