from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List
import json
import base64
import os

app = FastAPI()

bubbles: Dict[str, List[WebSocket]] = {}
file_buffers: Dict[str, bytearray] = {}

@app.websocket("/ws/{roomId}")
async def websocket_endpoint(websocket: WebSocket, roomId: str):
    await websocket.accept()

    if roomId not in bubbles:
        bubbles[roomId] = []

    bubbles[roomId].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)

            if message["type"] == "file":
                await handle_file_upload(message, websocket, roomId)

            for user in bubbles[roomId]:
                if user != websocket:
                    await user.send_text(json.dumps(message))

    except WebSocketDisconnect:
        bubbles[roomId].remove(websocket)

        if not bubbles[roomId]:
            del bubbles[roomId]
        print(f"User left the bubble: {roomId}")


async def handle_file_upload(message: dict, websocket: WebSocket, roomId: str):
    """Handle receiving and sending files in chunks."""
    file_name = message["fileName"]
    file_data = message["data"]

    if file_name not in file_buffers:
        file_buffers[file_name] = bytearray()

    # Add the new chunk of data
    decoded_data = base64.b64decode(file_data)
    file_buffers[file_name].extend(decoded_data)

    # Send an acknowledgment or status update to the user
    await websocket.send_text(json.dumps({
        "type": "file",
        "fileName": file_name,
        "status": "received chunk"
    }))

    if len(file_buffers[file_name]) == message.get("totalSize", 0):
        save_file(file_name, file_buffers[file_name])
        # Clear the buffer after saving the file
        del file_buffers[file_name]
        # Notify the user that the file has been fully received
        await websocket.send_text(json.dumps({
            "type": "file",
            "fileName": file_name,
            "status": "File received successfully"
        }))


def save_file(file_name: str, file_data: bytearray):
    """Save the file to the server."""
    with open(file_name, "wb") as f:
        f.write(file_data)
    print(f"File {file_name} saved successfully.")
