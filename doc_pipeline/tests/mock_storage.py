from typing import Dict, Optional
from ..models.document import Document, DocumentStatus
from ..models.job import Job, JobStatus

class MockDocumentStorage:
    def __init__(self):
        self.documents: Dict[str, Document] = {}
        self.jobs: Dict[str, Job] = {}

    async def initialize(self):
        pass

    async def add_document(self, document: Document) -> Document:
        self.documents[document.doc_id] = document
        return document

    async def store_document(self, document: Document) -> None:
        self.documents[document.doc_id] = document

    async def get_document(self, doc_id: str) -> Optional[Document]:
        return self.documents.get(doc_id)

    async def update_document_status(self, doc_id: str, status: DocumentStatus, error_message: Optional[str] = None) -> None:
        if doc_id in self.documents:
            doc = self.documents[doc_id]
            doc.status = status
            if error_message:
                doc.error_message = error_message

    async def update_job_status(self, job_id: str, status: JobStatus) -> None:
        if job_id in self.jobs:
            self.jobs[job_id].status = status

    async def close(self):
        pass