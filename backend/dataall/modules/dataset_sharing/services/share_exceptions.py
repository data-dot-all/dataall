

class ShareItemsFound(Exception):
    def __init__(self, action, message):
        self.action = action
        self.message = f"""
                    An error occurred (ShareItemsFound) when calling {self.action} operation:
                    {message}
                """

    def __str__(self):
        return f'{self.message}'
