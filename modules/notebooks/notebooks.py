from ..module import Module
from backend import api
import os

class Notebooks(Module):

    def define_graphql_api_path(self):
        return f"notebooks/backend/api"

    def define_ecs_task_path(self):
        return None

    def define_frontend_views_path(self):
        return None