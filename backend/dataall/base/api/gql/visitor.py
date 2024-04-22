class SchemaVisitor:
    @classmethod
    def instanciate(cls, schema):
        return cls(schema)

    def __init__(self, schema):
        self.schema = schema

    def enter_type(self, object_type, schema):
        pass

    def enter_field(self, field, object_type, schema):
        pass

    def leave_type(self, object_type, schema):
        pass

    def leave_field(self, field, object_type, schema):
        pass

    def enter_schema(self, schema):
        pass

    def leave_schema(self, schema):
        pass

    def visit(self):
        self.enter_schema(self.schema)
        for object_type in self.schema.types:
            self.enter_type(object_type=object_type, schema=self.schema)
            for field in object_type.fields:
                self.enter_field(field=field, object_type=object_type, schema=self.schema)
                self.leave_field(field=field, object_type=object_type, schema=self.schema)
            self.leave_type(object_type=object_type, schema=self.schema)
        self.leave_schema(schema=self.schema)
