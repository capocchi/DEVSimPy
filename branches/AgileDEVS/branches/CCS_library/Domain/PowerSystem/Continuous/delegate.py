"""delegate.py - delegation of work to multiple processes
Ka-Ping Yee, 15 December 1999

This module provides generic mechanisms for delegating work items.
At the moment, the main delegation mechanism is running work items in
parallel in child processes.  Call 'parallelize' with a function and a
list of items to start the work.  Here is an example:

    def work(arg): return arg * 3
    
    from delegate import parallelize
    print parallelize(work, [2, 5, "a", 7])

The function must return a value that can be pickled so that it can be
communicated back to the parent.  Most kinds of Python objects can be
pickled, including instances of custom classes as long as the class
allows the __init__ constructor to be called with no arguments.  See
the 'pickle' module for details.  The results are returned in a
dictionary that maps each item to its result.

The 'parallelize' function accepts an optional 'reporter' parameter
with which you can provide callbacks when jobs start and finish.  See
the documentation on 'parallelize' and the Reporter class for details.

The 'timeout' function will run a job in a child process in order to
limit its running time.  Here is an example:

    import time
    def work():
        time.sleep(10)
        return 5

    from delegate import timeout
    print timeout(work, 30)             # this will print 5 after 10 seconds
    print timeout(work, 5)              # this will print None after 5 seconds

See the documentation string on 'timeout' for details."""

import sys, traceback, os, signal, select
from math import *

try:
    import cPickle
    pickle = cPickle
except ImportError:
    import pickle

[SUCCESS, FAIL, BEGIN, EXIT] = range(4)

class Exception:
    """Class for passing on exceptions raised in child processes."""
    def __init__(self, type, value, tbdump=""):
        self.type = type
        self.value = value
        self.tbdump = tbdump

    def __repr__(self):
        return "<Exception %s: %s>" % (self.type, self.value)

class Reporter:
    """Abstract base class for Reporter objects.  To handle callbacks
    during processing, declare your own Reporter object that implements
    these methods."""

    def init(self, children):
        """Called by the Parallelizer just before processes are spawned."""
        pass

    def cleanup(self):
        """Called by the Parallelizer when child processes are cleaned up."""
        pass

    def spawn(self, pid):
        """Called by the Parallelizer for each individual child spawned."""
        pass

    def begin(self, pid, item):
        """Called by the Parallelizer when a child starts work on an item."""
        pass

    def success(self, pid, item, result):
        """Called by the Parallelizer when a child produces a result."""
        pass

    def fail(self, pid, item, exception):
        """Called by the Parallelizer when a child raises an exception."""
        pass

    def abort(self, pid, item):
        """Called by the Parallelizer when a child terminates unexpectedly."""
        pass

    def exit(self, pid):
        """Called by the Parallelizer when a child terminates."""
        pass

class LogReporter(Reporter):
    """A reporter that prints out status line-by-line."""
    def init(self, children):
        sys.stderr.write("init %d\n" % children)

    def cleanup(self):
        sys.stderr.write("cleanup\n")

    def spawn(self, pid):
        sys.stderr.write("spawn %d\n" % pid)

    def begin(self, pid, item):
        sys.stderr.write("%d: begin %s\n" % (pid, item))

    def success(self, pid, item, result):
        sys.stderr.write("%d: success %s -> %s\n" % (pid, item, result))

    def fail(self, pid, item, exception):
        sys.stderr.write("%d: fail %s -> %s\n" % (pid, item, exception))

    def abort(self, pid, item):
        sys.stderr.write("abort %d\n" % pid)

    def exit(self, pid):
        sys.stderr.write("exit %d\n" % pid)

class IdPrinter:
    def __init__(self, maxrows):
        self.idrow = {}
        self.rowid = {}
        self.maxrows = maxrows
        sys.stderr.write("\n" * maxrows)

    def printrow(self, row, text):
        sys.stderr.write("\x1b[A" * (self.maxrows - row))
        sys.stderr.write(text + "\x1b[K\r")
        sys.stderr.write("\n" * (self.maxrows - row))

    def printid(self, id, text):
        if self.idrow.has_key(id):
            row = self.idrow[id]
        else:
            row = 0
            while self.rowid.has_key(row): row = row + 1
            self.idrow[id] = row
            self.rowid[row] = id
        self.printrow(row, "%10d: %s" % (id, text))

    def delrow(self, row):
        if not self.rowid.has_key(row): return
        del self.idrow[self.rowid[id]]
        del self.rowid[id]

    def delid(self, id):
        if not self.idrow.has_key(id): return
        del self.rowid[self.idrow[id]]
        del self.idrow[id]

