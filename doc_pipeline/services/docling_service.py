from typing import List, Dict, Any, Optional
import os
import tempfile
import magic
from docling.document_converter import DocumentConverter, InputFormat
from ..models.document import DocumentChunk
from ..utils.logging import logger

class DoclingService:
    def __init__(self):
        self.mime = magic.Magic(mime=True)
        self.converter = DocumentConverter()

    def _detect_mime_type(self, content: bytes) -> str:
        """Detect MIME type of the content."""
        return self.mime.from_buffer(content)

    def _get_document_format(self, mime_type: str, filename: str) -> Optional[InputFormat]:
        """Get the appropriate Docling `InputFormat` based on MIME type and file extension."""
        ext = os.path.splitext(filename)[1].lower()
        
        format_map = {
            'application/pdf': InputFormat.PDF,
            'application/msword': InputFormat.DOCX,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': InputFormat.DOCX,
            'application/vnd.ms-excel': InputFormat.XLSX,
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': InputFormat.XLSX,
            'application/vnd.ms-powerpoint': InputFormat.PPTX,
            'application/vnd.openxmlformats-officedocument.presentationml.presentation': InputFormat.PPTX,
            'text/plain': InputFormat.MD,
            'text/markdown': InputFormat.MD,
            'text/html': InputFormat.HTML,
            'image/png': InputFormat.IMAGE,
            'image/jpeg': InputFormat.IMAGE,
            'image/tiff': InputFormat.IMAGE
        }

        if mime_type in format_map:
            return format_map[mime_type]

        ext_map = {
            '.pdf': InputFormat.PDF,
            '.doc': InputFormat.DOCX,
            '.docx': InputFormat.DOCX,
            '.xls': InputFormat.XLSX,
            '.xlsx': InputFormat.XLSX,
            '.ppt': InputFormat.PPTX,
            '.pptx': InputFormat.PPTX,
            '.txt': InputFormat.MD,
            '.md': InputFormat.MD,
            '.html': InputFormat.HTML,
            '.htm': InputFormat.HTML,
            '.png': InputFormat.IMAGE,
            '.jpg': InputFormat.IMAGE,
            '.jpeg': InputFormat.IMAGE,
            '.tiff': InputFormat.IMAGE,
            '.tif': InputFormat.IMAGE
        }

        return ext_map.get(ext, None)

    async def process_document(
        self,
        content: bytes,
        filename: str,
        content_type: Optional[str] = None
    ) -> List[DocumentChunk]:
        """Process a document using Docling and return chunks."""
        try:
            if not content_type:
                content_type = self._detect_mime_type(content)
                logger.info(f"Detected MIME type: {content_type} for file {filename}")

                    # Get document format for Docling
            doc_format = self._get_document_format(content_type, filename)
            if doc_format is None:
                raise ValueError(f"Unsupported document type: {content_type}")

            # Convert .txt to .md for processing
            file_extension = os.path.splitext(filename)[1]
            if file_extension == ".txt":
                logger.info(f"Converting .txt to .md for processing: {filename}")
                file_extension = ".md"  # Change extension to markdown

            if not file_extension:
                raise ValueError("File extension missing or invalid.")
            
                    # Save content to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name

            try:
                result = self.converter.convert(temp_path)

                if not result or not hasattr(result, 'document'):
                    raise ValueError(f"Failed to process document: {filename}")

                doc = result.document
                chunks = []

                if hasattr(doc, 'pages'):
                    for page_num, page in enumerate(doc.pages, 1):
                        for block in getattr(page, 'text_blocks', []):
                            chunks.append(DocumentChunk(
                                chunk_id=f"{page_num}_{block.id}",
                                content=block.text,
                                page_number=page_num,
                                position=getattr(block, 'bbox', {}),
                                metadata={"type": "text"}
                            ))
                        for table in getattr(page, 'tables', []):
                            table_text = [" | ".join(str(cell) for cell in row) for row in table.data]
                            chunks.append(DocumentChunk(
                                chunk_id=f"{page_num}_table_{table.id}",
                                content="\n".join(table_text),
                                page_number=page_num,
                                position=getattr(table, 'bbox', {}),
                                metadata={"type": "table", "rows": len(table.data)}
                            ))

                elif hasattr(doc, 'sheets'):
                    for sheet_num, sheet in enumerate(doc.sheets, 1):
                        for table in getattr(sheet, 'tables', []):
                            table_text = [" | ".join(str(cell) for cell in row) for row in table.data]
                            chunks.append(DocumentChunk(
                                chunk_id=f"sheet_{sheet_num}_table_{table.id}",
                                content="\n".join(table_text),
                                page_number=sheet_num,
                                metadata={"type": "spreadsheet", "sheet_name": sheet.name}
                            ))

                elif hasattr(doc, 'text_blocks'):
                    for block in doc.text_blocks:
                        chunks.append(DocumentChunk(
                            chunk_id=f"ocr_{block.id}",
                            content=block.text,
                            page_number=1,
                            position=getattr(block, 'bbox', {}),
                            metadata={"type": "ocr"}
                        ))

                else:
                    chunks.append(DocumentChunk(
                        chunk_id="content_1",
                        content=getattr(doc, 'text', ''),
                        page_number=1,
                        metadata={"type": str(doc_format)}
                    ))

                logger.info(f"Processed document {filename} with {len(chunks)} chunks")
                return chunks

            finally:
                try:
                    os.unlink(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary file: {str(e)}")

        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}", exc_info=True)
            raise
