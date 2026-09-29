### exposed when "from Patterns import *"" is used
__all__ = ["Factory", "Memoize", "Observer", "Proxy", "Singleton", "Strategy"]

### Allows invoking the class as from Patterns import Singleton, for example, anywhere in the code!
from .Factory import simulator_factory, get_process_memory, get_total_ram  # noqa: F401
from .Memoize import Memoized  # noqa: F401
from .Observer import Observer, Subject  # noqa: F401
from .Singleton import Singleton
from .Proxy import AbstractStreamProxy, AbstractReceiverProxy  # noqa: F401
