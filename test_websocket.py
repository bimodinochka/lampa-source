import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws"
    try:
        async with websockets.connect(uri) as websocket:
            print("WebSocket connected successfully!")
            
            # Отправляем тестовое сообщение
            test_message = {
                "method": "check_token",
                "data": {
                    "token": "test_token"
                }
            }
            
            await websocket.send(json.dumps(test_message))
            print(f"Sent message: {test_message}")
            
            # Получаем ответ
            response = await websocket.recv()
            print(f"Received response: {response}")
            
    except Exception as e:
        print(f"WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket()) 