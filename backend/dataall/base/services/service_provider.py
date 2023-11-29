import abc


class ServiceProvider:

    @abc.abstractmethod
    def get_user_emailids_from_group(self, groupName):
        raise NotImplementedError

    @abc.abstractmethod
    def get_groups_for_user(self, user_id):
        raise NotImplementedError

    @abc.abstractmethod
    def list_groups(self, envname: str, region: str):
        raise NotImplementedError
