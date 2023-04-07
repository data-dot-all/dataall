"""Contains the enums GraphQL mapping for Omics Pipelines"""

#
# (c) 2023 Amazon Web Services, Inc. or its affiliates. All Rights Reserved.
# This AWS Content is provided subject to the terms of the AWS Customer
# Agreement available at http://aws.amazon.com/agreement or other
# written agreement between Customer and Amazon Web Services, Inc.
#

from dataall.api.constants import GraphQLEnumMapper

class OmicsPipelineRole(GraphQLEnumMapper):
    Creator = "999"
    Admin = "900"
    NoPermission = "000"