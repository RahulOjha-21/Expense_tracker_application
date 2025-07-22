import os
from pathlib import Path
from utils.logger import setup_logger

logger = setup_logger()

IMAGE_PDF_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.pdf')

class FileOrganizer:
    def __init__(self, directory="inputs"):
        """
        Initialize the FileOrganizer with a directory to scan.

        Args:
            directory (str): Directory to search for files (default: 'inputs').
        """
        self.file_list = []
        self.directory = directory
        logger.info(f"Initializing FileOrganizer with directory: {self.directory} folder")
        self.file_organize_list()  # Call the method to populate lists on init

    def file_organize_list(self):
        """
        Find all image and PDF files in the specified directory.

        Returns:
            tuple: Tuple containing list of image file paths and list of PDF file paths.
        """
        try:
            # Ensure directory exists
            if not os.path.exists(self.directory):
                logger.error(f"Error: Directory '{self.directory}' does not exist.")
                return self.file_list

            # Walk through directory
            for root, dirs, files in os.walk(self.directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    logger.debug(f"Found file: {file_path}")
                    if file.lower().endswith(IMAGE_PDF_EXTENSIONS):
                        self.file_list.append(file_path)
            
            logger.info(f"Found {len(self.file_list)} files in the directory.")

        except Exception as e:
            logger.error(f"Error during file organization: {str(e)}")
