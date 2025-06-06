"""
Serverless Session Manager for Vercel Deployment
Handles session storage using Redis or in-memory fallback
"""

import os
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import jsonpickle

# Try to import Redis, fallback to in-memory if not available
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class ServerlessSessionManager:
    """
    Session manager that works in serverless environments
    Uses Redis if available, otherwise falls back to in-memory storage
    """
    
    def __init__(self):
        self.redis_client = None
        self.memory_sessions = {}  # Fallback for development
        self.session_timeout = 300  # 5 minutes default
        
        # Initialize Redis if available and configured
        if REDIS_AVAILABLE and os.environ.get('REDIS_URL'):
            try:
                self.redis_client = redis.from_url(
                    os.environ.get('REDIS_URL'),
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Test connection
                self.redis_client.ping()
                print("✅ Redis connected for serverless sessions")
            except Exception as e:
                print(f"⚠️ Redis connection failed, using memory fallback: {e}")
                self.redis_client = None
        else:
            print("📝 Using in-memory sessions (development mode)")
    
    def create_session(self, initial_data: Dict[str, Any] = None) -> str:
        """Create a new session and return session ID"""
        session_id = str(uuid.uuid4())
        session_data = {
            'created_at': datetime.now().isoformat(),
            'last_accessed': datetime.now().isoformat(),
            'data': initial_data or {}
        }
        
        self._store_session(session_id, session_data)
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by ID"""
        if not session_id:
            return None
            
        session_data = self._get_session(session_id)
        if not session_data:
            return None
        
        # Check if session is expired
        last_accessed = datetime.fromisoformat(session_data['last_accessed'])
        if datetime.now() - last_accessed > timedelta(seconds=self.session_timeout):
            self.delete_session(session_id)
            return None
        
        # Update last accessed time
        session_data['last_accessed'] = datetime.now().isoformat()
        self._store_session(session_id, session_data)
        
        return session_data['data']
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data"""
        session_data = self._get_session(session_id)
        if not session_data:
            return False
        
        session_data['data'].update(data)
        session_data['last_accessed'] = datetime.now().isoformat()
        self._store_session(session_id, session_data)
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if self.redis_client:
            try:
                self.redis_client.delete(f"session:{session_id}")
                return True
            except Exception as e:
                print(f"Redis delete error: {e}")
                return False
        else:
            return self.memory_sessions.pop(session_id, None) is not None
    
    def extend_session(self, session_id: str, additional_seconds: int = 300) -> bool:
        """Extend session timeout"""
        session_data = self._get_session(session_id)
        if not session_data:
            return False
        
        session_data['last_accessed'] = datetime.now().isoformat()
        self._store_session(session_id, session_data)
        return True
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions (mainly for memory storage)"""
        if not self.redis_client:
            current_time = datetime.now()
            expired_sessions = []
            
            for session_id, session_data in self.memory_sessions.items():
                last_accessed = datetime.fromisoformat(session_data['last_accessed'])
                if current_time - last_accessed > timedelta(seconds=self.session_timeout):
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.memory_sessions[session_id]
    
    def get_session_count(self) -> int:
        """Get total number of active sessions"""
        if self.redis_client:
            try:
                keys = self.redis_client.keys("session:*")
                return len(keys)
            except Exception:
                return 0
        else:
            self.cleanup_expired_sessions()
            return len(self.memory_sessions)
    
    def clear_all_sessions(self):
        """Clear all sessions"""
        if self.redis_client:
            try:
                keys = self.redis_client.keys("session:*")
                if keys:
                    self.redis_client.delete(*keys)
            except Exception as e:
                print(f"Redis clear error: {e}")
        else:
            self.memory_sessions.clear()
    
    def _store_session(self, session_id: str, session_data: Dict[str, Any]):
        """Store session data"""
        if self.redis_client:
            try:
                serialized = jsonpickle.encode(session_data)
                self.redis_client.setex(
                    f"session:{session_id}",
                    self.session_timeout,
                    serialized
                )
            except Exception as e:
                print(f"Redis store error: {e}")
                # Fallback to memory
                self.memory_sessions[session_id] = session_data
        else:
            self.memory_sessions[session_id] = session_data
    
    def _get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from storage"""
        if self.redis_client:
            try:
                serialized = self.redis_client.get(f"session:{session_id}")
                if serialized:
                    return jsonpickle.decode(serialized)
            except Exception as e:
                print(f"Redis get error: {e}")
                # Try memory fallback
                pass
        
        return self.memory_sessions.get(session_id)

# Global session manager instance
session_manager = ServerlessSessionManager() 