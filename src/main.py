from utils.logger import setup_logger
from UI.tk_UI import run_ui
import os
import logging

logger = setup_logger()

def main() -> None:
    """
    Main function that serves as the entry point of the application.
    """
    try:
        logger.info("Starting the Expense Tracker AI application")
        
        # Ensure required directories exist
        os.makedirs("inputs", exist_ok=True)
        os.makedirs(os.path.join("outputs", "DB"), exist_ok=True)
        os.makedirs(os.path.join("outputs", "logs"), exist_ok=True)
        
        # Launch the UI
        run_ui()
        
    except Exception as e:
        logger.error(f"Error during application startup: {str(e)}")
        raise

if __name__ == "__main__":
    main()