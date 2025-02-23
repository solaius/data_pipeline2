import os
import magic

from io import BytesIO
from typing import List, Optional, Dict, Any

from docling.document_converter import DocumentConverter
from docling.chunking import HybridChunker
from docling.datamodel.base_models import DocumentStream

from ..models.document import DocumentChunk
from ..utils.logging import logger

class ChunkingStrategy:
    """Enum-like class for chunking strategies"""
    HYBRID = "hybrid"
    MARKDOWN = "markdown"
    SENTENCE = "sentence"
    FALLBACK = "fallback"

class DoclingService:
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        default_strategy: str = ChunkingStrategy.HYBRID
    ):
        self.mime = magic.Magic(mime=True)
        self.converter = DocumentConverter()
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.default_strategy = default_strategy
        self._validate_config()
        logger.info(
            f"Initialized DoclingService with chunk_size={chunk_size}, "
            f"chunk_overlap={chunk_overlap}, strategy={default_strategy}"
        )

    def _validate_config(self) -> None:
        """Validate configuration parameters."""
        if self.chunk_size <= 0:
            raise ValueError("chunk_size must be positive")
        if self.chunk_overlap < 0:
            raise ValueError("chunk_overlap must be non-negative")
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")
        if self.default_strategy not in vars(ChunkingStrategy).values():
            raise ValueError(f"Invalid chunking strategy: {self.default_strategy}")

    def _detect_mime_type(self, content: bytes) -> str:
        """Detect MIME type of the content."""
        return self.mime.from_buffer(content)

    def _chunk_by_markdown(self, content: str) -> List[Dict[str, Any]]:
        """Chunk content based on markdown structure."""
        chunks = []
        current_chunk = []
        current_size = 0
        current_headings = []

        for line in content.split('\n'):
            # Check for headings
            if line.startswith('#'):
                # If we have content in current chunk, save it
                if current_chunk:
                    chunks.append({
                        "text": '\n'.join(current_chunk),
                        "headings": current_headings.copy()
                    })
                    current_chunk = []
                    current_size = 0
                current_headings = [line.strip()]
            else:
                line_size = len(line)
                # If adding this line would exceed chunk size, save current chunk
                if current_size + line_size > self.chunk_size and current_chunk:
                    chunks.append({
                        "text": '\n'.join(current_chunk),
                        "headings": current_headings.copy()
                    })
                    current_chunk = []
                    current_size = 0
                
                current_chunk.append(line)
                current_size += line_size

        # Add any remaining content
        if current_chunk:
            chunks.append({
                "text": '\n'.join(current_chunk),
                "headings": current_headings.copy()
            })

        return chunks

    def _chunk_by_sentences(self, content: str) -> List[Dict[str, Any]]:
        """Chunk content based on sentences."""
        import re
        sentence_endings = r'[.!?][\s]{1,2}'
        sentences = re.split(sentence_endings, content)
        
        chunks = []
        current_chunk = []
        current_size = 0

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.chunk_size and current_chunk:
                chunks.append({
                    "text": ' '.join(current_chunk),
                    "headings": []
                })
                current_chunk = []
                current_size = 0
            
            current_chunk.append(sentence)
            current_size += sentence_size

        if current_chunk:
            chunks.append({
                "text": ' '.join(current_chunk),
                "headings": []
            })

        return chunks

    async def process_document(
        self,
        content: bytes,
        filename: str,
        content_type: Optional[str] = None,
        chunking_strategy: Optional[str] = None
    ) -> List[DocumentChunk]:
        """Process a document using Docling and return chunks."""
        try:
            if not content_type:
                content_type = self._detect_mime_type(content)
                logger.info(f"Detected MIME type: {content_type} for file {filename}")

            # For text files, convert to markdown
            name, ext = os.path.splitext(filename)
            if ext.lower() == '.txt':
                logger.info(f"Converting .txt to .md for processing: {filename}")
                filename = name + ".md"

            # Create document stream
            buf = BytesIO(content)
            source = DocumentStream(name=filename, stream=buf)

            # Convert document
            logger.info(f"Converting document: {filename}")
            result = self.converter.convert(source)
            
            if not result or not hasattr(result, 'document'):
                raise ValueError(f"Failed to convert document: {filename}")

            doc = result.document
            markdown_content = doc.export_to_markdown()
            logger.debug(f"Markdown content length: {len(markdown_content)}")
            
            strategy = chunking_strategy or self.default_strategy
            chunks = []
            
            try:
                if strategy == ChunkingStrategy.HYBRID:
                    # Use Docling's HybridChunker
                    chunker = HybridChunker(
                        tokenizer="BAAI/bge-small-en-v1.5",
                        chunk_size=self.chunk_size,
                        chunk_overlap=self.chunk_overlap
                    )
                    chunk_results = list(chunker.chunk(doc))
                    logger.debug(f"Created {len(chunk_results)} chunks using HybridChunker")
                    
                    for i, chunk in enumerate(chunk_results, 1):
                        logger.debug(f"Processing chunk {i} of type {type(chunk)}")
                        chunks.append(DocumentChunk(
                            chunk_id=f"chunk_{i}",
                            content=chunk.text if hasattr(chunk, 'text') else str(chunk),
                            page_number=getattr(chunk, 'page_number', 1),
                            position=None,
                            metadata={
                                "headings": getattr(chunk, 'headings', []),
                                "type": "hybrid_chunk",
                                "chunk_number": i,
                                "total_chunks": len(chunk_results),
                                "strategy": strategy
                            }
                        ))
                
                elif strategy == ChunkingStrategy.MARKDOWN:
                    # Use markdown-based chunking
                    chunk_results = self._chunk_by_markdown(markdown_content)
                    for i, chunk in enumerate(chunk_results, 1):
                        chunks.append(DocumentChunk(
                            chunk_id=f"chunk_{i}",
                            content=chunk["text"],
                            page_number=1,
                            position=None,
                            metadata={
                                "headings": chunk["headings"],
                                "type": "markdown_chunk",
                                "chunk_number": i,
                                "total_chunks": len(chunk_results),
                                "strategy": strategy
                            }
                        ))
                
                elif strategy == ChunkingStrategy.SENTENCE:
                    # Use sentence-based chunking
                    chunk_results = self._chunk_by_sentences(markdown_content)
                    for i, chunk in enumerate(chunk_results, 1):
                        chunks.append(DocumentChunk(
                            chunk_id=f"chunk_{i}",
                            content=chunk["text"],
                            page_number=1,
                            position=None,
                            metadata={
                                "type": "sentence_chunk",
                                "chunk_number": i,
                                "total_chunks": len(chunk_results),
                                "strategy": strategy
                            }
                        ))
            
            except Exception as chunk_error:
                logger.warning(f"Chunking failed with strategy {strategy}: {str(chunk_error)}")
                strategy = ChunkingStrategy.FALLBACK

            # Fallback: use full content if no chunks were created
            if not chunks:
                logger.warning(f"No chunks created, using fallback strategy for {filename}")
                chunks.append(DocumentChunk(
                    chunk_id="chunk_1",
                    content=markdown_content,
                    page_number=1,
                    position=None,
                    metadata={
                        "type": "full_document",
                        "chunk_number": 1,
                        "total_chunks": 1,
                        "strategy": ChunkingStrategy.FALLBACK,
                        "is_fallback": True
                    }
                ))

            logger.info(f"Processed document {filename} with {len(chunks)} chunks using {strategy} strategy")
            return chunks

        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}", exc_info=True)
            raise