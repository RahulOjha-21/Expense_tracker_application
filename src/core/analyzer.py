import json
import requests
import base64
import os
import grpc
import mimetypes
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Dict
from utils.logger import setup_logger
import google.generativeai as genai

logger = setup_logger()
load_dotenv()

class GeminiImageAnalyzer:
    def __init__(self):
        self.api_key = None
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.load_api_key()

    def load_api_key(self):
        """Loads API key from environment variables and validates it."""
        logger.info("Checking API key.")
        
        # Load the API key from environment variables (via .env file)
        self.api_key = os.getenv("GEMINI_API_KEY")

        if not self.api_key:
            logger.error("API key is missing. Please ensure a .env file with GEMINI_API_KEY is present in the root directory.")
            raise ValueError("API key not found.")

        try:
            # Validate the API key
            headers = {"x-goog-api-key": self.api_key}
            response = requests.get(self.base_url, headers=headers, timeout=5)

            if response.status_code == 200:
                logger.info("API key validated successfully.")
                genai.configure(api_key=self.api_key)
                logger.info("Google API configured successfully.")
            elif response.status_code == 401:
                logger.error("Invalid API key: Unauthorized access.")
                raise PermissionError("Invalid API key.")
            else:
                logger.error(f"API key check failed with status code: {response.status_code}")
                raise ConnectionError(f"API validation failed. Status Code: {response.status_code}")

        except Exception as e:
            logger.error(f"Error during API key validation: {str(e)}")
            raise e

    def encode_file_to_base64(self, file_path: str) -> str:
        """
        Encodes a file to base64 format.

        Args:
            file_path (str): Path to the file.

        Returns:
            str: Base64 encoded file data.
        """
        try:
            with open(file_path, "rb") as file:
                return base64.b64encode(file.read()).decode("utf-8")
        except Exception as e:
            logger.error(f"Error encoding file to base64: {str(e)}")
            return None

    def get_file_analysis(self, question: str, file_path: str):
        """
        Sends a request to the Gemini API and returns the response for a file.
        """
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                return "Error: Could not determine MIME type."

            file_data = self.encode_file_to_base64(file_path)
            if not file_data:
                return f"Error: Failed to encode {mime_type.split('/')[1]}."

            model = genai.GenerativeModel("gemini-2.0-flash")
            prompt = (
                f"{question} From the {mime_type.split('/')[1]}, extract the most relevant date, the total amount, "
                "a suggested category (like Food, Travel, Office, Shopping, Medical, Other), and a comma-separated list of tags. "
                "The date should be in ISO format (DD_MM_YYYY) if possible. The amount should include any currency symbol present. "
                "Return only a JSON object with keys 'date', 'amount', 'category', and 'tags'. "
                "If a field is not found, set it to null."
            )
            response = model.generate_content([
                question,
                {"mime_type": mime_type, "data": file_data},
                prompt
            ])
            return response.text
        except Exception as e:
            logger.error(f"Error during Gemini API request: {str(e)}")
            return f"Error: {str(e)}"



def extract_json_data(response: str) -> Optional[Dict[str, str]]:
    """
    Extracts JSON data from the response string.

    Args:
        response (str): Response string from the Gemini API.

    Returns:
        Optional[Dict[str, str]]: Extracted JSON data or None if extraction fails.
    """
    try:
        if not response:
            raise ValueError("Empty response received")
        
        cleaned_response = response.replace("```json", "").replace("```", "").strip()
        json_data = json.loads(cleaned_response)
        logger.info("JSON data extracted successfully.")
        return json_data
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error in extract_json_data function during execution: {str(e)}")
        return None
    
# Force gRPC Shutdown to Prevent Timeout Errors
def shutdown_grpc():
    try:
        grpc.shutdown()
        logger.info("gRPC shutdown successfully.")
    except Exception as e:
        logger.error(f"Error during gRPC shutdown: {str(e)}")

shutdown_grpc()