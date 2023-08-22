import re


class Identifier:
    def __init__(self, *identifiers) -> None:
        if not identifiers:
            raise TypeError("Identifier cannot be empty")

        for id in identifiers:
            if not isinstance(id, str):
                raise TypeError("SQL identifier parts must be strings")
            if re.search(r"\W", id):
                raise TypeError(f"SQL identifier contains invalid characters: {id}")

        self._identifiers = identifiers

    @property
    def identifiers(self) -> str:
        return self._identifiers

    def __repr__(self) -> str:
        return ".".join(self._identifiers)
