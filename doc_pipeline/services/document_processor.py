import asyncio
import logging
import uuid
import base64
from ..models.document import Document, DocumentStatus, DocumentChunk
from ..models.job import Job, JobStatus, JobType
from ..services.document_storage import DocumentStorage
from ..services.job_storage import JobStorage

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.processing_queue = asyncio.Queue()
        self.doc_storage = DocumentStorage()
        self.job_storage = JobStorage()
        self._stop_event = asyncio.Event()  # Signal to stop processing
        self._processing_task = None  # Store processing task

    async def start(self):
        """Start the background processing queue."""
        logger.info("Starting DocumentProcessor queue")
        
        # Initialize storage services
        await self.doc_storage.initialize()
        await self.job_storage.initialize()
        
        self._stop_event.clear()
        self._processing_task = asyncio.create_task(self._process_queue())

    async def stop(self):
        """Stop the document processor gracefully."""
        logger.info("Stopping DocumentProcessor...")
        self._stop_event.set()  # Set the stop event
        await self.processing_queue.put((None, None))  # Send a stop signal to queue

        if self._processing_task:
            await self._processing_task  # Ensure processing task exits cleanly
            self._processing_task = None
        
        # Close storage services
        await self.doc_storage.close()
        await self.job_storage.close()

        logger.info("DocumentProcessor stopped successfully")

    async def submit_document(self, content: bytes, filename: str, content_type: str):
        """Submit a new document for processing."""
        
        # Encode bytes content as Base64 string
        encoded_content = base64.b64encode(content).decode("utf-8")

        document = Document(
            doc_id=str(uuid.uuid4()),  # Generate a unique ID
            filename=filename,
            content_type=content_type,
            content=encoded_content,  # ✅ Store as a string, not bytes
            status=DocumentStatus.PENDING
        )

        job = Job(
            job_id=str(uuid.uuid4()),  # Generate a unique job ID
            job_type=JobType.DOCUMENT_PROCESSING,
            status=JobStatus.QUEUED
        )

        # Store document and job in their respective databases
        await self.doc_storage.add_document(document)
        await self.job_storage.add_job(job)

        # Add to the processing queue
        await self.processing_queue.put((document, job))

        return document

    async def _process_queue(self):
        """Background task that processes documents from the queue."""
        while not self._stop_event.is_set():
            try:
                document, job = await self.processing_queue.get()
                
                if document is None:  # Check for stop signal
                    logger.info("Received stop signal. Exiting queue processing.")
                    break

                await self._process_document(document, job)
                self.processing_queue.task_done()  # Only call task_done() if we processed a document

            except asyncio.CancelledError:
                logger.info("Processing task was cancelled.")
                break  # Graceful exit on cancellation

            except Exception as e:
                logger.error(f"Error processing document: {str(e)}", exc_info=True)

    async def _process_document(self, document, job):
        """Simulated document processing logic."""
        try:
            logger.info(f"Processing document: {document.filename}")
            await asyncio.sleep(2)  # Simulate processing time

            # 🔹 Ensure chunks are created
            document.chunks = [
                DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    content="This is a processed chunk",
                    page_number=1,
                    position={"start": 0, "end": 100},
                    metadata={}
                )
            ]

            # 🔹 Ensure document chunks are updated in storage
            await self.doc_storage.update_document(document)

            # 🔹 Mark as completed
            document.status = DocumentStatus.COMPLETED
            job.status = JobStatus.COMPLETED

            await self.doc_storage.update_document_status(document.doc_id, document.status)
            await self.job_storage.update_job_status(job.job_id, job.status)

            logger.info(f"Document processing completed: {document.filename}")

        except Exception as e:
            document.status = DocumentStatus.FAILED
            job.status = JobStatus.FAILED
            document.error_message = str(e)

            await self.doc_storage.update_document_status(document.doc_id, document.status)
            await self.job_storage.update_job_status(job.job_id, job.status)
            logger.error(f"Document processing failed: {document.filename}. Error: {e}")

    async def _chunk_document(self, document: Document):
        """Chunk document content into smaller parts"""
        chunk_size = 100  # Adjust as needed
        content_str = document.decode_content().decode("utf-8")  # Ensure it's a string
        
        chunks = [
            {"chunk_id": f"{document.doc_id}-{i}", "content": content_str[i:i+chunk_size]}
            for i in range(0, len(content_str), chunk_size)
        ]
        
        return chunks

    async def get_document_status(self, doc_id):
        """Retrieve the status of a document."""
        document = await self.doc_storage.get_document(doc_id)
        return document.status if document else None

    async def get_document(self, doc_id):
        """Retrieve a document by ID."""
        return await self.doc_storage.get_document(doc_id)
