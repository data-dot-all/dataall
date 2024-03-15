import abc


class BaseEmailNotificationService:
    @abc.abstractmethod
    def send_email(self, to, message, subject):
        raise NotImplementedError
