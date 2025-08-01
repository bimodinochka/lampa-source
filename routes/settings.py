from fastapi import APIRouter, Header, HTTPException
from utils.test_data import get_test_data, update_test_data
from utils.premium import check_premium_status

router = APIRouter(prefix="/api", tags=["settings"])

# --- SETTINGS ---
@router.get("/settings/components")
def get_settings_components(token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    return {"components": get_test_data("settings_components", [])}


@router.post("/settings/components/add")
async def add_settings_component(component: dict, token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    components = get_test_data("settings_components", [])
    components.append(component)
    update_test_data("settings_components", components)
    return {"status": "ok", "component": component}


@router.get("/settings/params")
def get_settings_params(token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    return {"params": get_test_data("settings_params", [])}


@router.post("/settings/params/add")
async def add_settings_param(param: dict, token: str = Header(...)):
    status = check_premium_status(token)
    if not status["valid"]:
        raise HTTPException(status_code=403, detail="Invalid token")
    
    params = get_test_data("settings_params", [])
    params.append(param)
    update_test_data("settings_params", params)
    return {"status": "ok", "param": param} 