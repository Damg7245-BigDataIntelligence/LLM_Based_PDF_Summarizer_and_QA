import os
import json
import time
import uuid
from typing import Dict, Any, Optional, List, Callable
import redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RedisService:
    def __init__(self):
        """Initialize Redis connection using environment variables"""
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        # redis_password = os.getenv("REDIS_PASSWORD", None)
        
        # Connect to Redis
        self.redis_client = redis.Redis(
            host=redis_host,
            port=redis_port,
            # password=redis_password,
            decode_responses=True  # Automatically decode responses to strings
        )
        
        # Define stream names
        self.summary_request_stream = "summary_requests"
        self.summary_response_stream = "summary_responses"
        self.qa_request_stream = "qa_requests"
        self.qa_response_stream = "qa_responses"
        
        # Create consumer group names
        self.summary_consumer_group = "summary_processors"
        self.qa_consumer_group = "qa_processors"
        
        # Initialize streams and consumer groups
        self._initialize_streams()
    
    def _initialize_streams(self):
        """Initialize streams and consumer groups if they don't exist"""
        # Create streams if they don't exist by adding a dummy message
        try:
            self.redis_client.xgroup_create(
                self.summary_request_stream, 
                self.summary_consumer_group,
                mkstream=True,
                id='0'  # Start from the beginning of the stream
            )
        except redis.exceptions.ResponseError as e:
            # Group already exists
            pass
            
        try:
            self.redis_client.xgroup_create(
                self.qa_request_stream, 
                self.qa_consumer_group,
                mkstream=True,
                id='0'
            )
        except redis.exceptions.ResponseError as e:
            # Group already exists
            pass
    
    def publish_summary_request(self, document_id: str, content: str, model_id: str = "huggingface/HuggingFaceH4/zephyr-7b-beta") -> str:
        """Publish a summary request to the summary request stream"""
        request_id = str(uuid.uuid4())
        message = {
            "request_id": request_id,
            "document_id": document_id,
            "content": content,
            "model_id": model_id,
            "timestamp": time.time()
        }
        
        self.redis_client.xadd(
            self.summary_request_stream,
            {
                "data": json.dumps(message)
            }
        )
        
        return request_id
    
    def publish_qa_request(self, document_id: str, content: str, question: str, model_id: str = "huggingface/HuggingFaceH4/zephyr-7b-beta") -> str:
        """Publish a question-answering request to the QA request stream"""
        request_id = str(uuid.uuid4())
        message = {
            "request_id": request_id,
            "document_id": document_id,
            "content": content,
            "question": question,
            "model_id": model_id,
            "timestamp": time.time()
        }
        
        self.redis_client.xadd(
            self.qa_request_stream,
            {
                "data": json.dumps(message)
            }
        )
        
        return request_id
    
    def get_summary_response(self, request_id: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Poll for a summary response with the given request_id
        Returns None if timeout is reached
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Read all messages from the response stream
            messages = self.redis_client.xread(
                {self.summary_response_stream: '0'},
                block=1000,  # Block for 1 second
                count=10
            )
            
            if messages:
                for _, message_list in messages:
                    for message_id, message_data in message_list:
                        data = json.loads(message_data["data"])
                        if data.get("request_id") == request_id:
                            # Acknowledge the message
                            self.redis_client.xdel(self.summary_response_stream, message_id)
                            return data
            
            # Sleep briefly to avoid hammering Redis
            time.sleep(0.1)
        
        return None
    
    def get_qa_response(self, request_id: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """
        Poll for a QA response with the given request_id
        Returns None if timeout is reached
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Read all messages from the response stream
            messages = self.redis_client.xread(
                {self.qa_response_stream: '0'},
                block=1000,  # Block for 1 second
                count=10
            )
            
            if messages:
                for _, message_list in messages:
                    for message_id, message_data in message_list:
                        data = json.loads(message_data["data"])
                        if data.get("request_id") == request_id:
                            # Acknowledge the message
                            self.redis_client.xdel(self.qa_response_stream, message_id)
                            return data
            
            # Sleep briefly to avoid hammering Redis
            time.sleep(0.1)
        
        return None
    
    def consume_summary_requests(self, consumer_name: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Consume summary requests from the stream and process them with the callback
        This is meant to be run in a separate process or thread
        """
        while True:
            try:
                # Read new messages from the stream
                messages = self.redis_client.xreadgroup(
                    groupname=self.summary_consumer_group,
                    consumername=consumer_name,
                    streams={self.summary_request_stream: '>'},
                    count=1,
                    block=2000  # Block for 2 seconds
                )
                
                if not messages:
                    continue
                
                for stream_name, message_list in messages:
                    for message_id, message_data in message_list:
                        try:
                            data = json.loads(message_data["data"])
                            # Process the message with the callback
                            callback(data)
                            # Acknowledge the message
                            self.redis_client.xack(
                                self.summary_request_stream,
                                self.summary_consumer_group,
                                message_id
                            )
                        except Exception as e:
                            print(f"Error processing message: {e}")
            
            except Exception as e:
                print(f"Error consuming messages: {e}")
                time.sleep(1)  # Wait before retrying
    
    def consume_qa_requests(self, consumer_name: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Consume QA requests from the stream and process them with the callback
        This is meant to be run in a separate process or thread
        """
        while True:
            try:
                # Read new messages from the stream
                messages = self.redis_client.xreadgroup(
                    groupname=self.qa_consumer_group,
                    consumername=consumer_name,
                    streams={self.qa_request_stream: '>'},
                    count=1,
                    block=2000  # Block for 2 seconds
                )
                
                if not messages:
                    continue
                
                for stream_name, message_list in messages:
                    for message_id, message_data in message_list:
                        try:
                            data = json.loads(message_data["data"])
                            # Process the message with the callback
                            callback(data)
                            # Acknowledge the message
                            self.redis_client.xack(
                                self.qa_request_stream,
                                self.qa_consumer_group,
                                message_id
                            )
                        except Exception as e:
                            print(f"Error processing message: {e}")
            
            except Exception as e:
                print(f"Error consuming messages: {e}")
                time.sleep(1)  # Wait before retrying
    
    def publish_summary_response(self, request_id: str, summary: str, cost_info: Dict[str, Any]):
        """Publish a summary response to the summary response stream"""
        message = {
            "request_id": request_id,
            "summary": summary,
            "cost": cost_info,
            "timestamp": time.time()
        }
        
        self.redis_client.xadd(
            self.summary_response_stream,
            {
                "data": json.dumps(message)
            }
        )
    
    def publish_qa_response(self, request_id: str, answer: str, cost_info: Dict[str, Any]):
        """Publish a QA response to the QA response stream"""
        message = {
            "request_id": request_id,
            "answer": answer,
            "cost": cost_info,
            "timestamp": time.time()
        }
        
        self.redis_client.xadd(
            self.qa_response_stream,
            {
                "data": json.dumps(message)
            }
        ) 