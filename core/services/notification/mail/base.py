from abc import ABC, abstractmethod


class BaseMail(ABC):
    """
    Abstract base class for email backends. Defines the basic structure for email content
    and enforces implementation of the send method.
    """
    def __init__(self, from_email: str):
        """
        Initialize base email content and sender.
        """
        self.subject = "Your personalized poster is ready!"
        self.body = (
            "Hello,\n\n"
            "Your personalized poster has been successfully generated and is now ready.\n\n"
            "You can view or download it\n\n"
            "Thank you for using our service!"
        )
        self.from_email = from_email

    @abstractmethod
    def send(self, to_email: str):
        """
        Sends an email to the specified recipient.
        """
        raise NotImplementedError("Subclasses must implement this method")
