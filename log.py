import logging
import os.path

from config import LOG_PATH


def get_logger(name):
    if not os.path.exists(LOG_PATH):
        os.makedirs(LOG_PATH)

    log_name = '/'.join([LOG_PATH, name + '.log'])

    logger = logging.getLogger(log_name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s ')
        con_handle = logging.StreamHandler()
        file_handle = logging.FileHandler(log_name)

        file_handle.setFormatter(formatter)
        con_handle.setFormatter(formatter)

        logger.addHandler(file_handle)
        logger.addHandler(con_handle)

    return logger
