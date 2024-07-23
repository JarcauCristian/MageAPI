from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
clients = []


@router.websocket("/mage/ws")
async def main_websocket(websocket: WebSocket):
    await websocket.accept()
    clients.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(data)
            await broadcast_message(data)
    except WebSocketDisconnect:
        if websocket in clients:
            clients.remove(websocket)
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        if websocket in clients:
            clients.remove(websocket)


async def broadcast_message(message: str):
    disconnected_clients = []
    for client in clients:
        try:
            await client.send_text(message)
        except WebSocketDisconnect:
            disconnected_clients.append(client)
        except Exception as e:
            print(f"Error sending message to client: {e}")
            disconnected_clients.append(client)

    for client in disconnected_clients:
        if client in clients:
            clients.remove(client)
