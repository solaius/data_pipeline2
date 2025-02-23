import asyncio
import aioredis
from doc_pipeline.config.settings import settings

async def test_redis_connection():
    print(f"Testing connection to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
    
    redis = aioredis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        password=settings.REDIS_PASSWORD,
        encoding="utf-8",
        decode_responses=True
    )
    
    try:
        # Test connection
        await redis.ping()
        print("Successfully connected to Redis!")
        
        # Test basic operations
        await redis.set("test_key", "test_value")
        value = await redis.get("test_key")
        print(f"Test key-value operation successful: {value == 'test_value'}")
        
        # Clean up
        await redis.delete("test_key")
        
    except Exception as e:
        print(f"Error connecting to Redis: {str(e)}")
    
    finally:
        await redis.close()

if __name__ == "__main__":
    asyncio.run(test_redis_connection())