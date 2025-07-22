from utils.logger import setup_logger
from core.analyzer import GeminiImageAnalyzer
from core.renamer import FileOrganizer
import json
from datetime import datetime
import shutil
import os
from typing import Optional, Dict, Generator, Tuple
import uuid

logger = setup_logger()

def extract_json_data(response: str) -> Optional[Dict[str, str]]:
    """
    Extracts JSON data from the response string.
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

def get_image_data(source_path: str, db_path: str) -> Generator[Tuple[int, int], None, None]:
    """
    Processes image files and extracts data to save into the database.
    """
    try:
        file_organized = FileOrganizer(source_path)
        image_files = file_organized.file_list
        logger.info(f"Found {len(image_files)} image files.")

        image_analyzer = GeminiImageAnalyzer()

        db_dir = os.path.dirname(db_path)
        failed_dir = os.path.join("outputs", "failed")
        os.makedirs(db_dir, exist_ok=True)
        os.makedirs(failed_dir, exist_ok=True)

        from utils.db_manager import clear_db_data, save_to_sqlite_db
        clear_db_data(db_path)

        processed_files = []
        for i, file_path in enumerate(image_files):
            try:
                logger.info(f"Processing image file: {file_path}")
                response = image_analyzer.get_file_analysis("Find the amount and Date", file_path)
                
                if not response or response.startswith("Error:"):
                    raise ValueError(f"API Error: {response}")

                json_data = extract_json_data(response)
                if not json_data:
                    raise ValueError("Failed to extract JSON data.")

                json_data.update({"file_path": file_path})
                rename_name = f"{json_data['date']}_RS{json_data['amount']}"
                json_data.update({"rename_name": rename_name})
                


                date_str = json_data['date']
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    date = datetime.strptime(date_str, '%d_%m_%Y')

                # Use AI-suggested category/tags, fallback to empty string if missing
                category = json_data.get('category') or ''
                tags = json_data.get('tags') or ''

                if isinstance(tags, list):
                    tags = json.dumps(tags)

                save_to_sqlite_db(
                    unique_id=str(uuid.uuid4()),
                    amount=json_data['amount'],
                    date=date,
                    original_path=file_path,
                    rename_name=json_data['rename_name'],
                    db_path=db_path,
                    category=category,
                    tags=tags
                )
                processed_files.append((i + 1, len(image_files)))
                logger.info("Image data extracted and saved to database successfully.")

            except (ValueError, FileNotFoundError) as e:
                logger.warning(f"Failed to process file {file_path}: {e}")
                try:
                    shutil.move(file_path, os.path.join(failed_dir, os.path.basename(file_path)))
                    logger.info(f"Moved failed file to {failed_dir}")
                except Exception as move_error:
                    logger.error(f"Could not move file {file_path} to failed directory: {move_error}")
            except Exception as e:
                logger.error(f"An unexpected error occurred while processing {file_path}: {e}")

            # Return progress information
            yield (i + 1, len(image_files))

    except Exception as e:
        logger.error(f"Error in get_image_data function during execution: {str(e)}")
        yield (0, 0)  # Indicate error through progress 