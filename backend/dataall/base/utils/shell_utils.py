import re


class CommandSanitizer:
    def __init__(self, *args) -> None:
        if not args:
            raise TypeError("Identifier cannot be empty")

        for arg in args:
            if not isinstance(arg, str):
                raise TypeError("arguments must be strings")
            if re.search(r"\W", arg):
                raise TypeError(f"argument contains invalid characters: {arg}")

        self._command = ".".join(args)

    @property
    def command(self) -> str:
        return self._command
