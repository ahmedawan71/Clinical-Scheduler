from datetime import datetime, timedelta
from typing import Optional
import json

class ConversationContext:
    """Manages conversation state and extracted entities"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.history = []
        self.extracted_info = {}
        self.max_history = 10
        self.created_at = datetime.utcnow()
        self.last_activity = datetime.utcnow()
    
    def add_turn(self, user_msg: str, intent: str, parameters: dict, response: dict):
        """Add a conversation turn"""
        self.history.append({
            "user": user_msg,
            "intent": intent,
            "parameters": parameters,
            "response_summary": self._summarize_response(response),
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep only recent history
        if len(self.history) > self.max_history:
            self.history.pop(0)
        
        self.last_activity = datetime.utcnow()
    
    def update_entity(self, key: str, value):
        """Store extracted entity for context"""
        if value:
            self.extracted_info[key] = {
                "value": value,
                "updated_at": datetime.utcnow().isoformat()
            }
    
    def get_entity(self, key: str) -> Optional[str]:
        """Retrieve stored entity"""
        entity = self.extracted_info.get(key)
        return entity["value"] if entity else None
    
    def get_context_summary(self) -> str:
        """Get summary for AI prompt"""
        if not self.extracted_info:
            return "No previous context."
        
        summary = []
        for key, data in self.extracted_info.items():
            summary.append(f"- {key}: {data['value']}")
        
        return "Known information:\n" + "\n".join(summary)
    
    def get_recent_history_for_prompt(self, turns: int = 3) -> list:
        """Get recent turns formatted for AI prompt"""
        return self.history[-turns:]
    
    def _summarize_response(self, response: dict) -> str:
        """Create brief summary of response"""
        if response.get("success"):
            return response.get("message", "Action completed")
        return response.get("error", "Action failed")
    
    def is_expired(self, timeout_minutes: int = 30) -> bool:
        """Check if session has expired"""
        return datetime.utcnow() - self.last_activity > timedelta(minutes=timeout_minutes)
    
    def clear(self):
        """Clear conversation context"""
        self.history = []
        self.extracted_info = {}


class ContextStore:
    """Manages multiple conversation contexts"""
    
    def __init__(self):
        self._contexts: dict[str, ConversationContext] = {}
    
    def get_or_create(self, session_id: str) -> ConversationContext:
        """Get existing context or create new one"""
        self._cleanup_expired()
        
        if session_id not in self._contexts:
            self._contexts[session_id] = ConversationContext(session_id)
        
        return self._contexts[session_id]
    
    def _cleanup_expired(self):
        """Remove expired sessions"""
        expired = [
            sid for sid, ctx in self._contexts.items() 
            if ctx.is_expired()
        ]
        for sid in expired:
            del self._contexts[sid]
    
    def clear_session(self, session_id: str):
        """Explicitly clear a session"""
        if session_id in self._contexts:
            del self._contexts[session_id]


# Global context store
context_store = ContextStore()