from dataall.core.resource_threshold.db.resource_threshold import ResourceThreshold
from sqlalchemy import and_, func
from dataall.base.config import config
from dataall.base.db import exceptions
from functools import wraps


class ResourceThresholdRepository:
    _RESOURCE_PATHS = {'nlq': 'modules.worksheets.features.max_count_per_day'}

    @staticmethod
    def _get_count_today(session, username, action_type):
        amount = (
            session.query(ResourceThreshold.count)
            .filter(
                and_(
                    ResourceThreshold.username == username,
                    ResourceThreshold.actionType == action_type,
                    ResourceThreshold.date == func.current_date(),
                )
            )
            .scalar()
        )
        return amount if amount else 0

    @staticmethod
    def _add_entry(session, username, action_type):
        user_entry = ResourceThresholdRepository._get_user_entry(session, username, action_type)
        if user_entry:
            user_entry.update(
                {ResourceThreshold.count: 1, ResourceThreshold.date: func.current_date()}, synchronize_session=False
            )
            session.commit()
        else:
            action_entry = ResourceThreshold(username=username, actionType=action_type)
            session.add(action_entry)

    @staticmethod
    def _increment_count(session, username, action_type):
        session.query(ResourceThreshold).filter(
            and_(
                ResourceThreshold.username == username,
                ResourceThreshold.actionType == action_type,
                ResourceThreshold.date == func.current_date(),
            )
        ).update({ResourceThreshold.count: ResourceThreshold.count + 1}, synchronize_session=False)
        session.commit()

    @staticmethod
    def _get_user_entry(session, username, action_type):
        entry = session.query(ResourceThreshold).filter(
            and_(ResourceThreshold.username == username, ResourceThreshold.actionType == action_type)
        )
        return entry

    @staticmethod
    def check_invocation_count(action_type):
        def decorator(func):
            @wraps(func)
            def wrapper(session, username, *args, **kwargs):
                count = ResourceThresholdRepository._get_count_today(
                    session=session, username=username, action_type=action_type
                )
                max_count = config.get_property(ResourceThresholdRepository._RESOURCE_PATHS[action_type], 10)
                if count < max_count:
                    if count == 0:
                        ResourceThresholdRepository._add_entry(
                            session=session, username=username, action_type=action_type
                        )
                    else:
                        ResourceThresholdRepository._increment_count(
                            session=session, username=username, action_type=action_type
                        )
                    return func(session, username, *args, **kwargs)
                else:
                    raise exceptions.ResourceThresholdExceeded(username=username, action=action_type)

            return wrapper

        return decorator
