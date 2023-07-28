import logging
import datetime
import os

def generate_filename_with_datetime():
    current_datetime = datetime.datetime.now()
    formated_datetime = current_datetime.strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{formated_datetime}.txt"
    abs_path = os.path.abspath(f"logs/{filename}")
    return abs_path

filename=generate_filename_with_datetime()
logging.basicConfig(filename=filename, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Logger():
    def __init__(self) -> None:
        logger = logging.getLogger()
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

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
