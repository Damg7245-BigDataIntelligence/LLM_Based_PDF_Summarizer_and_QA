import os
from typing import Dict, Any, Tuple, Optional
import litellm
import requests
import time
import tiktoken
class LLMService:
    def __init__(self, api_key: Optional[str] = None):
        # HuggingFace API token (can be empty for some public models)
        self.hf_token = os.getenv("HUGGINGFACE_TOKEN")
        
        # Google API key for Gemini
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        
        # Warn if the Google API key is not set
        if not self.google_api_key:
            print("Warning: GOOGLE_API_KEY environment variable is not set. Gemini API calls will fail.")
        
        # Define model pricing (per 1M tokens) in USD - based on provided pricing
        self.model_pricing = {
            "huggingface/HuggingFaceH4/zephyr-7b-beta": {
                "input": 0.0,
                "output": 0.0
            },
            "gemini/gemini-pro": {
                "input": {
                    "standard": 1.25,  # $1.25 per 1M input tokens (≤128k)
                    "high": 2.50       # $2.50 per 1M input tokens (>128k)
                },
                "output": {
                    "standard": 5.00,  # $5.00 per 1M output tokens (≤128k)
                    "high": 10.00      # $10.00 per 1M output tokens (>128k)
                },
                "threshold": 128000    # Token threshold for pricing tier
            }
        }
        
        # Initialize tiktoken encoder for token counting
        self.encoder = tiktoken.get_encoding("cl100k_base")
    
    def get_available_models(self) -> list:
        """Return list of available models"""
        models = [
            {
                "id": "huggingface/HuggingFaceH4/zephyr-7b-beta",
                "name": "Zephyr 7B",
                "provider": "HuggingFace via LiteLLM"
            }
        ]
        
        # Add Gemini model if API key is available
        if self.google_api_key:
            models.append({
                "id": "gemini/gemini-pro",
                "name": "Google Gemini Pro",
                "provider": "Google via LiteLLM"
            })
            
        return models
    
    def _count_tokens(self, text: str) -> int:
        return len(self.encoder.encode(text))
            
    def generate_summary(self, document_content: str, model_id: str = "huggingface/HuggingFaceH4/zephyr-7b-beta") -> Tuple[str, Dict[str, Any]]:
        """
        Generate a summary of the document using the specified model.
        
        Args:
            document_content: The text content of the document.
            model_id: The ID of the model to use.
            
        Returns:
            Tuple containing the summary and cost information.
        """
        system_prompt = "You are a helpful assistant that summarizes documents. Provide a concise but comprehensive summary of the document."
        user_prompt = f"Please summarize the following document:\n\n{document_content}"
        
        try:
            if model_id.startswith("gemini"):
                summary = self._call_gemini_api(system_prompt, user_prompt)
            else:
                summary = self._call_huggingface_api(system_prompt, user_prompt)
            
            # Count tokens with tiktoken
            prompt_tokens = self._count_tokens(system_prompt + user_prompt)
            completion_tokens = self._count_tokens(summary)
            
            cost_info = self._calculate_cost(model_id, prompt_tokens, completion_tokens)
            
            return summary, cost_info
        except Exception as e:
            print(f"Error calling LLM API: {str(e)}")
            return "Unable to generate summary due to an error.", {
                "model": model_id,
                "input_tokens": 0,
                "output_tokens": 0,
                "input_cost": 0,
                "output_cost": 0,
                "total_cost": 0
            }
    
    def answer_question(self, document_content: str, question: str, model_id: str = "huggingface/HuggingFaceH4/zephyr-7b-beta") -> Tuple[str, Dict[str, Any]]:
        """
        Answer a question about the document using the specified model.
        
        Args:
            document_content: The text content of the document.
            question: The question to answer.
            model_id: The ID of the model to use.
            
        Returns:
            Tuple containing the answer and cost information.
        """
        system_prompt = "You are a helpful assistant that answers questions about documents. Provide accurate and concise answers based on the document content only."
        user_prompt = f"Document: {document_content}\n\nQuestion: {question}\n\nAnswer:"
        
        try:
            if model_id.startswith("gemini"):
                answer = self._call_gemini_api(system_prompt, user_prompt)
            else:
                answer = self._call_huggingface_api(system_prompt, user_prompt)
            
            # Count tokens with tiktoken
            prompt_tokens = self._count_tokens(system_prompt + user_prompt)
            completion_tokens = self._count_tokens(answer)
            
            cost_info = self._calculate_cost(model_id, prompt_tokens, completion_tokens)
            
            return answer, cost_info
        except Exception as e:
            print(f"Error calling LLM API: {str(e)}")
            return "Unable to answer question due to an error.", {
                "model": model_id,
                "input_tokens": 0,
                "output_tokens": 0,
                "input_cost": 0,
                "output_cost": 0,
                "total_cost": 0
            }
    
    def _call_huggingface_api(self, system_prompt: str, user_prompt: str) -> str:
        """Call the HuggingFace API."""
        try:
            # Create a more structured prompt with clear instructions
            formatted_prompt = f"""{system_prompt} Instructions: Please provide a clear, coherent, and accurate summary of the following document.  Focus on the main points and key information. The summary should be well-structured and make sense.
            Document:
            {user_prompt.replace('Please summarize the following document:', '').strip()}

            Summary:
            """
            
            # Use the HuggingFace Inference API endpoint
            api_url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
            headers = {"Authorization": f"Bearer {self.hf_token}"}
            
            # Make a direct API call with more conservative parameters
            payload = {
                "inputs": formatted_prompt,
                "parameters": {
                    "max_new_tokens": 500,
                    "temperature": 0.3,  # Lower temperature for more focused output
                    "do_sample": True,
                    "top_p": 0.9,  # Add top_p sampling
                    "repetition_penalty": 1.2,  # Penalize repetition
                    "return_full_text": False
                }
            }
            
            response = requests.post(api_url, headers=headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated_text = result[0].get("generated_text", "")
                    # Clean up the response
                    if "Summary:" in generated_text:
                        generated_text = generated_text.split("Summary:")[1].strip()
                    return generated_text
                return "No valid response from HuggingFace model."
            else:
                return f"Error: API returned status code {response.status_code}"
                
        except Exception as e:
            print(f"Exception calling HuggingFace API: {str(e)}")
            return f"Error: {str(e)}"
        
    def _call_gemini_api(self, system_prompt: str, user_prompt: str) -> str:
            """Call the Google Gemini API using LiteLLM."""
            try:
                # Set the API key as an environment variable
                os.environ['GEMINI_API_KEY'] = self.google_api_key
                
                # Print debug info (remove in production)
                print(f"Using Gemini API with key: {self.google_api_key[:5]}...{self.google_api_key[-4:] if len(self.google_api_key) > 8 else ''}")
                
                # Ensure a valid Google API key is provided
                if not self.google_api_key:
                    raise ValueError("Google API key is not provided. Set the GOOGLE_API_KEY environment variable with a valid key.")
                
                # Create messages for the API call
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                
                # Call the Gemini API
                response = litellm.completion(
                    model="gemini/gemini-1.5-pro",  # Using the 1.5 version
                    messages=messages,
                    max_tokens=512,
                    temperature=0.7
                )
                
                # Extract the generated text if available
                if response and hasattr(response, 'choices') and len(response.choices) > 0:
                    return response.choices[0].message.content
                
                return "No valid response from Gemini model."
            except Exception as e:
                print(f"Exception calling Gemini API: {str(e)}")
                return f"Error: {str(e)}"
    
    def _calculate_cost(self, model_id: str, input_tokens: int, output_tokens: int) -> Dict[str, Any]:
        """Calculate the cost of the API call based on token usage."""
        if model_id.startswith("gemini"):
            # Get the pricing tiers
            pricing = self.model_pricing.get("gemini/gemini-pro", {})
            threshold = pricing.get("threshold", 128000)
            
            # Determine which pricing tier to use
            input_tier = "high" if input_tokens > threshold else "standard"
            output_tier = "high" if output_tokens > threshold else "standard"
            
            # Calculate costs
            input_cost = (input_tokens / 1000000) * pricing["input"][input_tier]
            output_cost = (output_tokens / 1000000) * pricing["output"][output_tier]
        else:
            # For other models
            model_price = self.model_pricing.get(model_id, {"input": 0, "output": 0})
            input_cost = (input_tokens / 1000) * model_price["input"]
            output_cost = (output_tokens / 1000) * model_price["output"]
            
        total_cost = input_cost + output_cost
        
        return {
            "model": model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost
        }