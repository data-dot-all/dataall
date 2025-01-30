from .graphql_field import Field
from .graphql_scalar import String
from .graphql_type import ObjectType


class Schema:
    def __init__(self, types=None, inputs=None, enums=None, unions=[]):
        self.types = types if types else []
        self.inputs = inputs if inputs else []
        self.enums = enums if enums else []
        self.unions = unions if unions else []
        self.ensure_query()
        self.ensure_mutation()
        self.context = {}

    def update_context(self, key, value):
        self.context[key] = value

    def ensure_query(self):
        if not self.type('Query'):
            self.add_type(ObjectType(name='Query', fields=[Field(name='test', type=String)]))
        elif not len(self.type('Query').fields):
            self.type('Query').add_field(field=Field(name='test', type=String))

    def ensure_mutation(self):
        if not self.type('Mutation'):
            self.add_type(ObjectType(name='Mutation', fields=[Field(name='test', type=String)]))
        elif not len(self.type('Mutation').fields):
            self.type('Mutation').add_field(field=Field(name='test', type=String))

    def enum(self, enum_name):
        return next(filter(lambda t: t.name == enum_name, self.enums), None)

    def union(self, union_name):
        return next(filter(lambda t: t.name == union_name, self.unions), None)

    def type(self, type_name) -> ObjectType:
        return next(filter(lambda t: t.name == type_name, self.types), None)

    def input_type(self, type_name):
        return next(filter(lambda t: t.name == type_name, self.inputs), None)

    def add_type(self, type):
        if not self.type(type.name):
            self.types.append(type)
        else:
            raise Exception('Type already exists')

    def remove_type(self, type_name):
        if self.type(type_name):
            self.types = [t for t in self.types if t.name != type_name]
        else:
            raise Exception('Type not found')

    def add_input_type(self, input_type):
        if not self.input_type(input_type.name):
            self.inputs.append(input_type)
        else:
            raise Exception('InputType already exists')

    def remove_input_type(self, input_type_name):
        if self.input_type(input_type_name):
            self.inputs = [t for t in self.inputs if t.name != input_type_name]
        else:
            raise Exception('InputType not found')

    def get_types_by_directive_name(self, directive_name):
        if isinstance(directive_name, list):
            types = {}
            for t in self.types:
                for directive in directive_name:
                    if t.has_directive(directive):
                        if not types.get(t.name):
                            types[t.name] = []
                        types[t].append(directive)
            return types
        else:
            return [t for t in self.types if t.has_directive(directive_name)]

    def gql(self, with_directives=True):
        n = '\n'
        input_types = ''
        enums = ''
        unions = ''
        if len(self.inputs):
            input_types = f"""{n.join([i.gql() for i in self.inputs])}{n}"""
        if len(self.enums):
            enums = f"""{n.join([e.gql() for e in self.enums])}{n}"""

        if len(self.unions):
            unions = f"""{n.join([u.gql() for u in self.unions])}{n}"""

        types = f"""{n} {n.join([n + t.gql(with_directives=with_directives) + n for t in self.types])}"""
        return f"""{enums}{input_types}{unions}{types}"""

    def visit(self, visitors=[]):
        if not (isinstance(visitors, list)):
            visitor_list = [v for v in [visitors]]
        else:
            visitor_list = [v for v in visitors]
        for VisitorClass in visitor_list:
            v = VisitorClass.instanciate(schema=self)
            v.visit()

    def resolve(self, path, context, source, **kwargs):
        object_type_name, field_name = path.split('/')
        print(f'>{object_type_name}.{field_name}<')
        object_type = self.type(object_type_name)
        field = object_type.field(field_name)
        print('?', field)
        if field and field.resolver:
            return field.resolver(context, source, **kwargs)


if __name__ == '__main__':
    schema = Schema(types=[ObjectType(name='Account', fields=[Field(name='uri', type=String)])])

    print(schema.gql())
