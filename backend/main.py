from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from .api import router as api_router
import asyncio
import json

app = FastAPI(title="Chamo-web API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
app.include_router(api_router)

async def generate_derivative_data(data, time_data):
    """Generálja a derivált adatokat darabonként"""
    for i in range(1, len(data)):
        # Számítsuk ki a deriváltat
        derivative = (data[i] - data[i-1]) / (time_data[i] - time_data[i-1])
        
        # Küldjük el az adatot
        yield f"data: {json.dumps({'x': time_data[i], 'y': derivative})}\n\n"
        await asyncio.sleep(0.01)  # Kis késleltetés a valós idejű hatásért

@app.get("/stream-derivative")
async def stream_derivative(request: Request):
    """SSE végpont a derivált adatok streameléséhez"""
    # TODO: Itt kellene lekérni a valós adatokat
    # Példa adatok:
    data = [1, 2, 3, 4, 5]
    time_data = [0, 1, 2, 3, 4]
    
    return StreamingResponse(
        generate_derivative_data(data, time_data),
        media_type="text/event-stream"
    )
