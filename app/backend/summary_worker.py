import os
import time
from dotenv import load_dotenv
from app.backend.redis_service import RedisService
from app.backend.llm_service import LLMService

# Load environment variables
load_dotenv()

def process_summary_request(data):
    """Process a summary request from Redis stream"""
    print(f"Processing summary request: {data['request_id']}")
    
    # Initialize LLM service
    llm_service = LLMService()
    
    # Get model ID from request (default to Zephyr if not specified)
    model_id = data.get("model_id", "huggingface/HuggingFaceH4/zephyr-7b-beta")
    
    # Generate summary
    summary, cost_info = llm_service.generate_summary(data["content"], model_id)
    
    # Publish response back to Redis
    redis_service.publish_summary_response(
        data["request_id"],
        summary,
        cost_info
    )
    
    print(f"Summary request {data['request_id']} processed")

if __name__ == "__main__":
    # Initialize Redis service
    redis_service = RedisService()
    
    # Generate a unique consumer name
    consumer_name = f"summary_worker_{os.getpid()}"
    
    print(f"Starting summary worker with consumer name: {consumer_name}")
    
    # Start consuming summary requests
    redis_service.consume_summary_requests(consumer_name, process_summary_request)