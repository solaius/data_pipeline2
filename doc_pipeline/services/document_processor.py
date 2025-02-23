import asyncio
import logging
import uuid
from ..models.document import Document, DocumentStatus
from ..models.job import Job, JobStatus, JobType
from ..services.document_storage import DocumentStorage

logger = logging.getLogger(__name__)

class DocumentProcessor:
    def __init__(self):
        self.processing_queue = asyncio.Queue()
        self.storage = DocumentStorage()
        self._stop_event = asyncio.Event()  # Signal to stop processing
        self._processing_task = None  # Store processing task

    async def start(self):
        """Start the background processing queue."""
        logger.info("Starting DocumentProcessor queue")
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

        logger.info("DocumentProcessor stopped successfully")

    async def submit_document(self, content, filename, content_type):
        """Submit a new document for processing."""
        document = Document(
            doc_id=str(uuid.uuid4()),  # Generate a unique ID
            filename=filename,
            content_type=content_type,
            content=content,
            status=DocumentStatus.PENDING
        )

        # Create a job with required fields
        job = Job(
            job_id=str(uuid.uuid4()),  # Generate a unique job ID
            job_type=JobType.DOCUMENT_PROCESSING,  # Assign appropriate job type
            status=JobStatus.QUEUED
        )

        # Add document and job to the processing queue
        await self.storage.add_document(document)
        await self.job_queue.put((document, job))

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

            document.status = DocumentStatus.COMPLETED
            job.status = JobStatus.COMPLETED

            await self.storage.update_document_status(document.doc_id, document.status)
            await self.storage.update_job_status(job.job_id, job.status)

            logger.info(f"Document processing completed: {document.filename}")

        except Exception as e:
            document.status = DocumentStatus.FAILED
            job.status = JobStatus.FAILED
            await self.storage.update_document_status(document.doc_id, document.status)
            await self.storage.update_job_status(job.job_id, job.status)
            logger.error(f"Document processing failed: {document.filename}. Error: {e}")

    async def get_document_status(self, doc_id):
        """Retrieve the status of a document."""
        document = await self.storage.get_document(doc_id)
        return document.status if document else None

    async def get_document(self, doc_id):
        """Retrieve a document by ID."""
        return await self.storage.get_document(doc_id)
