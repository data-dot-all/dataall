from dataall.base.api.context import Context
from dataall.base.db import exceptions
from dataall.modules.warehouses.services.warehouse_service import WarehouseService


def create_warehouse_connection(context, source, input: dict = None):
    """Creates a Warehouse connection"""
    RequestValidator.validate_creation_request(input)
    return WarehouseService.create_warehouse_connection(
        uri=input["environmentUri"], #todo; DECIDE: DO WE MAKE IT AN ENVIRONMENT PERMISSION?
        admin_group=input["SamlAdminGroupName"],
        input=input
    )

def create_warehouse_consumer(context, source, input: dict = None):
    """Creates a Warehouse consumer"""
    RequestValidator.validate_creation_request(input)
    return WarehouseService.create_warehouse_consumer(
        uri=input["environmentUri"],
        admin_group=input["SamlAdminGroupName"],
        input=input
    )

def update_warehouse_connection(context, source, input: dict = None):
    """Updates a Warehouse connection"""
    RequestValidator.validate_creation_request(input)
    return WarehouseService.update_warehouse_connection(
        uri=input["connectionUri"],
        admin_group=input["SamlAdminGroupName"],
        input=input
    )

def update_warehouse_consumer(context, source, input: dict = None):
    """Updates a Warehouse consumer"""
    RequestValidator.validate_creation_request(input)
    return WarehouseService.update_warehouse_consumer(
        uri=input["consumerUri"],
        admin_group=input["SamlAdminGroupName"],
        input=input
    )

def delete_warehouse_connection(context, source, connectionUri: str):
    """Deletes a Warehouse connection"""
    RequestValidator.required_uri(connectionUri)
    return WarehouseService.delete_warehouse_connection(
        uri=connectionUri,
    )

def delete_warehouse_consumer(context, source, consumerUri: str):
    """Deletes a Warehouse consumer"""
    RequestValidator.required_uri(consumerUri)
    return WarehouseService.delete_warehouse_consumer(
        uri=consumerUri,
    )


def list_warehouse_connections(context, source, input: dict = None):
    """Lists user Warehouse connections"""
    return WarehouseService.list_warehouse_connections()


def list_warehouse_consumers(context, source, input: dict = None):
    """Lists user Warehouse consumers"""
    return WarehouseService.list_warehouse_consumers()


class RequestValidator:
    """Aggregates all validation logic for operating with Warehouses"""
    @staticmethod
    def required_uri(uri):
        if not uri:
            raise exceptions.RequiredParameter('URI')

    @staticmethod
    def validate_creation_request(data):
        required = RequestValidator._required
        if not data:
            raise exceptions.RequiredParameter('data')
        if not data.get('label'):
            raise exceptions.RequiredParameter('name')

        required(data, "environmentUri")
        required(data, "SamlAdminGroupName")

    @staticmethod
    def _required(data: dict, name: str):
        if not data.get(name):
            raise exceptions.RequiredParameter(name)
