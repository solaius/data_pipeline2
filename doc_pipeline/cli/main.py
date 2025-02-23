import click
import requests
import json
from pathlib import Path
from typing import Optional

API_URL = "http://localhost:50007"

@click.group()
def cli():
    """Document Processing Pipeline CLI"""
    pass

@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
def upload(file_path: str):
    """Upload a document for processing"""
    path = Path(file_path)
    files = {'file': (path.name, open(path, 'rb'))}
    response = requests.post(f"{API_URL}/documents/", files=files)
    if response.status_code == 200:
        click.echo(f"Document uploaded successfully: {response.json()}")
    else:
        click.echo(f"Error uploading document: {response.text}", err=True)

@cli.command()
@click.argument('doc_id')
def status(doc_id: str):
    """Get document processing status"""
    response = requests.get(f"{API_URL}/documents/{doc_id}/status")
    if response.status_code == 200:
        click.echo(f"Document status: {response.json()}")
    else:
        click.echo(f"Error getting status: {response.text}", err=True)

@cli.command()
@click.argument('query')
@click.option('--provider', default='nomic', help='Embedding provider to use')
@click.option('--k', default=10, help='Number of results to return')
def search(query: str, provider: str, k: int):
    """Search for similar documents"""
    params = {
        'query': query,
        'provider': provider,
        'k': k
    }
    response = requests.post(f"{API_URL}/documents/search", json=params)
    if response.status_code == 200:
        click.echo(json.dumps(response.json(), indent=2))
    else:
        click.echo(f"Error searching documents: {response.text}", err=True)

if __name__ == '__main__':
    cli()