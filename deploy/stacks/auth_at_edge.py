from aws_cdk import (
    aws_ssm as ssm,
    aws_sam as sam,
)

from .pyNestedStack import pyNestedClass


class AuthAtEdge(pyNestedClass):
    def __init__(self, scope, id, envname='dev', resource_prefix='dataall', **kwargs):
        super().__init__(scope, id, **kwargs)

        userpool_arn = ssm.StringParameter.value_for_string_parameter(
            self, parameter_name=f'/dataall/{envname}/cognito/userpoolarn'
        )

        userpool_client_id = ssm.StringParameter.value_for_string_parameter(
            self, parameter_name=f'/dataall/{envname}/cognito/appclient'
        )

        devdoc_app = sam.CfnApplication(
            self,
            f'{resource_prefix}-{envname}-authatedge',
            location={
                'applicationId': 'arn:aws:serverlessrepo:us-east-1:520945424137:applications/cloudfront-authorization-at-edge',
                'semanticVersion': '2.1.5',
            },
            parameters={
                'UserPoolArn': userpool_arn,
                'UserPoolClientId': userpool_client_id,
                'EnableSPAMode': 'true',
                'CreateCloudFrontDistribution': 'false',
            },
        )
        self.devdoc_app = devdoc_app

        self.parse = ssm.StringParameter(
            self,
            f'ParseParam',
            parameter_name=f'/dataall/{envname}/authatedge/parseauth',
            string_value=devdoc_app.get_att('Outputs.ParseAuthHandler').to_string(),
        )

        self.refresh = ssm.StringParameter(
            self,
            f'RefreshParam',
            parameter_name=f'/dataall/{envname}/authatedge/refreshauth',
            string_value=devdoc_app.get_att('Outputs.RefreshAuthHandler').to_string(),
        )

        self.signout = ssm.StringParameter(
            self,
            f'SignoutParam',
            parameter_name=f'/dataall/{envname}/authatedge/singoutauth',
            string_value=devdoc_app.get_att('Outputs.SignOutHandler').to_string(),
        )

        self.check = ssm.StringParameter(
            self,
            f'CheckParam',
            parameter_name=f'/dataall/{envname}/authatedge/checkauth',
            string_value=devdoc_app.get_att('Outputs.CheckAuthHandler').to_string(),
        )

        self.httpheaders = ssm.StringParameter(
            self,
            f'HttpHeadersParam',
            parameter_name=f'/dataall/{envname}/authatedge/httpheadersauth',
            string_value=devdoc_app.get_att('Outputs.HttpHeadersHandler').to_string(),
        )
