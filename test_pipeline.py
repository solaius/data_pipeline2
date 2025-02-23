import asyncio
import aiohttp
import json
import sys
from pathlib import Path
import time

async def test_pipeline(file_path: str):
    """Test the document processing pipeline with a file."""
    base_url = "http://localhost:8000/api/v1/documents/documents"
    
    async with aiohttp.ClientSession() as session:
        # 1. Upload document
        print(f"\n1. Uploading document: {file_path}")
        with open(file_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file',
                         f,
                         filename=Path(file_path).name,
                         content_type='application/octet-stream')
            
            async with session.post(f"{base_url}/", data=data) as response:
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
            async with session.get(f"{base_url}/{doc_id}/status") as response:
                if response.status != 200:
                    print(f"Error checking status: {await response.text()}")
                    return
                
                status = await response.text()
                status = status.strip('"')  # Remove quotes from status string
                print(f"Status: {status}")
                
                if status in ['COMPLETED', 'FAILED']:
                    break
                
                attempt += 1
                await asyncio.sleep(1)
        
        if attempt >= max_attempts:
            print("Timeout waiting for processing to complete")
            return
        
        # 3. Retrieve processed document
        print("\n3. Retrieving processed document...")
        async with session.get(f"{base_url}/{doc_id}") as response:
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
            
            print("\nFirst few chunks:")
            for chunk in document['chunks'][:3]:  # Show first 3 chunks
                print("\nChunk ID:", chunk['chunk_id'])
                print("Page:", chunk['page_number'])
                print("Content:", chunk['content'][:200] + "..." if len(chunk['content']) > 200 else chunk['content'])
                print("Metadata:", json.dumps(chunk['metadata'], indent=2))

def main():
    if len(sys.argv) != 2:
        print("Usage: python test_pipeline.py <file_path>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not Path(file_path).exists():
        print(f"File not found: {file_path}")
        sys.exit(1)
    
    asyncio.run(test_pipeline(file_path))

if __name__ == "__main__":
    main()