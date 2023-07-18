class DbConfig:
    def __init__(self, **kwargs):
        self.params = kwargs
        self.url = f"postgresql+pygresql://{self.params['user']}:{self.params['pwd']}@{self.params['host']}/{self.params['db']}"

    def __str__(self):
        lines = []
        lines.append('  DbConfig >')
        hr = ' '.join(['+', ''.ljust(10, '-'), '+', ''.ljust(65, '-'), '+'])
        lines.append(hr)
        header = ' '.join(['+', 'Db Param'.ljust(10), ' ', 'Value'.ljust(65), '+'])
        lines.append(header)
        hr = ' '.join(['+', ''.ljust(10, '-'), '+', ''.ljust(65, '-'), '+'])
        lines.append(hr)
        for k in self.params:
            v = self.params[k]
            if k == 'pwd':
                v = '*' * len(self.params[k])
            lines.append(' '.join(['|', k.ljust(10), '|', v.ljust(65), '|']))

        hr = ' '.join(['+', ''.ljust(10, '-'), '+', ''.ljust(65, '-'), '+'])
        lines.append(hr)
        return '\n'.join(lines)
