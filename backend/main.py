from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sys
import os

# ✅ Add project root to sys.path so agent and calendar_api are discoverable
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from agent.agent import process_message  # ✅ works if agent.py is inside agent/

app = FastAPI(title="TailorTalk Booking Agent")

class MessageRequest(BaseModel):
    message: str

@app.post("/process_message")
async def process_user_message(request: MessageRequest):
    try:
        response = process_message(request.message)
        return {"response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
