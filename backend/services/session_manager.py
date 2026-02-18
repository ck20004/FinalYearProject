from typing import Dict, Any, Optional, List
import time
import uuid
from redis_db.connection import redis_manager
from redis_db.config import redis_config

class RedisSessionManager:
    """Redis-based session manager"""
    
    def __init__(self):
        self.session_timeout = redis_config.session_timeout
        self.session_prefix = "session:"
        self.redis = redis_manager
    
    def _get_session_key(self, session_id: str) -> str:
        """Get Redis key for session"""
        return f"{self.session_prefix}{session_id}"
    
    async def store_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Store session data in Redis"""
        if not session_id:
            return False
        
        # Add timestamp
        data["created_at"] = time.time()
        data["last_accessed"] = time.time()
        
        key = self._get_session_key(session_id)
        success = await self.redis.set_json(key, data, expire=self.session_timeout)
        
        if success:
            print(f"✅ Session {session_id} stored in Redis")
        else:
            print(f"❌ Failed to store session {session_id} in Redis")
        
        return success
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data from Redis"""
        if not session_id:
            return None
        
        key = self._get_session_key(session_id)
        data = await self.redis.get_json(key)
        
        if data:
            # Update last accessed time
            data["last_accessed"] = time.time()
            await self.redis.set_json(key, data, expire=self.session_timeout)
            print(f"✅ Session {session_id} retrieved from Redis")
        else:
            print(f"⚠️  Session {session_id} not found in Redis")
        
        return data
    
    async def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update existing session data"""
        if not session_id:
            return False
        
        key = self._get_session_key(session_id)
        
        # Get existing data
        existing_data = await self.redis.get_json(key)
        if not existing_data:
            print(f"⚠️  Session {session_id} not found for update")
            return False
        
        # Merge data
        existing_data.update(data)
        existing_data["last_accessed"] = time.time()
        
        success = await self.redis.set_json(key, existing_data, expire=self.session_timeout)
        
        if success:
            print(f"✅ Session {session_id} updated in Redis")
        else:
            print(f"❌ Failed to update session {session_id} in Redis")
        
        return success
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete session from Redis"""
        if not session_id:
            return False
        
        key = self._get_session_key(session_id)
        success = await self.redis.delete(key)
        
        if success:
            print(f"✅ Session {session_id} deleted from Redis")
        else:
            print(f"⚠️  Session {session_id} not found for deletion")
        
        return success
    
    async def extend_session(self, session_id: str, additional_seconds: int = None) -> bool:
        """Extend session expiration"""
        if not session_id:
            return False
        
        key = self._get_session_key(session_id)
        expire_time = additional_seconds or self.session_timeout
        
        success = await self.redis.expire(key, expire_time)
        
        if success:
            print(f"✅ Session {session_id} expiration extended")
        
        return success
    
    async def get_all_sessions(self) -> List[str]:
        """Get all session IDs (for debugging)"""
        pattern = f"{self.session_prefix}*"
        keys = await self.redis.get_keys(pattern)
        return [key.replace(self.session_prefix, "") for key in keys]
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (Redis handles this automatically, but useful for stats)"""
        all_sessions = await self.get_all_sessions()
        valid_sessions = []
        
        for session_id in all_sessions:
            data = await self.get_session(session_id)
            if data:
                valid_sessions.append(session_id)
        
        expired_count = len(all_sessions) - len(valid_sessions)
        if expired_count > 0:
            print(f"🧹 Found {expired_count} expired sessions")
        
        return expired_count
    
    async def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        all_sessions = await self.get_all_sessions()
        
        return {
            "total_sessions": len(all_sessions),
            "session_timeout": self.session_timeout,
            "redis_connected": await self.redis.ping()
        }

# Global session manager instance
session_manager = RedisSessionManager()


# from typing import Dict, Any, Optional
# import time
# import uuid
# from redis_db.connection import redis_manager
# from redis_db.config import redis_config

# class SessionManager:
#     """Simple in-memory session storage. TODO: Replace with Redis/Database for production"""
    
#     def __init__(self):
#         self._sessions: Dict[str, Dict[str, Any]] = {}
#         self._session_timestamps: Dict[str, float] = {}
#         self.session_timeout = 3600  # 1 hour
    
#     def store_session(self, session_id: str, data: Dict[str, Any]) -> None:
#         """Store session data"""
#         self._sessions[session_id] = data
#         self._session_timestamps[session_id] = time.time()
    
#     def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
#         """Get session data"""
#         if session_id not in self._sessions:
#             return None
        
#         # Check if session has expired
#         if time.time() - self._session_timestamps[session_id] > self.session_timeout:
#             self.delete_session(session_id)
#             return None
        
#         return self._sessions[session_id]
    
#     def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
#         """Update existing session data"""
#         if session_id not in self._sessions:
#             return False
        
#         self._sessions[session_id].update(data)
#         self._session_timestamps[session_id] = time.time()
#         return True
    
#     def delete_session(self, session_id: str) -> bool:
#         """Delete session"""
#         if session_id in self._sessions:
#             del self._sessions[session_id]
#             del self._session_timestamps[session_id]
#             return True
#         return False
    
#     def cleanup_expired_sessions(self) -> None:
#         """Clean up expired sessions"""
#         current_time = time.time()
#         expired_sessions = [
#             session_id for session_id, timestamp in self._session_timestamps.items()
#             if current_time - timestamp > self.session_timeout
#         ]
        
#         for session_id in expired_sessions:
#             self.delete_session(session_id)