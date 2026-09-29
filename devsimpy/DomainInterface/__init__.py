### Exposed when "from DomainInterface import *"" is used
__all__ = [
	"DomainBehavior",
	"DomainStructure",
	"MasterModel",
	"Object",
	"handler",
	"transition",
]

### Allows invoking the class as from DomainInterface import DomainBehavior, for example, anywhere in the code!
from .DomainBehavior import *
from .DomainStructure import *
from .MasterModel import Master  # noqa: F401
from .Object import Message  # noqa: F401

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
