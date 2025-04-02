from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import uvicorn

app = FastAPI()

bubbles : Dict[str, List[WebSocket]] = {}

@app.websocket("/ws/{roomId}")
async def websocketEndpoint(websocket: WebSocket, roomId: str):
    await websocket.accept()

    if roomId not in bubbles:
        bubbles[roomId] = []

    bubbles[roomId].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
        
            for user in bubbles[roomId]:
                if user != websocket:
                    await user.send_text(json.dumps(message))
    
    except WebSocketDisconnect:
        bubbles[roomId].remove(websocket)

        if not bubbles[roomId]:
            del bubbles[roomId]
        print(f"User left the bubble: {roomId}")

if __name__ == "__main__":
    uvicorn.run(app , host="0.0.0.0", port=8000)