import logging
import sys

from wattro_sync.file_access.read_write import get_base_folder_path

formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")


def get_file_handler() -> logging.FileHandler:
    wattro_folder = get_base_folder_path()
    logging_fh = logging.FileHandler(wattro_folder / "logs.log", mode="a")
    logging_fh.setFormatter(formatter)
    logging_fh.setLevel(logging.DEBUG)
    return logging_fh


def get_stdout_handler() -> logging.StreamHandler:
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.DEBUG)
    stdout_handler.setFormatter(formatter)
    return stdout_handler
