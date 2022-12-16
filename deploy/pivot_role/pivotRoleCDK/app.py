#!/usr/bin/env python3

from aws_cdk import (
    App,
)

from .dataall_base_infra import dataAllBaseInfra

config = {
    "NAME": "someenvironment",
    "DATAALL_ACCOUNT": "AWSAccountId",
    "EXTERNAL_ID": "externalId",
    "RESOURCE_PREFIX": "resourcePrefix"
}

app = App()

# data.all base resources: pivot role and LakeFormation service role
dataall_infra = dataAllBaseInfra(
    app,
    f"BaseInfra-dataall-{config.NAME}",
    config=config,
)

app.synth()
