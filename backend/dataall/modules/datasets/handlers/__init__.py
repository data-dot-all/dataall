"""
Contains code with the handlers that are need for async
processing in a separate lambda function
"""
from dataall.modules.datasets.handlers import (
    glue_column_handler,
    glue_table_handler
)

__all__ = ["glue_column_handler", "glue_table_handler"]
