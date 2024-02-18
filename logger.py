import os
import sys
import logging
from datetime import datetime
from pathlib import Path

LOG_FILE = Path(__file__).parent / 'log.txt'
LOG_LEVEL = logging.INFO
VisualPygameOn = os.environ.get('VisualPygameOn', 'on') == 'on'


def __remember_logger(func):
    logger = []

    def wrap(level=LOG_LEVEL, log_file=None, std_out=True) -> logging.Logger:
        if not logger:
            logger.append(func(level, log_file, std_out))
        return logger[0]

    return wrap


def add_std_handler(logger: logging.Logger):
    formatter = logging.Formatter('%(asctime)s|%(levelname)s %(filename)s %(lineno)d: %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)


@__remember_logger
def get_logger(level=LOG_LEVEL, log_file=None, std_out=True) -> logging.Logger:
    log_file = log_file if log_file else ('client_logs' if VisualPygameOn else 'server_logs')
    # f"{log_file}_{datetime.now().strftime('%m_%d_%H_%M_%S')}.txt"

    try:
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
    except:
        pass
    logging.basicConfig(filename=LOG_FILE,
                        filemode='w',
                        level=level,
                        format='%(asctime)s|%(levelname)s %(filename)s %(lineno)d: %(message)s',
                        datefmt='%H:%M:%S', )
    logger = logging.getLogger(log_file)

    if std_out:
        add_std_handler(logger)

    logger.info(f'{log_file} logger initiated.')
    logger.info(f'Game root {LOG_FILE.parent}.')
    return logger


LOGGER = get_logger()
