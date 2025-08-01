from fastapi import FastAPI, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from typing import Optional
import os
from datetime import datetime

# Импортируем все роуты
from routes.premium import router as premium_router
from routes.account import router as account_router
from routes.device import router as device_router
from routes.user import router as user_router
from routes.person import router as person_router
from routes.bookmarks import router as bookmarks_router
from routes.notifications import router as notifications_router
from routes.discussions import router as discussions_router
from routes.reactions import router as reactions_router
from routes.collections import router as collections_router
from routes.trailers import router as trailers_router
from routes.timeline import router as timeline_router
from routes.feed import router as feed_router
from routes.ad import router as ad_router
from routes.ai import router as ai_router
from routes.plugins import router as plugins_router
from routes.logs import router as logs_router
from routes.search import router as search_router
from routes.settings import router as settings_router
from routes.iptv import router as iptv_router
from routes.torrents import router as torrents_router
from routes.metric import router as metric_router
from routes.notice import router as notice_router
from routes.debug import router as debug_router
from routes.static import router as static_router
from routes.tmdb import router as tmdb_router
from routes.websocket import router as websocket_router

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

# Подключаем все роуты
app.include_router(premium_router)
app.include_router(account_router)
app.include_router(device_router)
app.include_router(user_router)
app.include_router(person_router)
app.include_router(bookmarks_router)
app.include_router(notifications_router)
app.include_router(discussions_router)
app.include_router(reactions_router)
app.include_router(collections_router)
app.include_router(trailers_router)
app.include_router(timeline_router)
app.include_router(feed_router)
app.include_router(ad_router)
app.include_router(ai_router)
app.include_router(plugins_router)
app.include_router(logs_router)
app.include_router(search_router)
app.include_router(settings_router)
app.include_router(iptv_router)
app.include_router(torrents_router)
app.include_router(metric_router)
app.include_router(notice_router)
app.include_router(debug_router)
app.include_router(static_router)
app.include_router(tmdb_router)
app.include_router(websocket_router)

# --- ROOT HANDLER ---
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
                from utils.tmdb import handle_tmdb_request
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
        from utils.tmdb import handle_tmdb_request
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
        
        from utils.tmdb import handle_tmdb_request
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
    uvicorn.run(app, host="0.0.0.0", port=8009)