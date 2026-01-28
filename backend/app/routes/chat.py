from fastapi import APIRouter
from app.agents.orchestrator import route_request
from app.agents.dispatcher import execute

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/")
def chat(message: str):
    orchestration = route_request(message)

    intent = orchestration["intent"]
    parameters = orchestration["parameters"]

    result = execute(intent, parameters)

    return {
        "intent": intent,
        "parameters": parameters,
        "result": result
    }
