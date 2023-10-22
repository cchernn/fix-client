import os
import logging
import pandas as pd

def parse_fix_message(message):
    """
    Convert a FIX message to readable string
    """
    return message.toString().replace("\x01", " ")

def setup_logger(name, log_file, format_str, level=logging.INFO):
    """
    Setup Logger
    """
    formatter = logging.Formatter(format_str)
    handler = logging.FileHandler(log_file)
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

def log(logger, message, level="INFO", _print=False):
    """
    Log Messages and print
    """
    if logger is not None:
        if level == "ERROR":
            logger.error(message)
        elif level == "DEBUG":
            logger.debug(message)
        else:
            logger.info(message)
    
    if _print:
        print(message)

def saveData(data, filepath):
    """
    Save data to Results folder
    """
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)

def ensureDirectories():
    """
    Create necessary folders
    - Files
    - Log
    - Results
    """
    for folder in ["Files", "Log", "Results"]:
        if not os.path.exists(folder):
            os.makedirs(folder)