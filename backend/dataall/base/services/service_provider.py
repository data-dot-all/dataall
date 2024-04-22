import abc


class ServiceProvider:
    """
    Abstract function to fetch emailds for group
        groupName: str - Group / Team name present in the user pool service provider
    """

    @abc.abstractmethod
    def get_user_emailids_from_group(self, groupName):
        raise NotImplementedError

    """
    Abstract function to fetch groups belonging to a user
        user_id: str - user id information needed by the user pool service provider to fetch groups
     """

    @abc.abstractmethod
    def get_groups_for_user(self, user_id):
        raise NotImplementedError

    """
    Abstract function to list groups
        envname: str - Deployment environment name as specified in the cdk.json
        region: str - Region which is configured in the cdk.json
    """

    @abc.abstractmethod
    def list_groups(self, envname: str, region: str):
        raise NotImplementedError
