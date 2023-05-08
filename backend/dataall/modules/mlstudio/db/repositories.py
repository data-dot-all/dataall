"""
DAO layer that encapsulates the logic and interaction with the database for ML Studio
Provides the API to retrieve / update / delete ml studio
"""
from sqlalchemy import or_
from sqlalchemy.orm import Query

from dataall.db import paginate
from dataall.modules.mlstudio.db.models import MLStudio


class SageMakerStudioRepository:
    """DAO layer for ML Studio"""
    _DEFAULT_PAGE = 1
    _DEFAULT_PAGE_SIZE = 10
