import asyncio
from elasticsearch import AsyncElasticsearch
import redis as redis_client  # Renamed to avoid conflict
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get settings from environment
ES_HOST = os.getenv('ELASTICSEARCH_HOST', 'http://192.168.1.17')
ES_PORT = os.getenv('ELASTICSEARCH_PORT', '9200')
ES_USER = os.getenv('ELASTICSEARCH_USERNAME', '')
ES_PASS = os.getenv('ELASTICSEARCH_PASSWORD', '')

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_PASS = os.getenv('REDIS_PASSWORD', '')

async def test_elasticsearch():
    print(f"\nTesting Elasticsearch connection to {ES_HOST}:{ES_PORT}")
    
    es = AsyncElasticsearch(
        hosts=[f"{ES_HOST}:{ES_PORT}"],
        basic_auth=(ES_USER, ES_PASS) if ES_USER else None
    )
    
    try:
        info = await es.info()
        print("✓ Successfully connected to Elasticsearch!")
        print(f"  Version: {info['version']['number']}")
        print(f"  Cluster: {info['cluster_name']}")
        
        # Check indices
        indices = await es.indices.get_alias()
        print("\nExisting indices:")
        for index in indices:
            print(f"  - {index}")
            
    except Exception as e:
        print(f"✗ Error connecting to Elasticsearch: {str(e)}")
    
    finally:
        await es.close()

def test_redis():
    print(f"\nTesting Redis connection to {REDIS_HOST}:{REDIS_PORT}")
    
    try:
        # Create Redis client
        r = redis_client.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            password=REDIS_PASS if REDIS_PASS else None,
            decode_responses=True
        )
        
        # Test connection
        if r.ping():
            print("✓ Successfully connected to Redis!")
            
            # Test operations
            r.set("test_key", "test_value")
            value = r.get("test_key")
            if value == "test_value":
                print("✓ Redis operations working correctly")
            else:
                print("✗ Redis operations failed")
            
            # Clean up
            r.delete("test_key")
        else:
            print("✗ Redis ping failed")
            
    except redis_client.ConnectionError as e:
        print(f"✗ Error connecting to Redis: Connection refused. Is Redis running?")
    except Exception as e:
        print(f"✗ Error with Redis: {str(e)}")
    
    finally:
        try:
            r.close()
        except:
            pass

async def main():
    print("Testing connections to services...")
    await test_elasticsearch()
    test_redis()  # Redis test is now synchronous

if __name__ == "__main__":
    asyncio.run(main())