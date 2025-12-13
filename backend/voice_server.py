import asyncio
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()

    try:
        # Import here to avoid errors if pipecat not installed
        from pipecat.transports.smallwebrtc.connection import SmallWebRTCConnection
        from pipeline import run_pipeline

        conn = SmallWebRTCConnection()

        # Receive offer from client
        offer = await ws.receive_json()
        await conn.initialize(sdp=offer["sdp"], type=offer["type"])

        # Send answer back
        answer = conn.get_answer()
        await ws.send_json({"sdp": answer.sdp, "type": answer.type})

        # Run pipeline (keeps connection alive)
        await run_pipeline(conn)

    except WebSocketDisconnect:
        print("Client disconnected")
    except ImportError as e:
        await ws.send_json({"error": f"Missing dependency: {e}"})
    except Exception as e:
        print(f"Error: {e}")
        await ws.send_json({"error": str(e)})

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=7860)
