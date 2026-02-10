import json
from datetime import datetime
from app.agents.context_manager import context_store
from app.config import client, DEPLOYMENT_NAME
from app.utils.logger import agent_logger

def route_request(user_message: str, session_id: str = "default"):
    """
    Uses GPT to extract intent and parameters.
    """

    context = context_store.get_or_create(session_id)
    
    system_prompt = f"""You are an AI orchestrator for a clinical scheduling system that determines user intent.

Current date/time: {datetime.now().strftime("%Y-%m-%d %H:%M")}

CONVERSATION CONTEXT:
{context.get_context_summary()}

INSTRUCTIONS:
1. Extract the user's intent from their message
2. Use context to fill in missing information (e.g., if patient name was mentioned before)
3. If critical information is missing and not in context, set needs_clarification=true
4. Extract any new entities mentioned (names, dates, times, etc.)

SUPPORTED INTENTS:
- check_availability: Check if a doctor is available (needs: doctor_name, date)
- book_appointment: Book an appointment (needs: patient_name, doctor_name, date, time)
- cancel_appointment: Cancel an appointment (needs: appointment_id OR patient_name+date)
- reschedule_appointment: Reschedule (needs: appointment_id, new_date, new_time)
- get_appointments: View appointments (needs: patient_name OR doctor_name)
- get_history: View patient history (needs: patient_name)
- find_next_available: Find next open slot (needs: doctor_name, preferred_date)
- suggest_alternatives: Find other doctors (needs: specialty, date)
- general_inquiry: General questions about the system

RESPONSE FORMAT (JSON only):
{{
    "intent": "intent_name",
    "parameters": {{
        "param1": "value1"
    }},
    "needs_clarification": false,
    "clarification_question": null,
    "extracted_entities": {{
        "patient_name": "extracted name if mentioned",
        "doctor_name": "extracted doctor if mentioned",
        "date": "extracted date if mentioned (YYYY-MM-DD format)",
        "time": "extracted time if mentioned (HH:MM format)"
    }},
    "confidence": 0.95
}}
"""

    messages = [{"role": "system", "content": system_prompt}]
    
    #Add recent conversation histoy
    for turn in context.get_recent_history_for_prompt(3):
        messages.append({"role": "user", "content": turn["user"]})
        messages.append({"role": "assistant", "content": json.dumps({
            "intent" : turn["intent"],
            "parameters" : turn["parameters"],
        })})
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=messages,
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
    
    #update context with extracted entities
        for key, value in result.get("extracted_entities", {}).items():
            if value:
                context.update_entity(key, value)
        
        #fill in parameters with context if missing
        result["parameters"] = _fill_from_context(result["parameters"], context)
        
        agent_logger.info(f"Routed to intent: {result.get('intent')} with confidence: {result.get('confidence', 'N/A')}")

        return result
    
    except json.JSONDecodeError  as e:
        agent_logger.error(f"Failed to parse AI response: {str(e)}")
        return {"intent": "unknown", "parameters": {},"needs_clarification": True, "clarification_question": "Could you please clarify your request?","error": "Failed to parse intent"}

    
    except Exception as e:
        agent_logger.error(f"Orchestration error: {e}")
        return {
            "intent":"error",
            "parameters": {},
            "error": str(e)
        }

def _fill_from_context(parameters: dict, context) -> dict:
    """Fill missing parameters from conversation context"""
    
    context_mappings = {
        "patient_name": "patient_name",
        "doctor_name": "doctor_name",
        "date": "date",
        "time": "time",
        "appointment_type": "appointment_type"
    }
    
    for param, context_key in context_mappings.items():
        if not parameters.get(param):
            context_value = context.get_entity(context_key)
            if context_value:
                parameters[param] = context_value
    
    return parameters

def update_context_after_execution(session_id: str, user_message: str, intent: str, parameters: dict, result: dict):
    """Update conversation context after executing an action"""
    context = context_store.get_or_create(session_id)
    context.add_turn(user_message, intent, parameters, result)
    
def clear_context(session_id: str):
    """Clear conversation context for a session"""
    context_store.clear_session(session_id)