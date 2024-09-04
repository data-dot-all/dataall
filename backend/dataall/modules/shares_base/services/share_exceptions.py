class BaseShareException(Exception):
    def __init__(self, type, action, message):
        self.type = type
        self.action = action
        self.message = f"""
                    An error occurred ({self.type}) when calling {self.action} operation:
                    {message}
                """

    def __str__(self):
        return f'{self.message}'


class ShareItemsFound(BaseShareException):
    def __init__(self, action, message):
        super().__init__('ShareItemsFound', action, message)


class PrincipalRoleNotFound(BaseShareException):
    def __init__(self, action, message):
        super().__init__('PrincipalRoleNotFound', action, message)


class InvalidConfiguration(BaseShareException):
    def __init__(self, action, message):
        super().__init__('InvalidConfiguration', action, message)
