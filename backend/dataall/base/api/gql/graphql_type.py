from ._cache import cache_instances


@cache_instances
class ObjectType:
    def __init__(self, name, fields, directives=None, description=''):
        self.name = name
        self.description = description
        self._fields = fields
        self.directives = [] if directives is None else directives

    @property
    def fields(self):
        return self._fields

    def gql(self, with_directives=True):
        n = '\n'
        directives_gql = ''
        description_str = f'"""{self.description}"""{n}' if self.description else ''

        if len(self.directives):
            directives_gql = f'{n} {n.join([d.gql() for d in self.directives])}'
        if with_directives:
            return f'{description_str}type {self.name} {directives_gql} {{ {n} {n.join([f.gql(with_directives=with_directives) for f in self.fields])}{n} }}{n}'
        else:
            return f'{description_str}type {self.name} {{ {n} {n.join([f.gql(with_directives=with_directives) for f in self.fields])}{n} }}{n}'

    def field(self, name):
        return next(filter(lambda f: f.name == name, self.fields), None)

    def get_fields_with_directive(self, *directives):
        fields = {}
        for directive in directives:
            for f in self.fields:
                if f.directive(directive):
                    if not fields.get(f.name):
                        fields[f.name] = {}
                    fields[f.name][directive] = f.directive(directive)
        return fields

    def has_fields_with_directives(self, *directives):
        fields = self.get_fields_with_directive(*directives)
        if len(fields.keys()):
            return True
        return False

    def get_fields_without_directive(self, *directives):
        fields = {}
        for field in self.fields:
            has_none = True
            for directive in directives:
                if field.directive(directive):
                    has_none = False
            if has_none:
                fields[field.name] = field
        return fields

    def directive(self, directive_name):
        return next(filter(lambda d: d.name == directive_name, self.directives), None)

    def has_directive(self, directive_name):
        return self.directive(directive_name) is not None

    def add_field(self, field):
        if not self.field(field.name):
            self.fields.append(field)
        else:
            raise Exception('Field already exists')

    def remove_field(self, field_name):
        if self.field(field_name):
            self.fields = [f for f in self.fields if f.name != field_name]
        else:
            raise Exception('Field does not exist')
