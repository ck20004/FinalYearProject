import redis.asyncio as aioredis
import redis
import json
import pickle
from typing import Any, Optional, Dict, List
from .config import redis_config
import asyncio

class RedisManager:
    """Redis connection and operation manager"""
    
    def __init__(self):
        self.redis_url = redis_config.get_redis_url()
        self.async_redis: Optional[aioredis.Redis] = None
        self.sync_redis: Optional[redis.Redis] = None
        self._connection_pool = None
    
    async def connect(self):
        """Establish async Redis connection"""
        try:
            # Create connection pool
            self._connection_pool = aioredis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=redis_config.redis_max_connections,
                retry_on_timeout=redis_config.redis_retry_on_timeout,
                socket_timeout=redis_config.redis_socket_timeout,
                socket_connect_timeout=redis_config.redis_socket_connect_timeout
            )
            
            # Create async Redis client
            self.async_redis = aioredis.Redis(connection_pool=self._connection_pool)
            
            # Test connection
            await self.async_redis.ping()
            print("✅ Connected to Redis (async)")
            
        except Exception as e:
            print(f"❌ Failed to connect to Redis: {e}")
            print("Make sure Redis is running: redis-server")
            self.async_redis = None
    
    def connect_sync(self):
        """Establish synchronous Redis connection"""
        try:
            self.sync_redis = redis.Redis.from_url(
                self.redis_url,
                max_connections=redis_config.redis_max_connections,
                retry_on_timeout=redis_config.redis_retry_on_timeout,
                socket_timeout=redis_config.redis_socket_timeout,
                socket_connect_timeout=redis_config.redis_socket_connect_timeout
            )
            
            # Test connection
            self.sync_redis.ping()
            print("✅ Connected to Redis (sync)")
            
        except Exception as e:
            print(f"❌ Failed to connect to Redis (sync): {e}")
            self.sync_redis = None
    
    async def disconnect(self):
        """Close Redis connections"""
        if self.async_redis:
            await self.async_redis.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()
    
    def is_connected(self) -> bool:
        """Check if Redis is connected"""
        return self.async_redis is not None
    
    async def ping(self) -> bool:
        """Test Redis connection"""
        try:
            if self.async_redis:
                await self.async_redis.ping()
                return True
        except:
            pass
        return False
    
    # JSON operations
    async def set_json(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Store JSON data in Redis"""
        try:
            if not self.async_redis:
                return False
            
            json_data = json.dumps(value, default=str)
            result = await self.async_redis.set(key, json_data, ex=expire)
            return result is True
        except Exception as e:
            print(f"Redis set_json error: {e}")
            return False
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON data from Redis"""
        try:
            if not self.async_redis:
                return None
            
            data = await self.async_redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis get_json error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            if not self.async_redis:
                return False
            
            result = await self.async_redis.delete(key)
            return result > 0
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            if not self.async_redis:
                return False
            
            result = await self.async_redis.exists(key)
            return result > 0
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for key"""
        try:
            if not self.async_redis:
                return False
            
            result = await self.async_redis.expire(key, seconds)
            return result is True
        except Exception as e:
            print(f"Redis expire error: {e}")
            return False
    
    async def get_keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern"""
        try:
            if not self.async_redis:
                return []
            
            keys = await self.async_redis.keys(pattern)
            return [key.decode() for key in keys]
        except Exception as e:
            print(f"Redis get_keys error: {e}")
            return []
    
    # Hash operations (useful for session data)
    async def hset_json(self, key: str, field: str, value: Any) -> bool:
        """Set hash field with JSON value"""
        try:
            if not self.async_redis:
                return False
            
            json_data = json.dumps(value, default=str)
            result = await self.async_redis.hset(key, field, json_data)
            return result >= 0
        except Exception as e:
            print(f"Redis hset_json error: {e}")
            return False
    
    async def hget_json(self, key: str, field: str) -> Optional[Any]:
        """Get hash field as JSON"""
        try:
            if not self.async_redis:
                return None
            
            data = await self.async_redis.hget(key, field)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis hget_json error: {e}")
            return None
    
    async def hgetall_json(self, key: str) -> Dict[str, Any]:
        """Get all hash fields as JSON"""
        try:
            if not self.async_redis:
                return {}
            
            data = await self.async_redis.hgetall(key)
            result = {}
            for field, value in data.items():
                try:
                    result[field.decode()] = json.loads(value)
                except:
                    result[field.decode()] = value.decode()
            return result
        except Exception as e:
            print(f"Redis hgetall_json error: {e}")
            return {}

# Global Redis manager instance
redis_manager = RedisManager()