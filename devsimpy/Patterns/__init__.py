### exposed when "from Patterns import *"" is used
__all__ = [ 'Observer',
	'Strategy',
	'Memoize',
	'Factory',
    'Singleton'
 ]

### Allows invoking the class as from Patterns import Singleton, for example, anywhere in the code!
from .Factory import simulator_factory,  get_process_memory, get_total_ram
from .Memoize import Memoized
from .Observer import Observer, Subject
from .Singleton import Singleton