from dataall.core.environment.services.environment_resource_manager import EnvironmentResource
from dataall.core.resource_threshold.db.resource_threshold import ResourceTreshold
from sqlalchemy import and_, func
from dataall.base.config import config


class ResourceThresholdRepository(EnvironmentResource):
    resource_paths = {'nlq': 'modules.worksheets.features.max_count_per_day'}

    @staticmethod
    def get_count_today(session, username, action_type):
        amount = (
            session.query(ResourceTreshold.count)
            .filter(
                and_(
                    ResourceTreshold.username == username,
                    ResourceTreshold.actionType == action_type,
                    ResourceTreshold.date == func.current_date(),
                )
            )
            .scalar()
        )
        return amount if amount else 0

    @staticmethod
    def add_entry(session, username, action_type):
        user_entry = ResourceThresholdRepository.get_user_entry(session, username, action_type)
        if user_entry:
            user_entry.update(
                {ResourceTreshold.count: 1, ResourceTreshold.date: func.current_date()}, synchronize_session=False
            )
            session.commit()
        else:
            action_entry = ResourceTreshold(username=username, actionType=action_type)
            session.add(action_entry)

    @staticmethod
    def increment_count(session, username, action_type):
        session.query(ResourceTreshold).filter(
            and_(
                ResourceTreshold.username == username,
                ResourceTreshold.actionType == action_type,
                ResourceTreshold.date == func.current_date(),
            )
        ).update({ResourceTreshold.count: ResourceTreshold.count + 1}, synchronize_session=False)
        session.commit()

    @staticmethod
    def get_user_entry(session, username, action_type):
        entry = session.query(ResourceTreshold).filter(
            and_(ResourceTreshold.username == username, ResourceTreshold.actionType == action_type)
        )
        return entry

    @staticmethod
    def invocation_handler(action_type):
        def decorator(func):
            def wrapper(session, username, *args, **kwargs):
                count = ResourceThresholdRepository.get_count_today(
                    session=session, username=username, action_type=action_type
                )
                max_count = config.get_property(ResourceThresholdRepository.resource_paths[action_type], 10)
                if count < max_count:
                    response = func(session, *args, **kwargs)
                    if count == 0:
                        ResourceThresholdRepository.add_entry(
                            session=session, username=username, action_type=action_type
                        )
                    else:
                        ResourceThresholdRepository.increment_count(
                            session=session, username=username, action_type=action_type
                        )
                    return response
                else:
                    return {'error': None, 'response': 'Error: too many requests'}

            return wrapper

        return decorator
