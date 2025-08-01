from fastapi import APIRouter, Header, Request, HTTPException
from utils.test_data import get_test_data, update_test_data

router = APIRouter(prefix="/api", tags=["device"])

# --- USER PROFILE ---
@router.get("/profiles/all")
def get_profiles(token: str = Header(...)):
    print(f"Profiles requested with token: {token}")
    response = {
        "secuses": True,
        "profiles": get_test_data("profiles", [])
    }
    print(f"Returning profiles: {response}")
    return response


@router.post("/device/add")
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


@router.get("/device/qr")
def get_device_qr():
    """Get QR code for device addition"""
    return get_test_data("device_qr", {
        "qr_url": "/img/other/qr-add-device.png",
        "site_url": "/add",
        "code_length": 6
    }) 