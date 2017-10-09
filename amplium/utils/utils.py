"""Contains utility functions"""
from amplium.api.exceptions import AmpliumException
from amplium.utils.jitter import Jitter


def retry(func, max_time, *args, **kwargs):
    """
    Retries functions with provided arguments until max time is passed or an exception not in
    ignored_exceptions is returned.
    :param func: The python function to retry
    :param max_time: The maximum amount of time, in seconds, to retry the function
    :param args: Arguments to pass into func
    :param kwargs: Keyword arguments to pass into func
    :return: The result of calling func
    """

    jitter = Jitter()
    time_passed = 0
    while True:
        try:
            return func(*args, **kwargs)
        except AmpliumException:
            if time_passed < max_time:
                time_passed = jitter.backoff()
            else:
                raise
