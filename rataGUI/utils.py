import os
import sys
import logging.handlers

def get_project_logger(logging_file):
    logging_file = os.path.abspath(logging_file)
    os.makedirs(os.path.dirname(logging_file), exist_ok=True)
    with open(logging_file, 'a') as f:
        f.write('\n\n')

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # set up logging INFO messages or higher to log file
    file_handler = logging.handlers.RotatingFileHandler(logging_file, mode='a', maxBytes=1e7, backupCount=3)
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s.%(msecs)03d  %(levelname)-8s %(name)-24s %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # set up logging INFO messages or higher to sys.stdout
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(levelname)-8s %(name)-24s %(message)s')
    console.setFormatter(formatter)
    logger.addHandler(console)

    logger.info(f"Logging to {logging_file}")

    return logger


import unicodedata
import re

def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value)
    return re.sub(r'[-\s]+', '-', value).strip('-_')


from PyQt6.QtCore import QRunnable, QObject, pyqtSlot, pyqtSignal

class ThreadSignals(QObject):
    finished = pyqtSignal()
    error = pyqtSignal(Exception)
    result = pyqtSignal(object)

class WorkerThread(QRunnable):
    '''
    Worker that runs an arbitrary function in QThreadPool.
    
    Emits finished, error and result pyqtSignals.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function
    '''

    def __init__(self, func, *args, **kwargs):
        super().__init__()

        # Store constructor arguments (re-used for processing)
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = ThreadSignals()

        # Add the callback to our kwargs
        # self.kwargs['progress_callback'] = self.signals.progress

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''

        # Retrieve args/kwargs here; and fire processing using them
        try:
            result = self.func(*self.args, **self.kwargs)
        except Exception as err:
            self.signals.error.emit(err)
            raise err
        else:
            self.signals.result.emit(result)  # Return the result of the process
        finally:
            self.signals.finished.emit()  # Done