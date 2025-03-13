import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import json
from dotenv import load_dotenv
from pathlib import Path

from .models import (
    Document, DocumentResponse, DocumentListResponse, 
    DocumentContentResponse, SummarizeRequest, SummarizeResponse,
    QuestionRequest, QuestionResponse, ModelsResponse
)
from .pdf_processor import PDFProcessor
from .llm_service import LLMService
from .utils import DocumentStore
from .redis_service import RedisService

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="PDF Summarizer API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
pdf_processor = PDFProcessor()
document_store = DocumentStore()
llm_service = LLMService()  # No API key needed for HuggingFace public models
redis_service = RedisService()

@app.get("/")
async def root():
    return {"message": "PDF Summarizer API is running"}

@app.get("/models", response_model=ModelsResponse)
async def get_models():
    """Get available LLM models"""
    models = llm_service.get_available_models()
    return {"models": models}

@app.get("/documents", response_model=DocumentListResponse)
async def get_documents():
    """Get list of all processed documents"""
    documents = document_store.get_documents()
    return {"documents": documents}

@app.get("/documents/{document_id}", response_model=DocumentContentResponse)
async def get_document(document_id: str):
    """Get content of a specific document"""
    document_data = document_store.get_document_content(document_id)
    if not document_data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {
        "document_id": document_id,
        "original_filename": document_data["metadata"]["original_filename"],
        "content": document_data["content"],
        "markdown_content": document_data["content"],
        "metadata": document_data["metadata"]
    }

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file"""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    # Read file content
    file_content = await file.read()
    
    # Process PDF
    content, markdown_content, metadata = pdf_processor.process_pdf(file_content, file.filename)
    
    # Add document to store
    document_id = document_store.add_document(metadata, markdown_content)
    
    return {
        "document_id": document_id,
        "original_filename": metadata["original_filename"],
        "processing_date": metadata["processing_date"]
    }

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    """Generate a summary for a document using Redis streams"""
    # Get document
    document_data = document_store.get_document_content(request.document_id)
    if not document_data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Publish summary request to Redis stream
    request_id = redis_service.publish_summary_request(
        request.document_id, 
        document_data["content"],
        request.model_id
    )
    
    # Wait for response from the worker
    response = redis_service.get_summary_response(request_id)
    
    if not response:
        raise HTTPException(status_code=504, detail="Summary generation timed out")
    
    return {
        "summary": response["summary"],
        "cost": response["cost"]
    }

@app.post("/ask_question", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Answer a question about a document using Redis streams"""
    # Get document
    document_data = document_store.get_document_content(request.document_id)
    if not document_data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Publish QA request to Redis stream
    request_id = redis_service.publish_qa_request(
        request.document_id,
        document_data["content"],
        request.question,
        request.model_id
    )
    
    # Wait for response from the worker
    response = redis_service.get_qa_response(request_id)
    
    if not response:
        raise HTTPException(status_code=504, detail="Question answering timed out")
    
    return {
        "answer": response["answer"],
        "cost": response["cost"]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 