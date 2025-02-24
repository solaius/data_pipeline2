import asyncio
import aiohttp
import json
import sys
from pathlib import Path
from elasticsearch import AsyncElasticsearch
from doc_pipeline.config.settings import settings

async def test_full_pipeline(file_path: str):
    """Test the complete document processing pipeline including embeddings and vector storage."""
    base_url = "http://localhost:8000/api/v1/documents"
    
    async with aiohttp.ClientSession() as session:
        # 1. Upload document
        print(f"\n1. Uploading document: {file_path}")
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file',
                         f,
                         filename=Path(file_path).name,
                         content_type='application/octet-stream')
            
            async with session.post(f"{base_url}/documents/", data=data) as response:
                if response.status != 200:
                    print(f"Error uploading document: {await response.text()}")
                    return
                
                result = await response.json()
                doc_id = result['doc_id']
                print(f"Document uploaded successfully. ID: {doc_id}")
        
        # 2. Monitor processing status
        print("\n2. Monitoring processing status...")
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            async with session.get(f"{base_url}/documents/{doc_id}/status") as response:
                if response.status != 200:
                    print(f"Error checking status: {await response.text()}")
                    return
                
                status = await response.text()
                status = status.strip('"')
                print(f"Status: {status}")
                
                if status in ['COMPLETED', 'FAILED']:
                    break
                
                attempt += 1
                await asyncio.sleep(1)
        
        if attempt >= max_attempts:
            print("Timeout waiting for processing to complete")
            return
        
        # 3. Retrieve processed document and chunks
        print("\n3. Retrieving processed document...")
        async with session.get(f"{base_url}/documents/{doc_id}") as response:
            if response.status != 200:
                print(f"Error retrieving document: {await response.text()}")
                return
            
            document = await response.json()
            
            print("\nDocument Details:")
            print(f"ID: {document['doc_id']}")
            print(f"Filename: {document['filename']}")
            print(f"Status: {document['status']}")
            print(f"Content Type: {document['content_type']}")
            print(f"Number of chunks: {len(document['chunks'])}")
            
            # 4. Generate embeddings for first chunk
            if document['chunks']:
                first_chunk = document['chunks'][0]
                print("\n4. Generating embeddings for first chunk...")
                
                # Generate Nomic embedding
                print("\nGenerating Nomic embedding...")
                async with session.post(
                    f"{base_url}/embeddings/generate",
                    json={
                        "text": first_chunk['content'],
                        "provider": "nomic"
                    }
                ) as response:
                    if response.status != 200:
                        print(f"Error generating Nomic embedding: {await response.text()}")
                    else:
                        nomic_result = await response.json()
                        print(f"Nomic embedding generated. Dimension: {len(nomic_result['embedding'])}")
                
                # Generate Granite embedding
                print("\nGenerating Granite embedding...")
                async with session.post(
                    f"{base_url}/embeddings/generate",
                    json={
                        "text": first_chunk['content'],
                        "provider": "granite"
                    }
                ) as response:
                    if response.status != 200:
                        print(f"Error generating Granite embedding: {await response.text()}")
                    else:
                        granite_result = await response.json()
                        print(f"Granite embedding generated. Dimension: {len(granite_result['embedding'])}")

        # 5. Verify vectors in Elasticsearch
        print("\n5. Verifying vectors in Elasticsearch...")
        es = AsyncElasticsearch(
            hosts=[f"{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"],
            basic_auth=(
                settings.ELASTICSEARCH_USERNAME,
                settings.ELASTICSEARCH_PASSWORD
            ) if settings.ELASTICSEARCH_USERNAME else None
        )
        
        try:
            # Check index exists
            index_exists = await es.indices.exists(index="document_embeddings")
            if index_exists:
                print("Document embeddings index exists")
                
                # Get index mapping
                mapping = await es.indices.get_mapping(index="document_embeddings")
                print("\nIndex mapping:")
                print(json.dumps(mapping, indent=2))
                
                # Search for embeddings of the first chunk
                search_result = await es.search(
                    index="document_embeddings",
                    body={
                        "query": {
                            "match": {
                                "chunk_id": first_chunk['chunk_id']
                            }
                        }
                    }
                )
                
                hits = search_result['hits']['hits']
                print(f"\nFound {len(hits)} embeddings for chunk {first_chunk['chunk_id']}")
                for hit in hits:
                    print(f"Provider: {hit['_source']['embedding_provider']}")
                    print(f"Embedding dimension: {len(hit['_source']['embedding'])}")
                    print(f"Score: {hit['_score']}")
            else:
                print("Document embeddings index does not exist!")
                
        except Exception as e:
            print(f"Error checking Elasticsearch: {str(e)}")
        
        finally:
            await es.close()

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_full_pipeline.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    asyncio.run(test_full_pipeline(file_path))

if __name__ == "__main__":
    main()