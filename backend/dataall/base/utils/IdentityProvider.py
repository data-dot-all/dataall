import abc


class IdentityProvider:

    @abc.abstractmethod
    def get_user_emailids_from_group(self, groupName):
        raise NotImplementedError
