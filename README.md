# **LLM Based PDF Summarizer and Q&A**

This application enables users to upload PDF documents, extract their content, and interact with them using Large Language Models (LLMs). Users can generate summaries and ask questions about the document's content.

The system integrates **FastAPI, Streamlit, LiteLLM, Redis, and PyMuPDF** to provide a seamless experience for document summarization and Q&A.

---

## **🔹 Project Resources**
- 🌐 **App (Streamlit Cloud):** [Streamlit Link](https://your-streamlit-app-link.com)  
- 🎥 **YouTube Demo:** [Demo Link](https://youtu.be/your-demo-link)  

---

## **🔹 Technologies**

![Streamlit](https://img.shields.io/badge/-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)
![FastAPI](https://img.shields.io/badge/-FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![Redis](https://img.shields.io/badge/-Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)
![LiteLLM](https://img.shields.io/badge/-LiteLLM-0078D7?style=for-the-badge&logo=OpenAI&logoColor=white)
![PyMuPDF](https://img.shields.io/badge/-PyMuPDF-4B8BBE?style=for-the-badge&logo=python&logoColor=white)

---

## **🔹 Architecture Diagram**

<p align="center">
  <img src="https://your-repo-link.com/architecture-diagram.png"
       alt="Architecture Diagram" width="600">
</p>

---

## **🔹 Project Flow**

### **Step 1: User Interaction via Streamlit UI**
- Users can upload a PDF document or select from previously parsed PDFs.
- Choose from multiple LLM providers for document analysis.

### **Step 2: Sending Request to FastAPI**
- Uploaded PDFs and user queries are sent to the **FastAPI** backend.

### **Step 3: Document Processing**
- **PDF Parsing**: PDFs are processed using **PyMuPDF**.
- **LLM Interaction**: Queries are processed via **LiteLLM**, supporting multiple providers.

### **Step 4: Communication via Redis**
- **Redis** facilitates message-passing between FastAPI and Streamlit.

### **Step 5: Displaying Output in Streamlit UI**
- Summaries and question responses are sent back to the Streamlit UI for display.

---
## **🔹 Repository Structure**

---

## **🔹 Contribution**

| **Contributor**                    | **Contribution**                                                                                           |
|-------------------------------------|-----------------------------------------------------------------------------------------------------------|
| **Janvi Bharatkumar Chitroda**      | 33% – Developed the Streamlit interface,  managed Redis Streams for real-time processing, and integrated AWS S3 for storing Markdown outputs. |
| **Ketki Mude**                      | 33% – Built the FastAPI backend, implemented PDF upload and parsing, and integrated multiple LLMs via LiteLLM. |
| **Sahil Mutha**                     | 33% – Implemented multi-LLM interaction, optimized asynchronous data handling, and ensured system deployment using Docker Compose. |
----------


## **🔹 Attestation**

WE CERTIFY THAT WE HAVE NOT USED ANY OTHER STUDENTS' WORK IN OUR ASSIGNMENT AND COMPLY WITH THE POLICIES OUTLINED IN THE STUDENT HANDBOOK.

