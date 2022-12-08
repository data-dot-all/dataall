"""
    1) I created it								DatasetCreator
    2) I belong to the Object Admin group		DatasetAdmin
    5) It's shared with one of My groups		Shared
    6) no permission at all						NoPermission
"""


from backend.api import GraphQLEnumMapper


class SagemakerNotebookRole(GraphQLEnumMapper):
    Creator = '950'
    Admin = '900'
    Shared = '300'
    NoPermission = '000'

