"""
Contains code with the handlers that are need for async
processing in a separate lambda function
"""

from dataall.modules.datapipelines.handlers import (
    codecommit_datapipeline_handler,
)

__all__ = ['codecommit_datapipeline_handler']
