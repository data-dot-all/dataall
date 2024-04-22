import aws_cdk as core
import aws_cdk.assertions as assertions

from data_pipeline_blueprint.dataall_pipeline_app.dataall_pipeline_app_stack import DataallPipelineStack


# example tests. To run these tests, uncomment this file along with the example
# resource in data_pipeline_blueprint/data_pipeline_blueprint_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = DataallPipelineStack(app, 'dataall-pipeline-stack', 'test')
    template = assertions.Template.from_stack(stack)


#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
