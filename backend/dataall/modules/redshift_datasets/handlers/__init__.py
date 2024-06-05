"""
Contains code with the handlers that are need for async
processing in a separate lambda function
"""

from dataall.modules.redshift_datasets.handlers import redshift_datashare_handler

__all__ = ['redshift_datashare_handler']
