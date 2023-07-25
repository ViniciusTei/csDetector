import logging
import datetime

def generate_filename_with_datetime():
    current_datetime = datetime.datetime.now()
    formated_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{formated_datetime}.txt"
    return filename


filename=generate_filename_with_datetime()
logging.basicConfig(filename=filename, encoding='utf-8', level=logging.DEBUG)

class Logger():
    def __init__(self) -> None:
        logger = logging.getLogger()
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
                        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        self.__logger = logger
        pass
        
    def log(self, type, mensage):
        if (type == 'info'):
            self.__logger.info(msg=mensage)
        elif (type == 'erro'):
            self.__logger.error(msg=mensage)
        else:
            self.__logger.info(msg=mensage)
        pass
