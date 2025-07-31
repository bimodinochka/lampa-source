from fastapi import FastAPI, Request, Header, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import Optional
import json
import os
import time
from datetime import datetime

app = FastAPI(title="Cube API Replacement", version="1.0")

# --- CORS MIDDLEWARE ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене лучше указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- STATIC FILES ---
# Создаем папку для статических файлов если её нет
os.makedirs("static/img/other", exist_ok=True)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- CONFIG ---
TMDB_API_KEY = "4ef0d7355d9ffb5151e987764708ce96"
TMDB_API_VERSION = "3"  # Можно изменить на "4" для новой версии API
TMDB_BASE_URL = f"https://api.themoviedb.org/{TMDB_API_VERSION}"
PREMIUM_EXPIRY = 1761683315507  # Реальная дата окончания премиума


# --- LOAD TEST DATA ---
def load_test_data():
    """Load test data from JSON file"""
    try:
        with open("test_data.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Warning: test_data.json not found, using empty data")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error loading test_data.json: {e}")
        return {}


def get_test_data(key, default=None):
    """Safely get test data with fallback"""
    return TEST_DATA.get(key, default if default is not None else [])


def save_test_data():
    """Save test data back to JSON file"""
    try:
        with open("test_data.json", "w", encoding="utf-8") as f:
            json.dump(TEST_DATA, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving test_data.json: {e}")


def update_test_data(key, value):
    """Update test data and save to file"""
    TEST_DATA[key] = value
    save_test_data()


TEST_DATA = load_test_data()


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


# --- PREMIUM STATUS ---
@app.get("/api/premium/status")
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


@app.get("/api/premium/status/debug")
def get_premium_status_debug():
    """Debug endpoint to check premium status without token"""
    return {
        "devices": get_test_data("devices", []),
        "current_time": int(time.time()),
        "premium_expiry": PREMIUM_EXPIRY,
        "is_premium": int(time.time()) < PREMIUM_EXPIRY
    }


@app.get("/api/account/status")
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


@app.get("/api/premium/check")
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


@app.get("/api/premium/status/simple")
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


@app.get("/api/premium/check/app")
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


# --- USER PROFILE ---
@app.get("/api/profiles/all")
def get_profiles(token: str = Header(...)):
    print(f"Profiles requested with token: {token}")
    response = {
        "secuses": True,
        "profiles": get_test_data("profiles", [])
    }
    print(f"Returning profiles: {response}")
    return response


@app.post("/api/device/add")
async def add_device(request: Request):
    """Add device using 6-digit code from website"""
    try:
        # Получаем данные из формы
        form_data = await request.form()
        code = form_data.get("code")

        if not code:
            # Попробуем получить из JSON
            body = await request.json()
            code = body.get("code")

        if not code:
            raise HTTPException(status_code=400, detail="Code parameter required")

        print(f"Received code: {code}")
        code_str = str(code)

        device_codes = get_test_data("device_codes", {})
        if code_str in device_codes:
            device_data = device_codes[code_str]

            # Add device to devices list
            devices = get_test_data("devices", [])
            device_id = len(devices) + 1
            new_device = {
                "id": device_id,
                "name": device_data["name"],
                "platform": device_data["platform"],
                "token": device_data["token"]
            }
            devices.append(new_device)
            update_test_data("devices", devices)

            response_data = {
                "secuses": True,
                "email": "igor.tonin@inbox.ru",
                "id": 148608,
                "token": device_data["token"],
                "profile": {
                    "id": 153918,
                    "cid": 148608,
                    "name": "Общий",
                    "main": 1,
                    "icon": "l_1"
                }
            }

            print(f"Returning response: {response_data}")
            return response_data
        else:
            print(f"Invalid code: {code_str}")
            raise HTTPException(status_code=400, detail="Invalid device code")
    except Exception as e:
        print(f"Error in add_device: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# --- BOOKMARKS ---
@app.get("/api/bookmarks/all")
def get_bookmarks(token: str = Header(...), category: Optional[str] = Query(None)):
    # Проверяем премиум статус для синхронизации закладок
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for bookmarks sync")

    # Добавляем поддержку категорий
    bookmarks = get_test_data("bookmarks", [])
    
    if category:
        bookmarks = [b for b in bookmarks if b.get("category") == category]
    
    return {"bookmarks": bookmarks}


@app.get("/api/bookmarks/categories")
def get_bookmark_categories(token: str = Header(...)):
    # Новый эндпоинт для получения категорий
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for bookmarks sync")

    return {
        "categories": ["book", "like", "wath", "viewed", "scheduled", "continued", "thrown"]
    }


@app.post("/api/bookmarks/add")
async def add_bookmark(bookmark: dict, token: str = Header(...)):
    # Проверяем премиум статус для синхронизации закладок
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for bookmarks sync")

    bookmarks = get_test_data("bookmarks", [])
    bookmarks.append(bookmark)
    update_test_data("bookmarks", bookmarks)
    return {"status": "ok", "bookmark": bookmark}


@app.post("/api/bookmarks/clear")
async def clear_bookmarks(data: dict, token: str = Header(...)):
    return {"status": "ok", "cleared": True}


# --- NOTIFICATIONS ---
@app.get("/api/notifications/all")
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


@app.post("/api/notifications/add")
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


# --- LOGS ---
@app.post("/api/lampa/logs/write")
async def write_log(log: dict, token: str = Header(...)):
    logs = get_test_data("logs", [])
    logs.append(log)
    update_test_data("logs", logs)
    return {"status": "ok"}


# --- PERSON SUBSCRIBE/UNSUBSCRIBE ---
@app.post("/api/person/subscribe")
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


@app.post("/api/person/unsubscribe")
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


# --- DISCUSSIONS ---
@app.get("/api/discuss/get/{method_id}/{page}/{lang}")
def get_discuss(method_id: str, page: int, lang: str, token: Optional[str] = Header(None)):
    key = f"{method_id}_{page}_{lang}"
    return get_test_data("discuss", {}).get(key, {"result": [], "total": 0, "total_pages": 1})


@app.post("/api/discuss/add")
async def add_discuss(comment: dict, token: str = Header(...)):
    key = f"{comment.get('method_id', 'unknown')}_1_{comment.get('lang', 'ru')}"
    discuss = get_test_data("discuss", {})
    if key not in discuss:
        discuss[key] = {"result": [], "total": 0, "total_pages": 1}
    discuss[key]["result"].append(comment)
    discuss[key]["total"] += 1
    update_test_data("discuss", discuss)
    return {"status": "ok", "comment": comment}


@app.post("/api/discuss/voite")
async def voite_discuss(data: dict, token: str = Header(...)):
    return {"status": "ok", "voted": True}


# --- REACTIONS ---
@app.get("/api/reactions/get/{method_id}")
def get_reactions(method_id: str, token: Optional[str] = Header(None)):
    return get_test_data("reactions", {}).get(method_id, {"result": []})


@app.post("/api/reactions/add/{method_id}/{type}")
async def add_reaction(method_id: str, type: str, reaction: dict, token: str = Header(...)):
    reactions = get_test_data("reactions", {})
    if method_id not in reactions:
        reactions[method_id] = {"result": []}
    reactions[method_id]["result"].append({"type": type, **reaction})
    update_test_data("reactions", reactions)
    return {"status": "ok"}


# --- COLLECTIONS ---
@app.get("/api/collections/list")
def get_collections(category: Optional[str] = None, token: Optional[str] = Header(None)):
    collections = get_test_data("collections", [])
    if category:
        collections = [c for c in collections if c.get("category") == category]
    return {"results": collections}


# --- TRAILERS ---
@app.get("/api/trailers/short/trailers/{type}")
def get_trailers(type: str, token: Optional[str] = Header(None)):
    return get_test_data("trailers", {}).get(type, {"results": []})


@app.get("/api/trailers/get/trailers/{type}/{page}")
def get_trailers_with_page(type: str, page: int, token: str = Header(...)):
    """Get trailers with pagination"""
    return {
        "secuses": True,
        "page": page,
        "total_pages": 22,
        "results": get_test_data("trailers", {}).get(f"{type}_{page}", [])
    }


# --- TIMELINE ---
@app.get("/api/timeline/all")
def get_timeline(token: str = Header(...)):
    # Проверяем премиум статус для timeline
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for timeline sync")

    return {"timelines": get_test_data("timeline", [])}


# --- FEED ---
@app.get("/api/feed/all")
def get_feed(token: Optional[str] = Header(None)):
    return {"secuses": True, "result": get_test_data("feed", [])}


# --- AD/ADV/STAT ---
@app.get("/api/ad/stat")
def ad_stat(platform: str = Query(...), type: str = Query(...), method: str = Query(None), name: str = Query(None)):
    ad_stat = get_test_data("ad_stat", [])
    ad_stat.append({"platform": platform, "type": type, "method": method, "name": name})
    update_test_data("ad_stat", ad_stat)
    return {"status": "ok"}


@app.get("/api/ad/all")
def ad_all(token: str = Header(None)):
    return get_test_data("ad_all", [])


@app.get("/api/ad/vast")
def ad_vast(token: str = Header(None)):
    return get_test_data("ad_vast", {})


@app.post("/api/adv/log")
async def adv_log(data: dict, token: str = Header(None)):
    adv_log = get_test_data("adv_log", [])
    adv_log.append(data)
    update_test_data("adv_log", adv_log)
    return {"status": "ok"}


@app.post("/api/payment/event_prime")
async def payment_event_prime(data: dict, token: str = Header(None)):
    event_prime = get_test_data("event_prime", [])
    event_prime.append(data)
    update_test_data("event_prime", event_prime)
    return {"status": "ok"}


# --- AI ---
@app.get("/api/ai/generate/facts/{card_id}/{card_type}")
async def ai_generate_facts(card_id: str, card_type: str, token: str = Header(None)):
    """Generate AI facts for a card"""
    if not check_premium_status(token):
        raise HTTPException(status_code=403, detail="Premium required")
    
    # Get AI facts from test data
    key = f"{card_id}_{card_type}"
    ai_facts = get_test_data("ai_facts", {})
    card_facts = ai_facts.get(key, {})
    
    if card_facts and "results" in card_facts:
        return {"facts": [fact["fact"] for fact in card_facts["results"]]}
    
    # Fallback to mock data if not found
    return {
        "facts": [
            f"AI generated fact 1 for {card_type} {card_id}",
            f"AI generated fact 2 for {card_type} {card_id}",
            f"AI generated fact 3 for {card_type} {card_id}"
        ]
    }

@app.get("/api/ai/generate/recommend/{card_id}/{card_type}")
async def ai_generate_recommendations(card_id: str, card_type: str, token: str = Header(None)):
    """Generate AI recommendations for a card"""
    if not check_premium_status(token):
        raise HTTPException(status_code=403, detail="Premium required")
    
    # Get AI recommendations from test data
    key = f"{card_id}_{card_type}"
    ai_recommend = get_test_data("ai_recommend", {})
    card_recommendations = ai_recommend.get(key, {})
    
    if card_recommendations and "results" in card_recommendations:
        return {"recommendations": card_recommendations["results"]}
    
    # Fallback to mock data if not found
    return {
        "recommendations": [
            {"id": "rec1", "title": f"Recommended {card_type} 1", "type": card_type},
            {"id": "rec2", "title": f"Recommended {card_type} 2", "type": card_type},
            {"id": "rec3", "title": f"Recommended {card_type} 3", "type": card_type}
        ]
    }

@app.get("/api/ai/search/{query}")
async def ai_search(query: str, token: str = Header(None)):
    """AI search functionality"""
    if not check_premium_status(token):
        raise HTTPException(status_code=403, detail="Premium required")
    
    # Get AI search results from test data
    ai_search_data = get_test_data("ai_search", {})
    search_results = ai_search_data.get(query, {})
    
    if search_results and "results" in search_results:
        return {"results": search_results["results"]}
    
    # Fallback to mock data if not found
    return {
        "results": [
            {"id": "ai1", "title": f"AI result for: {query}", "type": "movie"},
            {"id": "ai2", "title": f"AI result for: {query}", "type": "tv"},
            {"id": "ai3", "title": f"AI result for: {query}", "type": "anime"}
        ]
    }


# --- PLUGINS ---
@app.get("/api/plugins/blacklist")
def get_plugins_blacklist(token: str = Header(None)):
    return get_test_data("plugins_blacklist", [])


@app.get("/api/plugins/all")
def get_plugins_all(token: str = Header(...)):
    return {
        "secuses": True,
        "plugins": get_test_data("plugins", [])
    }


@app.get("/api/extensions/list")
def get_extensions_list(token: str = Header(...)):
    return {
        "secuses": True,
        "results": get_test_data("extensions", [])
    }


@app.post("/api/extensions/status")
async def extensions_status(data: dict, token: str = Header(...)):
    return {"status": "ok"}


@app.post("/api/plugins/status")
async def plugins_status(data: dict, token: str = Header(...)):
    return {"status": "ok"}


# --- USERS ---
@app.get("/api/users/get")
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


@app.post("/api/users/backup/import")
async def users_backup_import(data: dict, token: str = Header(...)):
    return {"status": "ok", "imported": True}


# --- NOTICE ---
@app.get("/api/notice/all")
def get_notice_all(token: str = Header(...)):
    return {"notice": get_test_data("notice", [])}


# --- TORRENTS ---
@app.get("/api/torrents/all")
def get_torrents(token: str = Header(...)):
    # Проверяем премиум статус для торрентов
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    if not status["premium"]:
        raise HTTPException(status_code=402, detail="Premium required for torrents")

    return {"torrents": get_test_data("torrents", [])}


@app.post("/api/torrents/add")
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


@app.post("/api/torrents/remove")
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


# --- PERSON LIST ---
@app.get("/api/person/list")
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


# --- SEARCH HISTORY ---
@app.get("/api/search/history")
def get_search_history(token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    return {"history": get_test_data("search_history", [])}


@app.post("/api/search/history/add")
async def add_search_history(query: str, token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    history = get_test_data("search_history", [])
    if query not in history:
        history.insert(0, query)
        history = history[:50]  # Ограничиваем 50 элементами
        update_test_data("search_history", history)
    
    return {"status": "ok"}


@app.post("/api/search/history/clear")
async def clear_search_history(token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    update_test_data("search_history", [])
    return {"status": "ok", "cleared": True}


# --- METRIC ---
@app.get("/api/metric/unic")
def get_metric_unic(platform: str = Query(...), uid: str = Query(...)):
    return {"status": "ok", "metric": "recorded"}


# --- SETTINGS ---
@app.get("/api/settings/components")
def get_settings_components(token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    return {"components": get_test_data("settings_components", [])}


@app.post("/api/settings/components/add")
async def add_settings_component(component: dict, token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    components = get_test_data("settings_components", [])
    components.append(component)
    update_test_data("settings_components", components)
    return {"status": "ok", "component": component}


@app.get("/api/settings/params")
def get_settings_params(token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    return {"params": get_test_data("settings_params", [])}


@app.post("/api/settings/params/add")
async def add_settings_param(param: dict, token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    params = get_test_data("settings_params", [])
    params.append(param)
    update_test_data("settings_params", params)
    return {"status": "ok", "param": param}


# --- IPTV ---
@app.get("/api/iptv/channels")
def get_iptv_channels(token: str = Header(None)):
    iptv_data = get_test_data("iptv", {})
    return {"channels": iptv_data.get("channels", [])}


@app.get("/api/iptv/playlists")
def get_iptv_playlists(token: str = Header(None)):
    iptv_data = get_test_data("iptv", {})
    return {"playlists": iptv_data.get("playlists", [])}


# --- NEW ENDPOINTS FROM ITERATIVE SEARCH ---

@app.get("/api/checker")
def get_checker():
    """Mirror checker endpoint"""
    return get_test_data("checker", {})


@app.get("/api/reset")
def reset_account():
    """Reset account data - for development purposes"""
    return get_test_data("reset", {
        "status": "ok",
        "message": "Account reset. Please clear localStorage and reload page.",
        "clear_storage": [
            "account",
            "account_user",
            "account_email",
            "account_notice",
            "account_bookmarks"
        ]
    })


@app.get("/plugin/sport")
async def get_sport_plugin():
    """Serve sport plugin"""
    return JSONResponse(
        content="// Sport plugin stub",
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=3600"}
    )


@app.get("/plugin/vast")
async def get_vast_plugin():
    """Serve vast plugin"""
    return JSONResponse(
        content="// Vast plugin stub",
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=3600"}
    )


@app.get("/blocked")
async def get_blocked():
    """Get blocked status"""
    return {"blocked": False}


@app.get("/tmdb/blocked")
async def get_tmdb_blocked():
    """Get TMDB blocked status"""
    return []  # Возвращаем пустой массив для dcma


@app.get("/tmdb/watch")
async def get_tmdb_watch(id: str = Query(...), cat: str = Query(...)):
    """Get TMDB watch data"""
    return {"status": "ok", "id": id, "category": cat}


@app.get("/")
async def root_with_tmdb_params(request: Request):
    """Handle root path with TMDB-like parameters"""
    # Проверяем, есть ли параметры, которые указывают на TMDB запрос
    params = dict(request.query_params)

    if any(key in params for key in ["sort", "cat", "genre", "page", "query"]):
        try:
            # Формируем путь для TMDB на основе параметров
            tmdb_path = ""
            
            # Обрабатываем параметр page
            page = params.get("page", "1")
            
            # Обрабатываем параметр cat (категория)
            cat = params.get("cat", "")
            
            # Обрабатываем параметр sort
            sort = params.get("sort", "")
            
            # Обрабатываем параметр genre
            genre = params.get("genre", "")
            
            # Обрабатываем параметр airdate
            airdate = params.get("airdate", "")
            
            # Обрабатываем параметр vote
            vote = params.get("vote", "")
            
            # Обрабатываем параметр uhd
            uhd = params.get("uhd", "")
            
            # Определяем тип контента
            if cat == "tv":
                content_type = "tv"
            elif cat == "anime":
                content_type = "tv"
                params["with_genres"] = "16"  # Анимация
                params["with_original_language"] = "ja"  # Японский язык
            else:
                content_type = "movie"
            
            # Формируем путь для TMDB на основе параметров
            if sort == "now_playing":
                if content_type == "movie":
                    tmdb_path = "movie/now_playing"
                else:
                    tmdb_path = "discover/tv"
                    params["with_status"] = "0"
            elif sort == "latest":
                tmdb_path = f"discover/{content_type}"
                if content_type == "movie":
                    params["sort_by"] = "release_date.desc"
                else:
                    params["sort_by"] = "first_air_date.desc"
            elif sort == "top":
                tmdb_path = f"discover/{content_type}"
                params["sort_by"] = "popularity.desc"
            elif sort == "now":
                tmdb_path = f"discover/{content_type}"
                if content_type == "movie":
                    params["sort_by"] = "release_date.desc"
                    params["primary_release_year"] = str(datetime.now().year)
                else:
                    params["sort_by"] = "first_air_date.desc"
                    params["first_air_date_year"] = str(datetime.now().year)
            elif sort == "airing":
                tmdb_path = "discover/tv"
                params["with_status"] = "0"
            elif sort == "update":
                tmdb_path = "discover/tv"
                params["with_status"] = "0"
            else:
                # По умолчанию используем discover
                tmdb_path = f"discover/{content_type}"
                params["sort_by"] = "popularity.desc"
            
            if "cat" in params:
                if params["cat"] == "tv":
                    tmdb_path = "discover/tv"
                    if "sort" in params:
                        if params["sort"] == "now_playing":
                            params["with_status"] = "0"
                        elif params["sort"] == "latest":
                            params["sort_by"] = "first_air_date.desc"
                        elif params["sort"] == "top":
                            params["sort_by"] = "popularity.desc"
                elif params["cat"] == "anime":
                    tmdb_path = "discover/tv"
                    params["with_genres"] = "16"
                    params["with_original_language"] = "ja"
            
            if "genre" in params:
                if "with_genres" not in params:
                    params["with_genres"] = params["genre"]
                del params["genre"]
                
                # Для жанров используем рейтинг вместо популярности
                if "sort_by" in params and params["sort_by"] == "popularity.desc":
                    params["sort_by"] = "vote_average.desc"
                    params["vote_count.gte"] = "100"
            
            if "uhd" in params:
                params["vote_average.gte"] = "7.0"
                del params["uhd"]
            
            # Обрабатываем параметр airdate (дата выхода)
            if "airdate" in params:
                airdate = params["airdate"]
                if "-" in airdate:
                    # Диапазон дат
                    start_year, end_year = airdate.split("-")
                    if "cat" in params and params["cat"] == "tv":
                        params["first_air_date.gte"] = f"{start_year}-01-01"
                        params["first_air_date.lte"] = f"{end_year}-12-31"
                    else:
                        params["primary_release_date.gte"] = f"{start_year}-01-01"
                        params["primary_release_date.lte"] = f"{end_year}-12-31"
                else:
                    # Один год
                    if "cat" in params and params["cat"] == "tv":
                        params["first_air_date_year"] = airdate
                    else:
                        params["primary_release_year"] = airdate
                del params["airdate"]
            
            # Обрабатываем параметр vote (рейтинг)
            if "vote" in params:
                vote = params["vote"]
                if "-" in vote:
                    min_vote, max_vote = vote.split("-")
                    params["vote_average.gte"] = min_vote
                    params["vote_average.lte"] = max_vote
                else:
                    params["vote_average.gte"] = vote
                del params["vote"]
            
            # Убираем параметры, которые не нужны для TMDB
            for key in ["email"]:
                if key in params:
                    del params[key]
            
            if tmdb_path:
                print(f"Root handler: Calling handle_tmdb_request with path={tmdb_path}, params={params}")
                # Создаем копию параметров для передачи в handle_tmdb_request
                tmdb_params = params.copy()
                result = await handle_tmdb_request(tmdb_path, tmdb_params, request)
                if "error" in result:
                    return JSONResponse(content=result, status_code=500)
                else:
                    return JSONResponse(
                        content=result,
                        status_code=200,
                        headers={"Cache-Control": "public, max-age=3600"}
                    )
        except Exception as e:
            print(f"Error handling root TMDB request: {e}")
            return JSONResponse(
                content={"error": "Root TMDB error", "message": str(e)},
                status_code=500
            )
    
    # Проверяем специальные пути
    path = request.url.path.lstrip("/")
    
    # Обрабатываем специальные пути
    if path.startswith("top/fire/") or path.startswith("top/hundred/"):
        # Определяем тип контента (movie/tv)
        content_type = path.split("/")[-1]
        
        # Извлекаем параметры из запроса
        params = dict(request.query_params)
        
        # Формируем параметры для TMDB
        tmdb_params = {
            "sort_by": "vote_average.desc",
            "vote_count.gte": "1000",
            "vote_average.gte": "7.0" if "fire" in path else "8.0"
        }
        
        # Добавляем параметр page если он есть
        if "page" in params:
            tmdb_params["page"] = params["page"]
        
        # Используем правильный путь для TMDB
        tmdb_path = f"discover/{content_type}"
        
        # Получаем данные из TMDB
        result = await handle_tmdb_request(tmdb_path, tmdb_params, request)
        
        if "error" in result:
            return {
                "page": 1,
                "results": [],
                "total_pages": 1,
                "total_results": 0
            }
        else:
            return result
    
    elif path.startswith("collections/"):
        collection_id = path.split("/")[1]
        
        # Извлекаем параметры из запроса
        params = dict(request.query_params)
        
        # Получаем коллекцию из TMDB
        tmdb_path = f"collection/{collection_id}"
        tmdb_params = {}
        
        # Добавляем параметр page если он есть
        if "page" in params:
            tmdb_params["page"] = params["page"]
        
        result = await handle_tmdb_request(tmdb_path, tmdb_params, request)
        
        if "error" in result:
            return {
                "page": 1,
                "results": [],
                "total_pages": 1,
                "total_results": 0
            }
        else:
            return result
    
    # Если это не TMDB запрос, возвращаем базовую информацию
    return {"status": "ok", "message": "Lampa API Server"}


# --- TMDB PROXY ENDPOINTS ---
@app.get("/apitmdb./{path:path}")
async def tmdb_api_proxy(path: str, request: Request):
    """Proxy for TMDB API requests"""
    import httpx

    try:
        # Собираем параметры запроса
        params = dict(request.query_params)

        # Добавляем API ключ TMDB
        params["api_key"] = TMDB_API_KEY

        # Формируем URL для TMDB API
        tmdb_url = f"{TMDB_BASE_URL}/{path}"

        print(f"TMDB API Proxy: {tmdb_url}")
        print(f"Params: {params}")

        async with httpx.AsyncClient() as client:
            response = await client.get(tmdb_url, params=params)

            if response.status_code == 200:
                return JSONResponse(
                    content=response.json(),
                    status_code=200,
                    headers={"Cache-Control": "public, max-age=3600"}
                )
            else:
                print(f"TMDB API error: {response.status_code}")
                return JSONResponse(
                    content={"error": "TMDB API error", "status": response.status_code},
                    status_code=response.status_code
                )

    except Exception as e:
        print(f"Error proxying to TMDB: {e}")
        return JSONResponse(
            content={"error": "Proxy error", "message": str(e)},
            status_code=500
        )


@app.get("/imagetmdb./{path:path}")
async def tmdb_image_proxy(path: str, request: Request):
    """Proxy for TMDB image requests"""
    import httpx

    try:
        # Формируем URL для изображения TMDB
        # Убираем дублирование t/p/ в пути
        if path.startswith("t/p/"):
            image_path = path
        else:
            image_path = f"t/p/{path}"
        
        image_url = f"https://image.tmdb.org/{image_path}"

        print(f"TMDB Image Proxy: {image_url}")

        async with httpx.AsyncClient() as client:
            response = await client.get(image_url)

            if response.status_code == 200:
                return Response(
                    content=response.content,
                    media_type=response.headers.get("content-type", "image/jpeg"),
                    headers={"Cache-Control": "public, max-age=86400"}  # Кэшируем изображения на 24 часа
                )
            else:
                print(f"TMDB image error: {response.status_code}")
                return JSONResponse(
                    content={"error": "Image not found"},
                    status_code=404
                )

    except Exception as e:
        print(f"Error proxying image from TMDB: {e}")
        return JSONResponse(
            content={"error": "Image proxy error", "message": str(e)},
            status_code=500
        )


# --- UNIFIED TMDB HANDLER ---
async def handle_tmdb_request(path: str, params: dict, request: Request):
    """Unified handler for all TMDB requests"""
    import httpx

    try:
        # Специальная обработка для /blocked
        if path == "blocked":
            return []

        # Специальная обработка для top/hundred и top/fire
        if path.startswith("top/hundred/") or path.startswith("top/fire/"):
            # Определяем тип контента (movie/tv)
            content_type = path.split("/")[-1]
            
            # Формируем параметры для TMDB
            tmdb_params = {
                "sort_by": "vote_average.desc",
                "vote_count.gte": "1000",
                "vote_average.gte": "7.0" if "fire" in path else "8.0"
            }
            
            # Используем правильный путь для TMDB
            tmdb_path = f"discover/{content_type}"
            
            # Получаем данные из TMDB
            result = await handle_tmdb_request(tmdb_path, tmdb_params, request)
            
            if "error" in result:
                return {
                    "page": 1,
                    "results": [],
                    "total_pages": 1,
                    "total_results": 0
                }
            else:
                return result

        # Специальная обработка для collections
        if path.startswith("collections/"):
            collection_id = path.split("/")[1]
            
            # Получаем коллекцию из TMDB
            tmdb_path = f"collection/{collection_id}"
            tmdb_params = {}
            
            result = await handle_tmdb_request(tmdb_path, tmdb_params, request)
            
            if "error" in result:
                return {
                    "page": 1,
                    "results": [],
                    "total_pages": 1,
                    "total_results": 0
                }
            else:
                return result

        # Подготавливаем параметры для TMDB
        tmdb_params = dict(params)

        # Добавляем API ключ если его нет
        if "api_key" not in tmdb_params:
            tmdb_params["api_key"] = TMDB_API_KEY

        # Добавляем язык если его нет
        if "language" not in tmdb_params:
            tmdb_params["language"] = "ru"

        # Обрабатываем множественные языки
        if "langs" in tmdb_params:
            langs = tmdb_params.pop("langs")
            if isinstance(langs, list):
                tmdb_params["language"] = ",".join(langs)
            elif isinstance(langs, str):
                tmdb_params["language"] = langs

        # Обрабатываем специальные параметры Lampa
        if "genres" in tmdb_params:
            tmdb_params["with_genres"] = tmdb_params.pop("genres")
        
        # Обрабатываем параметр genre
        if "genre" in tmdb_params:
            genre_id = tmdb_params.pop("genre")
            
            # Используем ИСКЛЮЧАЮЩИЙ фильтр вместо включающего
            # Это заставит TMDB возвращать только контент с этим жанром
            tmdb_params["with_genres"] = genre_id
            
            # Убираем популярность как критерий сортировки
            if "sort_by" in tmdb_params:
                del tmdb_params["sort_by"]
            
            # Используем строгую сортировку по рейтингу
            tmdb_params["sort_by"] = "vote_average.desc"
            tmdb_params["vote_count.gte"] = "50"
            tmdb_params["vote_average.gte"] = "6.0"
                
            # Добавляем фильтр по дате для исключения будущих релизов
            if "primary_release_date.gte" not in tmdb_params and "first_air_date.gte" not in tmdb_params:
                current_year = datetime.now().year
                if "cat" in tmdb_params and tmdb_params["cat"] == "tv":
                    tmdb_params["first_air_date.lte"] = f"{current_year}-12-31"
                else:
                    tmdb_params["primary_release_date.lte"] = f"{current_year}-12-31"

        # Обрабатываем фильтры
        if "filter" in tmdb_params:
            filter_params = tmdb_params.pop("filter")
            if isinstance(filter_params, dict):
                tmdb_params.update(filter_params)

        # Обрабатываем параметр query для поиска
        if "query" in tmdb_params and path.startswith("search/"):
            # Для поисковых запросов query должен быть в корне параметров
            tmdb_params["query"] = tmdb_params["query"]

        # Обрабатываем дополнительные параметры из cub.js
        if "keywords" in tmdb_params:
            tmdb_params["with_keywords"] = tmdb_params.pop("keywords")

        if "watch_region" in tmdb_params:
            tmdb_params["watch_region"] = tmdb_params["watch_region"]

        if "watch_providers" in tmdb_params:
            tmdb_params["with_watch_providers"] = tmdb_params.pop("watch_providers")

        if "networks" in tmdb_params:
            tmdb_params["with_networks"] = tmdb_params.pop("networks")

        if "sort_by" in tmdb_params:
            tmdb_params["sort_by"] = tmdb_params["sort_by"]

        # Обрабатываем параметр append_to_response для полных запросов
        if "append_to_response" in tmdb_params:
            tmdb_params["append_to_response"] = tmdb_params["append_to_response"]

        # Обрабатываем специальные параметры для discover запросов
        if "cat" in tmdb_params and "sort" in tmdb_params:
            cat = tmdb_params.get("cat", "movie")
            sort = tmdb_params.get("sort", "top")
            genre = tmdb_params.get("genre", "")
            page = tmdb_params.get("page", "1")
            airdate = tmdb_params.get("airdate", "")
            vote = tmdb_params.get("vote", "")
            uhd = tmdb_params.get("uhd", "")

            # Формируем правильный TMDB API запрос
            if cat == "movie":
                tmdb_url = "https://api.themoviedb.org/3/discover/movie"
                tmdb_params = {
                    "api_key": TMDB_API_KEY,
                    "language": "ru",
                    "page": page,
                    "with_genres": genre if genre else None,
                    "sort_by": "popularity.desc" if sort == "top" else "release_date.desc"
                }

                # Добавляем фильтр для фильмов в кинотеатрах
                if sort == "now_playing":
                    tmdb_params["with_release_type"] = "1"  # Только в кинотеатрах

                # Добавляем фильтры по дате
                if airdate:
                    if "-" in airdate:
                        # Диапазон дат
                        start_year, end_year = airdate.split("-")
                        tmdb_params["primary_release_date.gte"] = f"{start_year}-01-01"
                        tmdb_params["primary_release_date.lte"] = f"{end_year}-12-31"
                    else:
                        # Один год
                        tmdb_params["primary_release_year"] = airdate

                # Добавляем фильтры по рейтингу
                if vote and "-" in vote:
                    min_vote, max_vote = vote.split("-")
                    tmdb_params["vote_average.gte"] = min_vote
                    tmdb_params["vote_average.lte"] = max_vote

                # Добавляем фильтр для высокого качества (uhd)
                if uhd:
                    tmdb_params["vote_average.gte"] = "7.0"  # Минимальный рейтинг для высокого качества

                # Убираем None значения
                tmdb_params = {k: v for k, v in tmdb_params.items() if v is not None}

            elif cat == "tv":
                tmdb_url = "https://api.themoviedb.org/3/discover/tv"
                tmdb_params = {
                    "api_key": TMDB_API_KEY,
                    "language": "ru",
                    "page": page,
                    "with_genres": genre if genre else None,
                    "sort_by": "popularity.desc" if sort == "top" else "first_air_date.desc"
                }

                # Добавляем фильтр для сериалов в эфире
                if sort == "airing":
                    tmdb_params["with_status"] = "0"  # Возвращающиеся сериалы

                # Добавляем фильтры по дате
                if airdate:
                    if "-" in airdate:
                        # Диапазон дат
                        start_year, end_year = airdate.split("-")
                        tmdb_params["first_air_date.gte"] = f"{start_year}-01-01"
                        tmdb_params["first_air_date.lte"] = f"{end_year}-12-31"
                    else:
                        # Один год
                        tmdb_params["first_air_date_year"] = airdate

                # Добавляем фильтры по рейтингу
                if vote and "-" in vote:
                    min_vote, max_vote = vote.split("-")
                    tmdb_params["vote_average.gte"] = min_vote
                    tmdb_params["vote_average.lte"] = max_vote

                # Добавляем фильтр для высокого качества (uhd)
                if uhd:
                    tmdb_params["vote_average.gte"] = "7.0"  # Минимальный рейтинг для высокого качества

                # Убираем None значения
                tmdb_params = {k: v for k, v in tmdb_params.items() if v is not None}

            elif cat == "anime":
                # Для аниме используем TV API с фильтрами
                tmdb_url = "https://api.themoviedb.org/3/discover/tv"
                tmdb_params = {
                    "api_key": TMDB_API_KEY,
                    "language": "ru",
                    "page": page,
                    "with_genres": "16",  # Анимация
                    "with_original_language": "ja",  # Японский язык
                    "sort_by": "popularity.desc" if sort == "top" else "first_air_date.desc"
                }

                # Добавляем фильтр для аниме в эфире
                if sort == "airing":
                    tmdb_params["with_status"] = "0"  # Возвращающиеся сериалы

                # Добавляем фильтры по дате
                if airdate:
                    if "-" in airdate:
                        # Диапазон дат
                        start_year, end_year = airdate.split("-")
                        tmdb_params["first_air_date.gte"] = f"{start_year}-01-01"
                        tmdb_params["first_air_date.lte"] = f"{end_year}-12-31"
                    else:
                        # Один год
                        tmdb_params["first_air_date_year"] = airdate

                # Добавляем фильтры по рейтингу
                if vote and "-" in vote:
                    min_vote, max_vote = vote.split("-")
                    tmdb_params["vote_average.gte"] = min_vote
                    tmdb_params["vote_average.lte"] = max_vote

                # Добавляем фильтр для высокого качества (uhd)
                if uhd:
                    tmdb_params["vote_average.gte"] = "7.0"  # Минимальный рейтинг для высокого качества

                # Убираем None значения
                tmdb_params = {k: v for k, v in tmdb_params.items() if v is not None}
            else:
                # Для других категорий используем обычный прокси
                tmdb_url = f"https://api.themoviedb.org/3/{path}"
        else:
            # Обрабатываем поисковые запросы для аниме
            if path == "search/anime":
                # Для поиска аниме используем поиск по TV с фильтрами
                tmdb_url = "https://api.themoviedb.org/3/search/tv"
                tmdb_params["with_genres"] = "16"  # Анимация
                tmdb_params["with_original_language"] = "ja"  # Японский язык
            elif path == "search/movie":
                # Поиск фильмов
                tmdb_url = "https://api.themoviedb.org/3/search/movie"
            elif path == "search/tv":
                # Поиск сериалов
                tmdb_url = "https://api.themoviedb.org/3/search/tv"
            elif path == "search/person":
                # Поиск актеров
                tmdb_url = "https://api.themoviedb.org/3/search/person"
            elif path == "movie/now_playing":
                # Фильмы в кинотеатрах
                tmdb_url = "https://api.themoviedb.org/3/movie/now_playing"
            elif path == "trending/movie/day":
                # Трендовые фильмы за день
                tmdb_url = "https://api.themoviedb.org/3/trending/movie/day"
            elif path == "trending/movie/week":
                # Трендовые фильмы за неделю
                tmdb_url = "https://api.themoviedb.org/3/trending/movie/week"
            elif path == "trending/tv/week":
                # Трендовые сериалы за неделю
                tmdb_url = "https://api.themoviedb.org/3/trending/tv/week"
            elif path == "movie/upcoming":
                # Скоро выходящие фильмы
                tmdb_url = "https://api.themoviedb.org/3/movie/upcoming"
            elif path == "movie/popular":
                # Популярные фильмы
                tmdb_url = "https://api.themoviedb.org/3/movie/popular"
            elif path == "movie/top_rated":
                # Лучшие фильмы
                tmdb_url = "https://api.themoviedb.org/3/movie/top_rated"
            elif path == "tv/top_rated":
                # Лучшие сериалы
                tmdb_url = "https://api.themoviedb.org/3/tv/top_rated"
            elif path.startswith("discover/"):
                # Discover запросы
                tmdb_url = f"https://api.themoviedb.org/3/{path}"
            elif path.startswith("collection/"):
                # Запросы к коллекциям
                tmdb_url = f"https://api.themoviedb.org/3/{path}"
            elif path.startswith("tv/") and "/season/" in path:
                # Запросы к сезонам сериалов
                tmdb_url = f"https://api.themoviedb.org/3/{path}"
            elif path.startswith("movie/") and "/" in path and path.split("/")[-1].isdigit():
                # Запросы к конкретным фильмам
                tmdb_url = f"https://api.themoviedb.org/3/{path}"
            elif path.startswith("tv/") and "/" in path and path.split("/")[-1].isdigit():
                # Запросы к конкретным сериалам
                tmdb_url = f"https://api.themoviedb.org/3/{path}"
            elif path.endswith("/credits"):
                # Запросы к актерам и съемочной группе
                tmdb_url = f"https://api.themoviedb.org/3/{path}"
            elif path.endswith("/recommendations"):
                # Рекомендации
                tmdb_url = f"https://api.themoviedb.org/3/{path}"
            elif path.endswith("/similar"):
                # Похожие фильмы/сериалы
                tmdb_url = f"https://api.themoviedb.org/3/{path}"
            elif path.endswith("/videos"):
                # Видео (трейлеры, клипы)
                tmdb_url = f"https://api.themoviedb.org/3/{path}"
            else:
                # Обычный прокси для других запросов
                # Проверяем, не начинается ли путь с "3/"
                if path.startswith("3/"):
                    clean_path = path[2:]  # Убираем "3/"
                    tmdb_url = f"https://api.themoviedb.org/3/{clean_path}"
                else:
                    tmdb_url = f"https://api.themoviedb.org/3/{path}"



        print(f"TMDB Request: {tmdb_url}")
        print(f"TMDB Params: {tmdb_params}")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(tmdb_url, params=tmdb_params)
            
            print(f"TMDB Response Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                
                # Фильтруем фильмы, которые еще не вышли (дата выхода в будущем)
                # Но только для запросов, которые не связаны с now_playing
                if "results" in data and isinstance(data["results"], list):
                    # Проверяем, является ли это запросом now_playing
                    is_now_playing = False
                    if "with_release_type" in tmdb_params and tmdb_params["with_release_type"] == "1":
                        is_now_playing = True
                    
                    # Также проверяем по пути запроса
                    if "discover/movie" in tmdb_url and "with_release_type" in tmdb_params:
                        is_now_playing = True
                    
                    # Фильтруем фильмы с будущими датами (кроме now_playing)
                    if not is_now_playing:
                        current_date = datetime.now().date()
                        filtered_results = []
                        original_count = len(data["results"])
                        
                        for item in data["results"]:
                            # Проверяем дату выхода для фильмов
                            if "release_date" in item and item["release_date"]:
                                try:
                                    release_date = datetime.strptime(item["release_date"], "%Y-%m-%d").date()
                                    if release_date <= current_date:
                                        filtered_results.append(item)
                                except:
                                    # Если не можем распарсить дату, включаем фильм
                                    filtered_results.append(item)
                            # Проверяем дату выхода для сериалов
                            elif "first_air_date" in item and item["first_air_date"]:
                                try:
                                    air_date = datetime.strptime(item["first_air_date"], "%Y-%m-%d").date()
                                    if air_date <= current_date:
                                        filtered_results.append(item)
                                except:
                                    # Если не можем распарсить дату, включаем сериал
                                    filtered_results.append(item)
                            else:
                                # Если нет даты, включаем
                                filtered_results.append(item)
                        
                        data["results"] = filtered_results
                        data["total_results"] = len(filtered_results)

                return data
            else:
                print(f"TMDB API error: {response.status_code}")
                return {"error": "TMDB API error", "status": response.status_code}

    except Exception as e:
        print(f"Error in TMDB handler: {e}")
        return {"error": "TMDB handler error", "message": str(e)}


@app.get("/tmdb/{path:path}")
async def tmdb_proxy(path: str, request: Request):
    """Main TMDB proxy endpoint"""
    params = dict(request.query_params)
    result = await handle_tmdb_request(path, params, request)

    if "error" in result:
        return JSONResponse(
            content=result,
            status_code=500
        )
    else:
        return JSONResponse(
            content=result,
            status_code=200,
            headers={"Cache-Control": "public, max-age=3600"}
        )


@app.get("/top/fire/{content_type}")
async def top_fire_handler(content_type: str, request: Request):
    """Handle top fire requests"""
    try:
        # Извлекаем параметры из запроса
        params = dict(request.query_params)
        
        # Формируем параметры для TMDB
        tmdb_params = {
            "sort_by": "vote_average.desc",
            "vote_count.gte": "1000",
            "vote_average.gte": "7.0"
        }
        
        # Добавляем параметр page если он есть
        if "page" in params:
            tmdb_params["page"] = params["page"]
        
        # Используем правильный путь для TMDB
        tmdb_path = f"discover/{content_type}"
        
        # Получаем данные из TMDB
        result = await handle_tmdb_request(tmdb_path, tmdb_params, request)
        
        if "error" in result:
            return {
                "page": 1,
                "results": [],
                "total_pages": 1,
                "total_results": 0
            }
        else:
            return result
            
    except Exception as e:
        return {
            "page": 1,
            "results": [],
            "total_pages": 1,
            "total_results": 0
        }

@app.get("/top/hundred/{content_type}")
async def top_hundred_handler(content_type: str, request: Request):
    """Handle top hundred requests"""
    try:
        # Извлекаем параметры из запроса
        params = dict(request.query_params)
        
        # Формируем параметры для TMDB
        tmdb_params = {
            "sort_by": "vote_average.desc",
            "vote_count.gte": "1000",
            "vote_average.gte": "8.0"
        }
        
        # Добавляем параметр page если он есть
        if "page" in params:
            tmdb_params["page"] = params["page"]
        
        # Используем правильный путь для TMDB
        tmdb_path = f"discover/{content_type}"
        
        # Получаем данные из TMDB
        result = await handle_tmdb_request(tmdb_path, tmdb_params, request)
        
        if "error" in result:
            return {
                "page": 1,
                "results": [],
                "total_pages": 1,
                "total_results": 0
            }
        else:
            return result
            
    except Exception as e:
        return {
            "page": 1,
            "results": [],
            "total_pages": 1,
            "total_results": 0
        }

@app.get("/collections/{collection_id}")
async def collections_handler(collection_id: str, request: Request):
    """Handle collections requests"""
    try:
        # Получаем коллекцию из TMDB
        tmdb_path = f"collection/{collection_id}"
        tmdb_params = {}
        
        result = await handle_tmdb_request(tmdb_path, tmdb_params, request)
        
        if "error" in result:
            return {
                "page": 1,
                "results": [],
                "total_pages": 1,
                "total_results": 0
            }
        else:
            return result
            
    except Exception as e:
        return {
            "page": 1,
            "results": [],
            "total_pages": 1,
            "total_results": 0
        }

@app.get("/{path:path}")
async def catch_all_subdomains(path: str, request: Request):
    """Catch all subdomain requests"""
    import httpx

    # Handle geo subdomain
    if path.startswith("geo."):
        return {"geo": "stub"}

    # Handle apitmdb subdomain
    if path.startswith("apitmdb.") or "apitmdb." in str(request.url):
        # Проксируем запросы к TMDB API
        try:
            # Убираем префикс apitmdb. из пути если есть
            tmdb_path = path.replace("apitmdb.", "") if path.startswith("apitmdb.") else path

            # Собираем параметры запроса
            params = dict(request.query_params)

            # Добавляем API ключ TMDB
            params["api_key"] = TMDB_API_KEY

            # Формируем URL для TMDB API
            tmdb_url = f"https://api.themoviedb.org/{tmdb_path}"

            print(f"Proxying to TMDB (GET): {tmdb_url}")
            print(f"Params: {params}")

            async with httpx.AsyncClient() as client:
                response = await client.get(tmdb_url, params=params)

                if response.status_code == 200:
                    return JSONResponse(
                        content=response.json(),
                        status_code=200,
                        headers={"Cache-Control": "public, max-age=3600"}
                    )
                else:
                    print(f"TMDB API error: {response.status_code}")
                    return JSONResponse(
                        content={"error": "TMDB API error", "status": response.status_code},
                        status_code=response.status_code
                    )

        except Exception as e:
            print(f"Error proxying to TMDB: {e}")
            return JSONResponse(
                content={"error": "Proxy error", "message": str(e)},
                status_code=500
            )

    # Handle imagetmdb subdomain
    if path.startswith("imagetmdb.") or "imagetmdb." in str(request.url) or path.startswith("t/p/"):
        # Проксируем запросы к изображениям TMDB
        try:
            # Убираем префикс imagetmdb. из пути если есть
            image_path = path.replace("imagetmdb.", "") if path.startswith("imagetmdb.") else path

            # Формируем URL для изображения TMDB
            # Убираем дублирование t/p/ в пути
            if image_path.startswith("t/p/"):
                final_image_path = image_path
            else:
                final_image_path = f"t/p/{image_path}"
            
            image_url = f"https://image.tmdb.org/{final_image_path}"

            print(f"Proxying image from TMDB (GET): {image_url}")

            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)

                if response.status_code == 200:
                    return Response(
                        content=response.content,
                        media_type=response.headers.get("content-type", "image/jpeg"),
                        headers={"Cache-Control": "public, max-age=86400"}  # Кэшируем изображения на 24 часа
                    )
                else:
                    print(f"TMDB image error: {response.status_code}")
                    return JSONResponse(
                        content={"error": "Image not found"},
                        status_code=404
                    )

        except Exception as e:
            print(f"Error proxying image from TMDB: {e}")
            return JSONResponse(
                content={"error": "Image proxy error", "message": str(e)},
                status_code=500
            )

    # Handle tmdb subdomain - это основной случай для Lampa
    if path.startswith("tmdb.") or "tmdb." in str(request.url) or "tmdb." in str(request.headers.get("host", "")):
        try:
            # Убираем префикс tmdb. из пути если есть
            tmdb_path = path.replace("tmdb.", "") if path.startswith("tmdb.") else path

            # Собираем параметры запроса
            params = dict(request.query_params)

            # Используем унифицированный обработчик
            result = await handle_tmdb_request(tmdb_path, params, request)

            if "error" in result:
                return JSONResponse(
                    content=result,
                    status_code=500
                )
            else:
                return JSONResponse(
                    content=result,
                    status_code=200,
                    headers={"Cache-Control": "public, max-age=3600"}
                )

        except Exception as e:
            return JSONResponse(
                content={"error": "Proxy error", "message": str(e)},
                status_code=500
            )

    # Handle apitmdb subdomain
    if path.startswith("apitmdb.") or "apitmdb." in str(request.url) or "apitmdb." in str(request.headers.get("host", "")):
        try:
            # Убираем префикс apitmdb. из пути если есть
            tmdb_path = path.replace("apitmdb.", "") if path.startswith("apitmdb.") else path

            # Собираем параметры запроса
            params = dict(request.query_params)

            # Используем унифицированный обработчик
            result = await handle_tmdb_request(tmdb_path, params, request)

            if "error" in result:
                return JSONResponse(
                    content=result,
                    status_code=500
                )
            else:
                return JSONResponse(
                    content=result,
                    status_code=200,
                    headers={"Cache-Control": "public, max-age=3600"}
                )

        except Exception as e:
            return JSONResponse(
                content={"error": "Proxy error", "message": str(e)},
                status_code=500
            )

    return {"status": "not_found", "path": path}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all_api_routes(path: str, request: Request):
    """Catch all API routes that weren't handled by specific endpoints"""
    import httpx

    # Handle subdomain requests
    if path.startswith("geo."):
        return {"geo": "stub"}

    if path.startswith("apitmdb.") or "apitmdb." in str(request.url):
        # Проксируем запросы к TMDB API
        try:
            # Убираем префикс apitmdb. из пути если есть
            tmdb_path = path.replace("apitmdb.", "") if path.startswith("apitmdb.") else path

            # Собираем параметры запроса
            params = dict(request.query_params)

            # Добавляем API ключ TMDB
            params["api_key"] = TMDB_API_KEY

            # Формируем URL для TMDB API
            tmdb_url = f"https://api.themoviedb.org/{tmdb_path}"

            print(f"Proxying to TMDB: {tmdb_url}")
            print(f"Params: {params}")

            async with httpx.AsyncClient() as client:
                response = await client.get(tmdb_url, params=params)

                if response.status_code == 200:
                    return JSONResponse(
                        content=response.json(),
                        status_code=200,
                        headers={"Cache-Control": "public, max-age=3600"}
                    )
                else:
                    print(f"TMDB API error: {response.status_code}")
                    return JSONResponse(
                        content={"error": "TMDB API error", "status": response.status_code},
                        status_code=response.status_code
                    )

        except Exception as e:
            print(f"Error proxying to TMDB: {e}")
            return JSONResponse(
                content={"error": "Proxy error", "message": str(e)},
                status_code=500
            )

    if path.startswith("imagetmdb.") or "imagetmdb." in str(request.url):
        # Проксируем запросы к изображениям TMDB
        try:
            # Убираем префикс imagetmdb. из пути если есть
            image_path = path.replace("imagetmdb.", "") if path.startswith("imagetmdb.") else path

            # Формируем URL для изображения TMDB
            # Убираем дублирование t/p/ в пути
            if image_path.startswith("t/p/"):
                final_image_path = image_path
            else:
                final_image_path = f"t/p/{image_path}"
            
            image_url = f"https://image.tmdb.org/{final_image_path}"

            async with httpx.AsyncClient() as client:
                response = await client.get(image_url)

                if response.status_code == 200:
                    return Response(
                        content=response.content,
                        media_type=response.headers.get("content-type", "image/jpeg"),
                        headers={"Cache-Control": "public, max-age=86400"}  # Кэшируем изображения на 24 часа
                    )
                else:
                    print(f"TMDB image error: {response.status_code}")
                    return JSONResponse(
                        content={"error": "Image not found"},
                        status_code=404
                    )

        except Exception as e:
            print(f"Error proxying image from TMDB: {e}")
            return JSONResponse(
                content={"error": "Image proxy error", "message": str(e)},
                status_code=500
            )

    if path.startswith("tmdb.") or "tmdb." in str(request.url):
        try:
            # Убираем префикс tmdb. из пути если есть
            tmdb_path = path.replace("tmdb.", "") if path.startswith("tmdb.") else path

            # Собираем параметры запроса
            params = dict(request.query_params)

            # Используем унифицированный обработчик
            result = await handle_tmdb_request(tmdb_path, params, request)

            if "error" in result:
                return JSONResponse(
                    content=result,
                    status_code=500
                )
            else:
                return JSONResponse(
                    content=result,
                    status_code=200,
                    headers={"Cache-Control": "public, max-age=3600"}
                )

        except Exception as e:
            return JSONResponse(
                content={"error": "Proxy error", "message": str(e)},
                status_code=500
            )

    if path.startswith("apitmdb.") or "apitmdb." in str(request.url):
        try:
            # Убираем префикс apitmdb. из пути если есть
            tmdb_path = path.replace("apitmdb.", "") if path.startswith("apitmdb.") else path

            # Собираем параметры запроса
            params = dict(request.query_params)

            # Используем унифицированный обработчик
            result = await handle_tmdb_request(tmdb_path, params, request)

            if "error" in result:
                return JSONResponse(
                    content=result,
                    status_code=500
                )
            else:
                return JSONResponse(
                    content=result,
                    status_code=200,
                    headers={"Cache-Control": "public, max-age=3600"}
                )

        except Exception as e:
            return JSONResponse(
                content={"error": "Proxy error", "message": str(e)},
                status_code=500
            )

    return {"status": "not_found", "path": path}


@app.get("/api/device/qr")
def get_device_qr():
    """Get QR code for device addition"""
    return get_test_data("device_qr", {
        "qr_url": "/img/other/qr-add-device.png",
        "site_url": "/add",
        "code_length": 6
    })


@app.get("/img/other/qr-add-device.png")
async def get_qr_image():
    """Serve QR code image"""
    try:
        return FileResponse(
            "static/img/other/qr-add-device.png",
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"}
        )
    except FileNotFoundError:
        # Если файл не найден, возвращаем пустой ответ
        return JSONResponse(
            status_code=404,
            content={"error": "QR image not found"}
        )


@app.get("/img/profiles/{profile_icon}.png")
async def get_profile_image(profile_icon: str):
    """Serve profile icon image"""
    try:
        # Создаем заглушку для изображения профиля
        return FileResponse(
            "static/img/other/qr-add-device.png",  # Используем то же изображение как заглушку
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=3600"}
        )
    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={"error": "Profile image not found"}
        )


@app.get("/api/collections/liked")
def get_collections_liked(token: str = Header(...)):
    """Get liked collections"""
    return {"results": get_test_data("collections_liked", [])}


@app.get("/api/collections/view/{url}")
def get_collections_view(url: str, page: int = Query(1), token: str = Header(...)):
    """Get collection view by URL"""
    key = f"{url}_{page}"
    collections_view = get_test_data("collections_view", {})
    if key not in collections_view:
        collections_view[key] = {
            "page": page,
            "results": [
                {"id": 1, "title": f"Collection Item {page}-1", "type": "movie"},
                {"id": 2, "title": f"Collection Item {page}-2", "type": "tv"}
            ],
            "total_pages": 3
        }
        update_test_data("collections_view", collections_view)
    return collections_view[key]


@app.get("/api/iptv/time")
def get_iptv_time(token: str = Header(None)):
    """Get IPTV current time"""
    iptv_data = get_test_data("iptv", {})
    return iptv_data.get("time", {})


@app.get("/api/iptv/program/{channel_id}/{time}")
def get_iptv_program(channel_id: str, time: str, full: bool = Query(False), token: str = Header(None)):
    """Get IPTV program for channel and time"""
    key = f"{channel_id}_{time}"
    iptv_data = get_test_data("iptv", {})
    program = iptv_data.get("program", {})
    if key not in program:
        program[key] = {
            "channel_id": channel_id,
            "time": int(time),
            "programs": [
                {"title": f"Program {channel_id}-1", "start": int(time), "end": int(time) + 3600},
                {"title": f"Program {channel_id}-2", "start": int(time) + 3600, "end": int(time) + 7200}
            ]
        }
        iptv_data["program"] = program
        update_test_data("iptv", iptv_data)
    return program[key]


# --- DEBUG ENDPOINT ---
@app.post("/api/debug")
async def debug_endpoint(request: Request):
    """Debug endpoint to see what data is being sent"""
    try:
        form_data = await request.form()
        body_text = await request.body()

        return {
            "form_data": dict(form_data),
            "body_text": body_text.decode() if body_text else None,
            "headers": dict(request.headers),
            "method": request.method,
            "url": str(request.url)
        }
    except Exception as e:
        return {"error": str(e)}


# --- SOCKET ENDPOINTS ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication"""
    await websocket.accept()
    print("WebSocket connection accepted")

    try:
        while True:
            # Получаем сообщение от клиента
            data = await websocket.receive_text()
            message = json.loads(data)

            print(f"WebSocket received: {message}")

            # Обрабатываем разные типы сообщений
            if message.get("method") == "check_token":
                # Проверяем токен и премиум статус
                # Токен может быть в разных местах сообщения
                token = message.get("data", {}).get("token")
                if not token:
                    # Попробуем найти токен в account
                    account = message.get("account", {})
                    token = account.get("token")
                
                print(f"WebSocket check_token: token={token}")
                if token:
                    status = check_premium_status(token)
                    print(f"WebSocket check_token: status={status}")
                    response = {
                        "method": "check_token",
                        "status": "valid" if status["valid"] else "invalid",
                        "data": {
                            "valid": status["valid"],
                            "premium": status["premium"],
                            "premium_expiry": status["premium_expiry"],
                            "current_time": status["current_time"]
                        }
                    }
                else:
                    response = {
                        "method": "check_token",
                        "status": "invalid",
                        "data": {
                            "valid": False, 
                            "premium": False,
                            "premium_expiry": 0,
                            "current_time": int(time.time())
                        }
                    }



            elif message.get("method") == "start":
                # Обрабатываем сообщение start с правильным премиум статусом
                account = message.get("account", {})
                token = account.get("token")
                print(f"WebSocket start: token={token}")

                if token:
                    status = check_premium_status(token)
                    print(f"WebSocket start: status={status}")
                    response = {
                        "method": "start",
                        "status": "ok",
                        "data": {
                            "valid": status["valid"],
                            "premium": status["premium"],
                            "premium_expiry": status["premium_expiry"],
                            "current_time": status["current_time"],
                            "account": {
                                "secuses": True,
                                "email": "igor.tonin@inbox.ru",
                                "id": 148608,
                                "token": token,
                                "profile": {
                                    "id": 153918,
                                    "cid": 148608,
                                    "name": "Общий",
                                    "main": 1,
                                    "icon": "l_1"
                                }
                            }
                        }
                    }
                else:
                    response = {
                        "method": "start",
                        "status": "error",
                        "data": {"valid": False, "premium": False, "premium_expiry": 0,
                                 "current_time": int(time.time())}
                    }

                await websocket.send_text(json.dumps(response))

            elif message.get("method") == "devices":
                # Возвращаем список устройств
                response = {
                    "method": "devices",
                    "data": get_test_data("devices", [])
                }
                await websocket.send_text(json.dumps(response))

            else:
                # Эхо для других сообщений
                response = {
                    "method": "echo",
                    "data": message
                }
                await websocket.send_text(json.dumps(response))

    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        try:
            await websocket.send_text(json.dumps({
                "method": "error",
                "error": str(e)
            }))
        except:
            pass


# --- UNIVERSAL API FALLBACK ---
@app.api_route("/api/{path:path}", methods=["GET", "POST"])
async def fallback_api(path: str, request: Request, token: Optional[str] = Header(None)):
    # Не обрабатываем известные эндпоинты
    known_endpoints = [
        "profiles/all", "device/add", "bookmarks/all", "bookmarks/add", "bookmarks/clear",
        "notifications/all", "notifications/add", "lampa/logs/write", "person/subscribe",
        "person/unsubscribe", "discuss/get", "discuss/add", "discuss/voite", "reactions/get",
        "reactions/add", "collections/list", "trailers/short/trailers", "timeline/all",
        "feed/all", "ad/stat", "ad/all", "ad/vast", "adv/log", "payment/event_prime",
        "ai/generate/facts", "ai/generate/recommend", "ai/search", "plugins/blacklist",
        "plugins/all", "extensions/list", "extensions/status", "plugins/status",
        "premium/status", "premium/status/debug", "premium/check", "account/status",
        "users/get", "users/backup/import", "notice/all", "person/list",
        "metric/unic", "iptv/channels", "iptv/playlists", "checker", "device/qr",
        "collections/liked", "collections/view", "iptv/time", "iptv/program"
    ]

    if path in known_endpoints:
        return JSONResponse({"status": "endpoint_exists", "path": path, "method": request.method})

    return JSONResponse({"status": "stub", "path": path, "method": request.method})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000) 