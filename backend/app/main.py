from fastapi import FastAPI
from app.routes.chat import router as chat_router

app = FastAPI(title="AI Clinical Scheduling System")

app.include_router(chat_router)
