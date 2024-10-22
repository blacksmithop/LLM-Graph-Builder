import logging
import os

import pandas as pd

FILE_DIR = "static"

FILE_MAP = {".xlsx": "Excel", ".xls": "Excel", ".csv": "CSV"}


def get_file_extension(file_path):
    # Split the file path to get the extension
    _, file_extension = os.path.splitext(file_path)
    return file_extension


class LocalFileHandler:
    def __init__(self) -> None:
        if not os.path.exists(FILE_DIR):
            os.makedirs(FILE_DIR)
            logging.debug(
                f"Created static folder at {os.path.join(os.getcwd(), FILE_DIR)}"
            )
        else:
            logging.info(f"Static folder found at {FILE_DIR}")

    def read_local_file(self, file_path: str):
        match extension := get_file_extension(file_path):
            case ".xlsx" | ".xls":
                df = pd.read_excel(file_path)
            case ".csv":
                df = pd.read_csv(file_path)
            case _:
                raise ValueError("Please pass a valid file type")

        logging.debug(f"Read file {file_path} of type {FILE_MAP[extension]}")
        return df
