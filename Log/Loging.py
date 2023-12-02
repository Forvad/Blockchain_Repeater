from sys import stderr
from loguru import logger


def log(numb=None):
    try:
        logger.remove()
        if not numb:
            logger.add(stderr, format='<white>{time:HH:mm:ss}</white>'
                                      ' | <level>{level: <2}</level>'
                                      ' | <level>{message}</level>')
        logger.add('./Log/Main.log')
        return logger
    except BaseException:
        return logger


def inv_log():
    try:
        logger.remove()
        logger.add(stderr, format='<white>{time:HH:mm:ss}</white>'
                                  ' | <level>{level: <2}</level>'
                                  ' | <level>{message}</level>')
        logger.remove(handler_id=None)
        logger.add('./Log/Main.log')
        return logger
    except BaseException:
        return logger

if __name__ == '__main__':
    pass
