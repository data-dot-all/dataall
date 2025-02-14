from abc import ABC
from typing import Dict

from dataall.base.api import GraphQLEnumMapper


class MetadataFormEntityTypes(GraphQLEnumMapper):
    Organization = 'Organization'
    OrganizationTeam = 'Organization Team'
    Environment = 'Environment'
    EnvironmentTeam = 'Environment Team'
    S3Dataset = 'S3-Dataset'
    RDDataset = 'Redshift-Dataset'
    Worksheet = 'Worksheet'
    Dashboard = 'Dashboard'
    ConsumptionRole = 'Consumption Role'
    Notebook = 'Notebook'
    MLStudioUser = 'ML Studio User'
    Pipeline = 'Pipeline'
    Table = 'Table'
    Folder = 'Folder'
    Bucket = 'Bucket'
    Share = 'Share'


class MetadataFormEntity(ABC):
    def owner_name(self):
        pass

    def entity_name(self):
        pass

    def uri(self):
        pass


class MetadataFormEntityManager:
    """
    API for managing entities, to which MF can be attached.
    """

    _resources: Dict[str, MetadataFormEntity] = {}

    @classmethod
    def register(cls, resource: MetadataFormEntity, resource_key):
        cls._resources[resource_key] = resource

    @classmethod
    def get_resource(cls, resource_key):
        if resource_key not in cls._resources:
            raise NotImplementedError(f'Entity {resource_key} is not registered')
        return cls._resources[resource_key]

    @classmethod
    def is_registered(cls, resource_key):
        return resource_key in cls._resources

    @classmethod
    def all_registered_keys(cls):
        return cls._resources.keys()
