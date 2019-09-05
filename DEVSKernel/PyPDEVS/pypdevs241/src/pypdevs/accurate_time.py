import time as python_time
import sys

def time():
    if sys.platform == "win32":
        return python_time.clock()
    else:
        return python_time.time()

def sleep(t):
    python_time.sleep(t)
