from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from utils.test_data import get_test_data, update_test_data

router = APIRouter(tags=["static"])

# --- STATIC FILES ---
@router.get("/img/other/qr-add-device.png")
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


@router.get("/img/profiles/{profile_icon}.png")
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


# --- PLUGIN FILES ---
@router.get("/plugin/sport")
async def get_sport_plugin():
    """Serve sport plugin"""
    return JSONResponse(
        content="// Sport plugin stub",
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=3600"}
    )


@router.get("/plugin/vast")
async def get_vast_plugin():
    """Serve vast plugin"""
    return JSONResponse(
        content="// Vast plugin stub",
        media_type="application/javascript",
        headers={"Cache-Control": "public, max-age=3600"}
    )
