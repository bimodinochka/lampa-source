from fastapi import APIRouter, Header, HTTPException, Request, Form
from fastapi.responses import PlainTextResponse
from utils.test_data import get_test_data, update_test_data

router = APIRouter(prefix="/api", tags=["debug"])

# --- DEBUG ENDPOINT ---
@router.post("/debug")
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


# --- CHECKER ---
@router.get("/checker")
def get_checker():
    """Mirror checker endpoint"""
    return get_test_data("checker", {})

@router.post("/checker")
async def post_checker(request: Request):
    """Mirror checker endpoint - returns the sent data back for validation"""
    try:
        form_data = await request.form()
        if 'data' in form_data:
            return PlainTextResponse(content=form_data['data'])
        return PlainTextResponse(content="")
    except Exception as e:
        return PlainTextResponse(content=str(e))


# --- RESET ---
@router.get("/reset")
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