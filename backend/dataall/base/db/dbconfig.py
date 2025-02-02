import os
import re

_SANITIZE_WORD_REGEX = r'[^\w]'  # A-Za-z0-9_
_SANITIZE_HOST_REGEX = r'[^\w.-]'
_SANITIZE_PWD_REGEX = r"[\"\s%+~`#$&*()|\[\]{}:;<>?!'/]+"
_AURORA_HOST_SUFFIX = 'rds.amazonaws.com'
_POSTGRES_MAX_LEN = 63
_MAX_HOST_LENGTH = 253

_envname = os.getenv('envname', 'local')


class DbConfig:
    def __init__(self, user: str, pwd: str, host: str, db: str, schema: str):
        for param in (user, db, schema):
            if len(param) > _POSTGRES_MAX_LEN:
                raise ValueError(
                    f"PostgreSQL doesn't allow values more than 63 characters parameters {user}, {db}, {schema}"
                )

        if len(host) > _MAX_HOST_LENGTH:
            raise ValueError(f'Hostname is too long: {host}')

        if _envname not in ['local', 'pytest', 'dkrcompose'] and not host.lower().endswith(_AURORA_HOST_SUFFIX):
            raise ValueError(f'Unknown host {host} for the rds')

        self.user = self._sanitize_and_compare(_SANITIZE_WORD_REGEX, user, 'username')
        self.host = self._sanitize_and_compare(_SANITIZE_HOST_REGEX, host, 'host')
        self.db = self._sanitize_and_compare(_SANITIZE_WORD_REGEX, db, 'database name')
        self.schema = self._sanitize_and_compare(_SANITIZE_WORD_REGEX, schema, 'schema')
        pwd = self._sanitize_and_compare(_SANITIZE_PWD_REGEX, pwd, 'password')
        self.url = f'postgresql+pygresql://{self.user}:{pwd}@{self.host}/{self.db}'

    def __str__(self):
        lines = ['  DbConfig >']
        hr = ' '.join(['+', ''.ljust(10, '-'), '+', ''.ljust(65, '-'), '+'])
        lines.append(hr)
        header = ' '.join(['+', 'Db Param'.ljust(10), ' ', 'Value'.ljust(65), '+'])
        lines.append(header)
        hr = ' '.join(['+', ''.ljust(10, '-'), '+', ''.ljust(65, '-'), '+'])
        lines.append(hr)
        lines.append(' '.join(['|', 'host'.ljust(10), '|', self.host.ljust(65), '|']))
        lines.append(' '.join(['|', 'db'.ljust(10), '|', self.db.ljust(65), '|']))
        lines.append(' '.join(['|', 'user'.ljust(10), '|', self.user.ljust(65), '|']))
        lines.append(' '.join(['|', 'pwd'.ljust(10), '|', '*****'.ljust(65), '|']))

        hr = ' '.join(['+', ''.ljust(10, '-'), '+', ''.ljust(65, '-'), '+'])
        lines.append(hr)
        return '\n'.join(lines)

    @staticmethod
    def _sanitize_and_compare(regex, string: str, param_name) -> str:
        sanitized = re.sub(regex, '', string)
        if sanitized != string:
            raise ValueError(
                f"Can't create a database connection. The {param_name} parameter has invalid symbols."
                f' The sanitized string length: {len(sanitized)} <  original : {len(string)}'
            )
        return sanitized
