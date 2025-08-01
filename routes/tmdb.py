from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse, Response
from typing import Optional
from utils.tmdb import handle_tmdb_request
import httpx

router = APIRouter(tags=["tmdb"])

# --- TMDB PROXY ENDPOINTS ---
@router.get("/apitmdb./{path:path}")
async def tmdb_api_proxy(path: str, request: Request):
    """Proxy for TMDB API requests"""
    try:
        # Собираем параметры запроса
        params = dict(request.query_params)

        # Добавляем API ключ TMDB
        params["api_key"] = "4ef0d7355d9ffb5151e987764708ce96"

        # Формируем URL для TMDB API
        tmdb_url = f"https://api.themoviedb.org/3/{path}"

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


@router.get("/imagetmdb./{path:path}")
async def tmdb_image_proxy(path: str, request: Request):
    """Proxy for TMDB image requests"""
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


@router.get("/tmdb/{path:path}")
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


@router.get("/top/fire/{content_type}")
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

@router.get("/top/hundred/{content_type}")
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


# --- BLOCKED STATUS ---
@router.get("/blocked")
async def get_blocked():
    """Get blocked status"""
    return {"blocked": False}


@router.get("/tmdb/blocked")
async def get_tmdb_blocked():
    """Get TMDB blocked status"""
    return []  # Возвращаем пустой массив для dcma


@router.get("/tmdb/watch")
async def get_tmdb_watch(id: str = Query(...), cat: str = Query(...)):
    """Get TMDB watch data"""
    return {"status": "ok", "id": id, "category": cat}