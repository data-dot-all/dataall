from aws_cdk import aws_dynamodb, core


class DynamoDBPropsMapperException(Exception):
    def __init__(self, error, arg_name):
        super().__init__()
        self.message = f'Failed to create Lambda function for attribute `{arg_name}` due to error: `{error}`'
        self.error = error
        self.arg_name = arg_name

    def __str__(self):
        return self.message


class DynamoDBPropsMapper:
    @classmethod
    def map_props(cls, stack, table_name, config_props: dict) -> dict:
        table = dict(
            table_name=table_name,
            partition_key=aws_dynamodb.Attribute(
                name=config_props['partition_key']['name'],
                type=cls.get_type(config_props['partition_key']['type']),
            ),
            sort_key=cls.map_sort_key(config_props),
            removal_policy=core.RemovalPolicy.DESTROY,
            encryption=aws_dynamodb.TableEncryption.AWS_MANAGED,
            read_capacity=config_props.get('read_capacity'),
            write_capacity=config_props.get('write_capacity'),
        )
        return table

    @classmethod
    def map_sort_key(cls, config_props):
        if config_props.get('sort_key'):
            return aws_dynamodb.Attribute(
                name=config_props.get('sort_key').get('name'),
                type=cls.get_type(config_props.get('sort_key').get('type')),
            )

    @classmethod
    def get_type(cls, typ):
        if typ == 'number':
            return aws_dynamodb.AttributeType.NUMBER
        elif typ == 'binary':
            return aws_dynamodb.AttributeType.BINARY
        elif typ == 'string':
            return aws_dynamodb.AttributeType.STRING
        else:
            raise DynamoDBPropsMapperException('Unknown type {}'.format(typ), 'type')
