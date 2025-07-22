import json
from pathlib import Path
import base64
from PIL import Image
from google.generativeai import GenerativeModel
from google.generativeai.types import  GenerationConfig

class GeminiImageAnalyzer:
    def __init__(self, api_key):
        self.model = GenerativeModel("gemini-2.0-flash", api_key=api_key)

    def encode_image_to_base64(self, image_path: str) -> str:
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("utf-8")
        except FileNotFoundError:
            raise ValueError(f"Image file not found at {image_path}")
        except Exception as e:
            raise ValueError(f"Error encoding image: {e}")

    def get_gemini_response(self, question: str, image_path: str) -> dict:
        """
        Sends a request to the Gemini API and returns the response.

        Args:
            question (str): The question to ask the model.
            image_path (str): Path to the image file.

        Returns:
            dict: Response from the Gemini API with 'date' and 'amount' keys, or an error dict.
        """
        try:
            # Encode image to base64
            image_data = self.encode_image_to_base64(image_path)
            image = Image(base64=image_data)

            # Define prompt
            prompt = (
                f"{question} From the image, extract the most relevant date and the total amount. "
                "The date should be in ISO format (YYYY-MM-DD) if possible. The amount should include "
                "any currency symbol present. Return only a JSON object with keys 'date' and 'amount'. "
                "If a field is not found, set it to null."
            )

            # Create content parts as a list
            content = [prompt, image]
            config = GenerationConfig(temperature=0.0)

            # Get response
            response = self.model.generate_content(content, generation_config=config)
            
            # Parse JSON response
            result = json.loads(response.text)
            if not isinstance(result, dict):
                print("Error: Response is not a dictionary.")
                return {"error": "Response is not a valid dictionary"}

            date = result.get("date")
            amount = result.get("amount")
            if date is None or amount is None:
                print("Warning: Date or Amount not found in the response.")

            return {"date": date, "amount": amount}

        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON response: {str(e)}")
            return {"error": f"Invalid JSON response: {str(e)}"}
        except ValueError as e:
            print(f"Error: {str(e)}")
            return {"error": str(e)}
        except Exception as e:
            print(f"Error: Unexpected error: {str(e)}")
            return {"error": f"Unexpected error: {str(e)}"}

# Standalone usage
if __name__ == "__main__":
    api_key = ""
    # Instantiate and use the analyzer
    image_analyzer = GeminiImageAnalyzer("AIzaSyCk4c0KXAhDWMGqxJjt7C7zrGwU_8d2WmY")
    response = image_analyzer.get_gemini_response(
        question="Find the amount and Date",
        image_path="input/s1.png"
    )
    print(response)
