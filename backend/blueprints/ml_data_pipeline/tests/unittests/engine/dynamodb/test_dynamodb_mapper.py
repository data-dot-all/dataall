from engine import DynamoDBPropsMapper
from engine.dynamodb.dynamodb_mapper import DynamoDBPropsMapperException
from aws_cdk import aws_dynamodb


from aws_cdk import core

class ATestStack(core.Stack):
    def __init__(self, **kwargs):
        super().__init__(None, **kwargs)
        self.env = {
            "CDK_DEFAULT_ACCOUNT": "012345678912",
            "CDK_DEFAULT_REGION": "eu-west-1",
        }
        self.pipeline_iam_role_arn = "arn:aws:iam::012345678901:role/dhdatasciencedevoqtnpj"
        self.ecr_repository_uri = "dkr.012345678912.eu-west-1"
        self.pipeline_region = "eu-west-1"
        self.resource_tags = {}

    def set_resource_tags(self, resource):
        pass

def test_map_props():
    stack = ATestStack()
    config = { "partition_key": { "name": "equipment", "type": "string"},
                           "sort_key": {"name": "cycle", "type": "number"}}
    assert DynamoDBPropsMapper.map_props(stack, "cyclesdb", config)

def test_map_props_no_sort_key():
    stack = ATestStack()
    config = { "partition_key": { "name": "equipment", "type": "string"}}

    assert DynamoDBPropsMapper.map_props(stack, "cyclesdb", config)

def test_get_type():
    assert DynamoDBPropsMapper.get_type("number") == aws_dynamodb.AttributeType.NUMBER
    assert DynamoDBPropsMapper.get_type("binary") == aws_dynamodb.AttributeType.BINARY
    assert DynamoDBPropsMapper.get_type("string") == aws_dynamodb.AttributeType.STRING

    failed = False
    try:
        DynamoDBPropsMapper.get_type("unknowntype")
    except DynamoDBPropsMapperException as e:
        print(e)
        assert "unknowntype" in e.message
        assert e.arg_name == "type"
        failed = True

    assert failed
