import re


class CommandSanitizer:
    """
    Takes a list of arguments and verifies that each argument is alphanumeric or "-" or "_" and of type string
    Trows a TypeError if any of these conditions is violated.
    """

    def __init__(self, args) -> None:
        if not args:
            raise TypeError('Arguments cannot be empty')

        for arg in args:
            if not isinstance(arg, str):
                raise TypeError(f'arguments must be strings, not {type(arg)} of {str(arg)}')
            if re.search(r'[^a-zA-Z0-9-_]', arg):
                raise TypeError(f'argument contains invalid characters: {arg}')

        self._arguments = args

    @property
    def arguments(self):
        return self._arguments
