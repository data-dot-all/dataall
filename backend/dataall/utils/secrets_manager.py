import logging
import os

import boto3

log = logging.getLogger("utils:Secrets")


class Secrets:
    prefix = "dataall"

    @classmethod
    def get_secret(cls, env, secret_name):
        print("will get secret", env, secret_name)
        if not secret_name:
            raise Exception("Secret name is None")
        secret_name = f"/{cls.prefix}/{env}/{secret_name}"
        secret_name = secret_name.replace("//", "/")
        print(secret_name)
        client = boto3.client("secretsmanager", region_name=os.getenv("AWS_REGION", "eu-west-1"))
        secret = client.get_secret_value(SecretId=secret_name).get("SecretString")
        print("secret = ", secret)
        return secret
