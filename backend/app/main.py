from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.chat import router as chat_router
from app.routes import reminders

app = FastAPI(
    title="AI Clinical Scheduling System",
    description="AI-powered appointment scheduling with natural language processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api", tags=["chat"])
app.include_router(reminders.router, prefix="/api/reminders", tags=["reminders"])

@app.get("/")
async def root():
    return {
        "name": "AI Clinical Scheduling System",
        "version": "2.0.0",
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}