class TerminalReporter(Reporter):
    """A reporter that displays animated status on an ANSI terminal."""
    def init(self, children):
        self.children = children
        self.printer = IdPrinter(children)

    def cleanup(self):
        sys.stderr.write("\n")

    def spawn(self, pid):
        self.printer.printid(pid, "started")

    def begin(self, pid, item):
        self.printer.printid(pid, "%s ..." % repr(item))

    def success(self, pid, item, result):
        self.printer.printid(pid, "%s -> %s" % (repr(item), repr(result)))

    def fail(self, pid, item, exception):
        self.printer.printid(pid, "%s: fail -> %s" % (repr(item), exception))

    def abort(self, pid, item):
        self.printer.printid(pid, "aborted")
        self.printer.delid(pid)

    def exit(self, pid):
        self.printer.printid(pid, "terminated")
        self.printer.delid(pid)

class PipeReader:
    """A file-like read-only interface to a file descriptor."""
    def __init__(self, fd):
        self.fd = fd

    def read(self, bytes):
        return os.read(self.fd, bytes)

    def readline(self):
        line = ""
        while line[-1:] != "\n":
            line = line + os.read(self.fd, 1)
        return line

# ---------------------------------------------------------- utility routines
def failsafe(function, *args, **kw):
    """Run the function with the given arguments and keyword arguments,
    returning the function's return value.  In the event of any exception,
    catch it and return None."""
    try: return apply(function, args, kw)
    except: return None

def reap():
    """Reap any defunct child processes."""
    while 1:
        try: os.waitpid(-1, os.WNOHANG)
        except os.error: return

def pipeload(fd):
    """Unpickle an object from the stream given by a numeric descriptor."""
    return pickle.load(PipeReader(fd))
    
def pipedump(object, fd):
    """Pickle an object to the stream given by a numeric descriptor."""
    os.write(fd, pickle.dumps(object))

def suicide():
    """Terminate this process.  Unlike sys.exit(), which raises a SystemExit
    exception that might be caught, this routine kills the current process.
    Spawned children must exit this way because exceptions must not be allowed
    to escape to code beyond the fork(), which would cause great confusion."""
    os.kill(os.getpid(), signal.SIGKILL)

# -------------------------------------------------------------- Parallelizer
class Parallelizer:
    """Class for maintaining the state of work being done in parallel.
    Usually, the parallelize() function in this module is sufficient; if
    you want to use this class directly, then:

        1. Create a Parallelizer object by passing in the work
           function and the optional Reporter object to the
           Parallelizer() constructor.

        2. Call the 'spawn(children)' method to spawn the specified
           number of child processes.

        3. Call the 'process(items)' method with a list of items to
           process.  You can do this as many times as you want.
           
        4. Be sure to call the 'cleanup()' method to clean away the
           child processes when you are done.

        5. Repeat steps 2 through 4 if you want to spawn more
           children and collect more results.  The results accrue
           in a dictionary in the 'results' attribute."""

    def __init__(self, function, reporter=Reporter()):
        self.function = function
        self.reporter = reporter
        self.results = {}
        self.children = 0

    def child(self, reader, writer):
        try:
            while 1:
                status = pipeload(reader)
                if status == BEGIN:
                    item = pipeload(reader)
                    try:
                        result = self.function(item)
                    except:
                        pipedump(FAIL, writer)
                        pipedump(sys.exc_type, writer)
                        pipedump(sys.exc_value, writer)
                        pipedump(traceback.format_tb(sys.exc_traceback), writer)
                    else:
                        pipedump(SUCCESS, writer)
                        pipedump(result, writer)
                elif status == EXIT:
                    break
        finally:
            os.close(reader)
            os.close(writer)
            suicide()  # Reliably terminate this child process.

    def spawn(self, children):
        if self.children:
            raise RuntimeError, "children are already running"

        self.childinfo = []
        self.fdchild = {}
        self.childitem = [None] * children
        self.readpipes = []
        self.reporter.init(children)
        self.children = children

        for i in range(children):
            childread, parentwrite = os.pipe()
            parentread, childwrite = os.pipe()
            pid = os.fork()
            self.fdchild[parentread] = i
            if pid > 0:
                os.close(childread)
                os.close(childwrite)
                self.childinfo.append((pid, parentread, parentwrite))
                self.reporter.spawn(pid)
            else:
                os.close(parentread)
                os.close(parentwrite)
                self.child(childread, childwrite)

    def process(self, items):
        if not self.children:
            raise RuntimeError, "no children available; call spawn() first"

        while items or self.readpipes:
            for i in range(len(self.childinfo)):
                if items and self.childitem[i] is None:
                    item, items = items[0], items[1:]
                    pid, reader, writer = self.childinfo[i]
                    pipedump(BEGIN, writer)
                    pipedump(item, writer)
                    self.readpipes.append(reader)
                    self.childitem[i] = item
                    self.reporter.begin(pid, item)

            rfds, wfds, efds = select.select(self.readpipes, [], [], None)
            for fd in rfds:
                i = self.fdchild[fd]
                pid, reader, writer = self.childinfo[i]
                item = self.childitem[i]
                self.childitem[i] = None
                self.readpipes.remove(reader)

                try:
                    status = pipeload(reader)
                except EOFError:
                    # A child process has abnormally terminated.
                    self.results[item] = Exception(RuntimeError,
                        "child process %d terminated abnormally" % pid, "")
                    self.reporter.abort(pid, item)
                    self.children = self.children - 1
                    # Stop any more work from being sent to this child.
                    self.childitem[i] = item
                    continue
                    
                if status == SUCCESS:
                    result = pipeload(reader)
                    self.reporter.success(pid, item, result)
                    self.results[item] = result
                else:
                    type, value = pipeload(reader), pipeload(reader)
                    tbdump = pipeload(reader)
                    exception = Exception(type, value, tbdump)
                    self.reporter.fail(pid, item, exception)
                    self.results[item] = exception

            if self.children == 0: break

    def cleanup(self):
        for pid, reader, writer in self.childinfo:
            failsafe(pipedump, EXIT, writer)
            #self.reporter.exit(pid)								# sinon efface le resultat
            os.close(reader)
            os.close(writer)
            failsafe(os.kill, pid, signal.SIGTERM)

        self.childinfo = []
        self.fdchild = {}
        self.childitem = []
        self.readpipes = []
        self.children = 0
        self.reporter.cleanup()
        reap()
        
