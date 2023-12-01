import os

from dataall.base.aws.cognito import Cognito


class ServiceProviderFactory:

    @staticmethod
    def get_service_provider_instance():
        if (os.environ.get("custom_auth", None)):
            # Return instance of your service provider which implements the ServiceProvider interface
            # Please take a look at the "Deploy to AWS" , External IDP section for steps
            return None
        else:
            return Cognito()
