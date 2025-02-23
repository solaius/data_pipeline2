import asyncio
from elasticsearch import AsyncElasticsearch
from doc_pipeline.config.settings import settings

async def test_elasticsearch_connection():
    print(f"Testing connection to Elasticsearch at {settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}")
    
    es = AsyncElasticsearch(
        hosts=[f"{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"],
        basic_auth=(
            settings.ELASTICSEARCH_USERNAME,
            settings.ELASTICSEARCH_PASSWORD
        ) if settings.ELASTICSEARCH_USERNAME else None
    )
    
    try:
        info = await es.info()
        print("Successfully connected to Elasticsearch!")
        print(f"Elasticsearch version: {info['version']['number']}")
        print(f"Cluster name: {info['cluster_name']}")
        
        # Check indices
        indices = await es.indices.get_alias()
        print("\nExisting indices:")
        for index in indices:
            print(f"- {index}")
            
    except Exception as e:
        print(f"Error connecting to Elasticsearch: {str(e)}")
    
    finally:
        await es.close()

if __name__ == "__main__":
    asyncio.run(test_elasticsearch_connection())