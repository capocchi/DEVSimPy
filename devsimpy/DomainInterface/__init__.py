### Exposed when "from DomainInterface import *"" is used
__all__ = [	"MasterModel",
			"DomainBehavior",
			"DomainStructure",
			"Object"
			]

### Allows invoking the class as from DomainInterface import DomainBehavior, for example, anywhere in the code!
from .DomainBehavior import *
from .DomainStructure import *
from .MasterModel import Master
from .Object import Message
