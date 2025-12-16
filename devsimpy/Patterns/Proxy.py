from abc import ABC, abstractmethod

class AbstractStreamProxy(ABC):
    """
    Abstract class for message-sending proxies (Producer).
    Defines the interface for all sended proxies.
    """
    
    @abstractmethod
    def send_message(self, *args, **kargs):
        """
        Send messages.
        """
        pass


class AbstractReceiverProxy(ABC):
    """
    Abstract class for receive message proxies (Consumer).
    Define the interface for all receiver proxies.
    """
    
    @abstractmethod
    def receive_messages(self, *args, **kargs):
        """ Wait messages.
        """
        pass