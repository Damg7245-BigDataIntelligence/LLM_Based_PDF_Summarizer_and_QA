# LLM-Based PDF Summarizer and Q&A

This application allows users to upload PDF documents, extract their content, and use Large Language Models (LLMs) to generate summaries and answer questions about the document content.

## Features

- Upload and parse PDF documents
- Select from previously parsed PDFs
- Generate summaries of document content using LLMs
- Ask questions about document content and receive AI-powered answers
- Support for multiple LLM providers through LiteLLM

## Architecture

The application consists of:

1. **Streamlit Frontend**: User interface for uploading PDFs, selecting models, and interacting with the content
2. **FastAPI Backend**: Handles API requests, PDF processing, and LLM interactions
3. **LiteLLM Integration**: Manages connections to various LLM providers
4. **Redis**: Used for communication between services

## Setup and Installation

1. Clone this repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables in a `.env` file:
   ```
   OPENAI_API_KEY=your_openai_api_key
   DEEPSEEK_API_KEY=your_deepseek_api_key
   ```
4. Start the Redis server
5. Start the FastAPI backend:
   ```
   uvicorn app.api.main:app --reload
   ```
6. Start the Streamlit frontend:
   ```
   streamlit run app/frontend/app.py
   ```

## Usage

1. Open the Streamlit app in your browser
2. Upload a PDF or select a previously parsed document
3. Choose an LLM provider
4. Generate a summary or ask specific questions about the document

## Technologies Used

- FastAPI
- Streamlit
- LiteLLM
- Redis
- PyMuPDF
- Docling
