import logging
import os
from pathlib import Path

def setup_logger():
    """
    Sets up a logger that writes to a file in the output directory.

    Returns:
        logging.Logger: Configured logger instance.
    """
    project_dir = Path(__file__).resolve().parents[1] # Go up to src, then to project root
    log_path = project_dir / "outputs" / "logs" / "app.log"
    log_level = "INFO"

    os.makedirs(log_path.parent, exist_ok=True)

    logger = logging.getLogger('Image_Analyser')
    logger.setLevel(log_level.upper())

    # Prevent adding duplicate handlers
    if not logger.handlers:
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        log_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        file_handler.setFormatter(log_format)
        console_handler.setFormatter(log_format)

        logger.addHandler(file_handler)
        # logger.addHandler(console_handler) # Keep this commented unless console output is desired

    return logger