# ------------------------------------------------------ delegation functions
def parallelize(function, items, children=6, reporter=Reporter()):
    """Run the given function on each member in the 'items' list in parallel,
    and return a dictionary that maps each item to the result returned by the
    function.  The return value of the function must be picklable so that it
    can be communicated from the child process to the parent.  If an exception
    is raised by the function, the result dictionary will map the item to an
    Exception object containing the exception's type and value and a string
    with a printout of the traceback.

    The number of child processes to be spawned is determined by 'children'.
    The optional 'reporter' argument provides a Reporter object to receive
    callbacks as the work proceeds.  See the definition of the Reporter class
    for the interface it should provide."""
    par = Parallelizer(function, reporter=reporter)
    if children > len(items):
        children = len(items)
    par.spawn(children)
    try:
        try:
            par.process(items)
        except:
            raise sys.exc_type, sys.exc_value, sys.exc_traceback
    finally:
        par.cleanup()
    return par.results

def timeout(function, time=2):
    """Run the given function in a child process and return its return value.
    If it raises an exception, return an Exception object containing the
    exception's type and value and a string with a printout of the traceback.
    If the function doesn't return within the given number of seconds, kill
    it and return None."""
    reader, writer = os.pipe()
    child = os.fork()
    if child <= 0:
        os.close(reader)
        try:
            result = function()
        except:
            pipedump(FAIL, writer)
            pipedump(sys.exc_type, writer)
            pipedump(sys.exc_value, writer)
            pipedump(traceback.format_tb(sys.exc_traceback), writer)
        else:
            pipedump(SUCCESS, writer)
            pipedump(result, writer)
        os.close(writer)
        suicide()  # Reliably terminate this child process.

    os.close(writer)
    rfd, wfd, efd = select.select([reader], [], [], time)
    try:
        if rfd:
            status = pipeload(reader)
            if status == SUCCESS:
                result = pipeload(reader)
            else:
                type, value = pipeload(reader), pipeload(reader)
                tbdump = pipeload(reader)
                result = Exception(type, value, tbdump)
        else:
            result = None
        return result
    finally:
        os.close(reader)
        failsafe(os.kill, child, signal.SIGTERM)
        reap()

if __name__ == "__main__":
    import time, random

    def testfunc(item):
        time.sleep(item)
        return 1.0 / (item * 3 - 15)

    print parallelize(testfunc, range(15), reporter=TerminalReporter())
