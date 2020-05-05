"""Contains jitter class"""
import time
from random import randint


class Jitter:
    """
    This class implements the logic to run a function using Backoff with Decorrelated Jitter.
    The logic is based on the following article:
    https://www.awsarchitectureblog.com/2015/03/backoff.html
    """
    BASE = 3
    MAX_POLL_INTERVAL = 60

    def __init__(self, min_wait=0):
        self._time_passed = 0
        self._cycle = 0
        self._min_wait = min_wait

    def backoff(self):
        """
        This function use a cycle count,
        calculates jitter and executes sleep for the calculated time.
        The minimum value 'cycle' can take is 1
        """
        self._cycle += 1
        new_interval = self._min_wait + min(Jitter.MAX_POLL_INTERVAL, randint(Jitter.BASE, self._cycle * 3))
        time.sleep(new_interval)
        self._time_passed += new_interval
        return self._time_passed
