import os
import time
from dotenv import load_dotenv
from app.backend.redis_service import RedisService
from app.backend.llm_service import LLMService

# Load environment variables
load_dotenv()

def process_qa_request(data):
    """Process a QA request from Redis stream"""
    print(f"Processing QA request: {data['request_id']}")
    
    # Initialize LLM service
    llm_service = LLMService()
    
    # Get model ID from request (default to Zephyr if not specified)
    model_id = data.get("model_id", "huggingface/HuggingFaceH4/zephyr-7b-beta")
    
    # Answer question
    answer, cost_info = llm_service.answer_question(data["content"], data["question"], model_id)
    
    # Publish response back to Redis
    redis_service.publish_qa_response(
        data["request_id"],
        answer,
        cost_info
    )
    
    print(f"QA request {data['request_id']} processed")

if __name__ == "__main__":
    # Initialize Redis service
    redis_service = RedisService()
    
    # Generate a unique consumer name
    consumer_name = f"qa_worker_{os.getpid()}"
    
    print(f"Starting QA worker with consumer name: {consumer_name}")
    
    # Start consuming QA requests
    redis_service.consume_qa_requests(consumer_name, process_qa_request)