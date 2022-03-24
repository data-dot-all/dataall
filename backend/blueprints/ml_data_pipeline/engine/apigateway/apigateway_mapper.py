from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_lambda_python as lambda_python

from ..lambdafx.lambda_mapper import LambdaFxPropsMapper


class ApiGatewayPropsMapper:
    @classmethod
    def map_props(
        cls,
        stack,
        api_name,
        config_props: dict,
    ) -> dict:
        base_api = apigw.RestApi(stack, api_name, rest_api_name=api_name)
        cls.add_resources(
            base_api, config_props.get('resources', []), base_api.root, stack
        )
        return base_api

    @classmethod
    def add_resources(cls, base_api, resources, parent, stack):
        for resource in resources:
            methods = ['OPTIONS']
            api_resource = parent.add_resource(resource['path'])
            if 'integrations' in resource:
                for lambda_integration in resource['integrations']:
                    api_resource_lambda_integration = apigw.LambdaIntegration(
                        lambda_python.PythonFunction(
                            stack,
                            lambda_integration['name'],
                            **LambdaFxPropsMapper.map_function_props(
                                stack,
                                lambda_integration['name'],
                                lambda_integration['config'],
                            ),
                        ),
                        proxy=resource.get('proxy', False),
                        integration_responses=[
                            {
                                'statusCode': '200',
                                'responseParameters': {
                                    'method.response.header.Access-Control-Allow-Origin': "'*'",
                                },
                            }
                        ],
                    )
                    api_resource.add_method(
                        lambda_integration['method'],
                        api_resource_lambda_integration,
                        method_responses=[
                            {
                                'statusCode': '200',
                                'responseParameters': {
                                    'method.response.header.Access-Control-Allow-Origin': True,
                                },
                            }
                        ],
                    )
                    methods.append(lambda_integration['method'])
            cls.add_options(methods, api_resource)
            #  child resources in apigw
            if 'resources' in resource:
                cls.add_resources(base_api, resource['resources'], api_resource, stack)

    @classmethod
    def add_options(cls, methods, api_resource):
        api_resource.add_method(
            'OPTIONS',
            apigw.MockIntegration(
                integration_responses=[
                    {
                        'statusCode': '200',
                        'responseParameters': {
                            'method.response.header.Access-Control-Allow-Headers': "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                            'method.response.header.Access-Control-Allow-Origin': "'*'",
                            'method.response.header.Access-Control-Allow-Methods': f"'{(',').join(methods)}'",
                        },
                    }
                ],
                passthrough_behavior=apigw.PassthroughBehavior.WHEN_NO_MATCH,
                request_templates={'application/json': '{"statusCode":200}'},
            ),
            method_responses=[
                {
                    'statusCode': '200',
                    'responseParameters': {
                        'method.response.header.Access-Control-Allow-Headers': True,
                        'method.response.header.Access-Control-Allow-Methods': True,
                        'method.response.header.Access-Control-Allow-Origin': True,
                    },
                }
            ],
        )
