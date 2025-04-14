from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import base64
import os
from typing import Dict

app = FastAPI()

bubbles: Dict[str, list] = {}

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
            
            if message['type'] == 'file':
                # Process file chunk
                file_name = message['fileName']
                file_data = message['data']
                total_size = message['totalSize']
                offset = message['offset']

                # Rebuild the file in chunks
                file_path = f"uploads/{file_name}"

                if not os.path.exists(file_path):
                    with open(file_path, 'wb') as f:
                        f.write(base64.b64decode(file_data))
                else:
                    with open(file_path, 'ab') as f:
                        f.write(base64.b64decode(file_data))

                # Notify all other users in the room about the received file
                for user in bubbles[roomId]:
                    if user != websocket:
                        await user.send_text(json.dumps({
                            'type': 'file',
                            'fileName': file_name,
                            'data': file_path
                        }))
    
    except WebSocketDisconnect:
        bubbles[roomId].remove(websocket)
        if not bubbles[roomId]:
            del bubbles[roomId]

        print(f"User left the bubble: {roomId}")
