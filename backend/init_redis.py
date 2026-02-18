import asyncio
from redis_db.connection import redis_manager
from services.session_manager import session_manager

async def init_redis():
    """Initialize Redis connection"""
    print("Initializing Redis Connection...")
    print("-" * 40)
    
    # Connect to Redis
    await redis_manager.connect()
    
    if redis_manager.is_connected():
        print("✅ Redis connection successful!")
        
        # Test basic operations
        test_key = "test:connection"
        test_data = {"message": "Redis is working!", "timestamp": "now"}
        
        # Test set
        success = await redis_manager.set_json(test_key, test_data, expire=60)
        if success:
            print("✅ Redis set operation successful")
        
        # Test get
        retrieved_data = await redis_manager.get_json(test_key)
        if retrieved_data:
            print(f"✅ Redis get operation successful: {retrieved_data}")
        
        # Test session manager
        test_session_id = "test-session-123"
        session_data = {
            "type": "test",
            "user": "test_user",
            "data": {"test": True}
        }
        
        # Store session
        session_stored = await session_manager.store_session(test_session_id, session_data)
        if session_stored:
            print("✅ Session storage successful")
        
        # Retrieve session
        retrieved_session = await session_manager.get_session(test_session_id)
        if retrieved_session:
            print(f"✅ Session retrieval successful")
        
        # Get stats
        stats = await session_manager.get_session_stats()
        print(f"📊 Session stats: {stats}")
        
        # Cleanup test data
        await redis_manager.delete(test_key)
        await session_manager.delete_session(test_session_id)
        print("🧹 Test data cleaned up")
        
    else:
        print("❌ Redis connection failed!")
        print("Make sure Redis server is running:")
        print("  Windows: Download and run Redis server")
        print("  Linux/Mac: redis-server")
        print("  Docker: docker run -d -p 6379:6379 redis:latest")

async def shutdown_redis():
    """Shutdown Redis connections"""
    await redis_manager.disconnect()
    print("👋 Redis connections closed")

if __name__ == "__main__":
    asyncio.run(init_redis())