from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from utils.test_data import get_test_data, update_test_data
from utils.premium import check_premium_status
import json
import time

router = APIRouter(tags=["websocket"])

# --- SOCKET ENDPOINTS ---
@router.websocket("/ws")
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