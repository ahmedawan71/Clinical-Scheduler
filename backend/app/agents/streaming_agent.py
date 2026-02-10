from app.config import client, DEPLOYMENT_NAME
from app.agents.dispatcher import execute
from app.agents.orchestrator import update_context_after_execution
from app.utils.logger import agent_logger
from typing import Generator

def stream_response(user_message: str, intent_data: dict, session_id: str = "default") -> Generator[str, None, None]:
    """
    Stream response with real-time status updates.
    Integrates with context management for multi-turn conversations.
    """
    
    # Handle errors from orchestrator
    if intent_data.get("error"):
        yield f"❌ Sorry, I encountered an error: {intent_data.get('error')}\n"
        yield "Please try rephrasing your request."
        return
    
    # Handle clarification needed
    if intent_data.get("needs_clarification"):
        question = intent_data.get("clarification_question", "Could you provide more details?")
        yield f"🤔 {question}"
        return
    
    intent = intent_data.get("intent")
    parameters = intent_data.get("parameters", {})
    confidence = intent_data.get("confidence", 0)
    
    # Log low confidence intents
    if confidence < 0.7:
        agent_logger.warning(f"Low confidence intent: {intent} ({confidence})")
    
    # Yield status update based on intent
    status_messages = {
        "check_availability": "🔍 Checking availability",
        "book_appointment": "📅 Processing your booking",
        "cancel_appointment": "🗑️ Processing cancellation",
        "reschedule_appointment": "🔄 Rescheduling appointment",
        "get_appointments": "📋 Fetching your appointments",
        "get_history": "📊 Loading appointment history",
        "find_next_available": "🔎 Searching for available slots",
        "suggest_alternatives": "👨‍⚕️ Finding alternative doctors",
        "add_to_waitlist": "📝 Adding you to the waitlist",
        "get_waitlist_status": "📋 Checking your waitlist status",
        "schedule_follow_up": "📆 Scheduling follow-up",
    }
    
    status = status_messages.get(intent, "⚙️ Processing your request")
    yield f"{status}...\n\n"
    
    # Execute the action
    try:
        result = execute(intent, parameters)
    except Exception as e:
        agent_logger.error(f"Execution failed: {e}")
        yield f"❌ Sorry, something went wrong: {str(e)}"
        return
    
    # Update conversation context
    update_context_after_execution(session_id, user_message, intent, parameters, result)
    
    # Handle execution errors
    if not result.get("success", True) and result.get("error"):
        yield f"❌ {result.get('error')}\n"
        
        # Provide helpful suggestions
        if result.get("suggestion"):
            yield f"\n💡 Suggestion: {result.get('suggestion')}"
        return
    
    # Handle confirmation required (e.g., late cancellation)
    if result.get("confirm_required"):
        yield f"⚠️ {result.get('warning')}\n\n"
        yield "Would you like to proceed anyway? Reply with 'yes' to confirm."
        return
    
    # Generate natural language response using AI
    yield from _generate_natural_response(intent, result)


def _generate_natural_response(intent: str, result: dict) -> Generator[str, None, None]:
    """Generate a conversational response from the result"""
    
    system_prompt = """You are a friendly clinical scheduling assistant. 
Convert the JSON result into a natural, conversational response.

Guidelines:
- Be concise but helpful
- Use emojis sparingly for readability (✅, 📅, 🕐, 👨‍⚕️)
- For appointments, clearly state date, time, and doctor
- For availability, list times in a readable format
- For errors, be apologetic and suggest next steps
- Don't mention JSON or technical terms
- Keep responses under 150 words"""

    user_prompt = f"""Intent: {intent}
Result: {result}

Generate a friendly response for the user."""

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=True,
            temperature=0.7,
            max_tokens=300
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        agent_logger.error(f"Streaming generation failed: {e}")
        # Fallback to simple response
        yield _generate_fallback_response(intent, result)


def _generate_fallback_response(intent: str, result: dict) -> str:
    """Generate simple fallback response if AI streaming fails"""
    
    if result.get("success") == False:
        return f"❌ {result.get('error', 'Request failed')}"
    
    fallback_templates = {
        "check_availability": lambda r: f"✅ Dr. {r.get('doctor')} has {r.get('available_count', 0)} slots available on {r.get('date')}.",
        "book_appointment": lambda r: f"✅ {r.get('message', 'Appointment booked successfully!')}",
        "cancel_appointment": lambda r: f"✅ {r.get('message', 'Appointment cancelled.')}",
        "get_appointments": lambda r: f"📋 Found {r.get('upcoming_count', 0)} upcoming appointments.",
        "find_next_available": lambda r: f"✅ Next available slot: {r.get('next_available_date')} at {r.get('available_slots', ['N/A'])[0]}",
    }
    
    template = fallback_templates.get(intent)
    if template:
        try:
            return template(result)
        except:
            pass
    
    return f"✅ {result.get('message', 'Request completed successfully.')}"


def stream_simple(message: str) -> Generator[str, None, None]:
    """Simple streaming for general responses without intent execution"""
    
    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful clinical scheduling assistant. Answer questions about scheduling, appointments, and clinic services."
                },
                {"role": "user", "content": message}
            ],
            stream=True,
            temperature=0.7
        )

        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
                
    except Exception as e:
        agent_logger.error(f"Simple streaming failed: {e}")
        yield "I apologize, but I'm having trouble responding right now. Please try again."
