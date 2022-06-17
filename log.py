import logging


def get_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # 判断logger是否已经添加过handler，是则直接返回logger对象，否则执行handler设定以及addHandler(console_handle)
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s ')
        con_handle = logging.StreamHandler()
        file_handle = logging.FileHandler(__name__)

        file_handle.setFormatter(formatter)
        con_handle.setFormatter(formatter)

        logger.addHandler(file_handle)
        logger.addHandler(con_handle)

    return logger
