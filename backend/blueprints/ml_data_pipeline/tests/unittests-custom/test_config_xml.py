
from utils.task_group_reader import TaskGroupReader
def test_parse_config_yaml():
    """ Parses config.yaml """
    pipeline = TaskGroupReader(
        path="config.yaml",
        template_vars={"model_name": "example"},
    )

    assert pipeline.definition.get("groups") or pipeline.definition.get("aws_resources") 
