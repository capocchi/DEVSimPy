# Based on threadpool implementation found at http://stackoverflow.com/
# questions/3033952/python-thread-pool-similar-to-the-multiprocessing-pool
try:
    import queue as queue
except ImportError:
    import queue
from threading import Thread

class Worker(Thread):
    """Thread executing tasks from a given tasks queue"""
    def __init__(self, tasks):
        Thread.__init__(self)
        self.tasks = tasks
        self.daemon = True
        self.start()

    def run(self):
        while True:
            func, args, kargs = self.tasks.get()
            try:
                func(*args, **kargs)
            except Exception as e:
                print(e)
            finally:
                self.tasks.task_done()

class ThreadPool(object):
    """Pool of threads consuming tasks from a queue"""
    def __init__(self, num_threads):
        self.tasks = queue.Queue()
        for _ in range(num_threads): 
            Worker(self.tasks)

    def __setstate__(self, obj):
        # Obj will be empty, accept it though
        self.__init__(10)

    def __getstate__(self):
        # A queue is unpicklable...
        return {}

    def add_task(self, func, *args, **kargs):
        """Add a task to the queue"""
        self.tasks.put((func, args, kargs))

    def wait_completion(self):
        """Wait for completion of all the tasks in the queue"""
        self.tasks.join()
