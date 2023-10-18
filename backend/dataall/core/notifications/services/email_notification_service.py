import abc


class EmailNotificationService:

    @abc.abstractmethod
    def send_email(self, to, message, subject):
        raise NotImplementedError
