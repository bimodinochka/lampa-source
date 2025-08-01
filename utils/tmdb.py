import httpx
from datetime import datetime

# --- CONFIG ---
TMDB_API_KEY = "4ef0d7355d9ffb5151e987764708ce96"
TMDB_API_VERSION = "3"  # Можно изменить на "4" для новой версии API
TMDB_BASE_URL = f"https://api.themoviedb.org/{TMDB_API_VERSION}"

# --- UNIFIED TMDB HANDLER ---
async def handle_tmdb_request(path: str, params: dict, request):
    """Unified handler for all TMDB requests"""
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