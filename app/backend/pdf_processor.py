import os
import tempfile
import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, Tuple, Any
from datetime import datetime
import shutil
from .s3_utils import upload_pdf_to_s3, upload_markdown_to_s3

class PDFProcessor:
    def __init__(self):
        """
        Initialize the PDF processor
        No need for documents_dir as we're using S3 storage
        """
        pass
    
    def process_pdf(self, file_content: bytes, original_filename: str) -> Tuple[str, str, Dict[str, Any]]:
        """
        Process a PDF file and extract its text content, storing in S3
        
        Args:
            file_content: The binary content of the PDF file
            original_filename: The original filename of the PDF
            
        Returns:
            Tuple containing the raw text content, markdown formatted content, and metadata
        """
        # Create a temporary file to store the PDF content
        temp_file_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            # Process PDF using PyMuPDF
            base_name = Path(original_filename).stem
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            document_id = f"{base_name}_{timestamp}"
            
            # Extract text from PDF
            doc = fitz.open(temp_file_path)
            raw_text = ""
            markdown_content = f"# {base_name}\n\n"
            
            for page_num, page in enumerate(doc):
                # Extract text
                page_text = page.get_text()
                raw_text += page_text + "\n\n"
                
                # Add page header to markdown
                markdown_content += f"## Page {page_num + 1}\n\n"
                
                # Add page text to markdown - process paragraphs
                paragraphs = page_text.split('\n')
                current_paragraph = ""
                
                for line in paragraphs:
                    line = line.strip()
                    if not line:
                        if current_paragraph:
                            markdown_content += f"{current_paragraph}\n\n"
                            current_paragraph = ""
                    else:
                        if not current_paragraph:
                            current_paragraph = line
                        else:
                            current_paragraph += " " + line
                
                # Add the last paragraph if there is one
                if current_paragraph:
                    markdown_content += f"{current_paragraph}\n\n"
            
            # Close the document
            doc.close()
            
            # Upload PDF to S3
            pdf_url = upload_pdf_to_s3(file_content, original_filename, document_id)
            
            # Upload markdown to S3
            markdown_url = upload_markdown_to_s3(markdown_content, document_id, base_name)
            
            metadata = {
                'document_id': document_id,
                'source_type': 'pdf',
                'original_filename': original_filename,
                'processing_date': timestamp,
                'content_type': 'document',
                'pdf_url': pdf_url,
                'markdown_url': markdown_url
            }
            
            return raw_text, markdown_content, metadata
            
        finally:
            # Clean up the temporary file - with proper error handling
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except PermissionError:
                    print(f"Warning: Could not delete temporary file {temp_file_path}") 