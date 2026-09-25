### Exposed when "from DomainInterface import *"" is used
__all__ = [
    "MasterModel",
    "DomainBehavior",
    "DomainStructure",
    "Object",
    "transition",
    "handler",
]

### Allows invoking the class as from DomainInterface import DomainBehavior, for example, anywhere in the code!
from .DomainBehavior import *
from .DomainStructure import *
from .MasterModel import Master
from .Object import Message

try:
    from devsimpy.DEVSKernel.PyDEVS.DEVS import transition as _transition, handler as _handler
except Exception:
    def _transition(kind):
        def decorator(fn):
            fn.__devs_transition__ = kind
            return fn
        return decorator

    def _handler(kind):
        def decorator(fn):
            fn.__devs_handler__ = kind
            return fn
        return decorator

import builtins
builtins.transition = _transition
builtins.handler = _handler